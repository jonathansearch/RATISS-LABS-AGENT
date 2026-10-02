# Phase 1 — Noyau : rapport

**Branche locale** : `openhands/phase-1-noyau`
**Base** : `main` @ `9d8f990` (contrats Phase 0 fusionnés)

---

## 0. Portage sur les contrats de `main` (après fusion de la Phase 0)

La première version du noyau avait été écrite contre les contrats **pré-Arena**
(`horodatage`, `donnees`, `acteur`, `run_id` à la racine des événements). Depuis
la fusion de la PR #2, les contrats sont alignés sur les standards externes :
**CloudEvents** pour `event`, **MCP** pour `tool`, **Agent Skills** pour `skill`.

Le noyau a donc été porté, sans modifier les contrats :

| Avant (pré-Arena) | Après (CloudEvents) |
|---|---|
| `horodatage` | `time` |
| `donnees` | `data` |
| `run_id` (racine) | `x-ratiss.run_id` |
| `acteur` (racine) | `x-ratiss.actor` |
| `task_id` (racine) | `x-ratiss.task_id` + `subject` |
| `seq` non sérialisé | `x-ratiss.seq` |
| `trace_id` / `span_id` | `traceparent` (extension CloudEvents de traçage distribué) |

Le `traceparent` est **déterministe** : le `trace_id` dérive du `run_id`, le
`span_id` du numéro d'événement. La corrélation OpenTelemetry demandée par le
brief est ainsi portée par le standard, sans dépendance à un collecteur.

L'ancienne branche est conservée sous `openhands/phase-1-noyau-archive`
(`8e81be1`), **à ne pas réutiliser** (contrats obsolètes).

---

## 1. Ce qui a été livré

Flux **question → réponse mock** traversant un graphe explicite, un adaptateur
de modèle et un registre d'outils statique, avec trace/manifeste vérifiable.

### Fichiers créés

| Fichier | Rôle |
|---|---|
| `src/ratiss_agent/__init__.py` | paquet |
| `src/ratiss_agent/hashes.py` | SHA-256 canonique (JSON trié) |
| `src/ratiss_agent/events.py` | événements séquencés, **CloudEvents** |
| `src/ratiss_agent/registry.py` | registre statique, **aucun outil actif par défaut** |
| `src/ratiss_agent/model_adapter.py` | `ModeleMock` + `ModeleLiteLLM` fail-closed |
| `src/ratiss_agent/manifest.py` | manifeste synthétique (non scellé) |
| `src/ratiss_agent/graph.py` | graphe stdlib Router→Planner→Executor→Verifier |
| `src/ratiss_agent/graph_langgraph.py` | **vrai** `StateGraph` LangGraph |
| `src/ratiss_agent/demo.py` | démo CLI hors ligne |
| `src/ratiss_agent/resume.py` | reprise/replay (checkpointer en mémoire) |
| `tests/test_phase1_noyau.py` | 34 tests |
| `tests/test_phase1_reprise.py` | 13 tests |
| `tests/test_phase1_byok.py` | 7 tests (clé factice) |
| `pyproject.toml`, `Makefile` | outillage |
| `requirements-phase1.txt` / `.lock.txt` | versions épinglées / lock |
| `scripts/inventaire_licences.py` | inventaire de licences |
| `docs/architecture/BYOK.md` | conception BYOK (inactive) |

### Évolution contractuelle

**Aucune.** Les contrats Phase 0 n'ont pas été modifiés. Le runtime s'y
**conforme** : les événements sont des CloudEvents, les champs RATISS vivent
dans `x-ratiss`. Le manifeste de démo n'emprunte **pas** le
`moteur: "RATISS-Framework"` du contrat `run` : il reste explicitement
`ratiss-agent-demo`, `scelle: false`.

---

## 2. Trace produite (exemple réel)

```
run_id        : run-lg-demo
task_id       : t1-demo
version_graphe: 0.1.0
alias_modele  : mock
moteur        : ratiss-agent-demo   (NON scellé)
hash_entree   : 59deff28df290b5b25c25af6d6ce2496…
hash_sortie   : 7b13e8706a75eae88141c508071172c3…
sha256_manif. : 19865dbbaee5c67db9d0eafdcab036fe…
événements    : 7
  run_demarre, task_demarree, politique_appliquee, modele_appele,
  outil_resultat, task_terminee, run_termine
```

---

## 3. Résultats de tests

| Environnement | Commande | Résultat |
|---|---|---|
| venv isolé (vraies deps) | `.venv/bin/python -m pytest tests/` | **107 passed** |
| système (sans LangGraph/LiteLLM) | `python3 -m pytest tests/` | **105 passed, 2 skipped** |

Les 2 skips sont les tests LangGraph réel : ils ne s'exécutent que si la
dépendance est présente. Ils **tournent** dans le venv.

### Couverture des exigences

- ✅ flux LangGraph mock déterministe avec réponse et trace complète ;
- ✅ replay/reprise sans duplication (ids séquencés, pas d'accumulation) ;
- ✅ registre : outil inconnu refusé, outil désactivé refusé, capability non accordée refusée ;
- ✅ hashes/événements/manifeste cohérents ; **altération détectée** (2 tests) ;
- ✅ aucune fausse affirmation de sceau Framework ;
- ✅ absence de réseau (test qui **coupe `socket`**), aucun secret, aucune persistance ;
- ✅ config modèle absente/incomplète → provider externe bloqué ;
- ✅ tests BYOK avec clé **factice** : aucun secret dans réponses/logs/manifeste ;
- ✅ conformité au contrat `event.schema.json` (validation `jsonschema` réelle),
  CloudEvents + `traceparent` déterministe ;
- ✅ le manifeste de démo **n'est pas** un Run du contrat (le contrat exige
  `provenance.engine = "RATISS-Framework"`) — vérifié par test.

---

## 4. Versions et licences vérifiées

| Paquet | Version | Licence (source : métadonnées PyPI/installées) |
|---|---|---|
| langgraph | 1.2.12 | MIT |
| litellm | 1.103.2 | MIT |
| pydantic | 2.13.5 | MIT |
| langchain-core | 1.6.6 | MIT |

- Fermeture transitive : **83 paquets**, **0 licence non déclarée**.
- 3 paquets en **MPL-2.0** (`certifi`, `orjson`, `tqdm`) : copyleft faible,
  **acceptés** par le propriétaire (décision Phase 0).
- Lock reproductible : `requirements-phase1.lock.txt`.

> Correction au `CATALOGUE.md` : LiteLLM y est noté `NOASSERTION`. Les
> métadonnées actuelles déclarent **MIT** (`license_expression = "MIT"`).

---

## 5. Prérequis indisponibles / non testé

| Élément | État |
|---|---|
| Docker | présent dans le workspace, mais **non démarré** (interdit ici) |
| runsc / gVisor | **absent** → toute exécution de code doit être refusée |
| PostgreSQL | non démarré (interdit ici) |
| Provider IA externe | **non testé** : aucun fournisseur/modèle/région/budget/classe de données fourni |
| UI / API | **aucune** démarrée ni exposée |
| BYOK | conception seule, **inactif**, aucun secret stocké |

---

## 6. Décisions bloquantes pour le propriétaire

1. **Auth UI** : VPN + TLS annoncés, mécanisme précis différé. Quelle solution
   retenir avant d'exposer quoi que ce soit ?
2. **Secret store** : aucun approuvé à ce jour. Lequel utiliser pour BYOK ?
3. **Fournisseur / modèle / région / plafond (par tâche et par mois) /
   classes de données autorisées** : non indiqués → provider **désactivé**.
4. **Rétention** : durées par catégorie non fournies → aucune donnée réelle
   enregistrée ; tests/mocks en mémoire, synthétiques.
5. **Hôte cible** : préflight Docker/runsc/PostgreSQL non fourni.

---

## 7. Services réellement démarrés

**Aucun.** Distinction code / tests / services :

- **code écrit** : oui (modules ci-dessus) ;
- **tests mock** : oui (107 verts dans le venv) ;
- **services démarrés** : **aucun** (ni UI, ni API, ni PostgreSQL, ni OPA,
  ni gateway MCP, ni Docker, ni sandbox, ni processus réseau).
