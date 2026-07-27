"""Tests for souppy learn operation."""

import pytest
from souppy.core import empty_memory
from souppy.operations.learn import get_learn_payload
from souppy.operations.claim import claim_agent


def test_learn_returns_protocol():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid", db_path="test.db")
    assert payload["protocol"] == "SOUP"
    assert "version" in payload
    assert "uuid" in payload


def test_learn_includes_workspace_stats():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid", db_path="test.db")
    ws = payload["workspace"]
    assert ws["pulse"] == 0
    assert ws["agents"] == 0
    assert ws["journal_entries"] == 0
    assert ws["data_keys"] == 0


def test_learn_includes_rules():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid")
    assert len(payload["rules"]) > 0
    assert any("intent" in rule.lower() for rule in payload["rules"])


def test_learn_includes_patterns():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid")
    assert "path_structure" in payload["patterns"]
    assert "intent_quality" in payload["patterns"]
    assert "conflict_resolution" in payload["patterns"]
    assert "link_integrity" in payload["patterns"]


def test_learn_includes_commands():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid")
    cmds = payload["commands"]
    assert "read" in cmds
    assert "write" in cmds
    assert "chat_send" in cmds
    assert "glob" in cmds
    assert "grep" in cmds


def test_learn_includes_concepts():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid")
    concepts = payload["concepts"]
    assert "pulse" in concepts
    assert "journal" in concepts
    assert "checksum" in concepts
    assert "vault" in concepts
    assert "intent" in concepts


def test_learn_includes_authority():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid")
    auth = payload["authority"]
    assert "agent_can" in auth
    assert "agent_cannot" in auth
    assert "Vault or unvault paths" in auth["agent_cannot"]


def test_learn_includes_links():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid")
    links = payload["links"]
    assert "knowledge" in links
    assert "github" in links
    assert links["knowledge"] == "https://heysoup.co/knowledge"


def test_learn_includes_agents():
    mem = empty_memory()
    claim_agent(mem, "alice", "secret", "test-uuid")
    claim_agent(mem, "bob", "secret", "test-uuid")
    payload = get_learn_payload(mem, "test-uuid")
    assert len(payload["agents"]) == 2
    names = [a["name"] for a in payload["agents"]]
    assert "alice" in names
    assert "bob" in names


def test_learn_includes_reference():
    mem = empty_memory()
    payload = get_learn_payload(mem, "test-uuid")
    assert "reference" in payload
    assert "heysoup.co" in payload["reference"]
