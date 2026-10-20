.PHONY: lint format fix test eval

lint:
	uv run ruff check .

format:
	uv run ruff format .

fix:
	uv run ruff check . --fix

test:
	uv run pytest -v

refresh-weekly:
	gcloud run jobs execute portfolio-weekly-refresh-job --region=us-central1

refresh-biweekly:
	gcloud run jobs execute portfolio-biweekly-refresh-job --region=us-central1

eval:
	uv run python -m evals.run_tool_calls_eval