"""Reprise/replay du noyau (Phase 1) — checkpointer EN MÉMOIRE uniquement.

⚠️ LIMITES EXPLICITES — à ne pas confondre avec de la persistance durable :

- `CheckpointMemoire` vit **uniquement en RAM**, dans le processus courant.
  Il est perdu au redémarrage du processus. Ce n'est **pas** PostgreSQL, ni un
  store durable, ni une reprise après véritable redémarrage.
- La reprise ici est une **reprise intra-processus** sur un faux checkpointer.
  Aucun service de persistance n'est ajouté, aucun contrat n'est étendu.

Mécanismes couverts :
- interrupt/resume (arrêt après une étape, reprise ensuite) ;
- double reprise sans duplication (déduplication par `operation_key`) ;
- exception simulée après planification, puis reprise ;
- cohérence des événements/hashs après reprise ;
- invalidation de l'approbation si le payload change.

Aucun réseau, aucun provider, aucune base, aucun conteneur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .events import SequenceurEvenements
from .graph import VERSION_GRAPHE, ResultatRun
from .hashes import hash_objet
from .manifest import construire_manifeste, verifier_manifeste
from .model_adapter import Modele, ModeleMock
from .registry import Registre

ETAPES = ["router", "planner", "executor", "verifier"]


class PanneSimulee(RuntimeError):
    """Exception injectée pour tester la reprise après échec."""


class ApprobationInvalide(PermissionError):
    """L'approbation ne couvre pas le payload courant."""


class RepriseImpossible(RuntimeError):
    """Aucun checkpoint disponible pour ce run."""


@dataclass
class Approbation:
    """Approbation humaine liée à un payload précis.

    Si le payload change, le hash ne correspond plus → approbation invalide.
    """

    payload_sha256: str
    approuve_par: str = "proprietaire"
    horodatage: str = ""

    def valide_pour(self, payload_sha256: str) -> bool:
        return self.payload_sha256 == payload_sha256


@dataclass
class Checkpoint:
    run_id: str
    task_id: str
    prompt: str
    etape: str = "debut"
    plan: dict[str, Any] | None = None
    reponse: str | None = None
    evenements: list[dict[str, Any]] = field(default_factory=list)
    operations_faites: list[str] = field(default_factory=list)
    approbation: dict[str, Any] | None = None

    @property
    def hash_entree(self) -> str:
        return hash_objet({"prompt": self.prompt})


class CheckpointMemoire:
    """Faux checkpointer en mémoire — NON durable, NON persistant.

    Vit dans le processus courant et disparaît à son arrêt.
    """

    def __init__(self) -> None:
        self._store: dict[str, Checkpoint] = {}

    def sauver(self, cp: Checkpoint) -> None:
        # Copie défensive : on ne partage pas la référence mutable.
        self._store[cp.run_id] = Checkpoint(
            run_id=cp.run_id,
            task_id=cp.task_id,
            prompt=cp.prompt,
            etape=cp.etape,
            plan=cp.plan,
            reponse=cp.reponse,
            evenements=list(cp.evenements),
            operations_faites=list(cp.operations_faites),
            approbation=cp.approbation,
        )

    def charger(self, run_id: str) -> Checkpoint | None:
        return self._store.get(run_id)

    def contient(self, run_id: str) -> bool:
        return run_id in self._store


class GrapheReprise:
    """Graphe reprenable : Router → Planner → Executor → Verifier.

    Chaque étape est une *opération* identifiée par une `operation_key`
    déterministe (`{run_id}:{etape}`). Une opération déjà faite n'est jamais
    rejouée : c'est la garantie anti-duplication sur reprise.
    """

    version = VERSION_GRAPHE

    def __init__(
        self,
        modele: Modele | None = None,
        registre: Registre | None = None,
        checkpointer: CheckpointMemoire | None = None,
        approbation: Approbation | None = None,
    ) -> None:
        self.modele = modele or ModeleMock()
        self.registre = registre or Registre()
        self.checkpointer = checkpointer or CheckpointMemoire()
        self.approbation = approbation

    # ------------------------------------------------------------------ API
    def demarrer(
        self,
        run_id: str,
        task_id: str,
        prompt: str,
        arret_apres: str | None = None,
        panne_apres: str | None = None,
    ) -> ResultatRun | None:
        """Démarre un run. Renvoie None si arrêté/échoué (checkpoint sauvegardé)."""
        cp = Checkpoint(run_id=run_id, task_id=task_id, prompt=prompt)
        self.checkpointer.sauver(cp)
        return self._avancer(cp, arret_apres, panne_apres)

    def reprendre(
        self,
        run_id: str,
        arret_apres: str | None = None,
        panne_apres: str | None = None,
    ) -> ResultatRun | None:
        """Reprend depuis le dernier checkpoint. Idempotent si déjà terminé."""
        cp = self.checkpointer.charger(run_id)
        if cp is None:
            raise RepriseImpossible(f"Aucun checkpoint pour {run_id!r}")
        if cp.etape == "termine":
            # Double reprise : on renvoie le résultat sans rejouer d'opération.
            return self._resultat(cp)
        return self._avancer(cp, arret_apres, panne_apres)

    # ------------------------------------------------------------- interne
    def _avancer(
        self,
        cp: Checkpoint,
        arret_apres: str | None,
        panne_apres: str | None,
    ) -> ResultatRun | None:
        seq = SequenceurEvenements.depuis_journal(cp.run_id, cp.evenements)

        for etape in ETAPES:
            if self._deja_faite(cp, etape):
                continue
            self._executer_etape(cp, seq, etape)
            cp.etape = etape
            cp.evenements = seq.journal_dict()
            self.checkpointer.sauver(cp)

            if panne_apres == etape:
                raise PanneSimulee(f"panne simulée après {etape!r}")
            if arret_apres == etape:
                return None  # interrupt : checkpoint sauvegardé, run suspendu

        cp.etape = "termine"
        cp.evenements = seq.journal_dict()
        self.checkpointer.sauver(cp)
        return self._resultat(cp)

    @staticmethod
    def _deja_faite(cp: Checkpoint, etape: str) -> bool:
        return f"{cp.run_id}:{etape}" in cp.operations_faites

    def _executer_etape(self, cp: Checkpoint, seq: SequenceurEvenements, etape: str) -> None:
        if etape == "router":
            seq.emettre("run_demarre", "control_plane", cp.task_id,
                        {"prompt_sha256": cp.hash_entree})
            seq.emettre("task_demarree", "control_plane", cp.task_id)

        elif etape == "planner":
            cp.plan = {"etapes": ["modeliser", "verifier"], "outils_requis": []}
            seq.emettre("politique_appliquee", "control_plane", cp.task_id,
                        {"outils_requis": [], "registre_actifs": self.registre.lister_actives()})

        elif etape == "executor":
            # Barrière d'approbation : si une approbation existe, elle doit
            # couvrir le payload courant, sinon refus.
            if self.approbation is not None and not self.approbation.valide_pour(cp.hash_entree):
                seq.emettre("approbation_refusee", "control_plane", cp.task_id,
                            {"motif": "payload modifié depuis l'approbation"})
                cp.evenements = seq.journal_dict()
                self.checkpointer.sauver(cp)
                raise ApprobationInvalide(
                    "Approbation invalide : le payload a changé depuis l'approbation."
                )
            if self.approbation is not None:
                seq.emettre("approbation_accordee", "control_plane", cp.task_id,
                            {"approuve_par": self.approbation.approuve_par})
            seq.emettre("modele_appele", "execution_plane", cp.task_id, {"alias": self.modele.alias})
            cp.reponse = self.modele.completer(cp.prompt)
            seq.emettre("outil_resultat", "execution_plane", cp.task_id,
                        {"reponse_sha256": hash_objet({"reponse": cp.reponse})})

        elif etape == "verifier":
            manifeste = construire_manifeste(
                cp.run_id, cp.task_id, self.version, self.modele.alias,
                cp.prompt, cp.reponse or "", seq.journal_dict(),
            )
            seq.emettre("task_terminee", "control_plane", cp.task_id,
                        {"sha256_manifeste": manifeste["sha256_manifeste"]})
            seq.emettre("run_termine", "control_plane", cp.task_id)

        cp.operations_faites.append(f"{cp.run_id}:{etape}")

    def _resultat(self, cp: Checkpoint) -> ResultatRun:
        manifeste = construire_manifeste(
            cp.run_id, cp.task_id, self.version, self.modele.alias,
            cp.prompt, cp.reponse or "", cp.evenements,
        )
        return ResultatRun(
            run_id=cp.run_id,
            task_id=cp.task_id,
            reponse=cp.reponse or "",
            manifeste=manifeste,
            evenements=cp.evenements,
        )


def verifier_coherence(resultat: ResultatRun) -> bool:
    """Vérifie la cohérence du manifeste et des identifiants d'événements."""
    if not verifier_manifeste(resultat.manifeste):
        return False
    ids = [e["id"] for e in resultat.evenements]
    if len(ids) != len(set(ids)):  # pas de doublon d'id
        return False
    attendus = [f"{resultat.run_id}-e{i:03d}" for i in range(1, len(ids) + 1)]
    return ids == attendus  # séquence continue, sans trou
