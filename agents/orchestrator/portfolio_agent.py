"""Minimal LangGraph agent that answers questions about the portfolio."""

import logging
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.tools.portfolio_tools import get_latest_price, get_portfolio_summary
from agents.tools.volatility_tools import get_volatility_forecast

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=os.environ["GOOGLE_API_KEY"],
)

agent = create_agent(
    llm, tools=[get_portfolio_summary, get_latest_price, get_volatility_forecast]
)


def main() -> None:
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
