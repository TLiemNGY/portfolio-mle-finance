FROM python:3.11-slim

# Installe uv en copiant son binaire officiel, plutôt que via pip (plus rapide, image plus légère)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copie d'abord uniquement les fichiers de dépendances (voir note sur le cache de layers plus bas)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copie le reste du code
COPY . .
RUN uv sync --frozen

EXPOSE 8080

CMD ["sh", "-c", "exec uv run uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]