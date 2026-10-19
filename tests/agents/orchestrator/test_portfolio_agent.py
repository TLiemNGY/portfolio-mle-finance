from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agents.orchestrator.portfolio_agent import extract_turn_artifacts


def test_extract_turn_artifacts_keeps_only_the_last_turn():
    first_call = [
        HumanMessage(content="news sur LVMH"),
        ToolMessage(
            content="texte pour le LLM",
            tool_call_id="call_1",
            name="get_news_sentiment",
            artifact={"ticker": "MC.PA"},
        ),
        AIMessage(content="Voici les news..."),
    ]

    second_call = [
        HumanMessage(content="news sur AIRBUS"),
        ToolMessage(
            content="texte pour le LLM",
            tool_call_id="call_2",
            name="get_volatility_forecast",
            artifact={"horizon_days": 20},
        ),
        AIMessage(content="Voici la volatilité..."),
    ]

    messages = list(first_call + second_call)

    result = extract_turn_artifacts(messages)
    assert result == [{"tool": "get_volatility_forecast", "data": {"horizon_days": 20}}]


def test_extract_turn_artifacts_skips_tool_messages_without_artifact():
    call = [
        HumanMessage(content="news sur LVMH"),
        ToolMessage(
            content="texte pour le LLM",
            tool_call_id="call_3",
            name="get_news_sentiment",
        ),
        ToolMessage(
            content="texte pour le LLM",
            tool_call_id="call_4",
            name="get_volatility_forecast",
            artifact={"horizon_days": 5},
        ),
        AIMessage(content="Voici la volatilité..."),
    ]

    result = extract_turn_artifacts(call)
    assert result == [{"tool": "get_volatility_forecast", "data": {"horizon_days": 5}}]


def test_extract_turn_artifacts_returns_empty_list_without_tool_call():
    call = [
        HumanMessage(content="Bonjour"),
        AIMessage(content="Bonjour, que puis-je faire pour toi ?"),
    ]
    result = extract_turn_artifacts(call)
    assert result == []
