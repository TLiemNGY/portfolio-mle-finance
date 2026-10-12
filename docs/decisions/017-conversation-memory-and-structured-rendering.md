# ADR-017: Conversation Memory and Structured Rendering of Agent Answers

**Status:** Accepted
**Date:** 2026-10-11

## Context

A manual test of the agent exposed a broken multi-turn conversation:

1. "Quelles sont les dernières news sur LVMH ?" → correct answer (news for `MC.PA`).
2. "Volatilité sur 20 jours ?" → the agent asked which ticker, although LVMH had just been discussed.
3. "LVMH" → the agent returned a **5-day** forecast (not 20), added prices and news nobody asked for, and switched to English.

Root causes:

- **No conversation memory.** Both the CLI loop and the `/chat` endpoint send only the current message to the agent. Every turn starts from scratch, so "20 jours" in turn 2 is lost by turn 3.
- **No system prompt.** Nothing fixes the language, the scope of an answer, the ticker format or the rule against inventing figures.
- **Numbers are re-typed by the LLM.** Tool outputs are dicts that the LLM paraphrases into prose. This contradicts the project rule: *the LLM is used for wording, never for numerical accuracy*. Any figure shown to the user should come from a tool, not from token generation.
- **Ambiguous units.** `forecast_pct` is a *daily* standard deviation of returns (~1.73 % for LVMH). Users and finance practitioners read volatility as *annualized* (~27.5 % = 1.73 % × √252). Showing the daily figure without context is misleading.

## Decision

1. **Conversation memory: LangGraph's native checkpointer.** The agent is built with `checkpointer=InMemorySaver()`, and each conversation is identified by a `thread_id` passed in the invocation config. Memory lasts for one conversation and is intentionally lost when the process restarts. No long-term memory across conversations.

2. **A system prompt** fixes the behavior: answer in French, be concise, answer only what was asked, reuse the context of previous turns (ticker, horizon), use Euronext Paris tickers (`MC.PA`), never state a figure that no tool returned, and state that answers are not investment advice when the user asks for a buy/sell decision.

3. **Tools return structured data alongside text** (`response_format="content_and_artifact"`). The `content` is a short summary the LLM reads; the `artifact` is the structured payload attached to the `ToolMessage`. The UI renders artifacts directly (tables, metrics). The LLM comments; it does not copy numbers.

4. **Volatility is displayed as ranges over the requested horizon.** The model predicts the daily standard deviation of returns; the tool converts it to the horizon (daily × √h) and returns ±1 and ±2 standard deviation ranges, in percent and in price, with their approximate probabilities (~68 % and ~95 %). These probabilities rely on a normal approximation, stated as such to the user; it will be checked against historical data (empirical coverage) in a follow-up. Stocks are compared at the same horizon. The daily and annualized values stay in the artifact, the annualized one only for comparison with external sources, which quote annualized figures.

5. **The interface is a Streamlit app**, a thin client of the `/chat` endpoint. Contract: request `{message, thread_id}` → response `{reply, artifacts}`. It runs locally and authenticates to the private Cloud Run service with the user's identity token: the service stays private.

6. **Bounded history.** The conversation history sent to the LLM is trimmed through agent middleware, so long conversations do not grow token cost and latency without limit.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Hand-written `dict[session_id, list[messages]]` in the API | Reimplements what the checkpointer already does (persistence per thread, tool-call bookkeeping), with more bugs and no upgrade path. |
| LLM writes markdown tables of the numbers | Still relies on the LLM to copy figures correctly; rendering depends on prompt compliance. |
| Custom HTML/JS page | More code to maintain for no gain over a dedicated framework; front-end work is not the focus of this project. |
| Chainlit | Chat-focused and polished, but its maintenance status has been uncertain since the original team stepped back in 2025. Streamlit is more widely used and also covers the later dataviz work. |
| Keep daily volatility as the headline figure | Technically correct but not the convention users expect; easy to misread. |

## Consequences

**Positive**
- Follow-up questions work ("et sur 20 jours ?").
- Figures on screen come from tools, not from text generation.
- One interface covers chat today and dataviz later.
- A multi-turn test replaying the failing sequence is added. It partly closes the "no agent evaluation" debt.

**Negative / limits**
- Memory lives in the process: it is lost on Cloud Run cold starts and is not shared between instances. Acceptable for a single-user tool with `max-instances` low. Upgrade path: a persistent checkpointer (e.g. Postgres/Firestore-backed) without changing the agent code.
- Tool outputs change shape → existing tool tests must be updated.
- The `/chat` contract changes (`thread_id` in, `artifacts` out): any existing client (curl commands, docs) must be updated.
- Supersedes the session-dict design discussed earlier, which was never committed.