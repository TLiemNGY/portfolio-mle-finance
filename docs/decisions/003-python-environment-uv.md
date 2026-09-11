# ADR-003: uv for Python Environment and Dependency Management

## Status
Accepted

## Context
The project needs a Python virtual environment and dependency
management workflow. The traditional pip + venv + requirements.txt
combination was the initial default, used without a lockfile in the
early ingestion scripts.

## Decision
Adopted uv (Astral) for virtual environment creation and dependency
management project-wide, with pyproject.toml and uv.lock committed
to version control.

## Alternatives Considered
- **pip + venv + requirements.txt**: rejected going forward — no
  lockfile by default, slower installs, and less representative of
  current industry practice.
- **poetry**: not evaluated in depth; uv was preferred for its speed
  and growing adoption as the emerging standard in 2026.

## Consequences
- Reproducible installs via uv.lock — anyone cloning the repo gets
  identical dependency versions.
- `uv run` removes the need for manual environment activation,
  which proved inconsistently reliable in the Git Bash terminal used
  for development.
- Existing pip-installed dependencies were migrated to uv without
  issue.
