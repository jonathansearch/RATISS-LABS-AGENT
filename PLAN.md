# 📋 PLAN — Phase 0 : Contrats

> Objectif : figer les contrats **avant** d'écrire la moindre ligne de logique.
> Règle : aucun composant ne communique hors de ces contrats.
>
> Statut : **en cours** · RATISS Labs — Jonathan Evina

---

## Pourquoi la Phase 0 d'abord

Un agent qui assemble 12 briques (runtime, gateway, outils, mémoire, policy…)
sans contrat commun devient une pelote. On fige donc les **6 objets** qui circulent
dans tout le système, avec leur JSON Schema. Ensuite seulement, on code.

---

## Livrables de la Phase 0

| # | Livrable | Fichier | Statut |
|---|---|---|---|
| 1 | Contrat **Tool** | `contrats/tool.schema.json` | ✅ fait |
| 2 | Contrat **Skill** | `contrats/skill.schema.json` | ✅ fait |
| 3 | Contrat **Task** | `contrats/task.schema.json` | ✅ fait |
| 4 | Contrat **Event** | `contrats/event.schema.json` | ✅ fait |
| 5 | Contrat **Run** | `contrats/run.schema.json` | ✅ fait |
| 6 | Contrat **Policy** | `contrats/policy.schema.json` | ✅ fait |
| 7 | Exemples valides (1 par contrat) | `exemples/*.exemple.json` | ✅ fait |
| 8 | Tests de validation | `tests/test_contrats.py` | ✅ fait |
| 9 | Stack locale minimale | `docker-compose.yml` | ✅ fait |
| 10 | README de construction | `CONSTRUCTION.md` | ✅ fait |

---

## Découpage en tâches (ordonné)

### T0.1 — Contrat Tool ✅
- **Objectif** : décrire une capacité atomique exposée par un serveur MCP.
- **Champs clés** : `nom`, `serveur_mcp`, `entrees`, `sorties`, `idempotent`, `effets_de_bord`, `niveau_risque`.
- **Critère de done** : schéma valide + exemple valide + exemple invalide rejeté.

### T0.2 — Contrat Skill ✅
- **Objectif** : décrire une procédure chargée progressivement (format `SKILL.md`).
- **Champs clés** : `declencheurs`, `niveau_chargement`, `outils_recommandes`, `licence`.
- **Critère de done** : idem.

### T0.3 — Contrat Task ✅
- **Objectif** : décrire une unité de travail planifiée.
- **Champs clés** : `objectif`, `statut`, `dependances`, `outils_autorises`, `critere_done`.
- **Critère de done** : idem.

### T0.4 — Contrat Event ✅
- **Objectif** : journaliser tout ce qui se passe, compatible OpenTelemetry.
- **Champs clés** : `type`, `horodatage`, `run_id`, `acteur`, `trace_id`, `span_id`.
- **Critère de done** : idem.

### T0.5 — Contrat Run ✅
- **Objectif** : décrire une exécution complète avec provenance obligatoire.
- **Champs clés** : `plan`, `tasks`, `evenements`, `artefacts`, `provenance`.
- **Critère de done** : un Run sans `provenance` est rejeté (test dédié).

### T0.6 — Contrat Policy ✅
- **Objectif** : décrire une règle de décision OPA.
- **Champs clés** : `decision` (ALLOW / DENY / REQUIRE_APPROVAL), `sujet`, `action`, `ressource`.
- **Critère de done** : les 3 verdicts sont les seuls autorisés (test dédié).

### T0.7 — Tests transverses ✅
- 6 × 3 tests paramétrés (schéma valide, exemple valide, exemple invalide rejeté)
- + 3 tests de règles RATISS (provenance obligatoire, moteur imposé, verdicts limités)
- **Résultat** : 22/22 tests verts.

### T0.8 — Stack locale ✅
- `docker-compose.yml` : PostgreSQL 16 + extension pgvector.
- Healthcheck, volume persistant, variables d'env.

### T0.9 — Documentation ✅
- `CONSTRUCTION.md` : comment lancer les tests et la stack.

---

## Résultat mesuré

```
$ python3 -m pytest tests/ -q
......................                                                   [100%]
22 passed in 0.12s
```

---

## Porte de sortie (avant Phase 1)

- [x] 6 contrats écrits et versionnés
- [x] 6 exemples valides
- [x] Tests de validation verts (22/22)
- [x] Stack locale définie
- [ ] **Validation humaine** ← en attente

---

## Phase 1 (rappel, ne pas commencer sans validation)

**Noyau** : Model Gateway (LiteLLM → GLM/Claude/Ollama) + Agent Runtime (LangGraph)
+ registre d'outils. Critère de done : un run simple « question → réponse »
tracé de bout en bout, avec un manifeste de provenance.
