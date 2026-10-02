# RATISS LABS AGENT — tâches de développement (local uniquement)
#
# Aucune cible ne démarre de service, ne contacte un provider ni ne publie.

.PHONY: help test test-venv demo lock licences clean

help:
	@echo "make test        - tests du socle (python système)"
	@echo "make test-venv   - tests dans le venv isolé (LangGraph/LiteLLM réels)"
	@echo "make demo        - démo question -> réponse mock (hors ligne)"
	@echo "make lock        - régénère le lock reproductible"
	@echo "make licences    - régénère l'inventaire de licences"
	@echo "make clean       - supprime les caches"

test:
	python3 -m pytest tests/

test-venv:
	.venv/bin/python -m pytest tests/

demo:
	PYTHONPATH=src python3 -m ratiss_agent.demo "Quelle est la capitale du Cameroun ?"

lock:
	.venv/bin/pip freeze --exclude-editable > requirements-phase1.lock.txt

licences:
	.venv/bin/python scripts/inventaire_licences.py > docs/architecture/LICENCES-PHASE1.md

clean:
	rm -rf .pytest_cache tests/__pycache__ src/ratiss_agent/__pycache__
