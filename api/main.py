"""FastAPI wrapper around the portfolio copilot agent."""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from agents.orchestrator.portfolio_agent import build_agent, extract_turn_artifacts
from core.models import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Builds the agent once at server startup, not at import time,
    so importing this module (e.g. in tests) never requires credentials."""
    app.state.agent = build_agent()
    yield


app = FastAPI(title="Portfolio MLE Copilot API", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str = Field(description="The user's message.")
    thread_id: str | None = Field(
        default=None,
        description="Conversation identifier. Omit it to start a new "
        "conversation; send back the one returned by the API to continue it.",
    )


class ToolArtifact(BaseModel):
    tool: str = Field(description="Name of the tool that produced the data.")
    data: dict = Field(description="Structured data returned by the tool.")


class ChatResponse(BaseModel):
    reply: str = Field(description="The agent's answer, as plain text.")
    thread_id: str = Field(description="Conversation identifier to send back.")
    artifacts: list[ToolArtifact] = Field(
        description="Structured data produced by tools during this turn, "
        "rendered directly by the interface."
    )


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

    Conversation memory: the agent's checkpointer keeps each conversation
    under its thread_id (in process, lost on restart — see ADR-017).
    """
    thread_id = body.thread_id or str(uuid.uuid4())
    result = await request.app.state.agent.ainvoke(
        {"messages": [{"role": "user", "content": body.message}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    messages = result["messages"]
    return ChatResponse(
        reply=messages[-1].text,
        thread_id=thread_id,
        artifacts=extract_turn_artifacts(messages),
    )


@app.get("/health")
def health() -> dict:
    """Reports overall status and whether the volatility models are
    actually loadable (from local disk or GCS) — not just that the
    server process is alive."""
    try:
        get_model("lightgbm_5d.pkl")
        return {"status": "ok", "models": "loaded"}
    except Exception as e:  # noqa: BLE001 — health check must report any failure, not crash the endpoint
        return {"status": "degraded", "models": f"error: {e}"}
