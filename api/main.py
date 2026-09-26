"""FastAPI wrapper around the portfolio copilot agent."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

from agents.orchestrator.portfolio_agent import build_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Builds the agent once at server startup, not at import time,
    so importing this module (e.g. in tests) never requires credentials."""
    app.state.agent = build_agent()
    yield


app = FastAPI(title="Portfolio MLE Copilot API", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def extract_reply_text(content) -> str:
    """Normalizes the agent's response content into a plain string,
    since Gemini sometimes returns a plain string, sometimes a list
    of structured content blocks (each with a 'text' key)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return str(content)


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """Async by design: lets the server handle multiple concurrent requests
    on a single worker instead of relying on FastAPI's thread-pool fallback
    (the default for sync `def` endpoints).

    Trade-off, stated explicitly: this is not fully non-blocking end to end.
    The agent's tools call `google.cloud.bigquery.Client`, which has no
    official async client — those calls remain synchronous under the hood.
    LangGraph offloads them to its own internal thread pool when invoked via
    `.ainvoke()`, similar in spirit to FastAPI's thread-pool fallback for
    sync routes. This still avoids blocking the main event loop on the
    Gemini API call itself (the genuinely async part), which is the
    dominant source of latency here — a real, partial improvement, not a
    complete one.

    For this project's actual traffic (solo personal use), the plain sync
    version would have been operationally indistinguishable — this async
    version exists to demonstrate the pattern correctly, not because it was
    load-bearing here.
    """
    result = await request.app.state.agent.ainvoke(
        {"messages": [{"role": "user", "content": body.message}]}
    )
    reply = extract_reply_text(result["messages"][-1].content)
    return ChatResponse(reply=reply)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
