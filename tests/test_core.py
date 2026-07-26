"""Tests for souppy core types."""

import pytest
from souppy.core import (
    MemoryData,
    UIConfig,
    AgentEntry,
    AgentProfile,
    JournalEntry,
    ChatMessage,
    UILease,
    empty_memory,
)
from souppy.core.common import get_timestamp


def test_empty_memory():
    mem = empty_memory()
    assert mem._ui is not None
    assert mem._agents == {}
    assert mem._journal == {}
    assert mem._data == {}
    assert mem._chat == {}
    assert mem._cursors == {}


def test_ui_config_defaults():
    ui = UIConfig()
    assert ui.headless is False
    assert ui.agents_paused is False
    assert ui.chat_paused is False
    assert ui.mutation_id == 0
    assert ui.tier == "free"


def test_agent_entry():
    profile = AgentProfile(role="frontend", model="gpt-4")
    agent = AgentEntry(
        claimed="2024-01-01 00:00:00",
        profile=profile,
        permissions=["read", "write"],
    )
    assert agent.claimed == "2024-01-01 00:00:00"
    assert agent.profile.role == "frontend"
    assert agent.permissions == ["read", "write"]


def test_journal_entry():
    entry = JournalEntry(ts="2024-01-01", cs="abc123", ro=True)
    assert entry.ts == "2024-01-01"
    assert entry.cs == "abc123"
    assert entry.ro is True
    assert entry.vault is False


def test_chat_message():
    msg = ChatMessage(from_name="alice", to_name="bob", msg="hello")
    assert msg.from_name == "alice"
    assert msg.to_name == "bob"
    assert msg.msg == "hello"


def test_get_timestamp():
    ts = get_timestamp()
    assert len(ts) == 19
    assert " " in ts
