"""RATISS LABS AGENT — noyau (Phase 1).

Assemblage minimal, hors ligne et déterministe :
- `hashes`        : SHA-256 canonique des entrées/sorties
- `events`        : événements séquencés + journal
- `registry`      : registre statique d'outils (désactivés par défaut)
- `model_mock`    : adaptateur de modèle déterministe (aucun réseau)
- `model_adapter` : interface LiteLLM + garde-fous (désactivé par défaut)
- `graph`         : graphe Router → Planner → Executor → Verifier (LangGraph optionnel)
- `manifest`      : manifeste de run synthétique (PAS un sceau RATISS-Framework)
"""

__version__ = "0.1.0"
