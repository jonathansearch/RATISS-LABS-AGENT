"""Tests du noyau Phase 1 — fixtures synthétiques uniquement.

Aucun réseau, aucun secret, aucune persistance réelle.
"""

from __future__ import annotations

import pytest

from ratiss_agent.graph import GraphePython, executer_run
from ratiss_agent.hashes import hash_objet
from ratiss_agent.manifest import verifier_manifeste
from ratiss_agent.model_adapter import (
    ConfigurationModele,
    ModeleIndisponible,
    ModeleLiteLLM,
    ModeleMock,
    modele_par_defaut,
)
from ratiss_agent.registry import OutilRefuse, Registre


# --------------------------------------------------------------------------
# Flux LangGraph mock : réponse et trace complète
# --------------------------------------------------------------------------
def test_flux_mock_reponse_et_trace_complete():
    res = executer_run(prompt="Bonjour RATISS")
    assert res.reponse
    assert res.manifeste["run_id"] == "run-demo-001"
    assert res.manifeste["task_id"] == "t1-demo"
    assert res.manifeste["version_graphe"] == "0.1.0"
    assert res.manifeste["alias_modele"] == "mock"
    assert len(res.evenements) >= 5
    types = [e["type"] for e in res.evenements]
    assert types[0] == "run_demarre"
    assert types[-1] == "run_termine"


def test_mock_est_deterministe():
    r1 = ModeleMock().completer("même entrée")
    r2 = ModeleMock().completer("même entrée")
    assert r1 == r2
    r3 = ModeleMock().completer("autre entrée")
    assert r3 != r1


def test_graphe_layeres_identiques_python_vs_langgraph():
    """Le wrapper LangGraph doit produire la même réponse déterministe que la stdlib."""
    from ratiss_agent.graph import GrapheLangGraph

    g_std = GraphePython()
    g_lg = GrapheLangGraph()
    a = g_std.executer("r1", "t", "question")
    b = g_lg.executer("r1", "t", "question")
    assert a.reponse == b.reponse
    # Les horodatages des événements varient entre deux runs ; on compare donc
    # les parties déterministes de la trace, pas le hash global.
    assert a.manifeste["hash_entree"] == b.manifeste["hash_entree"]
    assert a.manifeste["hash_sortie"] == b.manifeste["hash_sortie"]
    assert [e["type"] for e in a.evenements] == [e["type"] for e in b.evenements]


# --------------------------------------------------------------------------
# Reprises / replay sans duplication d'opération
# --------------------------------------------------------------------------
def test_replay_ne_duplique_pas_les_evenements():
    g = GraphePython()
    r1 = g.executer("run-a", "t", "question")
    r2 = g.executer("run-a", "t", "question")
    # Deux runs indépendants : même nombre d'événements, pas d'accumulation.
    assert len(r1.evenements) == len(r2.evenements)
    # L'ordre est porté par l'id séquencé (seq interne non sérialisé).
    ids = [e["id"] for e in r1.evenements]
    assert ids == [f"run-a-e{i:03d}" for i in range(1, len(ids) + 1)]


def test_sequenceur_nouveau_a_chaque_run():
    g = GraphePython()
    a = g.executer("run-1", "t", "x")
    b = g.executer("run-2", "t", "x")
    assert a.evenements[0]["x-ratiss"]["run_id"] == "run-1"
    assert b.evenements[0]["x-ratiss"]["run_id"] == "run-2"
    assert b.evenements[0]["id"] == "run-2-e001"


# --------------------------------------------------------------------------
# Registre statique : refus des outils inconnus / désactivés / capabilities
# --------------------------------------------------------------------------
def test_outil_inconnu_refuse():
    with pytest.raises(OutilRefuse, match="inconnu"):
        Registre().resoudre("rm_rf")


def test_outil_non_active_refuse():
    # 'echo' existe mais n'est PAS activé par défaut.
    with pytest.raises(OutilRefuse, match="désactivé"):
        Registre().resoudre("echo")


def test_outil_active_sans_capability_refuse():
    from ratiss_agent.registry import Outil

    reg = Registre(outils_actives={"echo"})
    # On force une capability sur l'outil pour vérifier le refus.
    reg._registre["echo"] = Outil(nom="echo", description="x", capabilities=frozenset({"reseau_sortant"}))
    with pytest.raises(OutilRefuse, match="Capability non accordée"):
        reg.resoudre("echo")


def test_aucun_outil_actif_par_defaut():
    assert Registre().lister_actives() == []


def test_aucun_outil_dangereux_dans_le_registre():
    noms = set(Registre().lister())
    interdits = {"shell", "python", "bash", "write_file", "browser", "github_write", "discord", "qpu"}
    assert not (noms & interdits)


def test_execution_outil_pur_autorisee():
    reg = Registre(outils_actives={"echo"})
    assert reg.executer("echo", {"texte": "salut"}) == {"resultat": "salut"}
    reg2 = Registre(outils_actives={"compte_mots"})
    assert reg2.executer("compte_mots", {"texte": "un deux trois"}) == {"mots": 3}


# --------------------------------------------------------------------------
# Hashes / manifeste cohérents, altération détectée, pas de faux sceau
# --------------------------------------------------------------------------
def test_manifeste_verifiable():
    res = executer_run()
    assert verifier_manifeste(res.manifeste) is True


def test_alteration_manifeste_detectee():
    res = executer_run()
    # On altère un champ couvert par le hash du manifeste.
    res.manifeste["hash_sortie"] = "0" * 64
    assert verifier_manifeste(res.manifeste) is False


def test_alteration_evenement_detectee():
    res = executer_run()
    res.manifeste["evenements"][0]["type"] = "run_termine"  # falsification
    assert verifier_manifeste(res.manifeste) is False


def test_pas_de_faux_sceau_framework():
    res = executer_run()
    assert res.manifeste["scelle"] is False
    assert res.manifeste["moteur"] == "ratiss-agent-demo"
    assert "RATISS-Framework" not in res.manifeste["moteur"]
    assert "non scellée" in res.manifeste["avertissement"].lower() or "trace synthétique" in res.manifeste["avertissement"].lower()


def test_hash_entree_sortie_presents():
    res = executer_run(prompt="abc")
    assert res.manifeste["hash_entree"] == hash_objet({"prompt": "abc"})
    assert len(res.manifeste["hash_sortie"]) == 64


# --------------------------------------------------------------------------
# Absence de réseau / secret / persistance
# --------------------------------------------------------------------------
def test_aucun_outil_requis_dans_le_plan():
    res = executer_run()
    pol = [e for e in res.evenements if e["type"] == "politique_appliquee"]
    assert pol and pol[0]["data"]["outils_requis"] == []
    assert pol[0]["data"]["registre_actifs"] == []


def test_pas_de_cle_dans_le_manifeste():
    res = executer_run()
    brut = str(res.manifeste).lower()
    for interdit in ("api_key", "token", "secret", "authorization", "sk-"):
        assert interdit not in brut


# --------------------------------------------------------------------------
# Configuration modèle absente / budget absent → provider externe bloqué
# --------------------------------------------------------------------------
def test_config_vide_bloque_provider():
    assert ConfigurationModele().est_complete() is False


@pytest.mark.parametrize(
    "config",
    [
        ConfigurationModele(fournisseur="x"),
        ConfigurationModele(fournisseur="x", modele="y"),
        ConfigurationModele(fournisseur="x", modele="y", region="eu"),
        ConfigurationModele(fournisseur="x", modele="y", region="eu", budget_tokens_max=0),
        ConfigurationModele(fournisseur="x", modele="y", region="eu", budget_tokens_max=100, classe_donnees="publique"),
    ],
)
def test_config_incomplete_bloque(config):
    assert config.est_complete() is False
    with pytest.raises(ModeleIndisponible):
        ModeleLiteLLM(config).completer("test")


def test_config_complete_mais_appel_refuse_en_phase1():
    config = ConfigurationModele(
        fournisseur="exemple",
        modele="exemple-modele",
        region="eu",
        budget_tokens_max=1000,
        classe_donnees="publique",
        approuve=True,
    )
    assert config.est_complete() is True
    # Même config complète : l'appel réel est refusé (fail-closed), que ce soit
    # faute de dépendance installée ou parce que BYOK n'est pas configuré.
    with pytest.raises(ModeleIndisponible):
        ModeleLiteLLM(config).completer("test")


def test_modele_par_defaut_est_mock():
    assert isinstance(modele_par_defaut(), ModeleMock)
    # Même avec une config incomplète, on reste sur le mock.
    assert isinstance(modele_par_defaut(ConfigurationModele(fournisseur="x")), ModeleMock)


# --------------------------------------------------------------------------
# Événements : types et acteurs contrôlés
# --------------------------------------------------------------------------
def test_type_evenement_non_autorise_rejete():
    from ratiss_agent.events import SequenceurEvenements

    seq = SequenceurEvenements("r")
    with pytest.raises(ValueError):
        seq.emettre("type_bidon", "control_plane")


def test_acteur_non_autorise_rejete():
    from ratiss_agent.events import SequenceurEvenements

    seq = SequenceurEvenements("r")
    with pytest.raises(ValueError):
        seq.emettre("run_demarre", "inconnu")


# --------------------------------------------------------------------------
# Conformité au contrat réel contrats/event.schema.json (Phase 0, CloudEvents)
# --------------------------------------------------------------------------
def test_evenements_conformes_au_contrat_cloudevents():
    jsonschema = pytest.importorskip("jsonschema")
    import json
    from pathlib import Path

    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "contrats" / "event.schema.json").read_text(encoding="utf-8")
    )
    res = executer_run()
    for evt in res.evenements:
        # Le contrat exige specversion, id, source, type, time ;
        # run_id/actor/task_id/seq sont dans x-ratiss.
        jsonschema.validate(evt, schema)
        assert evt["specversion"] == "1.0"
        assert evt["x-ratiss"]["run_id"] == res.run_id


def test_traceparent_present_et_bien_forme():
    """Corrélation OpenTelemetry via l'extension CloudEvents de traçage distribué."""
    import re

    res = executer_run()
    motif = re.compile(r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$")
    for evt in res.evenements:
        assert motif.match(evt["traceparent"]), evt["traceparent"]
    # Une seule trace par run : tous les événements partagent le même trace_id.
    trace_ids = {e["traceparent"].split("-")[1] for e in res.evenements}
    assert len(trace_ids) == 1
    # Le trace_id est déterministe : dérivé du run_id.
    from ratiss_agent.events import SequenceurEvenements

    assert trace_ids == {SequenceurEvenements(res.run_id).trace_id}


def test_manifeste_demo_nest_pas_un_run_du_contrat():
    """Le manifeste de démonstration n'est PAS un Run : le contrat `run` exige
    `provenance.engine = "RATISS-Framework"`, ce qu'un run mock ne peut pas
    prétendre honnêtement. Le manifeste reste donc un artefact distinct, marqué
    non scellé."""
    jsonschema = pytest.importorskip("jsonschema")
    import json
    from pathlib import Path

    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "contrats" / "run.schema.json").read_text(encoding="utf-8")
    )
    res = executer_run()
    assert res.manifeste["moteur"] != "RATISS-Framework"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(res.manifeste, schema)


# --------------------------------------------------------------------------
# Vrai StateGraph LangGraph (si la dépendance est installée dans le venv)
# --------------------------------------------------------------------------
def test_vrai_langgraph_meme_trace_que_python():
    pytest.importorskip("langgraph")
    from ratiss_agent.graph_langgraph import executer_langgraph

    a = GraphePython().executer("run-lg", "t", "question identique")
    b = executer_langgraph("run-lg", "t", "question identique", ModeleMock())

    assert a.reponse == b.reponse
    assert [e["type"] for e in a.evenements] == [e["type"] for e in b.evenements]
    assert a.manifeste["hash_entree"] == b.manifeste["hash_entree"]
    assert a.manifeste["hash_sortie"] == b.manifeste["hash_sortie"]


def test_vrai_langgraph_manifeste_verifiable():
    pytest.importorskip("langgraph")
    from ratiss_agent.graph_langgraph import executer_langgraph

    res = executer_langgraph("run-lg2", "t", "x", ModeleMock())
    assert verifier_manifeste(res.manifeste) is True
    assert res.manifeste["alias_modele"] == "mock"
    assert res.manifeste["scelle"] is False
