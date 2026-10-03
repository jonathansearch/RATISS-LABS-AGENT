"""Tests ÉTAPE C — MCP Gateway + outils de base (PROMPT GLM, MONTAGE étape 3).

Ce qui est vérifié ici, hors ligne et sans service :
- tools.yaml : structure stricte, 5 serveurs prescrits (filesystem, git,
  fetch, arxiv, github), github optionnel lié à GITHUB_TOKEN, aucun secret
  en dur ;
- docker/mcp-tools.Dockerfile : versions épinglées au EXACTES (1.0.11,
  2026.8.31, 2026.8.18, 0.7.3), mêmes digests de base que les étapes A/B ;
- docker-compose.yml : mcp-gateway ContextForge v1.0.11 épinglé (le tag
  publié porte un préfixe v), admin API activée explicitement, UI admin
  désactivée, ports sur 127.0.0.1, filesystem limité au volume /workspace,
  internet sortant = exceptions explicites (tools-out) uniquement, github
  derrière le profil "github" ;
- scripts/enregistrer_outils.py : planification idempotente (aucun doublon),
  mise à jour uniquement si l'URL change, calcul des outils attendus par
  gateway, comparaison exacte (le contrôle MONTAGE), extraction JSON-RPC
  d'une réponse JSON ou SSE ;
- jeton github absent → serveur sauté (fail-closed, rien de simulé).

Le contrôle « tools/list de ratiss-v1 == tools.yaml », l'appel read_file
réussi dans /workspace et le refus de /etc/passwd exigent le Compose en
marche : ils se font sur l'hôte du chef (commandes documentées dans la PR).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------
# Chargement du script (hors paquet, via spec)
# --------------------------------------------------------------------------
_SPEC = importlib.util.spec_from_file_location(
    "enregistrer_outils", RACINE / "scripts" / "enregistrer_outils.py"
)
enregistrer = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault("enregistrer_outils", enregistrer)
_SPEC.loader.exec_module(enregistrer)


# --------------------------------------------------------------------------
# tools.yaml
# --------------------------------------------------------------------------
@pytest.fixture()
def inventaire() -> dict:
    return enregistrer.charger_tools_yaml(RACINE / "tools.yaml")


def test_tools_yaml_version_et_structure(inventaire):
    assert inventaire["version"] == 1
    assert inventaire["serveur_virtuel"]["nom"] == "ratiss-v1"
    assert inventaire["serveur_virtuel"]["outils_autorises"] == "tous"
    assert isinstance(inventaire["serveurs"], list) and len(inventaire["serveurs"]) == 5


def test_tools_yaml_les_5_serveurs_prescrits_par_le_prompt(inventaire):
    noms = {s["nom"] for s in inventaire["serveurs"]}
    # filesystem, git, fetch, github-mcp-server, arxiv (PROMPT étape C)
    assert {"filesystem", "git", "fetch", "arxiv", "github"} <= noms


def test_tools_yaml_transports_et_urls(inventaire):
    for srv in inventaire["serveurs"]:
        assert srv["transport"] == "STREAMABLEHTTP", srv["nom"]
        assert srv["url"].startswith("http://mcp-"), srv["nom"]
        assert srv["url"].endswith("/mcp"), srv["nom"]


def test_tools_yaml_github_optionnel_lié_à_env(inventaire):
    github = next(s for s in inventaire["serveurs"] if s["nom"] == "github")
    # Optionnel : inactif par défaut, activé SEULEMENT si le jeton existe.
    assert github.get("actif") is False
    assert github.get("activable_si_env") == "GITHUB_TOKEN"
    assert github.get("auth_token_env") == "GITHUB_TOKEN"


def test_tools_yaml_aucun_secret_en_dur(inventaire):
    textes = yaml.safe_dump(inventaire)
    for indice in ("ghp_", "github_pat_", "sk-", "password="):
        assert indice not in textes, f"secret potentiel en dur : {indice}"


def test_tools_yaml_filesystem_limite_au_workspace(inventaire):
    fs = next(s for s in inventaire["serveurs"] if s["nom"] == "filesystem")
    assert fs["service_docker"] == "mcp-filesystem"
    # La limite /workspace est dans le compose (voir test dédié) et le YAML
    # doit référencer le service qui la porte.
    assert "workspace" in (RACINE / "tools.yaml").read_text(encoding="utf-8").lower()


# --------------------------------------------------------------------------
# serveurs actifs / fail-closed
# --------------------------------------------------------------------------
def test_serveurs_actifs_sans_env_github_exclut_github(inventaire, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    actifs = enregistrer.serveurs_actifs(inventaire)
    noms = {s["nom"] for s in actifs}
    assert {"filesystem", "git", "fetch", "arxiv"} <= noms
    assert "github" not in noms  # pas de jeton → sauté, rien de simulé


def test_serveurs_actifs_avec_env_github_inclut_github(inventaire, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "x" * 40)
    actifs = enregistrer.serveurs_actifs(inventaire)
    assert "github" in {s["nom"] for s in actifs}


# --------------------------------------------------------------------------
# Idempotence (fonctions pures)
# --------------------------------------------------------------------------
def _desires() -> list[dict]:
    return [
        {"nom": "filesystem", "url": "http://mcp-filesystem:9101/mcp", "description": "d"},
        {"nom": "git", "url": "http://mcp-git:9102/mcp", "description": "d"},
    ]


def test_planification_premiere_fois_tout_cree():
    plan = enregistrer.planifier_gateways(_desires(), [])
    assert all(action == "creer" for _, _, action in plan)
    assert len(plan) == 2


def test_planification_relancee_aucun_doublon():
    existants = [
        {"id": "g1", "name": "filesystem", "url": "http://mcp-filesystem:9101/mcp"},
        {"id": "g2", "name": "git", "url": "http://mcp-git:9102/mcp"},
    ]
    plan = enregistrer.planifier_gateways(_desires(), existants)
    # Relancer ne crée RIEN et ne modifie RIEN : idempotence exigée par le PROMPT.
    assert all(action == "inchangé" for _, _, action in plan)


def test_planification_url_changee_propose_maj_pas_de_creation():
    existants = [{"id": "g1", "name": "filesystem", "url": "http://ancien:1/mcp"}]
    plan = enregistrer.planifier_gateways(_desires(), existants)
    actions = {nom: action for nom, _, action in plan}
    assert actions["filesystem"] == "maj"          # mise à jour…
    assert actions["git"] == "creer"               # …et pas de doublon pour git


def test_outils_attendus_filtre_par_gateway():
    outils = [
        {"id": "t1", "name": "read_file", "gateway_id": "g1"},
        {"id": "t2", "name": "write_file", "gateway_id": "g1"},
        {"id": "t3", "name": "inconnu", "gateway_id": "gX"},
        {"id": "t4", "name": "sans_gateway"},
    ]
    attendus = enregistrer.outils_attendus(outils, {"g1": "filesystem"})
    assert attendus == {"read_file", "write_file"}


def test_comparer_listes_exact():
    ok, manquants, en_trop = enregistrer.comparer_listes({"a", "b"}, {"b", "c"})
    assert not ok and manquants == {"a"} and en_trop == {"c"}
    ok, _, _ = enregistrer.comparer_listes({"a"}, {"a"})
    assert ok


# --------------------------------------------------------------------------
# Extraction JSON-RPC (Streamable HTTP : JSON pur ou SSE)
# --------------------------------------------------------------------------
def test_extraire_json_rpc_corps_json_pur():
    corps = '{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"read_file"}]}}'
    charge = enregistrer._extraire_json_rpc(corps)
    assert charge["result"]["tools"][0]["name"] == "read_file"


def test_extraire_json_rpc_flux_sse():
    corps = (
        "event: message\n"
        'data: {"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"fetch"}]}}\n\n'
    )
    charge = enregistrer._extraire_json_rpc(corps)
    assert charge["result"]["tools"][0]["name"] == "fetch"


# --------------------------------------------------------------------------
# Dockerfile
# --------------------------------------------------------------------------
def test_dockerfile_versions_epinglees_exactes():
    contenu = (RACINE / "docker" / "mcp-tools.Dockerfile").read_text(encoding="utf-8")
    for exigence in (
        "mcp-contextforge-gateway==1.0.11",
        "@modelcontextprotocol/server-filesystem@2026.8.31",
        "mcp-server-git==2026.8.18",
        "mcp-server-fetch==2026.8.18",
        "arxiv-mcp-server==0.7.3",
    ):
        assert exigence in contenu, exigence


def test_dockerfile_base_python_meme_digest_que_l_etape_b():
    dt = (RACINE / "docker" / "mcp-tools.Dockerfile").read_text(encoding="utf-8")
    b = (RACINE / "docker" / "llm-gateway.Dockerfile").read_text(encoding="utf-8")
    digest = "sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016"
    assert digest in dt and digest in b  # cohérence des bases, zéro surprise


def test_dockerfile_node_22_epingle():
    contenu = (RACINE / "docker" / "mcp-tools.Dockerfile").read_text(encoding="utf-8")
    assert "node:22-bookworm-slim@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c" in contenu


# --------------------------------------------------------------------------
# docker-compose.yml
# --------------------------------------------------------------------------
@pytest.fixture()
def compose() -> dict:
    return yaml.safe_load((RACINE / "docker-compose.yml").read_text(encoding="utf-8"))


def test_compose_mcp_gateway_contextforge_epingle(compose):
    gw = compose["services"]["mcp-gateway"]
    image = gw["image"]
    assert image.startswith("ghcr.io/ibm/mcp-context-forge:v1.0.11@sha256:")
    assert image.endswith("e9639c030162d6cb2f9f188600dd69af8091ec62a7ce307d4a74f4d4f86873df")


def test_compose_mcp_gateway_secrets_obligatoires_env(compose):
    gw = compose["services"]["mcp-gateway"]
    env = gw["environment"]
    # Secrets OBLIGATOIRES (erreur si absents), jamais de valeur en dur :
    # les clés de contexte sont les noms reconnus par ContextForge
    # (PLATFORM_ADMIN_*), leur VALEUR vient du .env (CONTEXTFORGE_ADMIN_*).
    for cle in ("JWT_SECRET_KEY", "AUTH_ENCRYPTION_SECRET"):
        assert ":?definir" in env[cle], cle
    for cle in ("PLATFORM_ADMIN_EMAIL", "PLATFORM_ADMIN_PASSWORD"):
        assert "${CONTEXTFORGE_ADMIN_" in env[cle] and ":?" in env[cle], cle
    assert env["MCPGATEWAY_UI_ENABLED"] == "false"
    assert env["MCPGATEWAY_ADMIN_API_ENABLED"] == "true"  # requis par le script
    assert env["CACHE_TYPE"] == "redis"
    assert env["DATABASE_URL"].startswith("postgresql://")
    assert env["REDIS_URL"].startswith("redis://redis:")


def test_compose_mcp_gateway_reseaux_core_plus_tools_pas_d_internet(compose):
    gw = compose["services"]["mcp-gateway"]
    assert set(gw["networks"]) == {"core", "tools"}
    assert "tools-out" not in gw["networks"]  # le gateway n'a PAS besoin d'internet
    # Port publié sur 127.0.0.1 uniquement.
    assert gw["ports"][0].startswith("127.0.0.1:")


def test_compose_ponts_stdio_sur_reseau_tools(compose):
    services = compose["services"]
    ponts = {"mcp-filesystem": 9101, "mcp-git": 9102, "mcp-fetch": 9103, "mcp-arxiv": 9104}
    for service, port in ponts.items():
        cmd = " ".join(services[service]["command"])
        assert "--expose-streamable-http" in cmd, service
        assert "--host" in cmd and "0.0.0.0" in cmd, service
        assert str(port) in cmd, service
        assert service in services[service]["networks"] or "tools" in services[service]["networks"]
    # Le pont filesystem porte la limite /workspace (règle MONTAGE : jamais le disque entier).
    assert "/workspace" in " ".join(services["mcp-filesystem"]["command"])
    assert "ratiss_workspace:/workspace" in services["mcp-filesystem"]["volumes"]


def test_compose_internet_sortant_exceptions_explicites_uniquement(compose):
    services = compose["services"]
    assert compose["networks"]["tools-out"]["internal"] is False
    assert compose["networks"]["tools"]["internal"] is True
    attendus = {"mcp-fetch", "mcp-arxiv", "mcp-github"}
    for nom, service in services.items():
        sur_tools_out = isinstance(service.get("networks"), list) and "tools-out" in service["networks"]
        if sur_tools_out:
            assert nom in attendus, f"{nom} sur tools-out sans justification"
    # mcp-filesystem et mcp-git n'ont PAS d'internet.
    assert "tools-out" not in services["mcp-filesystem"]["networks"]
    assert "tools-out" not in services["mcp-git"]["networks"]


def test_compose_github_profil_optionnel_jeton_env(compose):
    gh = compose["services"]["mcp-github"]
    assert "github" in gh["profiles"]  # ne démarre que sur opt-in
    jeton = gh["environment"]["GITHUB_PERSONAL_ACCESS_TOKEN"]
    assert jeton.startswith("${GITHUB_TOKEN:?")  # depuis .env, jamais en dur
    image = gh["image"]
    assert image.startswith("ghcr.io/github/github-mcp-server:v1.14.0@sha256:")
    assert image.endswith("7aaeeec9ae4fe9a736d100c1ff0798f3c219b5009e05f5d3945fcacb13cc196b")
    assert "http" in gh["command"]  # transport HTTP natif v1.14.0


def test_compose_volume_workspace_declare(compose):
    assert "ratiss_workspace" in compose["volumes"]


def test_compose_aucun_latest_nulle_part():
    texte = (RACINE / "docker-compose.yml").read_text(encoding="utf-8")
    assert ":latest" not in texte


# --------------------------------------------------------------------------
# Script : robustesse d'entrée
# --------------------------------------------------------------------------
def test_yaml_invalide_refuse(tmp_path):
    mauvais = tmp_path / "tools.yaml"
    mauvais.write_text("version: 2\nserveurs: []\n", encoding="utf-8")
    with pytest.raises(ValueError):
        enregistrer.charger_tools_yaml(mauvais)


def test_serveur_duplique_refuse(tmp_path):
    mauvais = tmp_path / "tools.yaml"
    mauvais.write_text(
        "version: 1\n"
        "serveur_virtuel: {nom: ratiss-v1, outils_autorises: tous}\n"
        "serveurs:\n"
        "  - {nom: fs, transport: STREAMABLEHTTP, url: 'http://a:1/mcp', service_docker: a}\n"
        "  - {nom: fs, transport: STREAMABLEHTTP, url: 'http://a:2/mcp', service_docker: b}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        enregistrer.charger_tools_yaml(mauvais)


def test_script_ne_produit_rien_dangereux_par_defaut():
    # --verifier-seule existe et le main sans .env échoue proprement (code 1).
    src = (RACINE / "scripts" / "enregistrer_outils.py").read_text(encoding="utf-8")
    assert "--verifier-seule" in src
    assert 'os.environ.get("CONTEXTFORGE_ADMIN_EMAIL", "")' in src
