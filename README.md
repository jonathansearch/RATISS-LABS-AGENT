# 🤖 RATISS LABS AGENT

Agent de RATISS Labs **assemblé** à partir de briques open source existantes, MCP en priorité. Rien n'est construit de zéro.

📄 Architecture de référence : le brief `agentmd.txt` (control plane / execution plane, Tool / Skill / MCP Server séparés, Policy ALLOW / DENY / REQUIRE_APPROVAL, provenance hashée).

> **Statut : recensement terminé (campagne du 02/10/2026).** Aucun code. Le montage se fera avec GLM en suivant `MONTAGE.md`.

## 📂 Contenu
| Fichier | Rôle |
|---|---|
| **`MONTAGE.md`** | ⭐ **Le workflow de montage** : 12 étapes, chacune avec ses briques, son montage et son contrôle de passage |
| `CATALOGUE.md` | 84 dépôts vérifiés, classés par composant, plus la liste des dépôts écartés et renommés |
| `COMPATIBILITE.md` | Fiche technique et matrice des jonctions, avec la source de chaque affirmation (README / DOC / DÉDUIT) |
| `LICENCES.md` | Licences lues dans les fichiers LICENSE et leurs conséquences |
| `SOURCES.md` | Méthode et sources web de la campagne |
| `LIENS.csv` | Données en format machine |

## 🧩 Pile V1 retenue

| Brique du brief | Dépôt |
|---|---|
| UI | Open WebUI (banc d'essai), puis assistant-ui |
| Runtime (router, planner, executor, approbations) | LangGraph + deepagents + `langchain.mcp` |
| Model Gateway | LiteLLM (+ Ollama) |
| MCP Gateway + registre | IBM ContextForge (serveur virtuel « ratiss-v1 ») |
| Admission MCP | Cisco mcp-scanner (hors ligne) + MCP Inspector + hash dans `tools.yaml` |
| Policy | OPA, appelé par le runtime avant chaque outil |
| Outils MCP | filesystem, git, github, playwright, jupyter, arxiv, postgres ; cyber : mcp-security-hub |
| Sandboxes | llm-sandbox + gVisor, playwright-mcp, browser-use |
| Mémoire | PostgreSQL + pgvector + checkpoints LangGraph |
| Vérification | **RATISS-Framework** (SHA-256, journal, manifest de run) |
| Skills | format SKILL.md + K-Dense, Cybersecurity-Skills, diagram-design (10 à 20 skills en V1) |
| Stockage objet | RustFS |

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
