"""Démo hors ligne : question → réponse mock → manifeste (Phase 1).

Usage :
    python3 -m ratiss_agent.demo
    PYTHONPATH=src python3 src/ratiss_agent/demo.py

Aucun réseau, aucune clé, aucun outil, aucune écriture disque.
"""

from __future__ import annotations

import json
import sys

from .graph import executer_run


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    prompt = argv[0] if argv else "Quelle est la capitale du Cameroun ?"

    resultat = executer_run(prompt=prompt)

    print("=" * 68)
    print("RATISS LABS AGENT — démo Phase 1 (mock déterministe, hors ligne)")
    print("=" * 68)
    print(f"run_id : {resultat.run_id}")
    print(f"task_id: {resultat.task_id}")
    print(f"prompt : {prompt}")
    print(f"réponse: {resultat.reponse}")
    print(f"événements émis : {len(resultat.evenements)}")
    print("manifeste (trace synthétique, NON scellée) :")
    print(json.dumps(resultat.manifeste, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
