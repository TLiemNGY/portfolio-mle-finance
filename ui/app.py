"""Streamlit chat interface for the portfolio copilot.

A thin client of the /chat API: it holds no business logic, only sends the
user's messages and renders the reply and the tool artifacts (see ADR-017).

Run locally (with the API running on port 8000):
    uv run --group ui streamlit run ui/app.py
"""

import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = 120


def render_volatility(data: dict) -> None:
    """Renders the volatility ranges of get_volatility_forecast as a table."""
    st.caption(
        f"{data['ticker']} · {data['horizon_days']} jours de bourse · "
        f"méthode {data['method']} · dernier cours {data['last_close']:.2f} €"
    )
    rows = [
        {
            "Probabilité (approx. normale)": f"~{price_range['probability']:.0%}",
            "Écarts-types": f"±{price_range['std_devs']}",
            "Variation": f"±{price_range['high_pct']:.2%}",
            "Prix bas (€)": round(price_range["low_price"], 2),
            "Prix haut (€)": round(price_range["high_price"], 2),
        }
        for price_range in data["ranges"]
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True)


def render_news(data: dict) -> None:
    """Renders the articles of get_news_sentiment as a table."""
    st.caption(
        f"{data['ticker']} · articles des {data['lookback_days']} derniers jours"
    )
    rows = [
        {
            "Date": article["published_date"],
            "Source": article["source"],
            "Titre": article["title"],
            "Sentiment (-1 à +1)": article["sentiment_score"],
            "Lien": article["url"],
        }
        for article in data["articles"]
    ]
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        column_config={
            "Sentiment (-1 à +1)": st.column_config.NumberColumn(format="%.2f"),
            "Lien": st.column_config.LinkColumn(display_text="Ouvrir"),
        },
    )


# Tool name -> function that renders its artifact. Tools without a renderer
# are simply not displayed (their answer is still in the agent's reply).
RENDERERS = {
    "get_volatility_forecast": render_volatility,
    "get_news_sentiment": render_news,
}


def render_artifacts(artifacts: list[dict]) -> None:
    """Renders each artifact with the function registered for its tool."""
    for artifact in artifacts:
        renderer = RENDERERS.get(artifact["tool"])
        if renderer is not None:
            renderer(artifact["data"])


def send_message(message: str, thread_id: str | None) -> dict:
    """Sends one message to the /chat API and returns its JSON response."""
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": message, "thread_id": thread_id},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title="Copilote PEA", page_icon="📈")
st.title("Copilote PEA")

if "history" not in st.session_state:
    st.session_state.thread_id = None
    st.session_state.history = []

with st.sidebar:
    if st.button("Nouvelle conversation"):
        st.session_state.thread_id = None
        st.session_state.history = []
        st.rerun()
    st.caption(f"API : {API_URL}")
    st.caption("Outil personnel, pas un conseil en investissement.")

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        render_artifacts(turn.get("artifacts", []))

if prompt := st.chat_input("Pose ta question sur ton PEA..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Le copilote réfléchit..."):
            try:
                result = send_message(prompt, st.session_state.thread_id)
            except requests.RequestException as error:
                st.error(f"Erreur de l'API : {error}")
                st.stop()
        st.markdown(result["reply"])
        render_artifacts(result["artifacts"])

    st.session_state.thread_id = result["thread_id"]
    st.session_state.history.append(
        {
            "role": "assistant",
            "content": result["reply"],
            "artifacts": result["artifacts"],
        }
    )
