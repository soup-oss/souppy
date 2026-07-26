"""Chat operation — inter-agent messaging."""

from __future__ import annotations

from ..core import ChatMessage, MemoryData
from ..core.common import get_chat_timestamp
from ..chat import prune_chat


def chat_send(memory: MemoryData, from_name: str, to_name: str, msg: str) -> dict:
    """Send a chat message. Returns {sent, ts}."""
    if memory._ui.chat_paused:
        return {"error": "forbidden", "detail": "chat_paused", "status": 403}

    # Verify sender exists
    if from_name not in memory._agents:
        return {"error": "not_found", "detail": "agent_not_claimed", "status": 404}

    ts = get_chat_timestamp()
    key = f"{ts}_{from_name}_{to_name}"

    memory._chat[key] = ChatMessage(from_name=from_name, to_name=to_name, msg=msg)

    # Prune old messages
    prune_chat(memory._chat)

    return {"sent": True, "ts": ts}


def chat_read(memory: MemoryData, agent_name: str, limit: int = 50) -> list[dict]:
    """Read chat messages visible to the given agent."""
    keys = sorted(memory._chat.keys(), reverse=True)[:limit]
    messages = []
    for key in keys:
        msg = memory._chat[key]
        if msg.to_name == "all" or msg.to_name == agent_name or msg.from_name == agent_name:
            ts = key[: key.index("_")] if "_" in key else key
            messages.append({
                "key": key,
                "ts": ts,
                "from": msg.from_name,
                "to": msg.to_name,
                "msg": msg.msg,
            })
    return messages
