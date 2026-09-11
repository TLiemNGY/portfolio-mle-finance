# ADR-005: Single Batched GDELT Query with Local Attribution

## Status
Accepted

## Context
News ingestion needs to fetch recent articles for each portfolio
ticker from GDELT's DOC 2.0 API (via the unofficial `gdeltdoc`
Python client). An initial implementation issued one GDELT request
per ticker in a loop. In practice, even a small number of sequential
requests (5 tickers) reliably triggered GDELT's rate limit, and a
tenacity-based exponential backoff retry (up to 5 attempts, 30s-5min
waits) was insufficient to recover within a reasonable time.

## Decision
Issue a single GDELT request combining all tickers' search terms
with OR, then attribute each returned article back to its ticker(s)
locally, by checking whether each ticker's search term appears in
the article title.

## Alternatives Considered
- **One request per ticker (initial approach)**: rejected — too many
  requests against an aggressive, undocumented rate limit for a
  portfolio of even 5-10 tickers.
- **One request per ticker with a fixed delay between calls**:
  considered as a lighter mitigation, but did not address the root
  cause (total request count within a rate-limit window), only
  spacing.

## Consequences
- Reduces GDELT requests from N (one per ticker) to 1 per ingestion
  run, significantly lowering rate-limit exposure.
- Attribution is approximate: an article may be attributed to
  multiple tickers if it mentions several companies in its title, or
  to none if a ticker is mentioned only in the article body, not the
  title. Acceptable at this project's scale and for its current
  purpose (building a retrievable news corpus), but a known
  limitation to revisit if attribution accuracy becomes a problem
  for the sentiment model.
- The retry decorator is kept as a second layer of defense, in case
  the single combined request itself is rate-limited.
