"""Tests de reprise/replay (Phase 1) — checkpointer EN MÉMOIRE, données synthétiques.

⚠️ LIMITES : ces tests valident une reprise **intra-processus** sur un faux
checkpointer en RAM. Ils ne valident PAS PostgreSQL, la persistance durable,
ni une reprise après véritable redémarrage de processus.

Aucun provider, réseau, DB, conteneur, sandbox ou QPU.
"""

from __future__ import annotations

import pytest

from ratiss_agent.hashes import hash_objet
from ratiss_agent.manifest import verifier_manifeste
from ratiss_agent.model_adapter import ModeleMock
from ratiss_agent.resume import (
    ETAPES,
    Approbation,
    ApprobationInvalide,
    CheckpointMemoire,
    GrapheReprise,
    PanneSimulee,
    RepriseImpossible,
    verifier_coherence,
)

PROMPT = "question synthétique de test"


def _graphe(checkpointer=None, approbation=None) -> GrapheReprise:
    return GrapheReprise(
        modele=ModeleMock(),
        checkpointer=checkpointer or CheckpointMemoire(),
        approbation=approbation,
    )


# --------------------------------------------------------------------------
# Interrupt / resume
# --------------------------------------------------------------------------
def test_interrupt_puis_resume_complete_le_run():
    cp = CheckpointMemoire()
    g = _graphe(cp)
    # Interrupt après 'planner' : run suspendu, checkpoint sauvegardé.
    assert g.demarrer("r-int", "t", PROMPT, arret_apres="planner") is None
    assert cp.contient("r-int")
    assert cp.charger("r-int").etape == "planner"
    # Reprise : le run se termine.
    res = g.reprendre("r-int")
    assert res is not None
    assert res.manifeste["run_id"] == "r-int"
    assert [e["type"] for e in res.evenements][-1] == "run_termine"


def test_resume_sans_checkpoint_leve():
    g = _graphe()
    with pytest.raises(RepriseImpossible):
        g.reprendre("run-inexistant")


def test_run_complet_sans_interrupt():
    g = _graphe()
    res = g.demarrer("r-full", "t", PROMPT)
    assert res is not None
    assert res.manifeste["scelle"] is False
    assert verifier_manifeste(res.manifeste) is True


# --------------------------------------------------------------------------
# Double reprise : pas de duplication d'opération
# --------------------------------------------------------------------------
def test_double_reprise_ne_duplique_pas():
    cp = CheckpointMemoire()
    g = _graphe(cp)
    assert g.demarrer("r-dbl", "t", PROMPT, arret_apres="executor") is None
    r1 = g.reprendre("r-dbl")
    r2 = g.reprendre("r-dbl")  # double reprise
    assert r1 is not None and r2 is not None
    # Aucune opération rejouée : mêmes événements, pas de doublon d'id.
    assert [e["id"] for e in r1.evenements] == [e["id"] for e in r2.evenements]
    assert len(r1.evenements) == len(r2.evenements)
    ops = cp.charger("r-dbl").operations_faites
    assert len(ops) == len(set(ops)) == len(ETAPES)


def test_operation_key_empeche_rejeu():
    cp = CheckpointMemoire()
    g = _graphe(cp)
    assert g.demarrer("r-key", "t", PROMPT, arret_apres="router") is None
    # On reprend, puis on re-reprend : 'router' ne doit jamais être rejoué.
    g.reprendre("r-key")
    cp_apres = cp.charger("r-key")
    ops_router = [o for o in cp_apres.operations_faites if o.endswith(":router")]
    assert ops_router == ["r-key:router"]
    # Un seul événement run_demarre, malgré plusieurs appels.
    demarres = [e for e in cp_apres.evenements if e["type"] == "run_demarre"]
    assert len(demarres) == 1


# --------------------------------------------------------------------------
# Exception après planification, puis reprise
# --------------------------------------------------------------------------
def test_panne_apres_planner_puis_reprise():
    cp = CheckpointMemoire()
    g = _graphe(cp)
    with pytest.raises(PanneSimulee):
        g.demarrer("r-panne", "t", PROMPT, panne_apres="planner")
    # Le plan a été calculé et sauvegardé avant la panne.
    assert cp.charger("r-panne").plan == {"etapes": ["modeliser", "verifier"], "outils_requis": []}
    # La reprise termine le run sans rejouer le planning.
    res = g.reprendre("r-panne")
    assert res is not None
    politiques = [e for e in res.evenements if e["type"] == "politique_appliquee"]
    assert len(politiques) == 1  # pas de double planification
    assert verifier_manifeste(res.manifeste) is True


# --------------------------------------------------------------------------
# Cohérence des événements/hashs après reprise
# --------------------------------------------------------------------------
def test_coherence_apres_reprise():
    cp = CheckpointMemoire()
    g = _graphe(cp)
    assert g.demarrer("r-coh", "t", PROMPT, arret_apres="planner") is None
    res = g.reprendre("r-coh")
    assert verifier_coherence(res) is True
    # Les hashes correspondent bien au payload synthétique.
    assert res.manifeste["hash_entree"] == hash_objet({"prompt": PROMPT})
    assert len(res.manifeste["hash_sortie"]) == 64


def test_sequence_evenements_continue_apres_reprise():
    cp = CheckpointMemoire()
    g = _graphe(cp)
    assert g.demarrer("r-seq", "t", PROMPT, arret_apres="router") is None
    res = g.reprendre("r-seq")
    ids = [e["id"] for e in res.evenements]
    assert ids == [f"r-seq-e{i:03d}" for i in range(1, len(ids) + 1)]
    assert len(ids) == len(set(ids))


def test_reprise_deterministe_meme_reponse():
    """La reprise produit la même réponse que le run complet direct."""
    direct = _graphe().demarrer("r-det", "t", PROMPT)
    cp = CheckpointMemoire()
    g = _graphe(cp)
    assert g.demarrer("r-det", "t", PROMPT, arret_apres="planner") is None
    repris = g.reprendre("r-det")
    assert direct.reponse == repris.reponse


# --------------------------------------------------------------------------
# Approbation : changement de payload l'invalide
# --------------------------------------------------------------------------
def test_approbation_valide_quand_payload_inchange():
    payload = hash_objet({"prompt": PROMPT})
    app = Approbation(payload_sha256=payload)
    g = _graphe(approbation=app)
    res = g.demarrer("r-app", "t", PROMPT)
    assert res is not None
    assert any(e["type"] == "approbation_accordee" for e in res.evenements)


def test_approbation_invalidee_par_changement_de_payload():
    # Approbation liée à un AUTRE payload.
    app = Approbation(payload_sha256=hash_objet({"prompt": "un autre contenu"}))
    g = _graphe(approbation=app)
    with pytest.raises(ApprobationInvalide):
        g.demarrer("r-app2", "t", PROMPT)


def test_approbation_refusee_journalisee():
    app = Approbation(payload_sha256="0" * 64)
    cp = CheckpointMemoire()
    g = _graphe(cp, approbation=app)
    with pytest.raises(ApprobationInvalide):
        g.demarrer("r-app3", "t", PROMPT)
    refus = [e for e in cp.charger("r-app3").evenements if e["type"] == "approbation_refusee"]
    assert len(refus) == 1


# --------------------------------------------------------------------------
# Le faux checkpointer est bien en mémoire (limite explicite)
# --------------------------------------------------------------------------
def test_checkpoint_memoire_est_local_et_non_partage():
    cp1 = CheckpointMemoire()
    cp2 = CheckpointMemoire()
    g = _graphe(cp1)
    g.demarrer("r-mem", "t", PROMPT)
    assert cp1.contient("r-mem") is True
    # Un autre checkpointer ne voit rien : pas de persistance partagée.
    assert cp2.contient("r-mem") is False
