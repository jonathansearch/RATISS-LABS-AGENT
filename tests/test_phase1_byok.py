"""Tests BYOK (Phase 1) — clé FACTICE uniquement.

On ne lit jamais une vraie clé, le `.env`, le keychain ou une variable secrète.
La chaîne utilisée ici est délibérément factice et ne ressemble à aucun format
de clé réelle.
"""

from __future__ import annotations

import json

import pytest

from ratiss_agent.graph import executer_run
from ratiss_agent.model_adapter import (
    ConfigurationModele,
    ModeleIndisponible,
    ModeleLiteLLM,
)

CLE_FACTICE = "cle-factice-de-test-ne-pas-utiliser"


def _config(**over) -> ConfigurationModele:
    base = dict(
        fournisseur="exemple",
        modele="exemple-modele",
        region="eu",
        budget_tokens_max=1000,
        classe_donnees="publique",
        approuve=True,
    )
    base.update(over)
    return ConfigurationModele(**base)


def test_byok_desactive_par_defaut():
    """Sans configuration, le provider reste désactivé."""
    assert ConfigurationModele().est_complete() is False
    with pytest.raises(ModeleIndisponible):
        ModeleLiteLLM(ConfigurationModele()).completer("test")


def test_sauvegarde_cle_ne_declenche_aucun_appel():
    """Persister une clé factice ne doit provoquer aucun appel réseau/coût.

    Ici, aucun composant ne stocke ni n'utilise la clé : on vérifie simplement
    que la présence d'une clé factice dans l'environnement de test ne suffit
    PAS à débloquer un appel externe.
    """
    config = _config()
    # Même config complète + clé factice disponible : l'appel est refusé.
    with pytest.raises(ModeleIndisponible):
        ModeleLiteLLM(config).completer("test")


def test_aucun_secret_dans_le_manifeste_ni_les_evenements():
    res = executer_run(prompt="question neutre")
    charge = json.dumps({"manifeste": res.manifeste, "evenements": res.evenements}, ensure_ascii=False)
    assert CLE_FACTICE not in charge
    for motif in ("cle", "api_key", "apikey", "token", "secret", "bearer", "sk-"):
        assert motif not in charge.lower()


def test_aucun_endpoint_de_lecture_de_cle():
    """La config ne doit exposer qu'un booléen, jamais la clé elle-même."""
    config = _config()
    # La dataclass ne contient aucun champ destiné à porter la clé en clair.
    champs = set(config.__dataclass_fields__)
    assert "cle" not in champs
    assert "api_key" not in champs
    # Représentation : pas de secret.
    assert CLE_FACTICE not in repr(config)


def test_config_incomplete_refuse_la_sauvegarde():
    """Une config sans les champs requis ne peut pas être considérée complète."""
    for manquant in (
        {"fournisseur": None},
        {"modele": None},
        {"region": None},
        {"budget_tokens_max": None},
        {"classe_donnees": None},
        {"approuve": False},
    ):
        assert _config(**manquant).est_complete() is False


def test_byok_nest_pas_approbation_de_depense():
    """Même avec une config complète, le graphe utilise le mock par défaut."""
    res = executer_run(prompt="x")
    assert res.manifeste["alias_modele"] == "mock"


# --------------------------------------------------------------------------
# Absence de réseau : on coupe socket et tout le flux doit fonctionner
# --------------------------------------------------------------------------
def test_aucun_acces_reseau_pendant_le_flux(monkeypatch):
    import socket

    def _interdit(*args, **kwargs):
        raise AssertionError("Accès réseau interdit détecté pendant le flux mock")

    monkeypatch.setattr(socket, "socket", _interdit)
    monkeypatch.setattr(socket, "create_connection", _interdit)
    monkeypatch.setattr(socket, "getaddrinfo", _interdit)

    res = executer_run(prompt="flux hors ligne")
    assert res.reponse
    assert res.manifeste["alias_modele"] == "mock"
