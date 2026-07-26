"""Tests for souppy operations."""

import pytest
from souppy.core import MemoryData, empty_memory
from souppy.persistence import init_db, load_memory, save_memory
from souppy.operations.write import write_path
from souppy.operations.read import read_path
from souppy.operations.delete import delete_path
from souppy.operations.claim import claim_agent, list_agents
from souppy.operations.chat import chat_send, chat_read
from souppy.operations.search import glob_search, grep_search
from souppy.operations.vault import vault_path


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.soup.db")


@pytest.fixture
def workspace(db_path):
    conn = init_db(db_path)
    uuid = "test-uuid-1234"
    mem = empty_memory()
    save_memory(conn, uuid, mem)
    return conn, uuid, mem


class TestWrite:
    def test_write_simple(self, workspace):
        conn, uuid, mem = workspace
        result = write_path(mem, "goals/mvp", "Ship v1", "Setting initial scope")
        assert "pulse" in result
        assert result["pulse"] == 1
        save_memory(conn, uuid, mem)

    def test_write_intent_required(self, workspace):
        conn, uuid, mem = workspace
        result = write_path(mem, "goals/mvp", "Ship v1", "")
        assert result["error"] == "intent_too_short"

    def test_write_intent_too_short(self, workspace):
        conn, uuid, mem = workspace
        result = write_path(mem, "goals/mvp", "Ship v1", "hi")
        assert result["error"] == "intent_too_short"

    def test_write_increments_pulse(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "a", "1", "first write")
        write_path(mem, "b", "2", "second write")
        assert mem._ui.mutation_id == 2


class TestRead:
    def test_read_existing(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "Setting scope")
        result = read_path(mem, "goals/mvp")
        assert result["value"] == "Ship v1"

    def test_read_nonexistent(self, workspace):
        conn, uuid, mem = workspace
        result = read_path(mem, "nonexistent")
        assert result["value"] is None

    def test_read_directory(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "Setting scope")
        write_path(mem, "goals/stack", "React", "Tech choice")
        result = read_path(mem, "goals/")
        assert isinstance(result["value"], dict)
        assert result["value"]["mvp"] == "Ship v1"


class TestDelete:
    def test_delete_existing(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "Setting scope")
        result = delete_path(mem, "goals/mvp", "Cleaning up")
        assert result["deleted_count"] == 1

    def test_delete_nonexistent(self, workspace):
        conn, uuid, mem = workspace
        result = delete_path(mem, "nonexistent", "Trying to delete")
        assert result["error"] == "not_found"

    def test_delete_requires_intent(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "a", "1", "write")
        result = delete_path(mem, "a", "")
        assert result["error"] == "intent_too_short"


class TestClaim:
    def test_claim_new(self, workspace):
        conn, uuid, mem = workspace
        result = claim_agent(mem, "alice", "secret", uuid)
        assert "signature" in result
        assert result["agent"]["name"] == "alice"

    def test_claim_existing_same_sig(self, workspace):
        conn, uuid, mem = workspace
        result1 = claim_agent(mem, "alice", "secret", uuid)
        sig = result1["signature"]
        result2 = claim_agent(mem, "alice", "secret", uuid, signature=sig)
        assert result2["reclaimed"] is True

    def test_claim_invalid_name(self, workspace):
        conn, uuid, mem = workspace
        result = claim_agent(mem, "all", "secret", uuid)
        assert result["error"] == "invalid_name"

    def test_list_agents(self, workspace):
        conn, uuid, mem = workspace
        claim_agent(mem, "alice", "secret", uuid)
        claim_agent(mem, "bob", "secret", uuid)
        agents = list_agents(mem)
        assert len(agents) == 2
        names = [a["name"] for a in agents]
        assert "alice" in names
        assert "bob" in names


class TestChat:
    def test_chat_send(self, workspace):
        conn, uuid, mem = workspace
        claim_agent(mem, "alice", "secret", uuid)
        result = chat_send(mem, "alice", "all", "hello everyone")
        assert result["sent"] is True

    def test_chat_send_unclaimed(self, workspace):
        conn, uuid, mem = workspace
        result = chat_send(mem, "unknown", "all", "hello")
        assert result["error"] == "not_found"

    def test_chat_read(self, workspace):
        conn, uuid, mem = workspace
        claim_agent(mem, "alice", "secret", uuid)
        claim_agent(mem, "bob", "secret", uuid)
        chat_send(mem, "alice", "bob", "hello bob")
        messages = chat_read(mem, "bob")
        assert len(messages) == 1
        assert messages[0]["msg"] == "hello bob"


class TestSearch:
    def test_glob_search(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "v1", "Setting scope")
        write_path(mem, "goals/stack", "React", "Tech stack")
        results = glob_search(mem, "goals/*")
        assert len(results) == 2

    def test_grep_search(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "PostgreSQL database", "Tech stack")
        results = grep_search(mem, "PostgreSQL")
        assert len(results) == 1
        assert results[0]["path"] == "goals/mvp"


class TestVault:
    def test_vault_path(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "v1", "scope")
        result = vault_path(mem, "goals/mvp", "Archiving goal")
        assert result["vault"] is True

    def test_vault_nonexistent(self, workspace):
        conn, uuid, mem = workspace
        result = vault_path(mem, "nonexistent", "Trying to vault")
        assert result["error"] == "not_found"
