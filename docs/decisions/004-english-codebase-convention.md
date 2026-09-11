# ADR-004: English-Only Codebase and Documentation

## Status
Accepted

## Context
The developer is French-speaking and initially wrote code (variable
names, comments, docstrings) and documentation in French. The
project's purpose includes serving as a public GitHub portfolio for
an MLE job search that may target English-speaking employers.

## Decision
All code, comments, docstrings, and documentation (including ADRs)
are written in English, applied retroactively to already-written
files (ingestion scripts, sample data, first ADR).

## Alternatives Considered
- **Keep French, translate only public-facing docs (README)**:
  rejected — inconsistent codebase is a worse signal than a fully
  English one, and full English is better practice regardless of
  audience.

## Consequences
- Every new file must be written in English from the start.
- Sample CSV files, column names, and BigQuery table/column names
  were renamed to English equivalents, requiring existing BigQuery
  tables to be dropped and recreated.
