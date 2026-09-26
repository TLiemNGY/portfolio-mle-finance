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
- ADR-010's reported figures need to be regenerated with the fixed split
  before being trusted as final.
- A deeper validation (walk-forward cross-validation instead of a single
  split) remains deferred — this fix addresses the leak itself, not the
  broader evaluation robustness question.
