"""Tests de validation des contrats RATISS LABS AGENT (Phase 0).

Vérifie :
1. Chaque schéma est un JSON Schema draft 2020-12 valide.
2. Chaque exemple respecte son schéma.
3. Les garde-fous fonctionnent (champ manquant ou inconnu rejeté).
4. Les contrats acceptent les standards externes réels :
   - Skill  : un vrai SKILL.md de K-Dense ;
   - Tool   : une vraie définition d'outil MCP (`tools/list`) ;
   - Event  : un vrai événement CloudEvents (exemple officiel de la spécification).

Lancer : pytest tests/ -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

RACINE = Path(__file__).resolve().parent.parent
CONTRATS = RACINE / "contrats"
EXEMPLES = RACINE / "exemples"

PAIRES = {
    "tool": ("tool.schema.json", "tool.exemple.json"),
    "skill": ("skill.schema.json", "skill.exemple.json"),
    "task": ("task.schema.json", "task.exemple.json"),
    "event": ("event.schema.json", "event.exemple.json"),
    "run": ("run.schema.json", "run.exemple.json"),
    "policy": ("policy.schema.json", "policy.exemple.json"),
}


def _charger(chemin: Path) -> dict:
    return json.loads(chemin.read_text(encoding="utf-8"))


def _registre() -> Registry:
    """Registre des schémas pour résoudre les $ref relatifs entre contrats."""
    ressources = []
    for chemin in CONTRATS.glob("*.schema.json"):
        ressources.append((chemin.name, Resource.from_contents(_charger(chemin))))
    return Registry().with_resources(ressources)


def _validateur(nom_schema: str) -> Draft202012Validator:
    schema = _charger(CONTRATS / nom_schema)
    return Draft202012Validator(schema, registry=_registre(), format_checker=FormatChecker())


def _erreurs(validateur: Draft202012Validator, objet: dict) -> list[str]:
    return [f"{list(e.path)}: {e.message}" for e in validateur.iter_errors(objet)]


# --------------------------------------------------------------------------
# 1. Les schémas et les exemples
# --------------------------------------------------------------------------
@pytest.mark.parametrize("nom", sorted(PAIRES))
def test_schema_json_valide(nom: str) -> None:
    """Le schéma est un JSON Schema draft 2020-12 valide."""
    schema_fichier, _ = PAIRES[nom]
    schema = _charger(CONTRATS / schema_fichier)
    Draft202012Validator.check_schema(schema)
    assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("nom", sorted(PAIRES))
def test_exemple_valide(nom: str) -> None:
    """L'exemple respecte son schéma."""
    schema_fichier, exemple_fichier = PAIRES[nom]
    validateur = _validateur(schema_fichier)
    exemple = _charger(EXEMPLES / exemple_fichier)
    assert not _erreurs(validateur, exemple), "\n".join(_erreurs(validateur, exemple))


@pytest.mark.parametrize("nom", sorted(PAIRES))
def test_exemple_invalide_rejete(nom: str) -> None:
    """Garde-fou : un exemple privé d'un champ requis est bien rejeté."""
    schema_fichier, exemple_fichier = PAIRES[nom]
    validateur = _validateur(schema_fichier)
    exemple = _charger(EXEMPLES / exemple_fichier)
    champ_requis = _charger(CONTRATS / schema_fichier)["required"][0]
    exemple.pop(champ_requis)
    assert not validateur.is_valid(exemple), (
        f"Le schéma {schema_fichier} aurait dû rejeter un exemple sans '{champ_requis}'."
    )


def test_six_contrats_presents() -> None:
    """Les 6 contrats de la Phase 0 existent bien."""
    attendus = {f for f, _ in PAIRES.values()}
    presents = {p.name for p in CONTRATS.glob("*.schema.json")}
    assert attendus <= presents, f"Manquants : {attendus - presents}"


def test_policy_decisions_limitees() -> None:
    """Le contrat Policy n'autorise que les 3 verdicts prévus."""
    schema = _charger(CONTRATS / "policy.schema.json")
    assert schema["properties"]["decision"]["enum"] == ["ALLOW", "DENY", "REQUIRE_APPROVAL"]


def test_run_exige_provenance() -> None:
    """Un Run sans provenance est invalide (règle RATISS)."""
    validateur = _validateur("run.schema.json")
    run = _charger(EXEMPLES / "run.exemple.json")
    run.pop("provenance")
    assert not validateur.is_valid(run)


def test_run_exige_moteur_ratiss_framework() -> None:
    """La provenance doit pointer vers RATISS-Framework, pas une réinvention."""
    validateur = _validateur("run.schema.json")
    run = _charger(EXEMPLES / "run.exemple.json")
    run["provenance"]["engine"] = "maison"
    assert not validateur.is_valid(run)


# --------------------------------------------------------------------------
# 2. Nommage : aucun doublon, extensions RATISS dans `x-ratiss`
# --------------------------------------------------------------------------
def test_aucun_doublon_de_champ() -> None:
    """`name` seul (pas de `nom`), `license` seule (pas de `licence`)."""
    for nom_schema in ("skill.schema.json", "tool.schema.json"):
        props = _charger(CONTRATS / nom_schema)["properties"]
        assert "name" in props, nom_schema
        assert "nom" not in props, f"{nom_schema} ne doit plus contenir 'nom'"
    skill_props = _charger(CONTRATS / "skill.schema.json")["properties"]
    assert "license" in skill_props
    assert "licence" not in skill_props


def test_extensions_ratiss_isolees_dans_x_ratiss() -> None:
    """Les extensions RATISS vivent dans `x-ratiss`, pas à la racine."""
    for nom_schema in ("skill", "tool", "event", "task", "run", "policy"):
        props = _charger(CONTRATS / f"{nom_schema}.schema.json")["properties"]
        assert "x-ratiss" in props, nom_schema
        for extension in ("sha256", "provenance_hash"):
            assert extension not in props, f"{nom_schema}: '{extension}' doit être dans x-ratiss"


def test_additional_properties_false_a_la_racine() -> None:
    """La racine refuse tout champ hors standard et hors `x-ratiss`."""
    for nom_schema in ("skill", "tool", "event", "task", "run", "policy"):
        schema = _charger(CONTRATS / f"{nom_schema}.schema.json")
        assert schema.get("additionalProperties") is False, nom_schema


# --------------------------------------------------------------------------
# 3. Skill — spécification Agent Skills (agentskills.io)
# --------------------------------------------------------------------------
def _skill_base() -> dict:
    return _charger(EXEMPLES / "skill.exemple.json")


def test_skill_brut_kdense_accepte() -> None:
    """Un vrai SKILL.md de K-Dense (frontmatter brut) doit passer la validation."""
    validateur = _validateur("skill.schema.json")
    brut = {
        "name": "literature-review",
        "description": (
            "Conducts systematic, scoping, and narrative literature reviews using "
            "PubMed, arXiv, bioRxiv, Semantic Scholar, and other appropriate sources."
        ),
        "allowed-tools": "Read Write Edit Bash",
        "license": "MIT license",
        "compatibility": "Python 3.10+ with requests; network for DOI checks.",
        "metadata": {"version": "1.11", "skill-author": "K-Dense Inc."},
    }
    assert not _erreurs(validateur, brut), "\n".join(_erreurs(validateur, brut))


def test_skill_minimum_name_description() -> None:
    """Le minimum de la spec : `name` + `description`, rien d'autre."""
    validateur = _validateur("skill.schema.json")
    assert validateur.is_valid(
        {"name": "diagram-design", "description": "Créer des diagrammes clairs."}
    )


def test_skill_metadata_imbriquee_acceptee() -> None:
    """`metadata` accepte des valeurs imbriquées (cas réel K-Dense)."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["metadata"] = {"openclaw": {"primaryEnv": "OPENROUTER_API_KEY"}}
    assert validateur.is_valid(skill)


def test_skill_name_trop_long_rejete() -> None:
    """`name` est limité à 64 caractères (spécification Agent Skills)."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["name"] = "a" * 65
    assert not validateur.is_valid(skill)


def test_skill_name_format_rejete() -> None:
    """`name` interdit tirets consécutifs, majuscules et tirets en bord."""
    validateur = _validateur("skill.schema.json")
    for mauvais in ("skill--double", "-debut", "fin-", "Majuscule", "avec_underscore"):
        skill = _skill_base()
        skill["name"] = mauvais
        assert not validateur.is_valid(skill), f"{mauvais!r} aurait dû être rejeté"


def test_skill_description_trop_longue_rejetee() -> None:
    """`description` est limité à 1024 caractères (spécification Agent Skills)."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["description"] = "x" * 1025
    assert not validateur.is_valid(skill)


def test_skill_description_vide_rejetee() -> None:
    """`description` ne peut pas être vide."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["description"] = ""
    assert not validateur.is_valid(skill)


def test_skill_compatibility_trop_longue_rejetee() -> None:
    """`compatibility` est limité à 500 caractères."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["compatibility"] = "x" * 501
    assert not validateur.is_valid(skill)


def test_skill_champ_inconnu_rejete() -> None:
    """Un champ hors spec et hors `x-ratiss` reste refusé."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["champ_invente"] = "valeur"
    assert not validateur.is_valid(skill)


def test_skill_champ_ratiss_hors_x_ratiss_rejete() -> None:
    """`sha256` à la racine (hors `x-ratiss`) est refusé."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["sha256"] = "a" * 64
    assert not validateur.is_valid(skill)


def test_skill_sha256_dans_x_ratiss_accepte() -> None:
    """`x-ratiss.sha256` (SHA-256 valide) est accepté."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["x-ratiss"]["sha256"] = "a" * 64
    assert validateur.is_valid(skill)
    skill["x-ratiss"]["sha256"] = "pas-un-hash"
    assert not validateur.is_valid(skill)


def test_skill_allowed_tools_seul_accepte() -> None:
    """`allowed-tools` (orthographe de la spécification) est le seul nom accepté."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["allowed-tools"] = "Read Write"
    assert validateur.is_valid(skill)


def test_skill_alias_allowed_tools_refuse() -> None:
    """Doublon refusé : l'alias `allowed_tools` n'existe nulle part (règle n° 3)."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["allowed_tools"] = "Read Write"
    assert not validateur.is_valid(skill)
    skill = _skill_base()
    skill["x-ratiss"]["allowed_tools"] = "Read Write"
    assert not validateur.is_valid(skill)


def test_skill_nom_a_la_racine_refuse() -> None:
    """Doublon refusé : `nom` est supprimé, seul `name` existe."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["nom"] = "recherche-arxiv"
    assert not validateur.is_valid(skill)


def test_skill_licence_a_la_racine_refusee() -> None:
    """Doublon refusé : `licence` est supprimé, seul `license` existe."""
    validateur = _validateur("skill.schema.json")
    skill = _skill_base()
    skill["licence"] = "Apache-2.0"
    assert not validateur.is_valid(skill)


def test_skill_aucune_retrocompatibilite() -> None:
    """Rien n'est en production : les anciens champs RATISS ne sont plus tolérés à la racine."""
    validateur = _validateur("skill.schema.json")
    for ancien in ("nom", "declencheurs", "niveau_chargement", "source", "version", "licence"):
        skill = _skill_base()
        skill[ancien] = "x"
        assert not validateur.is_valid(skill), f"{ancien!r} ne doit plus être accepté à la racine"


# --------------------------------------------------------------------------
# 4. Tool — spécification MCP
# --------------------------------------------------------------------------
def test_tool_mcp_reel_accepte() -> None:
    """Une vraie définition d'outil MCP (`tools/list`) doit passer."""
    validateur = _validateur("tool.schema.json")
    outil = {
        "name": "read_file",
        "title": "Read File",
        "description": "Read the complete contents of a file from the file system.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "tail": {"type": "number"},
                "head": {"type": "number"},
            },
            "required": ["path"],
        },
        "outputSchema": {"type": "object", "properties": {"content": {"type": "string"}}},
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    }
    assert not _erreurs(validateur, outil), "\n".join(_erreurs(validateur, outil))


def test_tool_input_schema_requis() -> None:
    """`inputSchema` est requis (spec MCP)."""
    validateur = _validateur("tool.schema.json")
    assert not validateur.is_valid({"name": "echo"})


def test_tool_champ_inconnu_rejete() -> None:
    """Un champ inconnu à la racine est refusé."""
    validateur = _validateur("tool.schema.json")
    outil = _charger(EXEMPLES / "tool.exemple.json")
    outil["entrees"] = {"type": "object"}
    assert not validateur.is_valid(outil)


def test_tool_ancien_nom_rejete() -> None:
    """L'ancien champ `nom` n'existe plus."""
    validateur = _validateur("tool.schema.json")
    outil = _charger(EXEMPLES / "tool.exemple.json")
    outil["nom"] = "lire_fichier"
    assert not validateur.is_valid(outil)


# --------------------------------------------------------------------------
# 5. Event — CloudEvents
# --------------------------------------------------------------------------
def test_event_cloudevents_officiel_accepte() -> None:
    """L'exemple officiel de la spécification CloudEvents doit passer."""
    validateur = _validateur("event.schema.json")
    evenement = {
        "specversion": "1.0",
        "type": "com.github.pull_request.opened",
        "source": "https://github.com/cloudevents/spec/pull",
        "subject": "123",
        "id": "A234-1234-1234",
        "time": "2018-04-05T17:31:00Z",
        "comexampleextension1": "value",
        "comexampleothervalue": 5,
        "datacontenttype": "text/xml",
        "data": "<much wow=\"xml\"/>",
    }
    assert not _erreurs(validateur, evenement), "\n".join(_erreurs(validateur, evenement))


def test_event_attribut_extension_accepte() -> None:
    """Un attribut d'extension CloudEvents (minuscules/chiffres) est accepté."""
    validateur = _validateur("event.schema.json")
    evenement = _charger(EXEMPLES / "event.exemple.json")
    evenement["ratisscorrelation"] = "abc123"
    assert validateur.is_valid(evenement)


def test_event_extension_majuscule_rejetee() -> None:
    """CloudEvents n'autorise pas les majuscules dans les noms d'attributs."""
    validateur = _validateur("event.schema.json")
    evenement = _charger(EXEMPLES / "event.exemple.json")
    evenement["MaExtension"] = "valeur"
    assert not validateur.is_valid(evenement)


def test_event_champ_requis_manquant_rejete() -> None:
    """Les 5 champs CloudEvents requis sont exigés."""
    validateur = _validateur("event.schema.json")
    for champ in ("specversion", "id", "source", "type", "time"):
        evenement = _charger(EXEMPLES / "event.exemple.json")
        evenement.pop(champ)
        assert not validateur.is_valid(evenement), f"{champ!r} devrait être requis"


def test_event_run_id_requis_dans_x_ratiss() -> None:
    """RATISS exige `x-ratiss.run_id` (corrélation d'un run)."""
    validateur = _validateur("event.schema.json")
    evenement = _charger(EXEMPLES / "event.exemple.json")
    evenement["x-ratiss"].pop("run_id")
    assert not validateur.is_valid(evenement)


def test_event_traceparent_accepte() -> None:
    """L'extension CloudEvents de traçage distribué (corrélation OTel) est acceptée."""
    validateur = _validateur("event.schema.json")
    evenement = _charger(EXEMPLES / "event.exemple.json")
    evenement["traceparent"] = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    evenement["tracestate"] = "congo=t61rcWkgMzE"
    assert not _erreurs(validateur, evenement), "\n".join(_erreurs(validateur, evenement))


def test_event_traceparent_vide_refuse() -> None:
    """`traceparent` doit être une chaîne non vide (spec de l'extension)."""
    validateur = _validateur("event.schema.json")
    evenement = _charger(EXEMPLES / "event.exemple.json")
    evenement["traceparent"] = ""
    assert not validateur.is_valid(evenement)


def test_event_trace_id_dans_x_ratiss_refuse() -> None:
    """Doublon refusé : `trace_id`/`span_id` sont remplacés par `traceparent`."""
    validateur = _validateur("event.schema.json")
    for ancien in ("trace_id", "span_id"):
        evenement = _charger(EXEMPLES / "event.exemple.json")
        evenement["x-ratiss"][ancien] = "x"
        assert not validateur.is_valid(evenement), f"{ancien!r} doit être refusé"


def test_event_attribut_minuscule_traite_comme_extension() -> None:
    """Conséquence assumée de CloudEvents : tout attribut en minuscules est une extension.

    `horodatage` n'est donc pas rejeté : il est interprété comme un attribut
    d'extension CloudEvents (minuscules et chiffres). La protection contre les
    anciens champs vient du fait que les consommateurs lisent `time`, pas
    `horodatage`.
    """
    validateur = _validateur("event.schema.json")
    evenement = _charger(EXEMPLES / "event.exemple.json")
    evenement["horodatage"] = "2026-10-02T14:47:02Z"
    assert validateur.is_valid(evenement)
