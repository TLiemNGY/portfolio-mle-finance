# ADR-019: Image Tagging and Deployment Ownership

**Status:** Accepted
**Date:** 2026-10-15

## Context

The API service and the two ingestion jobs all run the same Docker image, tagged `api:latest`. The image is also written in `infra/cloud_run.tf`, managed by OpenTofu.

This raises three problems:

- **No traceability.** `latest` does not say which code is running. Rolling back means rebuilding an old commit, since the previous `latest` has been overwritten.
- **Two tools own the same field.** Once images carry a version tag, deploying a new one with `gcloud` makes the running service differ from `cloud_run.tf`, and the next `tofu apply` would silently revert it. Each `gcloud` deployment also sets `client` / `client_version` fields that show up as permanent noise in `tofu plan`.
- **Development tools ship to production.** `uv sync` installs the `dev` group by default, so the image contains `pytest`, `ruff` and `pre-commit`.

## Decision

1. **Images are tagged with the short git commit SHA** (e.g. `api:a1b2c3d`). Each tag is immutable and points to an exact commit.
2. **The deployment owns the image; OpenTofu owns everything else.** OpenTofu manages the service and jobs (existence, region, service account, secrets, timeouts). The image is set by the deployment step — `gcloud` today, the CD pipeline later. In `cloud_run.tf`, a `lifecycle { ignore_changes = [...] }` block excludes the image and the `client` / `client_version` fields; the image value written there is only the initial one.
3. **The image excludes development dependencies** (`uv sync --no-dev`), and `UV_NO_SYNC=1` prevents `uv run` from re-syncing — and so re-installing the `dev` group — when the container starts.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Keep `latest` | No traceability of the running code, no simple rollback. |
| OpenTofu owns the image (edit `cloud_run.tf` at each deployment) | Turns every code release into an infrastructure change, and conflicts with an automated CD pipeline. |
| Run `uvicorn` from the virtualenv `PATH` instead of `uv run` | Equally valid, but would also require changing the jobs' `command`; `UV_NO_SYNC` keeps both working unchanged. |

## Consequences

- To know which code is running: `gcloud run services describe ... --format="value(spec.template.spec.containers[0].image)"`, not `cloud_run.tf`.
- Rollback = redeploy the previous commit's tag; the image is still in Artifact Registry.
- The deployment commands (build, push, update the service and both jobs) are exactly what the CD pipeline will automate.
