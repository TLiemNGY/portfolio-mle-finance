# ADR-011: Feature/Target Separation and Two-Phase Training

## Status
Accepted

## Context
`compute_features()` (used for Phase 1 methodology validation, see
ADR-010) computes both backward-looking features and forward-looking
targets, then drops rows with incomplete targets — which always
removes the most recent rows (they lack enough future data for a
target yet).

Reusing this same function for real-time inference (the
`get_volatility_forecast` agent tool) would silently drop the most
recent row — exactly the row inference needs — and instead return
stale data (whatever row happened to survive the target-based
`dropna()`). This was caught as an actual bug during development, not
a hypothetical.

Separately, Phase 1 (`train.py`) trains on a chronological train split
only, to honestly measure model performance on held-out data. The
model actually deployed to the agent should not be handicapped by
withholding part of the data, once methodology has already been
validated this way.

## Decision
- Split feature computation into two functions:
  - `compute_return_and_volatility_features(df)` — backward-looking
    only, never drops the most recent row. Used for inference.
  - `add_targets(df)` — adds forward-looking target columns.
    `compute_features(df)` = both combined + `dropna()`. Used for
    training only.
- Two distinct training phases:
  - Phase 1 (`train.py`): chronological train/test split with purge
    gap (ADR-009), used only to validate methodology (produces the
    comparison table in ADR-010) — not to produce a deployable model.
  - Phase 2 (`train_final_models.py`): trains the final LightGBM
    models (5-day and 10-day horizons only, per ADR-010) on 100% of
    available data, since honest evaluation already happened in
    Phase 1. Saves models via joblib to `ml/models/*.pkl`.

## Alternatives Considered
- **Reuse `compute_features()` for inference, filtering out target
  columns afterward**: rejected — target-based `dropna()` still runs
  before the filtering, so the most recent row would already be
  dropped by the time targets are removed.
- **Deploy the Phase 1 (train-split-only) model instead of retraining
  on 100% of data**: rejected — needlessly withholds usable data from
  the production model for no remaining benefit, once Phase 1 has
  already produced its validation result.

## Consequences
- Any future tool or script needing "features as of today" must use
  `compute_return_and_volatility_features()`, never `compute_features()`.
- Two separate scripts must be kept in sync if the feature list
  changes (`FEATURE_COLUMNS` is duplicated across `train.py`,
  `train_final_models.py`, and `agents/tools/volatility_tools.py`) —
  a candidate for future centralization if it causes drift.
- Documented in detail in `ml/README.md`, including a Mermaid diagram
  of the full pipeline.
