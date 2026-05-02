.PHONY: install run dev test lint fmt typecheck eval sync-vectors seed-kb clean

install:
	uv sync

run:
	uv run uvicorn aptguide.main:app --host 0.0.0.0 --port 8100

dev:
	uv run uvicorn aptguide.main:app --reload --host 0.0.0.0 --port 8100

test:
	uv run pytest

lint:
	uv run ruff check src tests

fmt:
	uv run ruff format src tests

typecheck:
	uv run mypy src

eval:
	uv run python -m evals.runner

sync-vectors:
	uv run python scripts/sync_room_vectors.py

seed-kb:
	uv run python scripts/seed_kb.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache **/__pycache__
