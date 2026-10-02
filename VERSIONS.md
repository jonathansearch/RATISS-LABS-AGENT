# 📌 VERSIONS — pile V1 figée au 02/10/2026

Sources : PyPI, npm et les releases GitHub, relevés le 02/10/2026. Ce sont les dernières versions **stables** (pas de pré-release).

**Règle :** on monte avec ces versions exactes. Toute montée de version est un changement à noter dans le journal, puis à re-tester avec les contrôles de `MONTAGE.md`.

## 🐍 Environnement

| Élément | Version | Pourquoi |
|---|---|---|
| **Python** | **3.12** | ContextForge exige ≥ 3.12 et < 3.14 ; toutes les autres briques acceptent 3.12 |
| **Node.js** | **≥ 22.19** | exigé par MCP Inspector 2.9.0 (playwright-mcp demande seulement ≥ 18) |

## 📦 Paquets Python (PyPI)

| Brique | Paquet | Version | Python requis |
|---|---|---|---|
| LangGraph | `langgraph` | 1.2.12 | ≥ 3.10 |
| Checkpoints PostgreSQL | `langgraph-checkpoint-postgres` | 3.1.2 | ≥ 3.10 |
| deepagents | `deepagents` | 0.7.21 | ≥ 3.11, < 4.0 |
| LangChain (+ `langchain.mcp`, bêta) | `langchain[mcp]` | 1.4.3 | ≥ 3.10 |
| FastMCP | `fastmcp` | 4.0.10 | ≥ 3.10 |
| SDK MCP officiel | `mcp` | 2.2.0 | ≥ 3.10 |
| ContextForge | `mcp-contextforge-gateway` | 1.0.11 | ≥ 3.12, < 3.14 |
| LiteLLM | `litellm` | 1.103.2 | ≥ 3.10, < 3.15 |
| Cisco MCP Scanner | `cisco-ai-mcp-scanner` | 4.8.5 (release GitHub 4.8.6 du même jour, pas encore sur PyPI) | ≥ 3.11.4 |
| Snyk Agent Scan (option) | `snyk-agent-scan` | 0.6.8 | ≥ 3.10 |
| llm-sandbox | `llm-sandbox` | 0.3.45 | ≥ 3.10, < 4.0 |
| Jupyter MCP | `jupyter-mcp-server` | 2.2.3 | ≥ 3.10 |
| arXiv MCP | `arxiv-mcp-server` | 0.7.3 | ≥ 3.11 |
| Postgres MCP | `postgres-mcp` | 0.3.0 ⚠️ dernière release en mai 2025 | ≥ 3.12 |
| browser-use | `browser-use` | 0.13.10 | ≥ 3.11, < 4.0 |

## 📦 Paquets Node (npm)

| Brique | Paquet | Version |
|---|---|---|
| Playwright MCP | `@playwright/mcp` | 0.0.83 |
| MCP Inspector | `@modelcontextprotocol/inspector` | 2.9.0 |
| assistant-ui | `@assistant-ui/react` | 0.15.23 |

## 🐳 Services et binaires (releases GitHub)

| Brique | Version |
|---|---|
| GitHub MCP Server | v1.14.0 |
| Ollama | v0.35.1 |
| OPA | v1.21.1 |
| gVisor (`runsc`) | release-20260928.0 |
| pgvector | v0.8.7 (tag) |
| RustFS | 1.0.0 |
| Langfuse (option) | v4.50.0 |
| Open WebUI (banc d'essai) | v0.11.4 |
| mcp-security-hub | pas de release : épingler un **commit** au montage |

## ⚠️ Points d'attention
- **`langchain.mcp` est en bêta** : ne pas monter de version sans relancer les contrôles des étapes 3 à 6.
- **postgres-mcp** : pas de release depuis mai 2025, alors que le dépôt a encore reçu des commits (août 2026). Épingler un commit, ou s'en passer en V1.
- **playwright-mcp** est en 0.0.x : son API peut changer.
