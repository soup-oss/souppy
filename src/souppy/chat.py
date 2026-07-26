"""Chat inbox and cursor management."""

from __future__ import annotations

from .core import ChatMessage
from .core.common import CHAT_LIMIT


def prune_chat(chat: dict[str, ChatMessage]) -> list[str]:
    """Remove oldest chat messages if over limit. Returns removed keys."""
    keys = sorted(chat.keys())
    if len(keys) <= CHAT_LIMIT:
        return []
    to_remove = keys[: len(keys) - CHAT_LIMIT]
    for key in to_remove:
        del chat[key]
    return to_remove


def prune_cursors(cursors: dict[str, dict[str, int]], chat: dict[str, ChatMessage]) -> None:
    """Remove cursor entries for messages that no longer exist."""
    for agent in list(cursors.keys()):
        for key in list(cursors[agent].keys()):
            if key not in chat:
                del cursors[agent][key]


def is_message_visible(msg: ChatMessage, agent_name: str) -> bool:
    """Check if a message is visible to the given agent."""
    return msg.to_name == "all" or msg.to_name == agent_name or msg.from_name == agent_name


def get_agent_inbox(
    chat: dict[str, ChatMessage],
    cursors: dict[str, dict[str, int]],
    agent_name: str,
) -> tuple[list[dict], bool]:
    """Get unread messages for an agent. Returns (messages, dirty)."""
    if agent_name not in cursors:
        cursors[agent_name] = {}
    agent_cursors = cursors[agent_name]
    keys = sorted(chat.keys())
    messages: list[dict] = []
    dirty = False
    for key in keys:
        msg = chat[key]
        if key in agent_cursors:
            continue
        if not is_message_visible(msg, agent_name):
            continue
        ts = key[: key.index("_")] if "_" in key else key
        messages.append({"key": key, "ts": ts, "from": msg.from_name, "to": msg.to_name, "msg": msg.msg})
        agent_cursors[key] = 0
        dirty = True
    return messages, dirty


def ack_messages(cursors: dict[str, dict[str, int]], agent_name: str, keys: list[str]) -> bool:
    """Acknowledge messages. Returns True if any were updated."""
    if agent_name not in cursors:
        return False
    agent_cursors = cursors[agent_name]
    dirty = False
    for key in keys:
        if key in agent_cursors and agent_cursors[key] < 1:
            agent_cursors[key] = 1
            dirty = True
    return dirty
