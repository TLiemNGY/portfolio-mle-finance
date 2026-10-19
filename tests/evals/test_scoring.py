from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from evals.scoring import extract_turn_tool_calls, score_case


def volatility_call(horizon_days: int) -> dict:
    """Builds a get_volatility_forecast call for AXA at the given horizon."""
    return {
        "name": "get_volatility_forecast",
        "args": {"ticker": "CS.PA", "horizon_days": horizon_days},
    }


def test_score_case_ignores_call_order():
    expected = [volatility_call(5), volatility_call(10)]
    actual = [volatility_call(10), volatility_call(5)]

    assert score_case(expected, actual) == {"tools_ok": True, "args_ok": True}


def test_score_case_requires_each_expected_call_to_be_matched_once():
    expected = [volatility_call(5), volatility_call(10), volatility_call(20)]
    actual = [volatility_call(5), volatility_call(5), volatility_call(5)]

    assert score_case(expected, actual) == {"tools_ok": True, "args_ok": False}


def test_score_case_fails_on_missing_call():
    expected = [volatility_call(5), volatility_call(10)]
    actual = [volatility_call(5)]

    assert score_case(expected, actual) == {"tools_ok": False, "args_ok": False}


def test_score_case_expects_no_call():
    assert score_case([], []) == {"tools_ok": True, "args_ok": True}
    assert score_case([], [volatility_call(5)]) == {
        "tools_ok": False,
        "args_ok": False,
    }


def test_score_case_ignores_optional_tools():
    expected = [{"name": "get_latest_price", "args": {"ticker": "PE500.PA"}}]
    actual = [
        {"name": "get_portfolio_summary", "args": {}},
        {"name": "get_latest_price", "args": {"ticker": "PE500.PA"}},
    ]

    assert score_case(expected, actual) == {"tools_ok": False, "args_ok": False}
    assert score_case(expected, actual, optional_tools=["get_portfolio_summary"]) == {
        "tools_ok": True,
        "args_ok": True,
    }


def test_extract_turn_tool_calls_collects_calls_of_the_last_turn_only():
    messages = [
        HumanMessage(content="news sur LVMH"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_news_sentiment",
                    "args": {"ticker": "MC.PA"},
                    "id": "call_1",
                }
            ],
        ),
        ToolMessage(content="...", tool_call_id="call_1"),
        AIMessage(content="Voici les news."),
        HumanMessage(content="et le cours ?"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_latest_price",
                    "args": {"ticker": "MC.PA"},
                    "id": "call_2",
                }
            ],
        ),
        ToolMessage(content="...", tool_call_id="call_2"),
        AIMessage(content="Le cours est..."),
    ]

    assert extract_turn_tool_calls(messages) == [
        {"name": "get_latest_price", "args": {"ticker": "MC.PA"}}
    ]
