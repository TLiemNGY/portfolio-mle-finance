# ADR-008: LangGraph + Gemini API for the Agentic Layer

## Status
Accepted

## Context
The project needs an orchestration framework for an agent with tools
(BigQuery-backed portfolio queries, and future ML/news capabilities),
plus an LLM to power it, within the project's budget constraints.

## Decision
- **Orchestration**: LangGraph, specifically its `create_agent` helper
  (from the `langchain` package; the framework's ReAct-style
  prebuilt agent).
- **LLM**: Gemini API (`gemini-3.1-flash-lite`), via
  `langchain-google-genai`.

## Alternatives Considered
- **Google ADK**: rejected — native to GCP, but younger and less
  represented in current MLE job postings than LangGraph, which has
  more portfolio/CV value.
- **A non-Google LLM (e.g. OpenAI, Anthropic)**: not evaluated in
  depth; Gemini was preferred for budget reasons (competitive
  Flash-Lite pricing, native GCP integration) over a general
  comparison of providers.

## Consequences
- Tool functions must have precise docstrings and type annotations,
  since the LLM only sees this metadata (not the function body) to
  decide when and how to call a tool.
- Gemini model availability changes quickly (multiple models used
  during development were deprecated within the same session:
  gemini-2.0-flash, then gemini-2.5-flash). The model name should be
  expected to need periodic updates; check
  https://ai.google.dev/gemini-api/docs/models for the current list
  if a `404 NOT_FOUND` error occurs.
- The Gemini API key is tied to the same `portfolio-mle-finance`
  Cloud Billing account as the rest of the project (see ADR-007),
  under the Prepay billing plan — a small non-refundable minimum
  prepay ($5) was required, but per-request costs are negligible
  (a full agent interaction costs roughly $0.001).
