"""Hachage canonique SHA-256 (déterministe, sans dépendance externe).

Un hash doit être reproductible : même contenu → même digest, quel que soit
l'ordre des clés d'un dictionnaire. On sérialise donc en JSON canonique
(tri des clés, séparateurs fixes, UTF-8).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(data: Any) -> str:
    """Sérialisation JSON canonique (clés triées, compacte)."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(data: str | bytes) -> str:
    """SHA-256 hexadécimal d'une chaîne (UTF-8) ou d'octets."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def hash_objet(data: Any) -> str:
    """SHA-256 d'un objet quelconque via sa forme JSON canonique."""
    return sha256_hex(canonical_json(data))


def hacher_chaine(chaine: str) -> str:
    """SHA-256 d'une chaîne brute (utile pour un prompt utilisateur)."""
    return sha256_hex(chaine)
