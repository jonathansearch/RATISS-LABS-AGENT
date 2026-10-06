# RATISS LABS AGENT — image du Model Gateway (ÉTAPE B, PROMPT GLM)
#
# Pourquoi une image construite : le PROMPT exige LiteLLM proxy 1.103.2 EXACT
# (VERSIONS.md : litellm 1.103.2, déjà épinglé dans requirements-phase1.txt et
# testé par les 107 tests du noyau). Vérification faite le 03/10/2026 : le tag
# `main-v1.103.2` N'EXISTE PAS sur ghcr.io/berriai/litellm (aucun tag 1.103.2
# non plus sur Docker Hub berriai/litellm). Ce Dockerfile installe donc la
# version exacte depuis PyPI (étape de build verrouillée, jamais `latest`).
# Base épinglée par digest (relevé Docker Hub le 03/10/2026).

FROM python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016

# Version EXACTE du PROMPT/VERSIONS.md. L'extra [proxy] installe le serveur
# LiteLLM (uvicorn/fastapi). --no-cache-dir pour une image minimale.
RUN pip install --no-cache-dir "litellm[proxy]==1.103.2"

# Config montée en volume ro par docker-compose (config/litellm.yaml).
EXPOSE 4000

# Healthcheck : endpoint officiel de vivacité du proxy (doc LiteLLM :
# GET /health/liveliness -> "I'm alive!" en 200).
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:4000/health/liveliness', timeout=5)"

CMD ["litellm", "--config", "/app/config/litellm.yaml", "--host", "0.0.0.0", "--port", "4000"]
