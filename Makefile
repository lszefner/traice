.PHONY: help venv install run docker-build docker-run test test-integration lint format clean

PYTHON ?= python3
VENV := .venv
TAG ?= traice:dev

help:
	@printf '%s\n' 'make install           Create a virtualenv and install dependencies' 'make run               Run the API locally on :8000' 'make docker-build      Build the API image' 'make docker-run        Start the Compose stack' 'make test              Run tests with coverage (no live Neo4j required)' 'make test-integration  Run integration tests against a running stack' 'make lint              Run pylint on app' 'make format            Format app and tests with black' 'make clean             Remove Python caches and coverage outputs'

venv:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)

install: venv
	$(VENV)/bin/pip install -r requirements.txt

run:
	$(VENV)/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

docker-build:
	docker compose build

docker-run:
	docker compose up --build -d

test:
	$(VENV)/bin/pytest -m 'not integration' --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=60

test-integration:
	$(VENV)/bin/pytest -m integration

lint:
	$(VENV)/bin/pylint --fail-under=9.5 app

format:
	$(VENV)/bin/black -l 120 app tests

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .coverage coverage.xml htmlcov
