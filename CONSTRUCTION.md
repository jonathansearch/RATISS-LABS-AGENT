# 🏗️ CONSTRUCTION — RATISS LABS AGENT

Guide de la **Phase 0** : contrats, tests, stack locale.
Tout ce qui suit est exécutable et reproductible.

---

## Prérequis

- Python ≥ 3.11
- Docker + Docker Compose (pour la stack locale)

---

## 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## 2. Lancer les tests des contrats

```bash
python3 -m pytest tests/ -q
```

Résultat attendu :

```
......................                                                   [100%]
22 passed in 0.12s
```

Les tests vérifient :
- que chaque schéma est un JSON Schema draft 2020-12 valide ;
- que chaque exemple respecte son schéma ;
- qu'un exemple privé d'un champ requis est bien **rejeté** (garde-fou) ;
- qu'un `Run` sans provenance est rejeté ;
- que la provenance pointe bien vers `RATISS-Framework` ;
- que les verdicts `Policy` sont limités à `ALLOW` / `DENY` / `REQUIRE_APPROVAL`.

---

## 3. Démarrer la stack locale (PostgreSQL + pgvector)

```bash
cp .env.example .env      # puis renseigner POSTGRES_PASSWORD
docker compose up -d
docker compose ps         # le conteneur doit être "healthy"
```

Au premier démarrage, `sql/init/001_pgvector.sql` active l'extension `vector`
et crée la table de mémoire documentaire.

Arrêter :

```bash
docker compose down       # ajouter -v pour supprimer aussi les données
```

---

## 4. Structure

```
contrats/        les 6 JSON Schemas (Tool, Skill, Task, Event, Run, Policy)
exemples/        un exemple valide par contrat
tests/           validation des contrats (pytest)
sql/init/        initialisation PostgreSQL + pgvector
docker-compose.yml   stack locale minimale
PLAN.md          découpage détaillé de la Phase 0
```

---

## 5. Règle de la Phase 0

> Aucun composant ne communique hors des contrats de `contrats/`.
> On ne commence la Phase 1 (noyau) qu'après validation de cette phase.
