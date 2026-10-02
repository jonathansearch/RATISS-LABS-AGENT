# 📍 ÉTAT DU PROJET — RATISS LABS AGENT (02/10/2026, fin de journée)

## ✅ Terminé
| Étape (MONTAGE.md) | Contenu | Où |
|---|---|---|
| Recensement | 84 dépôts vérifiés, licences, compatibilité, versions, workflow en 12 étapes | CATALOGUE, MONTAGE, COMPATIBILITE, VERSIONS, LICENCES, SOURCES |
| Étape 0 — Contrat | 6 schémas alignés : Skill = Agent Skills, Tool = MCP, Event = CloudEvents + traceparent ; Task, Run, Policy en anglais ; extensions dans `x-ratiss` | `contrats/` (PR #2, fusionnée par le chef) |
| Noyau (mock) | LangGraph + registre statique + run mock tracé et hashé ; appel modèle externe verrouillé ; 107 tests | `src/ratiss_agent/` (PR #3, vérifiée et fusionnée par l'agent Arena) |

## ⏭️ Prochaine étape : MONTAGE, étape 6
**deepagents + middleware de politique (OPA)**, en mock :
- 3 tests : ALLOW, DENY, REQUIRE_APPROVAL (avec `interrupt()` puis reprise) ;
- nouvelle branche, nouvelle PR ;
- **pas de fusion par l'agent de construction** : c'est le chef ou l'agent Arena qui fusionne.

## ⏳ Décisions du chef en attente
Auth UI · secret store (BYOK) · fournisseur / modèle / région / plafond de coût · rétention · préflight hôte.

## 📌 Règles permanentes
- Aucune clé, aucun `.env` réel dans git.
- Aucun service lancé sans ordre.
- Rien n'est fusionné sans vérification.
- Un échec de test est une donnée : on le rapporte, on ne le cache pas.
