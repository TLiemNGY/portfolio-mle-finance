# ADR-002: BigQuery for Structured Storage

## Status
Accepted

## Context
The project needs to store structured data: portfolio positions,
transactions, sector allocation, and later market prices and ML
features. Two natural GCP candidates were considered: BigQuery
(analytical SQL database) and Firestore (NoSQL document database).

## Decision
BigQuery was chosen for all structured data in this project.

## Alternatives Considered
- **Firestore**: rejected as the primary store — better suited to
  frequent, low-latency reads/writes of individual documents (e.g.
  conversation state), not to analytical queries and aggregations
  over historical financial data, which is the dominant access
  pattern here. May be reintroduced later for a genuine real-time,
  document-shaped need (e.g. agent conversation history), but not
  as a replacement for BigQuery.

## Consequences
- SQL-native analytics (aggregations, window functions) map directly
  onto the developer's existing strong SQL skills.
- 1 TB of free queries/month comfortably covers this project's scale.
- Less suited to high-frequency single-row writes — acceptable here,
  since ingestion is batch/periodic rather than continuous per-row.
