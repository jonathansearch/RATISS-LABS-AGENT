"""Inventaire de licences (lecture seule, depuis les métadonnées installées).

Génère un inventaire Markdown des licences de la fermeture transitive installée
dans le venv. N'installe rien, n'accède à aucun réseau.
"""

from __future__ import annotations

import importlib.metadata as md
import sys


def licence_de(dist) -> str:
    meta = dist.metadata
    expr = meta.get("License-Expression")  # PEP 639
    if expr:
        return expr
    for c in meta.get_all("Classifier") or []:
        if c.startswith("License ::"):
            return c.replace("License :: ", "")
    legacy = meta.get("License")
    if legacy:
        if len(legacy) < 60:
            return legacy
        # Certains paquets embarquent le texte complet : on le reconnaît.
        t = legacy.lower()
        if "permission is hereby granted, free of charge" in t:
            return "MIT (texte)"
        if "apache license" in t and "version 2.0" in t:
            return "Apache-2.0 (texte)"
        if "redistribution and use in source and binary forms" in t:
            return "BSD (texte)"
    return "NON_DÉCLARÉE"


def main() -> int:
    dists = sorted(md.distributions(), key=lambda d: (d.metadata["Name"] or "").lower())
    print("| Paquet | Version | Licence |")
    print("|---|---|---|")
    for d in dists:
        nom = d.metadata["Name"] or "?"
        print(f"| {nom} | {d.version} | {licence_de(d)} |")
    print(f"\n_Total : {len(dists)} paquets (fermeture transitive)._", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
