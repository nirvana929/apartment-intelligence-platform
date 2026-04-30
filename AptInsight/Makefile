.PHONY: run test lint format eval

run:
	uv run uvicorn aptinsight.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

eval:
	uv run python -m evals.runners.text_to_sql

