"""Tests for the audit trail — snapshots, intents, and read inertia.

Mirrors heysoup.co's audit behavior: every mutation persists a snapshot
with its intent, and reads surface the recent mutations (inertia).
"""

import json

import pytest

from souppy.cli import main
from souppy.core import empty_memory
from souppy.persistence import init_db, load_memory, save_memory, get_snapshots
from souppy.operations.write import write_path
from souppy.operations.read import read_path
from souppy.operations.delete import delete_path
from souppy.operations.vault import vault_path
from souppy.operations.audit import get_inertia


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


class TestWriteSnapshot:
    def test_write_queues_snapshot(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "Setting initial scope", agent_name="dm")
        assert len(mem._pending_snapshots) == 1
        snap = mem._pending_snapshots[0]
        assert snap["path"] == "goals/mvp"
        assert snap["intent"] == "Setting initial scope"
        assert snap["agent_name"] == "dm"
        assert snap["mutation_id"] == 1
        assert snap["data_json"].startswith("gz:")
        assert snap["diff_b64"].startswith("gz:")

    def test_write_noop_does_not_snapshot(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "Setting scope", agent_name="dm")
        result = write_path(mem, "goals/mvp", "Ship v1", "Same value again", agent_name="dm")
        assert result.get("noop") is True
        assert len(mem._pending_snapshots) == 1

    def test_snapshot_persisted_to_db(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "Setting initial scope", agent_name="dm")
        save_memory(conn, uuid, mem)
        rows = get_snapshots(conn, uuid)
        assert len(rows) == 1
        assert rows[0]["path"] == "goals/mvp"
        assert rows[0]["intent"] == "Setting initial scope"
        assert rows[0]["agent_name"] == "dm"
        assert rows[0]["mutation_id"] == 1

    def test_parent_conversion_snapshot(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals", "old leaf", "initial leaf", agent_name="dm")
        write_path(mem, "goals/mvp", "Ship v1", "nested write", agent_name="dm")
        assert len(mem._pending_snapshots) == 3
        conversion = mem._pending_snapshots[2]
        assert conversion["path"] == "goals"
        assert "Converted to node" in conversion["intent"]
        import base64
        import gzip
        old_value = gzip.decompress(
            base64.b64decode(conversion["data_json"][3:])
        ).decode("utf-8")
        assert old_value == '"old leaf"'


class TestDeleteSnapshot:
    def test_delete_queues_snapshot_per_target(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "scope", agent_name="dm")
        write_path(mem, "goals/stack", "React", "stack", agent_name="dm")
        mem._pending_snapshots.clear()
        result = delete_path(mem, "goals", "Cleaning up goals", agent_name="dm")
        assert result["deleted_count"] == 2
        assert len(mem._pending_snapshots) == 2
        assert {s["path"] for s in mem._pending_snapshots} == {"goals/mvp", "goals/stack"}
        assert all(s["intent"] == "Cleaning up goals" for s in mem._pending_snapshots)


class TestVaultSnapshot:
    def test_vault_queues_snapshot(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "scope", agent_name="dm")
        mem._pending_snapshots.clear()
        result = vault_path(mem, "goals/mvp", "Archiving goal", agent_name="dm")
        assert result["vault"] is True
        assert len(mem._pending_snapshots) == 1
        snap = mem._pending_snapshots[0]
        assert snap["intent"] == "Archiving goal"
        assert snap["path"] == "goals/mvp"


class TestInertia:
    def test_get_inertia_local_and_global(self, workspace):
        conn, uuid, mem = workspace
        write_path(mem, "goals/mvp", "Ship v1", "scope", agent_name="dm")
        write_path(mem, "goals/stack", "React", "stack", agent_name="dm")
        save_memory(conn, uuid, mem)

        inertia = get_inertia(conn, uuid, "goals/mvp")
        local = inertia["local"]
        assert len(local) == 1
        assert local[0]["path"] == "goals/mvp"
        assert local[0]["intent"] == "scope"
        assert local[0]["agent_name"] == "dm"
        assert len(inertia["global"]) == 2
        assert inertia["global"][0]["path"] == "goals/stack"

    def test_inertia_empty_for_unknown_path(self, workspace):
        conn, uuid, mem = workspace
        save_memory(conn, uuid, mem)
        inertia = get_inertia(conn, uuid, "unknown")
        assert inertia == {"local": [], "global": []}


class TestReadOutput:
    def test_read_returns_envelope(self, db_path, capsys):
        main(["init", db_path])
        capsys.readouterr()
        main(["write", db_path, "goals/mvp", "Ship v1", "--intent", "Setting scope"])
        capsys.readouterr()
        main(["read", db_path, "goals/mvp"])
        result = json.loads(capsys.readouterr().out)
        assert result["path"] == "goals/mvp"
        assert result["value"] == "Ship v1"
        assert result["totalLength"] == len("Ship v1")
        assert result["offset"] == 0
        assert result["limit"] is None
        assert "inertia" in result
        assert result["inertia"]["local"][0]["intent"] == "Setting scope"

    def test_read_value_only(self, db_path, capsys):
        main(["init", db_path])
        capsys.readouterr()
        main(["write", db_path, "goals/mvp", "Ship v1", "--intent", "Setting scope"])
        capsys.readouterr()
        main(["read", db_path, "goals/mvp", "--value-only"])
        assert capsys.readouterr().out.strip() == "Ship v1"

    def test_read_directory_value_only(self, db_path, capsys):
        main(["init", db_path])
        capsys.readouterr()
        main(["write", db_path, "goals/mvp", "Ship v1", "--intent", "Setting scope"])
        capsys.readouterr()
        main(["read", db_path, "goals/", "--value-only"])
        result = json.loads(capsys.readouterr().out)
        assert result["mvp"] == "Ship v1"

    def test_read_missing_path(self, db_path, capsys):
        main(["init", db_path])
        capsys.readouterr()
        main(["read", db_path, "nope", "--value-only"])
        assert "Path not found: nope" in capsys.readouterr().out


class TestSnapshotsCommand:
    def test_snapshots_lists_audit_rows(self, db_path, capsys):
        main(["init", db_path])
        capsys.readouterr()
        main(["write", db_path, "goals/mvp", "Ship v1", "--intent", "Setting scope"])
        capsys.readouterr()
        main(["snapshots", db_path])
        result = json.loads(capsys.readouterr().out)
        assert len(result) == 1
        assert result[0]["path"] == "goals/mvp"
        assert result[0]["intent"] == "Setting scope"
