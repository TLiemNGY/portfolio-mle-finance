.PHONY: lint format fix test

lint:
	uv run ruff check .

format:
	uv run ruff format .

fix:
	uv run ruff check . --fix

test:
	uv run pytest -v