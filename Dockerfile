FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Production image: no development tools (pytest, ruff, pre-commit).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# The environment is fully built above: `uv run` must not re-sync it at
# startup (it would re-install the dev group). See ADR-019.
ENV UV_NO_SYNC=1

EXPOSE 8080

CMD ["sh", "-c", "exec uv run uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]