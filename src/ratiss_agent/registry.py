"""Registre statique d'outils (Phase 1).

Principes imposés par le brief :
- **Aucun outil n'est activé par défaut.** L'ensemble des outils activés est vide.
- Un outil inconnu ou désactivé est **refusé**.
- Une *capability* (effet de bord) non accordée est **refusée**.
- Toute description d'outil est une **donnée non fiable** : elle ne confère
  aucune permission. Seule la table statique ci-dessous fait foi.

Aucun outil dangereux n'est présent (shell, Python, filesystem écriture,
navigateur, GitHub write, Discord, QPU) : ils sont absents par construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CAPABILITIES_AUTORISEES = {
    "lecture_fichier",
    "ecriture_fichier",
    "reseau_sortant",
    "execution_code",
    "git_push",
    "ecriture_base",
}


class OutilRefuse(PermissionError):
    """Levée quand un outil est inconnu, désactivé ou dépourvu de capability."""


@dataclass(frozen=True)
class Outil:
    nom: str
    description: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    # Non fiable : purement informatif, ne donne jamais de droit.
    note_non_fiable: str = ""


# Registre statique : deux outils purs, à titre d'exemple.
# Tout autre nom est inconnu → refusé.
_REGISTRE: dict[str, Outil] = {
    "echo": Outil(
        nom="echo",
        description="Retourne la chaîne fournie, sans effet de bord.",
        capabilities=frozenset(),
        note_non_fiable="description non fiable : n'accorde aucune permission",
    ),
    "compte_mots": Outil(
        nom="compte_mots",
        description="Compte le nombre de mots d'une chaîne.",
        capabilities=frozenset(),
    ),
}


class Registre:
    """Registre statique. Les outils activés sont vides par défaut."""

    def __init__(
        self,
        outils_actives: set[str] | None = None,
        capabilities_accordees: dict[str, set[str]] | None = None,
    ) -> None:
        self._registre = dict(_REGISTRE)
        # Par défaut : AUCUN outil activé.
        self._actives: set[str] = set(outils_actives or set())
        self._capabilities: dict[str, set[str]] = capabilities_accordees or {}

    def lister(self) -> list[str]:
        return sorted(self._registre)

    def lister_actives(self) -> list[str]:
        return sorted(self._actives)

    def resoudre(self, nom: str) -> Outil:
        """Résout un outil vers sa définition statique, en appliquant les refus."""
        if nom not in self._registre:
            raise OutilRefuse(f"Outil inconnu : {nom!r}")
        outil = self._registre[nom]
        if nom not in self._actives:
            raise OutilRefuse(f"Outil désactivé : {nom!r} (aucun outil actif par défaut)")

        accordees = self._capabilities.get(nom, set())
        non_accordees = outil.capabilities - accordees
        if non_accordees:
            raise OutilRefuse(
                f"Capability non accordée pour {nom!r} : {sorted(non_accordees)}"
            )
        return outil

    def executer(self, nom: str, args: dict[str, Any]) -> dict[str, Any]:
        """Exécute un outil **pur** activé. Aucun effet de bord n'est possible."""
        outil = self.resoudre(nom)
        if outil.nom == "echo":
            return {"resultat": str(args.get("texte", ""))}
        if outil.nom == "compte_mots":
            texte = str(args.get("texte", ""))
            return {"mots": len(texte.split())}
        # Un outil activé sans branche d'exécution est un refus explicite.
        raise OutilRefuse(f"Aucune exécution définie pour {nom!r}")
