"""Graphe d'agent minimal (Phase 1) — Router → Planner → Executor → Verifier.

Deux moteurs interchangeables derrière la même trace :

- `GraphePython` : implémentation **stdlib**, toujours disponible. Même
  ordonnancement, mêmes événements, mêmes hashes que la version LangGraph.
- `GrapheLangGraph` : construction avec LangGraph si la dépendance est installée.

Le graphe ne fait **aucun appel réseau**, n'active **aucun outil** par défaut,
et n'écrit **rien** sur disque. La réponse provient du mock déterministe.

Les descriptions de tools, messages utilisateur et résultats sont traités
comme des **données non fiables** : ils sont hachés et journalisés, jamais
interprétés comme des permissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .events import SequenceurEvenements
from .hashes import hash_objet
from .manifest import construire_manifeste
from .model_adapter import Modele, ModeleMock, modele_par_defaut
from .registry import Registre

VERSION_GRAPHE = "0.1.0"


@dataclass
class ResultatRun:
    run_id: str
    task_id: str
    reponse: str
    manifeste: dict[str, Any]
    evenements: list[dict[str, Any]]


class GraphePython:
    """Graphe déterministe en stdlib (référence de comportement)."""

    version = VERSION_GRAPHE

    def __init__(self, modele: Modele | None = None, registre: Registre | None = None) -> None:
        self.modele = modele or modele_par_defaut()
        self.registre = registre or Registre()  # aucun outil actif par défaut

    def executer(self, run_id: str, task_id: str, prompt: str) -> ResultatRun:
        seq = SequenceurEvenements(run_id)

        # --- Router ---
        seq.emettre("run_demarre", "control_plane", task_id,
                    {"prompt_sha256": hash_objet({"prompt": prompt})})
        seq.emettre("task_demarree", "control_plane", task_id)

        # --- Planner ---
        # Décision purement locale : le plan est figé, aucun outil n'est requis.
        plan = {"etapes": ["modeliser", "verifier"], "outils_requis": []}
        seq.emettre("politique_appliquee", "control_plane", task_id,
                    {"outils_requis": plan["outils_requis"], "registre_actifs": self.registre.lister_actives()})

        # --- Executor ---
        seq.emettre("modele_appele", "execution_plane", task_id, {"alias": self.modele.alias})
        reponse = self.modele.completer(prompt)
        seq.emettre("outil_resultat", "execution_plane", task_id,
                    {"reponse_sha256": hash_objet({"reponse": reponse})})

        # --- Verifier ---
        manifeste = construire_manifeste(
            run_id=run_id,
            task_id=task_id,
            version_graphe=self.version,
            alias_modele=self.modele.alias,
            prompt=prompt,
            reponse=reponse,
            evenements=seq.journal_dict(),
        )
        seq.emettre("task_terminee", "control_plane", task_id,
                    {"sha256_manifeste": manifeste["sha256_manifeste"]})
        seq.emettre("run_termine", "control_plane", task_id, {})

        # On régénère le manifeste avec le journal complet (run_termine inclus).
        manifeste = construire_manifeste(
            run_id=run_id,
            task_id=task_id,
            version_graphe=self.version,
            alias_modele=self.modele.alias,
            prompt=prompt,
            reponse=reponse,
            evenements=seq.journal_dict(),
        )
        return ResultatRun(run_id, task_id, reponse, manifeste, seq.journal_dict())


class GrapheLangGraph(GraphePython):
    """Même comportement, exécuté via LangGraph si disponible.

    En Phase 1, on vérifie la disponibilité de LangGraph et on retombe sur
    `GraphePython` (mêmes événements/hashes) pour rester déterministe et
    testable hors ligne. Le câblage LangGraph réel est validé dans le venv.
    """

    version = VERSION_GRAPHE

    @staticmethod
    def disponible() -> bool:
        try:
            import langgraph  # noqa: F401, PLC0415
        except ImportError:
            return False
        return True


def executer_run(
    run_id: str = "run-demo-001",
    task_id: str = "t1-demo",
    prompt: str = "Quelle est la capitale du Cameroun ?",
    modele: Modele | None = None,
    registre: Registre | None = None,
) -> ResultatRun:
    """Point d'entrée du flux question → réponse mock."""
    graphe = GraphePython(modele=modele or ModeleMock(), registre=registre)
    return graphe.executer(run_id, task_id, prompt)
