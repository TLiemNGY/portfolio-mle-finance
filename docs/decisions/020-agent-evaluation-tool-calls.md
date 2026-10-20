# ADR-020: Agent Evaluation — Tool Calls

**Status:** Accepted
**Date:** 2026-10-20

## Context

Unit tests cover the tools and the API with the LLM replaced by fakes. Nothing measured the agent itself: does it call the right tool, with the right arguments? Manual testing had already revealed several agent bugs (a company name passed as a ticker, a 20-day question answered with a 5-day forecast), but each fix was checked by hand, once, with no way to detect a later regression.

## Decision

1. **A separate evaluation, outside the unit tests.** It lives in `evals/`, calls the real agent (Gemini and BigQuery), and runs on demand (`make eval`), not in the CI: it is slow, costs API calls and is not deterministic. Only its pure scoring functions are unit-tested in the CI.
2. **A hand-written YAML dataset** (`evals/datasets/tool_calls.yaml`), separate from the code. Each case holds a question, the expected tool calls, a `rationale` explaining why that behaviour is expected, and optionally `optional_tools` (calls tolerated but not required, e.g. a portfolio lookup to find an ETF ticker). New cases are added from real failures (error analysis); they are tagged `regression`.
3. **Cases tagged by capability**, inspired by the Berkeley Function Calling Leaderboard: `tool_selection`, `ticker_resolution`, `horizon_normalization`, `parallel_calls`, `irrelevance`, `regression`. Scores are reported per tag, as counts ("3/4") rather than percentages, given the small sample.
4. **Scoring:** a case passes if the agent called exactly the expected tools (in any order, optional tools ignored) and each expected call is matched by a distinct actual call whose arguments contain the expected ones.
5. **Each case runs in a fresh conversation** (new `thread_id`), and each run is saved to `evals/results/` (git-ignored) with the model and the commit hash, so that two runs can be compared.

## First results

| Run | Commit | Score | Change |
|---|---|---|---|
| 1 | `ca41e2c` | 11/17 | Baseline. Root causes: the agent looked up the portfolio before almost every call (5 cases), and did not map an unsupported 3-day horizon to 5 days (1 case). |
| 2 | (uncommitted) | 16/17 | System prompt: use known tickers directly. Tool docstring: use the closest supported horizon. New failure on the MSCI Europe ETF: the agent guessed a wrong ticker, a regression caused by the prompt change. |
| 3 | `7fccb2f` | 17/17 | System prompt: always check the portfolio first for ETFs, since several ETFs track the same index. |

The unnecessary portfolio lookups were more than a scoring issue: their artifact would have displayed the whole portfolio table under unrelated answers in the interface.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Evaluation inside the unit tests and the CI | Slow, costly and non-deterministic: it would make the CI flaky. |
| An evaluation platform (LangSmith, promptfoo, DeepEval) | Useful at a larger scale; a minimal in-house harness was preferred to understand the mechanics, and LangSmith would send conversations to a third party. |
| Order-sensitive comparison of the tool calls | The calls are independent; the LLM groups and orders them freely, so order checks would produce false failures. |
| Exact match on the tool calls, no optional tools | Penalises a portfolio lookup that the system prompt itself asks for when a ticker is ambiguous. |

## Consequences

- Every change to the system prompt, a tool docstring or the model can now be measured before deployment. Run 2 showed why: a fix for five cases broke a sixth one.
- A single 17/17 run is not proof: the LLM is not deterministic. A run must be repeated before concluding that a fix works; a repetition option is a planned improvement.
- With 17 cases, per-tag scores rely on 2 to 12 cases: they point to weaknesses but are not statistically robust.
- The evaluation only checks tool calls. The figures in the answer (faithfulness to the tool data) and multi-turn behaviour (memory, system prompt rules) are the next steps.