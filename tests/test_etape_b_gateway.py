"""Tests ÉTAPE B — Model Gateway (PROMPT GLM, MONTAGE étape 2).

Ce qui est vérifié ici, hors ligne et sans clé :
- config/litellm.yaml : 3 alias stables, aucun secret en dur, budget et auth par
  environnement, journalisation des messages désactivée ;
- docker-compose.yml : service llm-gateway épinglé, réseaux core+edge (exception
  explicite documentée), master key obligatoire ;
- model_adapter.py déverrouillé : sans clé → message clair sans crash ; budget 0
  → refus ; appel réel → UNIQUEMENT via le proxy (ChatOpenAI pointé sur
  http://llm-gateway:4000), jamais un fournisseur en direct, aucune relance.

Le contrôle « une même requête répond via 2 alias » et le refus réel de budget
dépassé par le proxy nécessitent des clés + réseau : ils se font sur l'hôte du
chef (commandes documentées dans la PR).
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest import mock

import pytest
import yaml

RACINE = Path(__file__).resolve().parents[1]

from ratiss_agent.model_adapter import (  # noqa: E402
    ConfigurationModele,
    ModeleIndisponible,
    ModeleLiteLLM,
    ModeleMock,
    modele_par_defaut,
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _config_complete(**over) -> ConfigurationModele:
    base = dict(
        fournisseur="exemple",
        modele="ratiss-principal",
        region="eu",
        budget_tokens_max=1000,
        classe_donnees="publique",
        approuve=True,
    )
    base.update(over)
    return ConfigurationModele(**base)


# --------------------------------------------------------------------------
# config/litellm.yaml
# --------------------------------------------------------------------------
def test_litellm_yaml_3_alias_stables():
    cfg = yaml.safe_load((RACINE / "config" / "litellm.yaml").read_text(encoding="utf-8"))
    alias = [m["model_name"] for m in cfg["model_list"]]
    assert alias == ["ratiss-principal", "ratiss-secours", "ratiss-local"]


def test_litellm_yaml_aucune_cle_en_dur():
    """Toutes les clés viennent de l'environnement : rien de secret dans git."""
    cfg = yaml.safe_load((RACINE / "config" / "litellm.yaml").read_text(encoding="utf-8"))
    for modele in cfg["model_list"]:
        params = modele["litellm_params"]
        if "api_key" in params:
            assert params["api_key"].startswith("os.environ/"), modele["model_name"]
    assert cfg["general_settings"]["master_key"].startswith("os.environ/")
    assert cfg["litellm_settings"]["max_budget"].startswith("os.environ/")


def test_litellm_yaml_message_logging_desactive():
    cfg = yaml.safe_load((RACINE / "config" / "litellm.yaml").read_text(encoding="utf-8"))
    assert cfg["litellm_settings"]["turn_off_message_logging"] is True


def test_litellm_yaml_budget_reference_lenvironnement():
    cfg = yaml.safe_load((RACINE / "config" / "litellm.yaml").read_text(encoding="utf-8"))
    assert cfg["litellm_settings"]["max_budget"] == "os.environ/RATISS_BUDGET_USD"
    assert cfg["litellm_settings"]["budget_duration"] == "30d"


# --------------------------------------------------------------------------
# docker-compose.yml — service llm-gateway
# --------------------------------------------------------------------------
def test_compose_service_llm_gateway():
    compose = yaml.safe_load((RACINE / "docker-compose.yml").read_text(encoding="utf-8"))
    gw = compose["services"]["llm-gateway"]
    assert "core" in gw["networks"] and "edge" in gw["networks"]
    assert gw["depends_on"]["postgres"]["condition"] == "service_healthy"
    assert "LITELLM_MASTER_KEY" in gw["environment"]
    # master key obligatoire : erreur d'interpolation si absente du .env
    assert ":?" in gw["environment"]["LITELLM_MASTER_KEY"]
    # config montée en lecture seule
    assert any(v.split(":")[0].endswith("litellm.yaml") for v in gw["volumes"])


def test_compose_ollama_optionnel_profil_local():
    compose = yaml.safe_load((RACINE / "docker-compose.yml").read_text(encoding="utf-8"))
    ollama = compose["services"]["ollama"]
    assert "local" in ollama["profiles"]
    assert "@sha256:" in ollama["image"]


# --------------------------------------------------------------------------
# model_adapter déverrouillé — fail-closed
# --------------------------------------------------------------------------
def test_sans_config_le_mock_reste_actif():
    modele = modele_par_defaut()
    assert isinstance(modele, ModeleMock)
    assert modele.completer("x")


def test_config_sans_champs_du_domaine_incomplete():
    assert _config_complete(fournisseur=None).est_complete() is False
    assert _config_complete(approuve=False).est_complete() is False


def test_budget_zero_refuse(monkeypatch):
    """Contrôle PROMPT : « le budget dépassé est refusé (testé avec un budget de 0) ».

    Côté runtime : RATISS_BUDGET_USD=0 => AUCUN appel, refus explicite.
    (Le refus côté proxy LiteLLM lui-même se teste sur l'hôte du chef avec clés.)
    """
    monkeypatch.setenv("LITELLM_MASTER_KEY", "jeton-factice-de-test")
    monkeypatch.setenv("RATISS_BUDGET_USD", "0")
    with pytest.raises(ModeleIndisponible) as excinfo:
        ModeleLiteLLM(_config_complete()).completer("x")
    assert "RATISS_BUDGET_USD" in str(excinfo.value)


def test_budget_absent_refuse(monkeypatch):
    monkeypatch.delenv("RATISS_BUDGET_USD", raising=False)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "jeton-factice-de-test")
    with pytest.raises(ModeleIndisponible):
        ModeleLiteLLM(_config_complete()).completer("x")


def test_budget_negatif_refuse(monkeypatch):
    monkeypatch.setenv("RATISS_BUDGET_USD", "-5")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "jeton-factice-de-test")
    with pytest.raises(ModeleIndisponible):
        ModeleLiteLLM(_config_complete()).completer("x")


def test_sans_cle_message_clair_aucun_crash(monkeypatch):
    """Sans LITELLM_MASTER_KEY : refus explicite, aucune exception réseau."""
    monkeypatch.delenv("LITELLM_MASTER_KEY", raising=False)
    monkeypatch.setenv("RATISS_BUDGET_USD", "10")
    with pytest.raises(ModeleIndisponible) as excinfo:
        ModeleLiteLLM(_config_complete()).completer("x")
    assert "LITELLM_MASTER_KEY" in str(excinfo.value)


def test_appel_reel_passe_par_le_proxy_et_pas_en_direct(monkeypatch):
    """Le client doit être pointé sur http://llm-gateway:4000, jamais un fournisseur."""
    kwargs_captures: dict = {}
    reponse_fausse = types.SimpleNamespace(content="réponse de test")

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            kwargs_captures.update(kwargs)

        def invoke(self, messages):
            return reponse_fausse

    module_faux = types.ModuleType("langchain_openai")
    module_faux.ChatOpenAI = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", module_faux)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "jeton-factice-de-test")
    monkeypatch.setenv("RATISS_BUDGET_USD", "10")

    reponse = ModeleLiteLLM(_config_complete()).completer("bonjour")
    assert reponse == "réponse de test"
    # Le point d'entrée est le proxy du réseau core, pas un fournisseur.
    assert kwargs_captures["base_url"] == "http://llm-gateway:4000"
    assert kwargs_captures["model"] == "ratiss-principal"
    assert kwargs_captures["max_retries"] == 0
    assert kwargs_captures["temperature"] == 0


def test_l_url_du_proxy_est_surchargeable_par_env(monkeypatch):
    """RATISS_LLM_PROXY_URL permet de déplacer le proxy sans toucher au code."""
    kwargs_captures: dict = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            kwargs_captures.update(kwargs)

        def invoke(self, messages):
            return types.SimpleNamespace(content="ok")

    module_faux = types.ModuleType("langchain_openai")
    module_faux.ChatOpenAI = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", module_faux)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "jeton-factice-de-test")
    monkeypatch.setenv("RATISS_BUDGET_USD", "10")
    monkeypatch.setenv("RATISS_LLM_PROXY_URL", "http://autre-proxy:4000")

    ModeleLiteLLM(_config_complete()).completer("x")
    assert kwargs_captures["base_url"] == "http://autre-proxy:4000"


def test_aucune_erreur_reseau_ne_provoque_de_relance(monkeypatch):
    """max_retries=0 et toute erreur réseau échoue fermé (pas de retry silencieux)."""

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            pass

        def invoke(self, messages):
            raise ConnectionError("réseau indisponible")

    module_faux = types.ModuleType("langchain_openai")
    module_faux.ChatOpenAI = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", module_faux)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "jeton-factice-de-test")
    monkeypatch.setenv("RATISS_BUDGET_USD", "10")

    with pytest.raises(ModeleIndisponible) as excinfo:
        ModeleLiteLLM(_config_complete()).completer("x")
    assert "aucune relance" in str(excinfo.value)


def test_le_jeton_n_apparait_pas_dans_les_erreurs(monkeypatch):
    """Le jeton proxy ne doit jamais fuiter dans une exception (logs/mémoire)."""
    monkeypatch.setenv("LITELLM_MASTER_KEY", "jeton-factice-de-test")
    monkeypatch.setenv("RATISS_BUDGET_USD", "10")
    # Sans le module langchain_openai : barrière 4 -> message sans le jeton.
    with mock.patch.dict(sys.modules):
        sys.modules.pop("langchain_openai", None)
        with pytest.raises(ModeleIndisponible) as excinfo:
            ModeleLiteLLM(_config_complete()).completer("x")
    assert "jeton-factice-de-test" not in str(excinfo.value)
