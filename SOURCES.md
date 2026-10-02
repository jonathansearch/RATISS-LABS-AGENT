# 🔎 SOURCES DE LA CAMPAGNE (02/10/2026)

## Méthode

1. **Liste initiale**, puis vérification de chaque dépôt via l'API GitHub : existence, archivage, licence, étoiles, dernière activité.
2. **Recherche web ouverte** sur 7 sujets :
   - passerelles MCP ;
   - sécurité MCP ;
   - LangGraph + MCP + approbation humaine ;
   - sandboxes auto-hébergées ;
   - serveurs MCP cyber ;
   - serveurs MCP scientifiques ;
   - microVM.
3. **Lecture des README** de 36 briques candidates : transports, prérequis, stockage, déploiement, état de maintenance.
4. **Lecture des fichiers LICENSE** de tous les dépôts ambigus.
5. Aucune installation, aucun code exécuté.

## Sources web qui ont changé des décisions

| Source | Ce qu'elle a apporté |
|---|---|
| Changelog LangChain — https://docs.langchain.com/oss/python/releases/changelog | MCP intégré à `langchain.mcp` (v1.4, bêta, sur FastMCP), qui remplace `langchain-mcp-adapters` ; élicitation MCP transformée en `interrupt()` |
| Comparatif de passerelles MCP — https://manveerc.substack.com/p/best-mcp-gateways | Docker MCP Gateway convient au local ; ContextForge à l'auto-hébergement avec fédération |
| Comparatif de passerelles open source — https://www.getmaxim.ai/articles/open-source-mcp-gateways-claude-code/ | Transports et licences de ContextForge, agentgateway, Obot et MetaMCP |
| Outils de sécurité MCP — https://www.getmaxim.ai/articles/best-mcp-security-tools-in-2026/ | Snyk Agent Scan succède à mcp-scan ; Cisco MCP Scanner propose un mode hors ligne |
| Alternatives à E2B — https://temps.sh/blog/best-e2b-alternatives-ai-sandboxes-2026 | Daytona non maintenu depuis juin 2026 (**confirmé dans son README**) |
| Comparatif de sandboxes — https://www.beam.cloud/blog/best-e2b-alternatives | microsandbox, dify-sandbox ; isolations comparées |
| Serveurs MCP cyber — https://github.com/FuzzingLabs/mcp-security-hub | Serveurs MCP offensifs avec docker-compose |
| Motif d'approbation LangGraph — https://www.permit.io/blog/delegating-ai-permissions-to-human-users-with-permitios-access-request-mcp | `interrupt()` + MCP pour l'approbation humaine |

## Documentation officielle (2e passe : vérification des jonctions)

| Source | Ce qu'elle confirme |
|---|---|
| deepagents, Skills — https://docs.langchain.com/oss/python/deepagents/skills | Spécification Agent Skills, SKILL.md, chargement en 3 niveaux |
| deepagents, Customization — https://docs.langchain.com/oss/python/deepagents/customization | Paramètres `skills=`, `middleware=`, `interrupt_on=`, `permissions=` |
| Référence du middleware skills — https://reference.langchain.com/python/deepagents/middleware/skills | Limites de `name` et `description`, champs optionnels |
| LangChain MCP — https://docs.langchain.com/oss/python/langchain/mcp | `MCPAdapter`, transports déduits de la cible |
| Migration — https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters | SSE déprécié, élicitation transformée en interrupts |
| FAQ ContextForge — https://ibm.github.io/mcp-context-forge/faq/ | Recette LangChain, `/mcp`, `/servers/<UUID>/mcp`, Bearer |
| LiteLLM — https://docs.litellm.ai/docs/providers/openai | `ChatOpenAI` pointé sur le proxy |
| Installation de gVisor (Read the Docs) — https://docs.readthedocs.com/dev/latest/guides/gvisor.html | `daemon.json`, test `dmesg`, réglage cgroup |
| PyPI, npm, releases GitHub | Versions et exigences de Python et Node (`VERSIONS.md`) |

## ⚠️ Contradictions relevées entre le web et les README

- Un article présente **Bifrost** comme passerelle MCP open source. Son README range la passerelle MCP dans l'**offre Enterprise**. → **C'est le README qui fait foi.**
- Un comparatif classe **ContextForge** comme « Commercial ». Son dépôt est sous **Apache-2.0** (API GitHub). → **Le dépôt fait foi.**
