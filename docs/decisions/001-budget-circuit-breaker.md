# ADR-001: Automatic Budget Circuit Breaker

## Status
Accepted

## Context
The project must stay within a strict budget of 5 to 15 EUR/month,
while using GCP services that are actually used in industry (rather
than "hacked together" free alternatives to stay at 0 EUR at all
costs). Uncontrolled budget overrun is the main identified risk on a
personal GCP account.

## Decision
An automated protection chain was put in place:
1. A GCP budget of 15 EUR/month with alerts at 50%, 80%, and 100%
2. A Pub/Sub notification (topic `billing-alerts`) triggered by the
   budget
3. A Cloud Function gen2 (`stop-billing`) subscribed to that topic,
   which automatically disables project billing once the 100%
   threshold is crossed

## Alternatives Considered
- **Email alerts only**: rejected — no technical guarantee, depends
  on a fast manual action on my part.
- **Staying 100% Always Free (0 EUR)**: rejected — would have meant
  replacing standard services (Pub/Sub, Dataflow, Vertex AI
  Pipelines) with alternatives not representative of real-world
  usage, less relevant to an MLE career-transition goal.
- **Quotas only (without a circuit breaker)**: insufficient alone —
  the quotas covered (BigQuery in particular) don't cover every
  service, whereas the circuit breaker protects at the project level
  as a whole.

## Consequences
- Automatic and guaranteed protection against any budget overrun.
- Accepted trade-off: an actual trigger will also stop all currently
  running services (acceptable for a solo project, not for a
  production service with real users).
- The `stop-billing-sa` service account must remain strictly scoped
  to the `roles/billing.projectManager` role (least-privilege
  principle).
