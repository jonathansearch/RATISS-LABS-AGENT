"""Adaptateur de modèle (Phase 1) — mock déterministe + LiteLLM désactivé.

Deux implémentations derrière une même interface :

- `ModeleMock` : déterministe, hors ligne, sans clé ni réseau. Réponse calculée
  par hachage de l'entrée → strictement reproductible.
- `ModeleLiteLLM` : appelle un fournisseur externe via LiteLLM, mais **échoue
  fermé** tant que la configuration n'est pas explicitement fournie
  (fournisseur, modèle, budget, approbation). Aucun appel par défaut.

Le brief impose : *tout appel modèle externe doit échouer fermé si le budget,
l'approbation, l'auth, l'isolation ou la configuration requise manque.*
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .hashes import hash_objet


class ModeleIndisponible(RuntimeError):
    """Levée quand le provider externe n'est pas configuré/approuvé."""


@dataclass(frozen=True)
class ConfigurationModele:
    """Configuration explicite requise pour un provider externe.

    Tant qu'un seul champ manque, le provider reste désactivé.
    """

    fournisseur: str | None = None
    modele: str | None = None
    region: str | None = None
    budget_tokens_max: int | None = None
    approuve: bool = False
    classe_donnees: str | None = None

    def est_complete(self) -> bool:
        return bool(
            self.fournisseur
            and self.modele
            and self.region
            and self.budget_tokens_max
            and self.classe_donnees
            and self.approuve
        )


class Modele(Protocol):
    alias: str
    version: str

    def completer(self, prompt: str) -> str: ...


class ModeleMock:
    """Modèle factice déterministe et hors ligne.

    La réponse est fonction pure du prompt : aucun état, aucun réseau,
    aucune source d'aléa. Deux exécutions identiques → réponse identique.
    """

    alias = "mock"
    version = "0.1.0"

    def completer(self, prompt: str) -> str:
        empreinte = hash_objet({"prompt": prompt, "alias": self.alias, "v": self.version})
        return (
            "[RÉPONSE MOCK SYNTHÉTIQUE — non scientifique, non matérielle] "
            f"requête reçue (sha256={empreinte[:16]}…). "
            "Aucun fournisseur externe n'a été contacté."
        )


class ModeleLiteLLM:
    """Passerelle LiteLLM — désactivée tant que la config n'est pas complète.

    Note : l'import de `litellm` est **différé** (à l'intérieur de `completer`),
    afin que ce module reste importable et testable sans la dépendance.
    """

    alias = "litellm"

    def __init__(self, config: ConfigurationModele) -> None:
        self.config = config
        self.version = "1.103.2"  # version épinglée visée

    def completer(self, prompt: str) -> str:
        # Barrière 1 : configuration complète exigée.
        if not self.config.est_complete():
            raise ModeleIndisponible(
                "Provider externe bloqué : configuration incomplète "
                "(fournisseur, modèle, région, budget, classe de données, approbation)."
            )
        # Barrière 2 : dépendance disponible exigée.
        try:
            import litellm  # noqa: PLC0415
        except ImportError as e:  # pragma: no cover - dépend du venv
            raise ModeleIndisponible(
                "Provider externe bloqué : litellm n'est pas installé dans cet environnement."
            ) from e
        # Barrière 3 : jamais d'appel implicite. Le propriétaire doit fournir
        # la clé hors bande (BYOK). Ici, on refuse tout de même l'appel réel.
        raise ModeleIndisponible(
            "Appel modèle externe refusé en Phase 1 (aucune clé transmise, BYOK non configuré)."
        )
        # pragma: no cover
        return litellm.completion(  # noqa: ARG001
            model=self.config.modele, messages=[{"role": "user", "content": prompt}]
        )


def modele_par_defaut(config: ConfigurationModele | None = None) -> Modele:
    """Renvoie le mock sauf si une config externe complète est fournie."""
    if config is not None and config.est_complete():
        return ModeleLiteLLM(config)
    return ModeleMock()
