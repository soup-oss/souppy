"""Tests for souppy chat utilities."""

import pytest
from souppy.core import ChatMessage
from souppy.chat import (
    prune_chat,
    is_message_visible,
    get_agent_inbox,
    ack_messages,
)


def test_prune_chat_under_limit():
    chat = {}
    for i in range(10):
        chat[f"ts_{i}"] = ChatMessage(from_name="a", to_name="b", msg=f"msg{i}")
    pruned = prune_chat(chat)
    assert pruned == []


def test_prune_chat_over_limit():
    chat = {}
    for i in range(1100):
        chat[f"{i:06d}_a_b"] = ChatMessage(from_name="a", to_name="b", msg=f"msg{i}")
    pruned = prune_chat(chat)
    assert len(pruned) == 100
    assert len(chat) == 1000


def test_is_message_visible():
    msg = ChatMessage(from_name="alice", to_name="bob", msg="hello")
    assert is_message_visible(msg, "alice") is True
    assert is_message_visible(msg, "bob") is True
    assert is_message_visible(msg, "charlie") is False


def test_is_message_visible_broadcast():
    msg = ChatMessage(from_name="alice", to_name="all", msg="hello everyone")
    assert is_message_visible(msg, "bob") is True


def test_get_agent_inbox():
    chat = {
        "ts1_alice_bob": ChatMessage(from_name="alice", to_name="bob", msg="hello"),
        "ts2_charlie_bob": ChatMessage(from_name="charlie", to_name="bob", msg="hi"),
    }
    cursors = {}
    messages, dirty = get_agent_inbox(chat, cursors, "bob")
    assert len(messages) == 2
    assert dirty is True


def test_ack_messages():
    cursors = {"bob": {"ts1_alice_bob": 0}}
    dirty = ack_messages(cursors, "bob", ["ts1_alice_bob"])
    assert dirty is True
    assert cursors["bob"]["ts1_alice_bob"] == 1
