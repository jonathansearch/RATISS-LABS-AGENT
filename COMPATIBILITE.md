# 🔌 COMPATIBILITÉ — comment les briques V1 se branchent

Chaque jonction porte la **source** de l'affirmation :
- **[README]** : écrit dans le README du dépôt, lu le 02/10/2026 ;
- **[DOC]** : documentation officielle ou changelog trouvés sur le web (voir `SOURCES.md`) ;
- **[DÉDUIT]** : cohérent techniquement mais **non documenté**, donc **à tester en premier**.

⚠️ Rien n'a été exécuté : ce sont des compatibilités sur papier.

**Bilan au 02/10/2026 :** toutes les jonctions entre briques existantes sont documentées ([README] ou [DOC]). Il ne reste que **2 pièces maison** : le middleware de politique (OPA) et le pont de provenance (RATISS-Framework).

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
| LangChain → MCP | `langchain.mcp` (v1.4, bêta) remplace `langchain-mcp-adapters`, désormais archivé ; `MultiServerMCPClient` devient `MCPAdapter`. Transport déduit de la cible : URL http(s) → Streamable HTTP, chemin → stdio, configuration `mcpServers` → plusieurs serveurs. **SSE est déprécié** par la spécification MCP | [DOC] ✅ |
| Demande d'information MCP → humain | une élicitation MCP en cours d'appel est transformée en `interrupt()` LangGraph | [DOC] |
| Approbation humaine | deepagents : « approve, edit, or reject tool calls before they run » | [README] |
| Runtime → ContextForge | FAQ ContextForge : recette LangChain sur `http://<hôte>:4444/mcp` en Streamable HTTP avec `Authorization: Bearer` ; endpoint par serveur virtuel `/servers/<UUID>/mcp`. Côté LangChain : `MCPAdapter` avec un transport Streamable HTTP et des en-têtes (la recette FAQ utilise encore l'ancien adaptateur, à transposer) | [DOC] ✅ |
| ContextForge → serveurs stdio | fédère les serveurs stdio via un wrapper | [README] |
| ContextForge → PostgreSQL / Redis | bases supportées | [README] |
| ContextForge → traces | émet de l'OpenTelemetry (Phoenix, Jaeger, Zipkin, OTLP) | [README] |
| Runtime → LiteLLM | La documentation LiteLLM montre `ChatOpenAI` de LangChain pointé sur le proxy (`base_url` ou `openai_api_base` = `http://<hôte>:4000`) | [DOC] ✅ |
| LiteLLM → Langfuse | intégration documentée (mode proxy) | [README Langfuse] |
| LangChain → Langfuse | intégration par callback handler | [README Langfuse] |
| **Runtime → OPA** | ContextForge ne mentionne pas OPA. deepagents offre officiellement `middleware=` (middleware ajouté à sa pile), `interrupt_on=` (pause avant les appels d'outils) et `permissions=` (contrôle d'accès par chemin). → Un **middleware RATISS** interroge OPA et applique la décision : refus, pause ou exécution | Points d'ancrage [DOC] ✅ ; middleware lui-même **à écrire** |
| llm-sandbox → gVisor | `runsc` se déclare dans `/etc/docker/daemon.json` (`runtimes.runsc.path`) ; ensuite tout conteneur lancé avec `--runtime=runsc`, ou par défaut via `default-runtime`, est isolé. llm-sandbox passe par Docker | [DOC] ✅ ; option de runtime côté llm-sandbox **à vérifier au montage** |
| skills → deepagents | deepagents suit la **spécification Agent Skills** : SKILL.md avec frontmatter `name` (≤ 64 caractères, minuscules et tirets) + `description` (≤ 1024), et en option `license`, `compatibility` (≤ 500), `metadata`, `allowed-tools` (orthographe de la spécification ; la référence deepagents écrit `allowed_tools` : divergence à tester au montage). Chargement en 3 niveaux (métadonnées → corps → ressources) ; corps conseillé < 5 000 tokens ; paramètre `skills=["./skills/"]` | [DOC] ✅ |
| Cisco scanner → admission | mode hors ligne sur des fichiers JSON, sans clé API (YARA) : utilisable en CI avant d'enregistrer un serveur | [README] |
| Open WebUI → RATISS | Open WebUI se connecte à MCP, MCPO et aux serveurs d'outils OpenAPI | [README] |
| Résultats → RATISS-Framework | hash SHA-256 de chaque artefact et événement | **Pièce maison** — interface définie en phase 0 |

## 3. Points de friction connus

1. 🟠 **`langchain.mcp` est en bêta.** Figer les versions (voir `VERSIONS.md`).
1b. 🟠 **SSE est déprécié** : exposer tout en Streamable HTTP (ContextForge le permet ; playwright-mcp et postgres-mcp, qui utilisent stdio/SSE, passent derrière ContextForge).
1c. 🟠 **gVisor et systemd** : la documentation signale qu'il peut falloir régler le pilote cgroup de Docker (`native.cgroupdriver=cgroupfs`).
2. ✅ **Python 3.12 prouvé** : ContextForge exige ≥ 3.12 et < 3.14 (PyPI) ; toutes les autres briques acceptent 3.12. L'Inspector MCP exige **Node ≥ 22.19**.
3. 🟠 **gVisor** : Linux uniquement. Il ne tournera pas sur un poste Windows ou macOS sans VM.
4. 🟠 **microsandbox** (alternative) : exige KVM. Vérifier que le VPS l'autorise avant de le choisir.
5. 🟠 **jupyter-mcp-server** : il faut un service JupyterLab séparé dans le Compose.
6. 🟠 **Serveurs MCP cyber** : nmap demande `--cap-add=NET_RAW`. Ils doivent tourner dans un réseau Docker isolé, sur des cibles autorisées uniquement.
7. 🟠 **Deux bases ?** Langfuse a sa propre pile de stockage. En V1, l'accepter, ou bien commencer sans Langfuse et se contenter du journal RATISS.
