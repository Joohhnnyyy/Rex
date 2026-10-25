.PHONY: install dev check test lint fmt infra-up infra-down progress

install:            ## install the Python workspace
	uv sync

dev:                ## run the API with reload (agent + web added in Phase 01)
	uv run uvicorn rex_api.main:app --reload --port 8000

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest

check: lint test    ## what CI runs

infra-up:           ## postgres + redis
	docker compose -f infra/docker-compose.yml up -d

infra-down:
	docker compose -f infra/docker-compose.yml down

progress:           ## regenerate PROGRESS.md from the project graph
	python3 scripts/progress.py
