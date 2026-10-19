"""Pure functions comparing the tool calls made by the agent to the expected ones."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def extract_turn_tool_calls(messages: list[BaseMessage]) -> list[dict]:
    """Returns the tool calls made by the agent during the last turn only,
    as a list of {"name": ..., "args": ...} dicts."""
    last_user_index = max(
        i for i, message in enumerate(messages) if isinstance(message, HumanMessage)
    )

    result = []
    for message in messages[last_user_index + 1 :]:
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                result.append({"name": call["name"], "args": call["args"]})

    return result


def score_case(
    expected: list[dict], actual: list[dict], optional_tools: list[str] | None = None
) -> dict:
    """Compares the actual tool calls to the expected ones.

    Returns {"tools_ok": bool, "args_ok": bool}:
    - tools_ok: the same tools were called, the same number of times,
      in any order;
    - args_ok: tools_ok, and each expected call is matched by a distinct
      actual call with the same name whose args contain the expected args;
    - calls to tools listed in optional_tools are ignored.
    """
    actual = [call for call in actual if call["name"] not in (optional_tools or [])]

    expected_names = sorted(call["name"] for call in expected)
    actual_names = sorted(call["name"] for call in actual)
    tools_ok = expected_names == actual_names
    if not tools_ok:
        return {"tools_ok": False, "args_ok": False}

    remaining = list(actual)
    for expected_call in expected:
        match = None
        for call in remaining:
            same_name = call["name"] == expected_call["name"]
            same_args = all(
                call["args"].get(key) == value
                for key, value in expected_call["args"].items()
            )
            if same_name and same_args:
                match = call
                break
        if match is None:
            return {"tools_ok": True, "args_ok": False}
        remaining.remove(match)

    return {"tools_ok": True, "args_ok": True}
