"""Tests for souppy persistence layer."""

import pytest
from souppy.core import empty_memory, UIConfig
from souppy.persistence import init_db, open_db, load_memory, save_memory, delete_workspace


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.soup.db")


def test_init_db(db_path):
    conn = init_db(db_path)
    assert conn is not None
    conn.close()


def test_open_db_nonexistent(tmp_path):
    with pytest.raises(FileNotFoundError):
        open_db(str(tmp_path / "nonexistent.db"))


def test_save_and_load_memory(db_path):
    conn = init_db(db_path)
    uuid = "test-uuid-1234"
    
    mem = empty_memory()
    mem._ui.headless = True
    mem._ui.mutation_id = 42
    save_memory(conn, uuid, mem)
    
    loaded = load_memory(conn, uuid)
    assert loaded._ui.headless is True
    assert loaded._ui.mutation_id == 42
    conn.close()


def test_save_load_agents(db_path):
    conn = init_db(db_path)
    uuid = "test-uuid"
    
    mem = empty_memory()
    from souppy.core import AgentEntry, AgentProfile
    mem._agents["alice"] = AgentEntry(
        claimed="2024-01-01",
        profile=AgentProfile(role="frontend"),
    )
    save_memory(conn, uuid, mem)
    
    loaded = load_memory(conn, uuid)
    assert "alice" in loaded._agents
    assert loaded._agents["alice"].profile.role == "frontend"
    conn.close()


def test_save_load_journal(db_path):
    conn = init_db(db_path)
    uuid = "test-uuid"
    
    mem = empty_memory()
    from souppy.core import JournalEntry
    mem._journal["goals/mvp"] = JournalEntry(ts="2024-01-01", cs="abc123")
    save_memory(conn, uuid, mem)
    
    loaded = load_memory(conn, uuid)
    assert "goals/mvp" in loaded._journal
    assert loaded._journal["goals/mvp"].cs == "abc123"
    conn.close()


def test_save_load_chat(db_path):
    conn = init_db(db_path)
    uuid = "test-uuid"
    
    mem = empty_memory()
    from souppy.core import ChatMessage
    mem._chat["ts_alice_bob"] = ChatMessage(from_name="alice", to_name="bob", msg="hello")
    save_memory(conn, uuid, mem)
    
    loaded = load_memory(conn, uuid)
    assert "ts_alice_bob" in loaded._chat
    assert loaded._chat["ts_alice_bob"].msg == "hello"
    conn.close()


def test_delete_workspace(db_path):
    conn = init_db(db_path)
    uuid = "test-uuid"
    
    mem = empty_memory()
    save_memory(conn, uuid, mem)
    
    delete_workspace(conn, uuid)
    
    loaded = load_memory(conn, uuid)
    assert loaded._agents == {}
    assert loaded._journal == {}
    conn.close()
