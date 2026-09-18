# ADR-010: Volatility Prediction Horizon and Model Choice

## Status
Accepted

## Context
Three prediction horizons (5, 10, 20 trading days) were compared across
four approaches (mean baseline, persistence baseline, linear regression,
LightGBM), trained on ~4,500 rows and evaluated on a chronologically
held-out, purge-gapped test set (see ADR-009 for the price history
ingestion strategy and the purge-gap methodology).

Results (MAE, lower is better):
| Horizon | Best model           | MAE      | vs. persistence baseline |
|---------|-----------------------|----------|---------------------------|
| 5 days  | LightGBM              | 0.005581 | -24%                      |
| 10 days | LightGBM              | 0.004126 | -24%                      |
| 20 days | Persistence baseline  | 0.003416 | LightGBM is +2% worse     |

Note: overlapping rolling windows mean consecutive test rows are not
fully independent observations; results should be read as indicative
of a real but noisy signal, not as 1,128 independent trials.

## Decision
- Use LightGBM for the 5-day and 10-day volatility signals exposed to
  the agent (real, measurable improvement over all baselines).
- Do NOT use a trained model for the 20-day horizon; expose the
  persistence baseline (today's volatility_20d) directly instead, since
  no trained model beats it at this horizon.

## Alternatives Considered
- **Force LightGBM at all horizons for consistency**: rejected —
  deploying a trained model that adds no value over a trivial baseline
  contradicts the project's real-utility principle; added complexity
  with no benefit.

## Consequences
- The future `get_volatility_forecast` agent tool will need horizon-
  aware logic: call the LightGBM model for 5/10-day requests, return
  the raw current volatility_20d value for 20-day requests.
- If a better long-horizon signal is needed later, richer features
  (e.g. macro indicators, cross-asset volatility) would need to be
  explored — out of scope for now.
