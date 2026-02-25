.PHONY: dev test lint format

dev:
	uv run uvicorn dcc.app:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
