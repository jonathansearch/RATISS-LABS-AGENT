# 📜 LICENCES — ce qu'on a le droit de faire

J'ai lu les fichiers LICENSE eux-mêmes le 02/10/2026 pour tous les dépôts où l'API GitHub affichait « NOASSERTION » ou « non déclarée ».

⚠️ Ceci est une lecture technique, pas un avis juridique.

## ✅ Briques V1 sans risque (licences permissives)

| Brique | Licence lue |
|---|---|
| LangGraph, deepagents, LangChain | MIT |
| FastMCP, ContextForge, OPA, gVisor, Cisco mcp-scanner, RustFS | Apache-2.0 |
| llm-sandbox, browser-use, assistant-ui, LibreChat, postgres-mcp | MIT |
| playwright-mcp, arxiv-mcp-server | Apache-2.0 |
| github-mcp-server | MIT |
| pgvector | licence PostgreSQL (permissive, type BSD) |
| in-toto, vercel/chatbot | Apache-2.0 |

## ⚠️ À connaître

| Dépôt | Ce que dit la licence | Conséquence pour RATISS |
|---|---|---|
| **MCP officiel** (spec, servers, SDK TS, inspector, registry) | Transition de MIT vers Apache-2.0 : le nouveau code est sous Apache-2.0, l'ancien reste MIT sans accord de relicenciement, la documentation est sous CC-BY-4.0 | Usage libre, garder les mentions |
| **LiteLLM** | MIT, **sauf** le dossier `enterprise/` qui a sa propre licence | Utiliser uniquement les fonctions hors `enterprise/` |
| **Langfuse** | MIT, **sauf** les dossiers `ee/`, `web/src/ee/` et `worker/src/ee/` | Version libre OK ; les fonctions « ee » sont payantes |
| **Open WebUI** | Licence type BSD **+ clause 4** : interdit de retirer ou de modifier la marque « Open WebUI », sauf si (i) ≤ 50 utilisateurs sur 30 jours glissants, (ii) accord écrit, ou (iii) licence entreprise | OK comme **banc d'essai**. Pour un produit « RATISS Agent » à son nom, utiliser assistant-ui (MIT) |
| **anthropics/skills** | **Pas de licence globale.** Licence **par skill** : par ex. `mcp-builder` et `skill-creator` sont sous Apache-2.0, alors que `pdf`, `docx`, `pptx` et `xlsx` sont « All rights reserved » et soumis aux conditions d'Anthropic | Copier seulement les skills Apache-2.0 ; pour les autres, s'inspirer du **format** SKILL.md sans copier le contenu |
| **Arize Phoenix** | Elastic License 2.0 : interdit de le fournir comme service hébergé à des tiers | Usage interne OK, revente en service interdite → Langfuse est préféré |
| **Bifrost** | Apache-2.0, mais la **passerelle MCP fait partie de l'offre Enterprise** (README) | Utilisable seulement comme LLM gateway |
| **Garage** | AGPL-3.0 | Modifications à publier si service réseau → RustFS (Apache-2.0) est préféré |
| **Semgrep** | LGPL-2.1 | Usage comme outil externe : OK |

## 🗂️ Les 5 dépôts à garder

| Dépôt | Licence |
|---|---|
| K-Dense-AI/scientific-agent-skills | MIT |
| mukul975/Anthropic-Cybersecurity-Skills | Apache-2.0 |
| cathrynlavery/diagram-design | MIT |
| thedotmack/claude-mem | Apache-2.0 |
| browser-use/browser-use | MIT |
