# Comparatif des deux arbres (Phase 0/1)

> **Statut : sans objet.** Le propriétaire a décidé d'**abandonner** l'archive
> `RATISS-PHASE-0-1-REVIEW.zip`. La base canonique est le dépôt `main` lui-même
> (`9d8f990`). Ce document est conservé comme trace de la méthode préparée.

## Méthode préparée (non destructive, non utilisée)

`scripts/comparer_arbres.py` compare l'arbre **local** à un arbre **extrait**
d'une archive, en lecture seule. Elle n'a pas été appliquée, faute d'archive.

## Ce que je vérifierai avant toute comparaison de contenu

1. **Contenu et empreintes** de l'archive (sha256 de l'archive, liste des
   entrées, absence de `.git`, `.venv`, caches, credentials).
2. **Extraction uniquement** dans `/tmp/revue` (hors dépôt, non destructive).
3. **Aucune écriture** dans l'arbre local ni dans l'arbre extrait.

## État préservé (à ne pas toucher)

| Élément | État |
|---|---|
| Branche `openhands/phase-1-noyau` | **portée sur `main` @ `9d8f990`** |
| Ancienne branche | `openhands/phase-1-noyau-archive` (`8e81be1`), contrats obsolètes |
| PR #1 (`openhands/phase-0-contrats`) | **fermée** (remplacée par la PR #2, fusionnée) |
| `origin/main` | `9d8f990` (Phase 0 fusionnée) |
| Merge / rebase / cherry-pick | **aucun** hors PR #2, fusionnée sur ordre du propriétaire |

## Archive `RATISS-PHASE-0-1-REVIEW.zip` : **abandonnée**

Décision du propriétaire (Phase 0) : l'archive est **abandonnée**. Ce comparatif
n'a donc plus d'objet. La base canonique est le dépôt `main` lui-même
(`9d8f990`), et le noyau Phase 1 s'y conforme.

## L'écart de dépôt est **résolu**

Le brief décrivait un dépôt (contrats Pydantic, 10 JSON Schemas, ADR, threat
model, `make check` 10 schémas / 20 tests, `docs/PHASE-0-1.md`, `DECISIONS.md`,
`THREAT-MODEL.md`). Rien de cela n'existait dans ce workspace ni sur le distant.

**Résolution** : ces artefacts venaient d'un workspace **Arena séparé**, et la
Phase 0 a été réconciliée dans `main` (`9d8f990`) : 6 schémas alignés sur les
standards externes, plus les docs `docs/architecture/LICENCES-VERIFICATION.md`
et `NOTES-MONTAGE.md`. La base canonique est `main`.

## Décision du propriétaire

La base canonique est **`main`** (`9d8f990`). Le noyau Phase 1 s'y conforme sans
modifier les contrats. Aucune conclusion « Phase 0 validée » n'est émise par
l'agent : c'est le propriétaire qui tranche.
