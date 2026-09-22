# ADR-013: No Caching for Tool BigQuery Calls (For Now)

## Status
Accepted

## Context
Each agent tool call (`get_portfolio_summary`, `get_latest_price`,
`get_volatility_forecast`) queries BigQuery live. Caching these
results (either short-lived request caching, or serving purely from
data pre-fetched by the existing ingestion scripts) was considered as
a potential latency optimization for the `/chat` endpoint.

Two caching strategies were discussed:
- **Result caching**: reuse a recent query result for identical
  requests within a short time window (e.g. a few minutes), to avoid
  redundant BigQuery round-trips.
- **Pre-fetch architecture**: rely entirely on data already ingested
  by scheduled batch/streaming jobs (`fetch_market_prices.py`,
  `load_price_history.py`), never querying external sources live from
  within a tool call — largely already the case today.

## Decision
Do not implement result caching at this stage. No architecture change
needed for the pre-fetch strategy either, since tools already only
read from BigQuery tables populated by the existing ingestion
pipeline, never from external APIs directly.

## Alternatives Considered
- **Add a short-lived cache (e.g. `functools.lru_cache`, or Redis)
  for tool queries**: rejected for now — BigQuery is not the
  measured bottleneck at this project's traffic and data volume
  (a query against ~6,000 rows returns in a fraction of a second).
  The dominant source of latency in a `/chat` request is the Gemini
  API call itself, not BigQuery. Optimizing a non-bottleneck would be
  premature optimization, and a poorly-scoped cache risks serving
  stale financial data (price, volatility) without a clear
  invalidation rule.

## Consequences
- No caching layer to design, invalidate, or reason about for now —
  simpler system, consistent with the project's real-utility
  principle (ML/infra complexity should be justified by a measured
  need, not added speculatively).
- Revisit if either becomes true: (a) actual concurrent usage grows
  enough that BigQuery cost/latency becomes measurable, or (b) a
  profiling pass (e.g. simple timing logs around each tool call)
  shows BigQuery, not Gemini, as the dominant latency source.
