"""Graphe LangGraph réel (Phase 1) — Router → Planner → Executor → Verifier.

Ce module construit un **vrai** `StateGraph` LangGraph (nœuds + arêtes), avec
un état typé et un réducteur d'accumulation pour le journal d'événements.
Il produit exactement les mêmes événements, hashes et manifeste que
`GraphePython`, ce qui permet de comparer les deux moteurs.

Import de `langgraph` **différé** : ce module reste importable sans la
dépendance ; seule la construction du graphe l'exige.

Aucun réseau, aucun outil, aucune écriture disque.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from .events import SequenceurEvenements
from .graph import VERSION_GRAPHE, ResultatRun
from .hashes import hash_objet
from .manifest import construire_manifeste
from .model_adapter import Modele
from .registry import Registre


class EtatNoyau(TypedDict, total=False):
    """État traversant le graphe. `evenements` s'accumule via `operator.add`."""

    prompt: str
    plan: dict[str, Any]
    reponse: str
    evenements: Annotated[list[dict[str, Any]], operator.add]
    sha256_manifeste: str


def _construire(
    modele: Modele,
    registre: Registre,
    run_id: str,
    task_id: str,
    seq: SequenceurEvenements,
):
    def noeud_router(etat: EtatNoyau) -> dict[str, Any]:
        e1 = seq.emettre(
            "run_demarre", "control_plane", task_id,
            {"prompt_sha256": hash_objet({"prompt": etat["prompt"]})},
        )
        e2 = seq.emettre("task_demarree", "control_plane", task_id)
        return {"evenements": [e1.to_dict(), e2.to_dict()]}

    def noeud_planner(etat: EtatNoyau) -> dict[str, Any]:
        plan = {"etapes": ["modeliser", "verifier"], "outils_requis": []}
        e = seq.emettre(
            "politique_appliquee", "control_plane", task_id,
            {"outils_requis": plan["outils_requis"], "registre_actifs": registre.lister_actives()},
        )
        return {"plan": plan, "evenements": [e.to_dict()]}

    def noeud_executor(etat: EtatNoyau) -> dict[str, Any]:
        e1 = seq.emettre("modele_appele", "execution_plane", task_id, {"alias": modele.alias})
        reponse = modele.completer(etat["prompt"])
        e2 = seq.emettre(
            "outil_resultat", "execution_plane", task_id,
            {"reponse_sha256": hash_objet({"reponse": reponse})},
        )
        return {"reponse": reponse, "evenements": [e1.to_dict(), e2.to_dict()]}

    def noeud_verifier(etat: EtatNoyau) -> dict[str, Any]:
        manifeste = construire_manifeste(
            run_id, task_id, VERSION_GRAPHE, modele.alias,
            etat["prompt"], etat["reponse"], seq.journal_dict(),
        )
        e1 = seq.emettre(
            "task_terminee", "control_plane", task_id,
            {"sha256_manifeste": manifeste["sha256_manifeste"]},
        )
        e2 = seq.emettre("run_termine", "control_plane", task_id)
        manifeste = construire_manifeste(
            run_id, task_id, VERSION_GRAPHE, modele.alias,
            etat["prompt"], etat["reponse"], seq.journal_dict(),
        )
        return {
            "sha256_manifeste": manifeste["sha256_manifeste"],
            "evenements": [e1.to_dict(), e2.to_dict()],
        }

    from langgraph.graph import END, START, StateGraph  # noqa: PLC0415

    g = StateGraph(EtatNoyau)
    g.add_node("router", noeud_router)
    g.add_node("planner", noeud_planner)
    g.add_node("executor", noeud_executor)
    g.add_node("verifier", noeud_verifier)
    g.add_edge(START, "router")
    g.add_edge("router", "planner")
    g.add_edge("planner", "executor")
    g.add_edge("executor", "verifier")
    g.add_edge("verifier", END)
    return g.compile()


def executer_langgraph(
    run_id: str,
    task_id: str,
    prompt: str,
    modele: Modele,
    registre: Registre | None = None,
) -> ResultatRun:
    """Exécute le flux via un vrai StateGraph LangGraph."""
    registre = registre or Registre()
    seq = SequenceurEvenements(run_id)
    graphe = _construire(modele, registre, run_id, task_id, seq)
    etat_final = graphe.invoke({"prompt": prompt})

    manifeste = construire_manifeste(
        run_id, task_id, VERSION_GRAPHE, modele.alias,
        prompt, etat_final["reponse"], seq.journal_dict(),
    )
    return ResultatRun(
        run_id=run_id,
        task_id=task_id,
        reponse=etat_final["reponse"],
        manifeste=manifeste,
        evenements=seq.journal_dict(),
    )
