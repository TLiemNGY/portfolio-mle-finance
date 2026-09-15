# ADR-009: Full Refresh (WRITE_TRUNCATE) for Price History Backfill

## Status
Accepted

## Context
`load_price_history.py` downloads 2 years of daily price history per
ticker via yfinance. The question was whether to re-download and
overwrite the full table each run (WRITE_TRUNCATE) or incrementally
append only new rows (WRITE_APPEND).

## Decision
Use WRITE_TRUNCATE: each run re-downloads and replaces the full
2-year history for all tickers.

## Alternatives Considered
- **WRITE_APPEND with deduplication**: rejected for now — would
  require tracking the latest date already loaded per ticker (or a
  MERGE/upsert), adding complexity not justified at this data volume.

## Consequences
- Simple, no duplicate-row risk, negligible cost at this scale
  (a handful of tickers, ~500 trading days each).
- This script is a periodic backfill/refresh job, not a daily
  incremental job — ongoing daily price updates continue to flow
  through `fetch_market_prices.py` (WRITE_APPEND into `market_prices`,
  a separate table).
- If ticker count or history length grows significantly, revisit in
  favor of incremental loading to control cost and runtime.
