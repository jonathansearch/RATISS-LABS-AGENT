# 📚 CATALOGUE — RATISS LABS AGENT (v1)

**84 dépôts**, chacun vérifié via l'API GitHub le **02/10/2026** : il existe et n'est pas archivé. Les étoiles et dates sont relevées ce jour-là. Les rôles viennent de la lecture des README (voir `COMPATIBILITE.md`).

Statuts : **V1** = à monter en premier · **alt** = alternative · **plus tard** = industrialisation · **hors V1** = déconseillé par le brief (§46) · **inspiration** / **catalogue** / **outil** = référence.

## 1. Protocole MCP (contrat)

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) | 9364 | NOASSERTION | 2026-10-02 | Spécification officielle : contrat de toute la couche outils |
| V1 | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | 24459 | MIT | 2026-10-02 | SDK officiel Python, clients et serveurs MCP |
| alt | [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | 13503 | NOASSERTION | 2026-10-02 | SDK officiel TypeScript |
| V1 | [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp) | 27959 | Apache-2.0 | 2026-10-02 | Écrire les serveurs MCP RATISS maison ; base de langchain.mcp |
| V1 | [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) | 11008 | NOASSERTION | 2026-10-02 | Banc de test visuel de chaque serveur MCP avant admission |
| alt | [modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry) | 7308 | NOASSERTION | 2026-09-30 | Registre communautaire : modèle pour tools.yaml / mcp.yaml |
| V1 | [cloudevents/spec](https://github.com/cloudevents/spec) | 5919 | Apache-2.0 | 2026-09-03 | Format standard pour le schéma Event (phase 0) |

## 2. MCP Gateway

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [IBM/mcp-context-forge](https://github.com/IBM/mcp-context-forge) | 4561 | Apache-2.0 | 2026-10-02 | Registre + proxy + serveurs virtuels ; SQLite puis PostgreSQL, Redis, OTel, Compose ; fédère stdio en HTTP |
| alt | [docker/mcp-gateway](https://github.com/docker/mcp-gateway) | 1588 | MIT | 2026-09-23 | Un conteneur par serveur MCP ; avec ou sans Docker Desktop ; plutôt usage local |
| alt | [obot-platform/obot](https://github.com/obot-platform/obot) | 1084 | MIT | 2026-10-02 | Plateforme de gouvernance MCP (catalogue, RBAC), MIT |
| alt | [agentgateway/agentgateway](https://github.com/agentgateway/agentgateway) | 5143 | Apache-2.0 | 2026-10-02 | Proxy agentique MCP + A2A, orienté Kubernetes |
| alt | [TheLunarCompany/lunar](https://github.com/TheLunarCompany/lunar) | 503 | MIT | 2026-10-01 | Passerelle MCP gouvernance et sécurité (MCPX) |
| alt | [microsoft/mcp-gateway](https://github.com/microsoft/mcp-gateway) | 858 | MIT | 2026-10-02 | Reverse proxy MCP orienté Kubernetes/Azure |
| alt | [metatool-ai/metamcp](https://github.com/metatool-ai/metamcp) | 2693 | MIT | 2026-06-22 | Agrégateur MCP en un seul Docker |
| outil | [sparfenyuk/mcp-proxy](https://github.com/sparfenyuk/mcp-proxy) | 2770 | MIT | 2026-07-20 | Pont stdio vers Streamable HTTP |

## 3. Serveurs MCP (outils)

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 90957 | NOASSERTION | 2026-10-01 | Référence : filesystem, git, fetch, memory, time |
| V1 | [github/github-mcp-server](https://github.com/github/github-mcp-server) | 33330 | MIT | 2026-10-02 | GitHub officiel (Repository sandbox) ; token GitHub requis |
| V1 | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 37766 | Apache-2.0 | 2026-09-28 | Navigateur piloté (Browser sandbox), Node 18+ |
| alt | [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | 52890 | Apache-2.0 | 2026-10-02 | Chrome DevTools pour agents |
| V1 | [datalayer/jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server) | 1293 | BSD-3-Clause | 2026-10-01 | Notebooks (Python sandbox) ; nécessite un JupyterLab en marche |
| V1 | [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) | 3186 | Apache-2.0 | 2026-10-02 | arXiv : recherche, LaTeX, BibTeX ; Python 3.11+ |
| alt | [LinXueyuanStdio/academic-mcp](https://github.com/LinXueyuanStdio/academic-mcp) | 44 | MIT | 2026-08-16 | 19 sources académiques (PubMed, bioRxiv, Semantic Scholar) ; projet jeune |
| V1 | [crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp) | 3364 | MIT | 2026-08-17 | Accès PostgreSQL contrôlé (lecture seule possible) |
| alt | [qdrant/mcp-server-qdrant](https://github.com/qdrant/mcp-server-qdrant) | 1542 | Apache-2.0 | 2026-09-04 | Mémoire vectorielle via MCP (si Qdrant plutôt que pgvector) |
| alt | [upstash/context7](https://github.com/upstash/context7) | 62609 | MIT | 2026-10-02 | Documentation de code à jour (workflow dev) |
| V1 cyber | [FuzzingLabs/mcp-security-hub](https://github.com/FuzzingLabs/mcp-security-hub) | 795 | MIT | 2026-04-08 | Serveurs MCP cyber (nmap, nuclei, semgrep, yara, trivy) avec docker-compose |
| outil | [semgrep/semgrep](https://github.com/semgrep/semgrep) | 16839 | LGPL-2.1 | 2026-10-02 | Le serveur MCP Semgrep est désormais intégré au binaire semgrep |
| catalogue | [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | 95767 | MIT | 2026-09-27 | Annuaire géant : piocher, jamais tout brancher |
| catalogue | [wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers) | 4342 | MIT | 2026-07-13 | Annuaire curé |

## 4. Sécurité MCP / Policy

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [cisco-ai-defense/mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner) | 1083 | Apache-2.0 | 2026-10-02 | Scan d'admission des serveurs MCP ; moteur YARA hors ligne sans clé API |
| alt | [snyk/agent-scan](https://github.com/snyk/agent-scan) | 3110 | Apache-2.0 | 2026-10-02 | Scan MCP + skills (ex-mcp-scan) ; dépend du service Snyk |
| V1 | [open-policy-agent/opa](https://github.com/open-policy-agent/opa) | 12305 | Apache-2.0 | 2026-10-02 | Policy Engine ALLOW / DENY / REQUIRE_APPROVAL, appelé par le runtime |
| alt | [cedar-policy/cedar](https://github.com/cedar-policy/cedar) | 1760 | Apache-2.0 | 2026-10-02 | Langage de politiques alternatif |
| alt | [invariantlabs-ai/invariant](https://github.com/invariantlabs-ai/invariant) | 466 | Apache-2.0 | 2026-01-12 | Garde-fous sur traces d'agent |
| alt | [NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) | 7234 | NOASSERTION | 2026-10-02 | Garde-fous conversationnels |
| plus tard | [pomerium/pomerium](https://github.com/pomerium/pomerium) | 5027 | Apache-2.0 | 2026-10-02 | Proxy d'accès par identité devant l'UI et l'API (reverse proxy HTTPS/Auth du §31) |

## 5. Agent Runtime

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 42626 | MIT | 2026-10-02 | Runtime en graphe : persistance, checkpoints, interrupt() = approbation humaine |
| V1 | [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) | 29907 | MIT | 2026-10-02 | Harnais sur LangGraph : planification, sous-agents, filesystem, skills à la demande, HITL approve/edit/reject, MCP |
| V1 | [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 147386 | MIT | 2026-10-02 | Fournit langchain.mcp (v1.4, bêta, bâti sur FastMCP) : remplace langchain-mcp-adapters (archivé) |
| alt | [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | 20361 | MIT | 2026-10-02 | Runtime typé, MCP natif |
| alt | [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 29807 | MIT | 2026-10-02 | Runtime léger, MCP natif |
| alt | [huggingface/smolagents](https://github.com/huggingface/smolagents) | 29652 | Apache-2.0 | 2026-09-30 | Agents minimalistes qui pensent en code |
| inspiration | [lastmile-ai/mcp-agent](https://github.com/lastmile-ai/mcp-agent) | 8568 | Apache-2.0 | 2026-01-25 | Patterns de workflows sur MCP (activité réduite depuis janvier 2026) |
| plus tard | [temporalio/temporal](https://github.com/temporalio/temporal) | 23423 | MIT | 2026-10-02 | Exécution durable des tâches longues |
| hors V1 | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 59289 | MIT | 2026-10-02 | Multi-agents par rôles : swarm déconseillé en V1 |
| hors V1 | [microsoft/autogen](https://github.com/microsoft/autogen) | 61248 | CC-BY-4.0 | 2026-04-15 | Multi-agents : référence seulement |

## 6. Model Gateway

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [BerriAI/litellm](https://github.com/BerriAI/litellm) | 60057 | NOASSERTION | 2026-10-02 | Proxy OpenAI-compatible vers GLM, Claude, Ollama ; MIT hors dossier enterprise/ |
| alt | [maximhq/bifrost](https://github.com/maximhq/bifrost) | 8525 | Apache-2.0 | 2026-10-02 | LLM gateway rapide ; sa passerelle MCP est réservée à l'offre Enterprise |
| alt | [Portkey-AI/gateway](https://github.com/Portkey-AI/gateway) | 13118 | MIT | 2026-05-25 | Passerelle IA avec garde-fous |
| V1 | [ollama/ollama](https://github.com/ollama/ollama) | 182061 | MIT | 2026-10-02 | Modèles locaux (GLM, Qwen, DeepSeek) |
| plus tard | [vllm-project/vllm](https://github.com/vllm-project/vllm) | 93077 | Apache-2.0 | 2026-10-02 | Inférence haut débit GPU |

## 7. Sandboxes d'exécution

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [vndee/llm-sandbox](https://github.com/vndee/llm-sandbox) | 1128 | MIT | 2026-10-01 | Exécution de code en conteneur Docker/Podman/K8s + serveur MCP intégré ; léger |
| V1 | [google/gvisor](https://github.com/google/gvisor) | 19477 | Apache-2.0 | 2026-10-02 | Runtime runsc branché sur Docker : durcit les conteneurs sans changer Compose |
| alt | [superradcompany/microsandbox](https://github.com/superradcompany/microsandbox) | 8518 | Apache-2.0 | 2026-10-02 | MicroVMs locales + serveur MCP ; exige KVM (Linux) ou Apple Silicon |
| alt | [langgenius/dify-sandbox](https://github.com/langgenius/dify-sandbox) | 1270 | Apache-2.0 | 2026-09-09 | Exécution Python/Node isolée seccomp, légère |
| plus tard | [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | 14116 | Apache-2.0 | 2026-10-02 | Excellent SDK ; auto-hébergement via Terraform (lourd pour une V1) |
| alt | [e2b-dev/code-interpreter](https://github.com/e2b-dev/code-interpreter) | 2419 | Apache-2.0 | 2026-09-30 | SDK code-interpreter E2B |
| plus tard | [firecracker-microvm/firecracker](https://github.com/firecracker-microvm/firecracker) | 37118 | Apache-2.0 | 2026-10-02 | MicroVMs : isolation forte (cyber) |
| V1 | [browser-use/browser-use](https://github.com/browser-use/browser-use) | 117003 | MIT | 2026-10-02 | Agent navigateur (Browser sandbox) — dépôt à garder ; Python 3.12 |
| catalogue | [fishman/awesome-agent-sandbox](https://github.com/fishman/awesome-agent-sandbox) | 18 | non déclarée | 2026-07-07 | Annuaire de sandboxes pour agents |

## 8. Mémoire

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [pgvector/pgvector](https://github.com/pgvector/pgvector) | 23222 | NOASSERTION | 2026-10-01 | Mémoire documentaire dans PostgreSQL (une seule base en V1) |
| inspiration | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | 95190 | Apache-2.0 | 2026-10-02 | Conçu pour Claude Code (plugin + worker) : modèle de compression mémoire — dépôt à garder |
| alt | [mem0ai/mem0](https://github.com/mem0ai/mem0) | 66484 | Apache-2.0 | 2026-10-01 | Couche mémoire auto-hébergeable (Compose) |
| alt | [getzep/graphiti](https://github.com/getzep/graphiti) | 31385 | Apache-2.0 | 2026-10-02 | Graphe de connaissances temporel |
| alt | [letta-ai/letta](https://github.com/letta-ai/letta) | 25005 | Apache-2.0 | 2026-09-10 | Agents à mémoire gérée |

## 9. Provenance / Vérification / Observabilité

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [jonathansearch/RATISS-Framework](https://github.com/jonathansearch/RATISS-Framework) | 0 | MIT | 2026-10-01 | Cœur de vérification transversal : SHA-256, journal, provenance (§32) |
| V1 | [langfuse/langfuse](https://github.com/langfuse/langfuse) | 35320 | NOASSERTION | 2026-10-02 | Traces : intégrations LangChain et LiteLLM documentées ; Compose ; MIT hors dossiers ee/ |
| V1 | [open-telemetry/opentelemetry-python](https://github.com/open-telemetry/opentelemetry-python) | 2655 | Apache-2.0 | 2026-10-02 | Standard de traces (ContextForge l'émet) |
| alt | [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | 11684 | NOASSERTION | 2026-10-02 | Observabilité ; licence Elastic 2.0 (pas de revente en service) |
| plus tard | [sigstore/cosign](https://github.com/sigstore/cosign) | 6343 | Apache-2.0 | 2026-10-02 | Signature des artefacts et versions de skills |
| plus tard | [in-toto/in-toto](https://github.com/in-toto/in-toto) | 1049 | NOASSERTION | 2026-08-27 | Chaîne de provenance (manifest de run), Apache-2.0 |
| alt | [mlflow/mlflow](https://github.com/mlflow/mlflow) | 28238 | Apache-2.0 | 2026-10-02 | Suivi d'expériences et d'artefacts |

## 10. Skills (chargement progressif)

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [anthropics/skills](https://github.com/anthropics/skills) | 179400 | non déclarée | 2026-09-29 | Format SKILL.md ; licence PAR skill (certaines Apache-2.0, d'autres propriétaires) |
| V1 | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 47367 | MIT | 2026-10-01 | Skills scientifiques — dépôt à garder, MIT |
| V1 | [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) | 33713 | Apache-2.0 | 2026-08-31 | 817 skills cyber MITRE ATT&CK — dépôt à garder, Apache-2.0 |
| V1 | [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | 43089 | MIT | 2026-10-01 | Skill de diagrammes — dépôt à garder, MIT |

## 11. Interface (UI)

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| banc d'essai | [open-webui/open-webui](https://github.com/open-webui/open-webui) | 153806 | NOASSERTION | 2026-10-02 | Chat + MCP/MCPO/OpenAPI ; marque Open WebUI obligatoire au-delà de 50 utilisateurs / 30 jours |
| alt | [LibreChat-AI/LibreChat](https://github.com/LibreChat-AI/LibreChat) | 45202 | MIT | 2026-10-02 | Chat auto-hébergé, MCP intégré, MIT |
| V1 | [assistant-ui/assistant-ui](https://github.com/assistant-ui/assistant-ui) | 12384 | MIT | 2026-10-02 | Option A : composants React pour l'UI maison RATISS, MIT |
| inspiration | [vercel/chatbot](https://github.com/vercel/chatbot) | 20983 | NOASSERTION | 2026-07-08 | Modèle Next.js complet, Apache-2.0 |

## 12. Stockage

| Statut | Dépôt | ⭐ | Licence (API) | Activité | Rôle dans RATISS |
|---|---|---|---|---|---|
| V1 | [postgres/postgres](https://github.com/postgres/postgres) | 22265 | NOASSERTION | 2026-10-02 | Base unique V1 (dépôt miroir ; image Docker officielle) |
| V1 | [rustfs/rustfs](https://github.com/rustfs/rustfs) | 34317 | Apache-2.0 | 2026-10-02 | Object storage S3, réimplémentation de MinIO, Apache-2.0 |
| alt | [seaweedfs/seaweedfs](https://github.com/seaweedfs/seaweedfs) | 35207 | Apache-2.0 | 2026-10-02 | Object storage S3 distribué, Apache-2.0 |
| alt | [deuxfleurs-org/garage](https://github.com/deuxfleurs-org/garage) | 4629 | AGPL-3.0 | 2026-10-02 | Object storage S3 léger (AGPL-3.0) |

## ❌ Écartés après vérification

| Dépôt | Raison |
|---|---|
| daytonaio/daytona | README : « This repository is no longer maintained » (développement passé en privé, juin 2026) |
| langchain-ai/langchain-mcp-adapters | Archivé ; remplacé par `langchain.mcp` dans LangChain v1.4 |
| minio/minio | Archivé ; développement arrêté en avril 2026 |
| e2b-dev/mcp-server | Archivé |
| appcypher/awesome-mcp-servers | Archivé |
| semgrep/mcp | Archivé ; le serveur MCP est intégré au binaire semgrep |

## 🔁 Dépôts renommés (corrigés)

- jlowin/fastmcp → PrefectHQ/fastmcp
- invariantlabs-ai/mcp-scan → snyk/agent-scan
- NVIDIA/NeMo-Guardrails → NVIDIA-NeMo/Guardrails
- danny-avila/LibreChat → LibreChat-AI/LibreChat
- vercel/ai-chatbot → vercel/chatbot
- zerocore-ai/microsandbox → superradcompany/microsandbox
