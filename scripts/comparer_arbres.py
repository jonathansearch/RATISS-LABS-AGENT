"""Comparateur non destructif de deux arbres (Phase 0/1).

Compare l'arbre LOCAL (ce dépôt) à un arbre EXTRAIT d'une archive de revue.
Ne modifie rien, n'intègre rien, n'écrit aucun fichier de l'arbre comparé.

Usage :
    python3 scripts/comparer_arbres.py /chemin/vers/arbre_arena_extraite

Sortie : inventaire des contrats/schémas, tests, fichiers, licences/locks et
écarts, sous forme de tableau lisible.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

RACINE_LOCALE = Path(__file__).resolve().parents[1]
IGNORER = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "artefacts"}


def parcourir(racine: Path) -> set[Path]:
    fichiers: set[Path] = set()
    for p in racine.rglob("*"):
        if any(part in IGNORER for part in p.parts):
            continue
        if p.is_file():
            fichiers.add(p.relative_to(racine))
    return fichiers


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def schemas(racine: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for d in ("contrats", "schemas", "contracts"):
        base = racine / d
        if not base.is_dir():
            continue
        for f in sorted(base.glob("*.json")):
            try:
                s = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                out[f"{d}/{f.name}"] = {"erreur": str(e)}
                continue
            props = s.get("properties", {})
            enums = {
                k: v["enum"]
                for k, v in props.items()
                if isinstance(v, dict) and "enum" in v
            }
            out[f"{d}/{f.name}"] = {
                "required": s.get("required", []),
                "proprietes": sorted(props.keys()),
                "enums": enums,
                "additionalProperties": s.get("additionalProperties"),
            }
    return out


def tests(racine: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    base = racine / "tests"
    if not base.is_dir():
        return out
    for f in sorted(base.glob("test_*.py")):
        contenu = f.read_text(encoding="utf-8", errors="ignore")
        out[f"tests/{f.name}"] = len(re.findall(r"^def test_", contenu, re.M))
    return out


def dependances(racine: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for nom in ("requirements.txt", "requirements-phase1.txt", "pyproject.toml"):
        f = racine / nom
        if f.is_file():
            out[nom] = [
                l.strip() for l in f.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.strip().startswith("#")
            ][:40]
    for nom in ("requirements-phase1.lock.txt", "poetry.lock", "uv.lock", "package-lock.json"):
        f = racine / nom
        if f.is_file():
            out[nom] = [f"({len(f.read_text(encoding='utf-8').splitlines())} lignes)"]
    return out


def adr(racine: Path) -> list[str]:
    trouve: list[str] = []
    for p in racine.rglob("*"):
        if any(part in IGNORER for part in p.parts):
            continue
        n = p.name.lower()
        if p.is_file() and ("adr" in n or "decision" in n or "threat" in n) and n.endswith(".md"):
            trouve.append(str(p.relative_to(racine)))
    return sorted(trouve)


def titre(t: str) -> None:
    print(f"\n## {t}\n")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    autre = Path(argv[1]).resolve()
    if not autre.is_dir():
        print(f"ERREUR : {autre} n'est pas un dossier.", file=sys.stderr)
        return 2

    print(f"LOCAL : {RACINE_LOCALE}")
    print(f"AUTRE : {autre}")
    print("\n⚠️  Comparaison en LECTURE SEULE. Aucune intégration, aucune écriture.")

    titre("1. Contrats / schémas")
    s_local, s_autre = schemas(RACINE_LOCALE), schemas(autre)
    tous = sorted(set(s_local) | set(s_autre))
    for nom in tous:
        a, b = s_local.get(nom), s_autre.get(nom)
        if a and b:
            ecart = []
            if set(a.get("proprietes", [])) != set(b.get("proprietes", [])):
                ecart.append("propriétés")
            if set(a.get("required", [])) != set(b.get("required", [])):
                ecart.append("required")
            if a.get("enums") != b.get("enums"):
                ecart.append("enums")
            etat = "identique" if not ecart else f"DIFF: {', '.join(ecart)}"
        elif a:
            etat = "seulement LOCAL"
        else:
            etat = "seulement AUTRE"
        print(f"  - {nom}: {etat}")
    print(f"  Total LOCAL={len(s_local)}  AUTRE={len(s_autre)}")

    titre("2. Tests")
    t_local, t_autre = tests(RACINE_LOCALE), tests(autre)
    tous = sorted(set(t_local) | set(t_autre))
    for nom in tous:
        print(f"  - {nom}: LOCAL={t_local.get(nom, '—')}  AUTRE={t_autre.get(nom, '—')}")

    titre("3. Dépendances / lockfiles")
    d_local, d_autre = dependances(RACINE_LOCALE), dependances(autre)
    for nom in sorted(set(d_local) | set(d_autre)):
        print(f"  - {nom}: LOCAL={'oui' if nom in d_local else '—'}  AUTRE={'oui' if nom in d_autre else '—'}")

    titre("4. ADR / threat model / décisions")
    print(f"  LOCAL : {adr(RACINE_LOCALE) or '—'}")
    print(f"  AUTRE : {adr(autre) or '—'}")

    titre("5. Fichiers : équivalents / concurrents / uniques")
    f_local, f_autre = parcourir(RACINE_LOCALE), parcourir(autre)
    communs = f_local & f_autre
    identiques, concurrents = [], []
    for rel in sorted(communs):
        if sha256(RACINE_LOCALE / rel) == sha256(autre / rel):
            identiques.append(rel)
        else:
            concurrents.append(rel)
    uniques_local = sorted(f_local - f_autre)
    uniques_autre = sorted(f_autre - f_local)
    print(f"  Identiques ({len(identiques)}) : {[str(x) for x in identiques[:20]]}")
    print(f"  Concurrents (même nom, contenu différent) ({len(concurrents)}) : "
          f"{[str(x) for x in concurrents[:20]]}")
    print(f"  Uniques LOCAL ({len(uniques_local)}) : {[str(x) for x in uniques_local[:30]]}")
    print(f"  Uniques AUTRE ({len(uniques_autre)}) : {[str(x) for x in uniques_autre[:30]]}")

    print("\n## 6. Proposition de base canonique")
    print("  À rédiger par l'agent après lecture : le script ne tranche pas.")
    print("  Le propriétaire décide. Aucune conclusion « Phase 0 validée ».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
