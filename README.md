# 🤖 RATISS LABS AGENT

Agent de RATISS Labs **assemblé** à partir de briques open source existantes, MCP en priorité. Rien n'est construit de zéro.

📄 Architecture de référence : le brief `agentmd.txt` (control plane / execution plane, Tool / Skill / MCP Server séparés, Policy ALLOW / DENY / REQUIRE_APPROVAL, provenance hashée).

> **Statut : phase de recensement.** Ce dépôt ne contient encore **aucun code**. Il réunit les liens vérifiés des briques à assembler. La construction se fera avec GLM.

## 📂 Contenu
- **`CATALOGUE.md`** : 69 dépôts classés par composant, avec statut, licence et rôle.
- **`LIENS.csv`** : les mêmes données en format machine.

## 🧩 Assemblage V1 proposé (brief §47)

| Brique du brief | Dépôt choisi pour la V1 |
|---|---|
| UI (Chat) | Open WebUI en banc d'essai, puis assistant-ui (UI maison) |
| API + Agent Runtime (router, planner, executor, approvals) | LangGraph (+ deepagents) ; interruptions = approbation humaine |
| Model Gateway | LiteLLM → GLM / Claude / Ollama (local) |
| MCP Gateway + tool registry | IBM mcp-context-forge (ou docker/mcp-gateway) |
| Contrat MCP | spécification + python-sdk + FastMCP (serveurs RATISS maison) |
| Outils MCP | servers (filesystem, git, fetch), github-mcp-server, playwright-mcp, jupyter-mcp-server, arxiv-mcp-server |
| Policy Engine | OPA ; scan d'admission avec snyk/agent-scan |
| Sandboxes (Python / Browser / Repository) | E2B + gVisor, browser-use |
| Mémoire (conversation, tâches, documentaire) | PostgreSQL + pgvector, claude-mem |
| Vérification / provenance | **RATISS-Framework** (SHA-256, journal) + Langfuse / OpenTelemetry |
| Skills (chargement progressif) | format anthropics/skills ; K-Dense (science), Cybersecurity-Skills, diagram-design |
| Stockage objet | SeaweedFS |

## 🗺️ Feuille de route (brief)
0. Contrat : schémas Tool / Skill / Task / Event / Run / Policy.
1. Noyau.
2. Exécution.
3. Mémoire.
4. Vérification RATISS.
5. Skills.
6. UI.
7. Industrialisation.

## 🚫 Hors V1 (brief §46)
Swarm multi-agents, 1000 outils, Kubernetes, inférence distribuée, application mobile, voix.

---
RATISS Labs — Jonathan
