"""Adaptateur de modèle (Phase 1 + ÉTAPE B) — mock déterministe + proxy LiteLLM.

Deux implémentations derrière une même interface :

- `ModeleMock` : déterministe, hors ligne, sans clé ni réseau. Réponse calculée
  par hachage de l'entrée → strictement reproductible.
- `ModeleLiteLLM` : appelle un fournisseur externe UNIQUEMENT via le proxy
  `llm-gateway` (config/litellm.yaml) — jamais un fournisseur en direct —
  et **échoue fermé** tant que la configuration, la clé proxy (`LITELLM_MASTER_KEY`)
  et un budget strictement positif ne sont pas explicitement fournis.

Le brief impose : *tout appel modèle externe doit échouer fermé si le budget,
l'approbation, l'auth, l'isolation ou la configuration requise manque.*

Règle BYOK (ÉTAPE B) : le jeton du proxy est lu depuis l'environnement au
moment de l'appel. Il n'est jamais porté par `ConfigurationModele`, jamais
sérialisé dans l'état LangGraph, les événements ou le manifeste.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from .hashes import hash_objet

# Adresse du proxy par défaut (réseau Docker `core` du socle).
API_BASE_PROXY_DEFAUT = "http://llm-gateway:4000"


class ModeleIndisponible(RuntimeError):
    """Levée quand le provider externe n'est pas configuré/approuvé."""


@dataclass(frozen=True)
class ConfigurationModele:
    """Configuration explicite requise pour un provider externe.

    Tant qu'un seul champ manque, le provider reste désactivé.
    Cette structure ne porte AUCUN secret ni paramètre de dépense (test BYOK :
    aucun champ `cle`/`api_key`) : le jeton du proxy et le plafond USD sont lus
    dans l'environnement au moment de l'appel (LITELLM_MASTER_KEY,
    RATISS_BUDGET_USD) — c'est la décision opérateur, hors code.
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
            import litellm  # noqa: F401, PLC0415
        except ImportError as e:  # pragma: no cover - dépend du venv
            raise ModeleIndisponible(
                "Provider externe bloqué : litellm n'est pas installé dans cet environnement."
            ) from e
        # Barrière 3 (ÉTAPE B, déverrouillage) : la clé du proxy vient de
        # l'ENVIRONNEMENT, jamais de la config ni du code. Absente => refus.
        jeton = os.environ.get("LITELLM_MASTER_KEY")
        if not jeton:
            raise ModeleIndisponible(
                "Provider externe bloqué : LITELLM_MASTER_KEY absente de l'environnement "
                "(BYOK non configuré). Aucun appel envoyé."
            )
        # Barrière 3-bis : plafond de dépense exigé, STRICTEMENT positif.
        # Budget 0 ou absent => tout appel est refusé (contrôle PROMPT étape B).
        brut_budget = os.environ.get("RATISS_BUDGET_USD")
        try:
            budget = float(brut_budget) if brut_budget is not None else None
        except ValueError as e:
            raise ModeleIndisponible(
                "Provider externe bloqué : RATISS_BUDGET_USD n'est pas un nombre "
                f"valide ({brut_budget!r}). Aucun appel envoyé."
            ) from e
        if budget is None or budget <= 0:
            raise ModeleIndisponible(
                "Provider externe bloqué : RATISS_BUDGET_USD absent ou <= 0 "
                "(aucun budget autorisé). Aucun appel envoyé."
            )
        # Barrière 4 : le client ChatOpenAI (recette officielle LiteLLM) doit être
        # installé. Import différé pour rester testable sans la dépendance.
        try:
            from langchain_openai import ChatOpenAI  # noqa: PLC0415
        except ImportError as e:
            raise ModeleIndisponible(
                "Provider externe bloqué : langchain-openai n'est pas installé "
                "(voir requirements-phase1.txt)."
            ) from e
        # Appel réel — UNIQUEMENT via le proxy (jamais un fournisseur en direct),
        # sans relance automatique, température 0 pour la reproductibilité.
        chat = ChatOpenAI(
            model=self.config.modele,
            api_key=jeton,
            base_url=os.environ.get("RATISS_LLM_PROXY_URL", API_BASE_PROXY_DEFAUT),
            temperature=0,
            timeout=30,
            max_retries=0,
        )
        try:
            reponse = chat.invoke([("user", prompt)])
        except Exception as e:  # noqa: BLE001 - toute erreur réseau/fournisseur échoue fermé
            raise ModeleIndisponible(
                f"Appel modèle via le proxy échoué (aucune relance automatique) : {e}"
            ) from e
        contenu = getattr(reponse, "content", None)
        if contenu is None:
            raise ModeleIndisponible("Réponse du proxy sans contenu exploitable.")
        return str(contenu)


def modele_par_defaut(config: ConfigurationModele | None = None) -> Modele:
    """Renvoie le mock sauf si une config externe complète est fournie."""
    if config is not None and config.est_complete():
        return ModeleLiteLLM(config)
    return ModeleMock()
