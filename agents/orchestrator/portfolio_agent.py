"""Minimal LangGraph agent that answers questions about the portfolio."""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.tools.portfolio_tools import get_latest_price, get_portfolio_summary

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=os.environ["GOOGLE_API_KEY"],
)

agent = create_agent(llm, tools=[get_portfolio_summary, get_latest_price])


def main() -> None:
    print("Portfolio copilot ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break

        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        answer = result["messages"][-1].content
        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    main()
