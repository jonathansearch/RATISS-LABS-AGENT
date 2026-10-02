"""Tests de validation des contrats RATISS LABS AGENT (Phase 0).

Vérifie trois choses :
1. Chaque schéma de `contrats/` est un JSON Schema valide (draft 2020-12).
2. Chaque exemple de `exemples/` respecte son schéma.
3. Les garde-fous fonctionnent : un exemple invalide est bien rejeté.

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
    return Draft202012Validator(
        schema,
        registry=_registre(),
        format_checker=FormatChecker(),
    )


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
    erreurs = sorted(validateur.iter_errors(exemple), key=lambda e: e.path)
    assert not erreurs, "\n".join(
        f"  - {list(e.path)}: {e.message}" for e in erreurs
    )


@pytest.mark.parametrize("nom", sorted(PAIRES))
def test_exemple_invalide_rejete(nom: str) -> None:
    """Garde-fou : un exemple privé d'un champ requis est bien rejeté."""
    schema_fichier, exemple_fichier = PAIRES[nom]
    validateur = _validateur(schema_fichier)
    exemple = _charger(EXEMPLES / exemple_fichier)
    schema = _charger(CONTRATS / schema_fichier)
    champ_requis = schema["required"][0]
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
    assert schema["properties"]["decision"]["enum"] == [
        "ALLOW",
        "DENY",
        "REQUIRE_APPROVAL",
    ]


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
    run["provenance"]["moteur"] = "maison"
    assert not validateur.is_valid(run)
