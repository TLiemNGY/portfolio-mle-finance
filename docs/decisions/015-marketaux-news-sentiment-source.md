# ADR-015: Marketaux as the News/Sentiment Source

## Status
Accepted

## Context
Following GDELT's unreliable rate limiting (ADR-006) and Alpha
Vantage NEWS_SENTIMENT's lack of European ticker coverage (ADR-014),
Marketaux was evaluated as a third candidate: a documented, official
REST API with a genuine free tier (100 requests/day, no payment
details required) and explicit French/European coverage.

Testing confirmed: standard Euronext Paris ticker format (`MC.PA`)
is recognized natively, with `country: 'fr'` correctly tagged, and
real article volume (269 articles found for LVMH alone) — unlike
Alpha Vantage's near-zero coverage for the same company.

## Decision
Use Marketaux as the news/sentiment ingestion source, replacing both
GDELT and Alpha Vantage NEWS_SENTIMENT for this need.

## Alternatives Considered
- **GDELT** (ADR-005/006): rejected — unresolved, persistent rate
  limiting issues even after identifying and patching a known
  library bug (missing User-Agent header).
- **Alpha Vantage NEWS_SENTIMENT** (ADR-014): rejected — structurally
  no coverage for European tickers, confirmed via both direct
  Euronext format (rejected outright) and US ADR proxies (accepted
  but zero articles returned).

## Consequences
- Free tier: 100 requests/day, 3 articles per request — sufficient
  for periodic (daily) ingestion across the ~10 relevant portfolio
  tickers (ETFs excluded, as before), with room to spare.
- Ticker format matches existing BigQuery tables exactly (`MC.PA`) —
  no mapping table needed, unlike the Alpha Vantage ADR approach that
  was briefly considered.
- Article limit per request (3 on free tier) means multiple requests
  or pagination may be needed for deeper historical backfill; daily
  incremental ingestion is not affected.

## Addendum (2026-10-22): sentiment scores of 0
After several weekly runs, some tickers show many sentiment scores of exactly
0 (24/24 articles for OR.PA, 23/24 for MC.PA; 0/24 for AIR.PA and SAN.PA).
Inspecting the raw API response showed that these are not missing values: each
score is computed on one highlight, the title of an event notice ("Presents at
… Conference", "Earnings Call Presentation") whose full content is paywalled
and which expresses no opinion. The scores are kept as is; the tool docstring
tells the agent to present them as "no clear tone". For these tickers, the free
tier of Marketaux provides little actual sentiment signal.