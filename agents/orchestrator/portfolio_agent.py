"""Minimal LangGraph agent that answers questions about the portfolio."""

import logging

from dotenv import load_dotenv
from langchain.agents import create_agent

from agents.tools.portfolio_tools import get_latest_price, get_portfolio_summary
from agents.tools.volatility_tools import get_volatility_forecast
from clients import get_llm

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def build_agent():
    """Builds the portfolio agent, with its LLM and tools."""
    llm = get_llm()
    return create_agent(
        llm, tools=[get_portfolio_summary, get_latest_price, get_volatility_forecast]
    )


def main() -> None:
    agent = build_agent()
    logger.info("Portfolio copilot ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break

        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        answer = result["messages"][-1].content
        logger.info(f"Agent: {answer}")


if __name__ == "__main__":
    main()
