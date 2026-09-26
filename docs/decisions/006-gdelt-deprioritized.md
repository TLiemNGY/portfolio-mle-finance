# ADR-006: GDELT News Ingestion Deprioritized

## Status
Accepted (revisit later)

## Context
News ingestion via the `gdeltdoc` Python client (see ADR-005)
consistently fails with a `RateLimitError`, even after:
- Waiting 30-60+ minutes between attempts
- Reducing to a single combined request per run (ADR-005)
- Patching `requests.get` to include a browser User-Agent header,
  based on a known upstream issue
  (github.com/alex9smith/gdelt-doc-api/issues/22) describing the
  same misleading rate-limit symptom caused by a missing
  User-Agent

The exact root cause was not conclusively identified: it may be a
genuine, persistent IP-level rate limit unrelated to the User-Agent
issue, a stricter or different limit than documented, or an
interaction between the two. Continuing to debug an undocumented,
free third-party API was judged not to be a good use of time
relative to this project's learning goals.

## Decision
Deprioritize GDELT-based news ingestion for now. The unstructured
news storage and RAG portions of the pipeline are paused, without
being abandoned. Development continues on the ML modeling and
agentic layers using the data already available (portfolio,
transactions, market prices).

## Alternatives Considered (for a future revisit)
- **A paid/authenticated news API** (e.g. NewsAPI, a commercial GDELT
  proxy such as APITube) — more reliable rate limits, at a cost that
  would need to fit the project's 5-15EUR/month budget.
- **Direct scraping of financial news sources** — rejected: most news sites' Terms of Service
  explicitly prohibit automated scraping. This is not a viable path to revisit later.
- **GDELT's raw HTTP API without the `gdeltdoc` wrapper** — rules out
  bugs specific to the wrapper, but reintroduces the raw query syntax
  issues encountered earlier (see ADR-005's context).

## Consequences
- The news/sentiment and RAG-over-news portions of the copilot
  product are deferred; the volatility model and portfolio-only
  copilot can proceed without them.
- `../../ingestion/streaming/fetch_news_sentiment.py` is kept in the repo, marked as
  non-functional pending this decision, rather than deleted — it
  documents the batched-query and User-Agent-patch approaches
  already tried, for whoever revisits this.
