from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from api.main import app


def build_test_client(messages: list) -> tuple[TestClient, MagicMock]:
    """Returns a test client whose agent is a fake returning the given messages.

    The client is created without `with`, so the real agent is never built
    (no credentials needed): the fake one is set in its place.
    """
    fake_agent = MagicMock()
    fake_agent.ainvoke = AsyncMock(return_value={"messages": messages})
    app.state.agent = fake_agent
    return TestClient(app), fake_agent


def test_chat_returns_reply_and_turn_artifacts():
    call = [
        HumanMessage(content="Volatilité sur LVMH"),
        ToolMessage(
            content="texte pour le LLM",
            tool_call_id="call_3",
            name="get_news_sentiment",
        ),
        ToolMessage(
            content="texte pour le LLM",
            tool_call_id="call_4",
            name="get_volatility_forecast",
            artifact={"horizon_days": 20},
        ),
        AIMessage(content="Voici la volatilité."),
    ]
    client, _ = build_test_client(call)

    response = client.post("/chat", json={"message": "volatilité de LVMH ?"})

    assert response.status_code == 200

    body = response.json()
    assert body["reply"] == "Voici la volatilité."
    assert body["artifacts"] == [
        {"tool": "get_volatility_forecast", "data": {"horizon_days": 20}}
    ]
    assert body["thread_id"]


def test_chat_reuses_the_given_thread_id():
    conversation = [
        HumanMessage(content="volatilité de LVMH sur 20 jours ?"),
        AIMessage(content="Sur 20 jours, ..."),
        HumanMessage(content="et sur 5 jours ?"),
        AIMessage(content="Sur 5 jours, ..."),
    ]
    client, fake_agent = build_test_client(conversation)
    response = client.post(
        "/chat", json={"message": "et sur 5 jours ?", "thread_id": "thread-test"}
    )

    body = response.json()
    assert body["thread_id"] == "thread-test"
    assert fake_agent.ainvoke.call_args.kwargs["config"] == {
        "configurable": {"thread_id": "thread-test"}
    }


def test_chat_rejects_a_request_without_message():
    conversation = [
        HumanMessage(content="volatilité de LVMH sur 20 jours ?"),
        AIMessage(content="Sur 20 jours, ..."),
    ]
    client, fake_agent = build_test_client(conversation)

    response = client.post("/chat", json={})

    assert response.status_code == 422
    fake_agent.ainvoke.assert_not_called()


def test_health_reports_degraded_when_models_cannot_be_loaded():
    conversation = [
        HumanMessage(content="volatilité de LVMH sur 20 jours ?"),
        AIMessage(content="Sur 20 jours, ..."),
    ]

    client, _ = build_test_client(conversation)

    with patch("api.main.get_model", side_effect=Exception("GCS unavailable")):
        response = client.get("/health")

        body = response.json()
        assert response.status_code == 200
        assert body["status"] == "degraded"
        assert body["models"] == "error: GCS unavailable"
