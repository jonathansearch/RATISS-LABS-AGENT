"""Manifeste de run synthétique (Phase 1).

⚠️ AVERTISSEMENT EXPLICITE : ce manifeste est une **trace synthétique de
démonstration**. Ce n'est PAS un manifeste scellé par RATISS-Framework, ni une
preuve scientifique, ni un résultat de production. Le champ `moteur` vaut
`"ratiss-agent-demo"` et `scelle` reste `False` pour éviter toute confusion.

Le manifeste relie au minimum, comme exigé :
task_id, run/trace id, version du graphe, alias mock, hash d'entrée,
hash de sortie et événements séquencés.
"""

from __future__ import annotations

from typing import Any

from .hashes import hash_objet


def construire_manifeste(
    run_id: str,
    task_id: str,
    version_graphe: str,
    alias_modele: str,
    prompt: str,
    reponse: str,
    evenements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Construit un manifeste déterministe à partir des artefacts du run."""
    hash_entree = hash_objet({"prompt": prompt})
    hash_sortie = hash_objet({"reponse": reponse})
    corps = {
        "run_id": run_id,
        "task_id": task_id,
        "version_graphe": version_graphe,
        "alias_modele": alias_modele,
        "hash_entree": hash_entree,
        "hash_sortie": hash_sortie,
        "evenements": evenements,
    }
    return {
        "moteur": "ratiss-agent-demo",
        "scelle": False,
        "avertissement": (
            "Trace synthétique de démonstration. Non scellée, non scientifique, "
            "non matérielle. Ne pas confondre avec un manifeste RATISS-Framework."
        ),
        "sha256_manifeste": hash_objet(corps),
        **corps,
    }


def verifier_manifeste(manifeste: dict[str, Any]) -> bool:
    """Revérifie le hash du manifeste. Détecte toute altération."""
    corps = {
        "run_id": manifeste["run_id"],
        "task_id": manifeste["task_id"],
        "version_graphe": manifeste["version_graphe"],
        "alias_modele": manifeste["alias_modele"],
        "hash_entree": manifeste["hash_entree"],
        "hash_sortie": manifeste["hash_sortie"],
        "evenements": manifeste["evenements"],
    }
    return hash_objet(corps) == manifeste["sha256_manifeste"]
