"""FastAPI wrapper around the portfolio copilot agent."""

from fastapi import FastAPI
from pydantic import BaseModel

from agents.orchestrator.portfolio_agent import agent

app = FastAPI(title="Portfolio MLE Copilot API")


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
def chat(request: ChatRequest) -> ChatResponse:
    result = agent.invoke({"messages": [{"role": "user", "content": request.message}]})
    reply = extract_reply_text(result["messages"][-1].content)
    return ChatResponse(reply=reply)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
