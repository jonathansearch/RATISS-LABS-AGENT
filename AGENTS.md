# AGENTS.md — mémoire du dépôt RATISS-LABS-AGENT

## Contexte

Projet RATISS Labs (Jonathan Evina). Tutoiement, emojis, honnêteté. Ne jamais
déclarer une phase « validée » à la place du propriétaire.

## Environnement

- `python3` système : `/usr/local/bin/python` (sans langgraph/litellm).
- `.venv` : environnement isolé avec les dépendances épinglées (inclus
  langgraph, litellm). **Jamais versionné** (`.gitignore`).
- Docker accessible via `sudo`, mais **non démarré** sauf autorisation.
- `unzip` absent → utiliser Python `zipfile` pour inspecter les archives.

## Commandes utiles

```bash
python3 -m pytest tests/          # socle, sans deps lourdes (2 skips)
.venv/bin/python -m pytest tests/ # avec vrais LangGraph/LiteLLM
make demo                         # démo hors ligne (mock)
python3 scripts/comparer_arbres.py <arbre>  # comparatif non destructif
.venv/bin/python scripts/inventaire_licences.py  # licences depuis les fichiers réels
```

## Règles de travail durables

1. **Ne pas modifier les contrats** `contrats/*.schema.json` sans décision du
   propriétaire. Le runtime s'y conforme : les événements sont des
   **CloudEvents** (`specversion`, `id`, `source`, `type`, `time`, `data`) et
   les champs RATISS (`run_id`, `task_id`, `actor`, `seq`) vivent dans
   `x-ratiss`.
2. **Règle n° 3 — aucun doublon** : `name` seul (pas `nom`), `license` seule
   (pas `licence`), `allowed-tools` seul (pas `allowed_tools`). Les extensions
   RATISS vont dans `x-ratiss`, jamais à la racine. Aucune rétrocompatibilité :
   les tolérances iraient dans le **chargeur**, au montage.
3. Le manifeste de démo **n'emprunte pas** `moteur: "RATISS-Framework"` :
   il reste `ratiss-agent-demo`, `scelle: false`. Le contrat `run` exige
   `provenance.engine = "RATISS-Framework"` : un run mock n'est donc **pas** un
   Run du contrat, et c'est volontaire.
4. **Docs vérifiables** : lire les **fichiers de licence réels**
   (`*.dist-info/licenses/`) plutôt qu'un champ metadata seul.
5. **Limites assumées** : un faux checkpointer en mémoire ne valide PAS
   PostgreSQL, la persistance durable, ni la reprise après vrai redémarrage.
6. Git : pas de push/merge/rebase/cherry-pick sans autorisation explicite.
   Sur ordre du propriétaire, PR #2 a été **fusionnée** dans `main`
   (`9d8f990`) ; PR #1 est **fermée** (remplacée, contenu inclus).

## Faits établis

- **Phase 0 : fusionnée dans `main`** (`9d8f990`, PR #2). 6 schémas alignés sur
  Agent Skills / MCP / CloudEvents ; 54 tests de contrat.
- **Phase 1 : portée sur les nouveaux contrats** (branche
  `openhands/phase-1-noyau`). `events.py` émet des CloudEvents avec
  `traceparent` déterministe (corrélation OTel). 105 passed / 2 skipped
  (système), 107 passed (venv).
- Ancienne branche Phase 1 conservée sous `openhands/phase-1-noyau-archive`
  (`8e81be1`), écrite contre les contrats pré-Arena : à ne pas réutiliser.
- Licences : directes MIT ; transitives MPL-2.0 (`certifi`, `orjson`, `tqdm`)
  désormais **acceptées** par le propriétaire (décision Phase 0). LiteLLM :
  fichier réel avec dossier `enterprise/` sous licence distincte.
