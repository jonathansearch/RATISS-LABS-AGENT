# 🔌 COMPATIBILITÉ — comment les briques V1 se branchent

Chaque jonction porte la **source** de l'affirmation :
- **[README]** : écrit dans le README du dépôt, lu le 02/10/2026 ;
- **[DOC]** : documentation officielle ou changelog trouvés sur le web (voir `SOURCES.md`) ;
- **[DÉDUIT]** : cohérent techniquement mais **non documenté**, donc **à tester en premier**.

⚠️ Rien n'a été exécuté : ce sont des compatibilités sur papier.

## 1. Fiche technique des briques V1

| Brique | Prérequis | Transports MCP | Stockage | Déploiement |
|---|---|---|---|---|
| LangGraph + deepagents | Python | client MCP via LangChain | checkpoints | bibliothèque |
| LangChain `langchain.mcp` | `pip install "langchain[mcp]"`, **bêta** | bâti sur FastMCP | — | bibliothèque |
| IBM ContextForge | Python (uvx) ou Docker | stdio (wrapper), SSE, Streamable HTTP | SQLite → PostgreSQL, Redis | Compose, Helm |
| LiteLLM proxy | Docker | — (passerelle LLM) | PostgreSQL, Redis (option) | Docker, Helm |
| OPA | binaire unique | — (API REST) | fichiers de politiques | conteneur |
| llm-sandbox | Python + Docker ou Podman | serveur MCP intégré | — | bibliothèque + MCP |
| gVisor (`runsc`) | Linux | — | — | runtime OCI branché sur Docker |
| github-mcp-server | token GitHub | stdio | — | `docker run` |
| playwright-mcp | Node 18+ | stdio, SSE | — | `docker run` |
| jupyter-mcp-server | un JupyterLab en marche | Streamable HTTP, stdio | — | Python |
| arxiv-mcp-server | Python 3.11+ | stdio, Streamable HTTP | — | Python |
| postgres-mcp | PostgreSQL | stdio, SSE | PostgreSQL | `docker run` |
| mcp-security-hub (cyber) | Docker | stdio par conteneur | — | docker-compose |
| Cisco mcp-scanner | Python 3.11+ | analyse stdio, SSE, HTTP | — | CLI ou API REST |
| browser-use | Python 3.12 | serveur MCP déclaré | — | bibliothèque |
| Langfuse | Docker | — | (sa propre base) | Compose, Helm |
| PostgreSQL + pgvector | — | — | — | image Docker |
| RustFS | — | — | API S3 | conteneur |

## 2. Matrice des jonctions

| De → Vers | Comment | Source |
|---|---|---|
| deepagents → LangGraph | deepagents est construit sur LangGraph (streaming, persistance, checkpoints) | [README] |
| deepagents → serveurs MCP | « bring your own functions or any MCP server » | [README] |
| LangChain → MCP | `langchain.mcp` (v1.4, bêta) remplace `langchain-mcp-adapters`, désormais archivé ; `MultiServerMCPClient` devient `MCPAdapter` | [DOC] |
| Demande d'information MCP → humain | une élicitation MCP en cours d'appel est transformée en `interrupt()` LangGraph | [DOC] |
| Approbation humaine | deepagents : « approve, edit, or reject tool calls before they run » | [README] |
| Runtime → ContextForge | ContextForge expose les outils en SSE / Streamable HTTP ; le runtime les consomme comme un seul serveur MCP | [README] + [DÉDUIT] pour la jonction exacte |
| ContextForge → serveurs stdio | fédère les serveurs stdio via un wrapper | [README] |
| ContextForge → PostgreSQL / Redis | bases supportées | [README] |
| ContextForge → traces | émet de l'OpenTelemetry (Phoenix, Jaeger, Zipkin, OTLP) | [README] |
| Runtime → LiteLLM | LiteLLM expose une API compatible OpenAI ; le runtime pointe son client OpenAI vers le proxy | [README] (API OpenAI) + [DÉDUIT] (réglage côté LangChain) |
| LiteLLM → Langfuse | intégration documentée (mode proxy) | [README Langfuse] |
| LangChain → Langfuse | intégration par callback handler | [README Langfuse] |
| **Runtime → OPA** | **ContextForge ne mentionne pas OPA.** La décision ALLOW / DENY / REQUIRE_APPROVAL doit être prise dans le runtime, juste avant l'appel d'outil : le hook HITL de deepagents interroge l'API REST d'OPA | [DÉDUIT] — **seul vrai collage à écrire** |
| llm-sandbox → gVisor | llm-sandbox lance des conteneurs Docker ; Docker peut utiliser `runsc` comme runtime | [README] des deux + [DÉDUIT] pour la combinaison |
| skills → deepagents | « Skills — reusable behaviors the agent can load on demand » (chargement progressif) | [README] ; compatibilité exacte avec le format SKILL.md **[DÉDUIT]** |
| Cisco scanner → admission | mode hors ligne sur des fichiers JSON, sans clé API (YARA) : utilisable en CI avant d'enregistrer un serveur | [README] |
| Open WebUI → RATISS | Open WebUI se connecte à MCP, MCPO et aux serveurs d'outils OpenAPI | [README] |
| Résultats → RATISS-Framework | hash SHA-256 de chaque artefact et événement | [DÉDUIT] — interface à définir en phase 0 |

## 3. Points de friction connus

1. 🟠 **`langchain.mcp` est en bêta.** Figer les versions dès le début.
2. 🟠 **Versions de Python** : browser-use demande 3.12, le scanner Cisco 3.11+. → Prendre **Python 3.12 partout**.
3. 🟠 **gVisor** : Linux uniquement. Il ne tournera pas sur un poste Windows ou macOS sans VM.
4. 🟠 **microsandbox** (alternative) : exige KVM. Vérifier que le VPS l'autorise avant de le choisir.
5. 🟠 **jupyter-mcp-server** : il faut un service JupyterLab séparé dans le Compose.
6. 🟠 **Serveurs MCP cyber** : nmap demande `--cap-add=NET_RAW`. Ils doivent tourner dans un réseau Docker isolé, sur des cibles autorisées uniquement.
7. 🟠 **Deux bases ?** Langfuse a sa propre pile de stockage. En V1, l'accepter, ou bien commencer sans Langfuse et se contenter du journal RATISS.
