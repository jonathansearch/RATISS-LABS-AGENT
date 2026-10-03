# RATISS LABS AGENT — ÉTAPE C : image des ponts stdio -> Streamable HTTP
#
# Contexte vérifié (relevés du 03/10/2026, PR étape C) :
#   - l'image officielle ContextForge (ghcr.io/ibm/mcp-context-forge:v1.0.11)
#     n'embarque NI Node ni uv (désinstallés en fin de son Containerfile) :
#     elle ne peut donc pas lancer directement les serveurs MCP stdio
#     prescrits par le PROMPT (filesystem npm, git/fetch/arxiv PyPI) ;
#   - la voie officielle ContextForge pour les serveurs stdio est son pont
#     intégré `mcpgateway.translate` (docs/docs/using/mcpgateway-translate.md) :
#     `python -m mcpgateway.translate --stdio "<cmd>" --expose-streamable-http`.
#
# Cette image n'invente rien : elle installe les paquets officiels épinglés
# au EXACTES versions de VERSIONS.md / relevés du 03/10/2026 et fournit les
# 4 commandes attendues sur le PATH. Le même paquet ContextForge 1.0.11 y
# est installé pour fournir `mcpgateway.translate` (une seule source du pont).
#
# Serveurs embarqués (tous lancés en stdio par le compose, un conteneur chacun) :
#   - mcp-server-filesystem  2026.8.31 (npm @modelcontextprotocol/server-filesystem)
#   - mcp-server-git         2026.8.18 (PyPI)
#   - mcp-server-fetch       2026.8.18 (PyPI)
#   - arxiv-mcp-server       0.7.3     (PyPI — VERSIONS.md)
#   - mcpgateway (translate) 1.0.11    (PyPI mcp-contextforge-gateway — VERSIONS.md)

# syntax=docker/dockerfile:1

###############################################################################
# Étape 1 : Node + serveur filesystem npm, épinglés.
# node:22-bookworm-slim (LTS 22, exigé >= 22.19 par l'Inspector MCP, VERSIONS.md).
# Digest relevé sur Docker Hub le 03/10/2026.
###############################################################################
ARG NODE_IMAGE=node:22-bookworm-slim@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c
FROM ${NODE_IMAGE} AS node
RUN npm install -g --no-audit --no-fund \
      @modelcontextprotocol/server-filesystem@2026.8.31 \
 && node -e "console.log('server-filesystem installé, node', process.version)"

###############################################################################
# Étape 2 (runtime) : Python 3.12 slim — le MÊME digest de base que
# docker/llm-gateway.Dockerfile (étape B), déjà vérifié.
###############################################################################
FROM python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016

# Node + paquet npm global (node et ses libs vivent sous /usr/local).
COPY --from=node /usr/local /usr/local

# Paquets Python épinglés dans un venv dédié, commandes sur le PATH.
# Aucun extra lourd : les ponts n'ont besoin que du noyau ContextForge.
RUN python -m venv /opt/ratiss-mcp-venv \
 && /opt/ratiss-mcp-venv/bin/pip install --no-cache-dir \
      "mcp-contextforge-gateway==1.0.11" \
      "mcp-server-git==2026.8.18" \
      "mcp-server-fetch==2026.8.18" \
      "arxiv-mcp-server==0.7.3" \
 && /opt/ratiss-mcp-venv/bin/python -c "import mcpgateway.translate" \
 && echo "ponts RATISS installés (contextforge 1.0.11 + 4 serveurs)"

ENV PATH="/opt/ratiss-mcp-venv/bin:/usr/local/bin:${PATH}"

# Les ponts sont lancés par docker-compose.yml (un service par serveur) :
#   python -m mcpgateway.translate --stdio "<cmd serveur>" \
#     --expose-streamable-http --host 0.0.0.0 --port <n>
# Commande par défaut d'aide (aucun service démarré par l'image elle-même).
CMD ["python", "-m", "mcpgateway.translate", "--help"]
