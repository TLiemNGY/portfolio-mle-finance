# ADR-012: Async `/chat` Endpoint, With a Known Partial Limitation

## Status
Accepted

## Context
FastAPI supports both sync (`def`) and async (`async def`) route
handlers. Sync handlers are automatically offloaded to a thread pool
so they don't block the server — functionally correct, but not the
idiomatic FastAPI pattern for I/O-bound endpoints like an LLM agent
call (network-bound: BigQuery + Gemini API).

## Decision
`/chat` is implemented as `async def`, using `agent.ainvoke(...)`
instead of `agent.invoke(...)`.

## Alternatives Considered
- **Keep the sync `def` + thread-pool fallback**: rejected as the
  final version — operationally equivalent at this project's actual
  (near-zero, solo) traffic, but async is the correct default pattern
  for an I/O-bound LLM endpoint and worth demonstrating properly.

## Consequences
- **Known limitation, stated honestly**: the agent's tools use
  `google.cloud.bigquery.Client`, which has no official async client.
  Those calls remain synchronous internally; LangGraph offloads them
  to its own thread pool when invoked via `.ainvoke()` — similar in
  effect to FastAPI's sync-route fallback, not a fully non-blocking
  chain end to end. The genuinely async portion is the Gemini API
  call itself, typically the dominant source of latency.
- A future improvement, if real concurrent load ever justified it,
  would be wrapping the BigQuery calls in `asyncio.to_thread(...)`
  explicitly within the tools, or exploring a community async BigQuery
  client — not pursued now, since current traffic doesn't warrant it.
