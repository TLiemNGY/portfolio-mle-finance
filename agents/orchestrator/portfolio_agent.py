"""Minimal LangGraph agent that answers questions about the portfolio."""

import logging
import uuid

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from agents.tools.news_tools import get_news_sentiment
from agents.tools.portfolio_tools import get_latest_price, get_portfolio_summary
from agents.tools.volatility_tools import get_volatility_forecast
from core.clients import get_llm

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a copilot for a French PEA (Plan d'Epargne en Actions) stock portfolio.

Language and style:
- Always answer in French, even if a tool returns English text.
- Be concise: answer exactly what was asked, nothing more.
- Only call the tools needed for the current question. Do not add prices,
  news or forecasts the user did not ask for.

Conversation context:
- Reuse the context of previous turns. If the user asks a follow-up such as
  "et sur 20 jours ?" or just gives a company name, combine it with what was
  asked before (ticker, horizon) instead of asking again.
- Ask a clarifying question only if the request is truly ambiguous.

Tickers:
- Tools expect Euronext Paris tickers (e.g. "MC.PA" for LVMH, "TTE.PA" for
  TotalEnergies), never company names.
- If you are unsure of a ticker, call get_portfolio_summary to find it among
  the user's positions.

Numbers:
- Never state a figure that was not returned by a tool. Do not estimate,
  round differently or compute new figures yourself.
- Report each figure with the unit and horizon given by the tool.

Volatility forecasts:
- Say what the figure is: a standard deviation of returns, i.e. the typical
  size of price moves. It measures risk, not direction. Never present it as a
  price prediction.
- Present the two ranges returned by the tool over the requested horizon, in
  percent and in price: about 2 chances in 3 (~68%) of staying within
  ±1 standard deviation, about 95% within ±2 standard deviations.
- State that these probabilities rely on a normal approximation, which tends
  to underestimate large moves.
- Do not mention annualized volatility unless the user asks to compare with
  an external source.

Advice:
- You do not give investment advice. If the user asks whether to buy or sell,
  provide the relevant data and state once that this is not investment advice.
"""


def build_agent():
    """Builds the portfolio agent, with its LLM, tools, system prompt and memory.

    Memory is kept in process (InMemorySaver): each conversation is identified
    by a thread_id and is lost when the process restarts. See ADR-017.
    """
    llm = get_llm()
    return create_agent(
        llm,
        tools=[
            get_portfolio_summary,
            get_latest_price,
            get_volatility_forecast,
            get_news_sentiment,
        ],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )


def extract_turn_artifacts(messages: list[BaseMessage]) -> list[dict]:
    """Returns the artifacts produced by tools during the last turn only.

    With a checkpointer, `messages` holds the whole conversation. Only the
    tool messages after the last user message belong to the current turn.
    Each artifact is tagged with the name of the tool that produced it, so the
    interface can pick the right rendering.
    """
    last_user_index = max(
        i for i, message in enumerate(messages) if isinstance(message, HumanMessage)
    )
    return [
        {"tool": message.name, "data": message.artifact}
        for message in messages[last_user_index + 1 :]
        if isinstance(message, ToolMessage) and message.artifact is not None
    ]


def main() -> None:
    agent = build_agent()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    logger.info("Portfolio copilot ready (thread %s). Type 'exit' to quit.", thread_id)
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break

        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
        )
        # .text returns the plain text of the message, whether its content
        # is a string or a list of content blocks (as Gemini 3 returns).
        answer = result["messages"][-1].text
        logger.info("Agent: %s", answer)


if __name__ == "__main__":
    main()
