.PHONY: install dev check test lint fmt

install:            ## install the Python workspace
	uv sync

dev:                ## run the API with reload
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
