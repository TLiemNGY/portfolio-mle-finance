# ADR-018: News Retrieval — Recency Window, Then Relevance

**Status:** Accepted
**Date:** 2026-10-15

## Context

Asked for "the latest news on LVMH" in mid-October, the agent returned articles from late July.

The `get_news_sentiment` tool sorted articles by `match_score` (relevance) over the **whole** history of the `news_sentiment` table. Since the weekly ingestion appends new articles without removing old ones (`WRITE_APPEND`), a highly relevant old article always outranked a recent one. The tool answered "most relevant ever", not "latest".

A manual test in the Streamlit interface also showed that:

- the agent summarized the articles without their date, source or sentiment score, which were only visible when explicitly asked for;
- the agent explained the sentiment scale (-1 to +1) from its general knowledge, not from tool data;
- the agent refused to say whether news was "rather positive", although the sentiment score answers exactly that, because the system prompt's no-advice rule was too broad.

## Decision

1. **Recency window, then relevance.** The tool only considers articles published in the last 30 days (`NEWS_LOOKBACK_DAYS`), keeps the 5 most relevant by `match_score`, and presents them most recent first.
2. **Structured output** (`content_and_artifact`, see ADR-017). The artifact holds the full article list (date, source, title, description, URL, sentiment), rendered as a table by the interface. The text content gives the LLM the articles and the sentiment scale, so it can summarize them in a few sentences without repeating the full list.
3. **The sentiment scale is stated in the tool output**: Marketaux entity sentiment, from -1 (very negative) to +1 (very positive), specific to the ticker.
4. **System prompt clarified**: describing facts (the tone of articles from their sentiment scores, the size of a volatility range) is not investment advice. The "not investment advice" disclaimer is reserved for buy, sell or hold questions.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Sort by publication date only | Marketaux returns articles that only mention the company in passing; the most recent are often the least relevant. |
| Keep relevance ordering over the whole history | Returns stale articles to a "latest news" question (the observed bug). |
| Delete old articles at ingestion | Loses the history, which will feed the future semantic search (RAG) and sentiment analyses. |

## Consequences

- A ticker with little coverage (e.g. Airbus) may have no article in the window: the tool then says so explicitly, and the agent reports it.
- The window is a single constant, easy to tune once real usage shows whether 30 days is too short or too long.
- The full history stays in BigQuery; only the tool's view of it is restricted.