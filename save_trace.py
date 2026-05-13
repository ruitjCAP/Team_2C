import json


def save_trace(result, path="trace.json"):
    serializable_messages = []

    for msg in result["messages"]:
        serializable_messages.append(
            {
                "type": msg.__class__.__name__,
                "content": getattr(msg, "content", None),
                "tool_calls": getattr(msg, "tool_calls", None),
                "name": getattr(msg, "name", None),
                "id": getattr(msg, "id", None),
            }
        )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            serializable_messages,
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )