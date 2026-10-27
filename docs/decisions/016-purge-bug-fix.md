# ADR-016: Fixed Purge Gap Bug (Calendar Days vs Trading Days)

## Status
Accepted

## Context
A code review (via Claude Code) found that `train_test_split_with_purge`
(ADR-009) applied `purge_days` as calendar days (`pd.Timedelta(days=...)`),
while target columns are built via a row-position shift per ticker
(trading days, see `build_features.add_targets`). This meant the purge
gap was too narrow — a real leak, exactly what the purge was meant to
prevent. The MAE figures reported in ADR-010 were computed with this bug
present and may be optimistic.

## Decision
The purge now operates on row counts per ticker (dropping the last
`purge_days` rows before the cutoff, per ticker), matching exactly how
the target shift works — exact regardless of weekends/holidays, rather
than an approximate calendar-day conversion.

## Consequences
- ADR-010's figures were regenerated with the fixed split (2026-09-26);
  figures computed before the fix are no longer reported. The decision
  recorded in ADR-010 — LightGBM at 5 and 10 days, persistence baseline
  at 20 days — is unchanged.
- The fix is covered by
  `tests/ml/training/test_split.py::test_train_test_split_purges_exact_row_count_per_ticker`.
- A deeper validation (walk-forward cross-validation instead of a single
  split) remains deferred — this fix addresses the leak itself, not the
  broader evaluation robustness question.
