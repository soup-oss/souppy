"""SQLite persistence layer for SOUP workspaces."""

from __future__ import annotations

import gzip
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from .core import (
    AgentEntry,
    AgentProfile,
    ChatMessage,
    JournalEntry,
    MemoryData,
    UIConfig,
    UILease,
    empty_memory,
)
from .core.common import get_timestamp


def _migrations_dir() -> Path:
    return Path(__file__).parent / "migrations"


def _split_sql(sql: str) -> list[str]:
    """Split SQL into individual statements, stripping comments."""
    statements = []
    current = []
    for line in sql.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            current = []
    # Handle last statement without trailing semicolon
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)
    return statements


def init_db(db_path: str) -> sqlite3.Connection:
    """Create a new SOUP database with the schema."""
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row

    migrations_dir = _migrations_dir()
    if migrations_dir.exists():
        for f in sorted(migrations_dir.glob("*.sql")):
            sql = f.read_text()
            # Strip comments and execute statement by statement
            statements = _split_sql(sql)
            for stmt in statements:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as e:
                    msg = str(e).lower()
                    # Skip unsupported operations (DROP COLUMN on SQLite < 3.35, etc.)
                    if "duplicate column" in msg or "no such column" in msg or "already exists" in msg or "syntax error" in msg:
                        continue
                    raise
    conn.commit()
    return conn


def open_db(db_path: str) -> sqlite3.Connection:
    """Open an existing SOUP database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Workspace not found: {db_path}. Run 'souppy init' first.")
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def load_memory(conn: sqlite3.Connection, workspace_uuid: str) -> MemoryData:
    """Load the full workspace state from SQLite."""
    mem = empty_memory()

    # Load data blob + pulse
    row = conn.execute(
        "SELECT data_json, mutation_id FROM memory_data WHERE uuid = ?", (workspace_uuid,)
    ).fetchone()
    if row:
        mem._data = json.loads(row["data_json"]) if row["data_json"] else {}
        mem._ui.mutation_id = row["mutation_id"] or 0

    # Load UI config
    row = conn.execute("SELECT * FROM memory_ui WHERE uuid = ?", (workspace_uuid,)).fetchone()
    if row:
        mem._ui.headless = bool(row["headless"])
        mem._ui.agents_paused = bool(row["agents_paused"])
        mem._ui.chat_paused = bool(row["chat_paused"])
        mem._ui.ts = row["ts"] or ""
        mem._ui.created_at = row["created_at"] or ""
        mem._ui.tier = row["tier"] or "free"
        mem._ui.global_revocation_ticker = row["global_revocation_ticker"] or 0
        mem._ui.invitation_ticker = row["invitation_ticker"] or 0
        mem._ui.user_token_uuid = row["user_token_uuid"]
        mem._ui.attestation_mode = bool(row["attestation_mode"]) if "attestation_mode" in row.keys() else False

    # Load agents
    for row in conn.execute("SELECT * FROM memory_agents WHERE uuid = ?", (workspace_uuid,)):
        profile_data = json.loads(row["profile_json"]) if row["profile_json"] else {}
        profile = AgentProfile(
            role=profile_data.get("role"),
            regex=profile_data.get("regex"),
            model=profile_data.get("model"),
        ) if profile_data else None
        permissions = json.loads(row["permissions_json"]) if row["permissions_json"] else []
        mem._agents[row["name"]] = AgentEntry(
            claimed=row["claimed"],
            profile=profile,
            project_id=row["project_id"] if "project_id" in row.keys() else None,
            epic_id=row["epic_id"] if "epic_id" in row.keys() else None,
            session_id=row["session_id"],
            last_ip=row["last_ip"],
            last_active_at=row["last_active_at"],
            revocation_ticker=row["revocation_ticker"] or 0,
            invitation_id=row["invitation_id"],
            permissions=permissions,
            revoked=bool(row["revoked"]),
        )

    # Load journal
    for row in conn.execute("SELECT * FROM memory_journal WHERE uuid = ?", (workspace_uuid,)):
        # Support both old column names (we/ve) and new (write_expiration/visibility_expiration)
        we = row["we"] if "we" in row.keys() else row["write_expiration"]
        ve = row["ve"] if "ve" in row.keys() else row["visibility_expiration"]
        mem._journal[row["path"]] = JournalEntry(
            ts=row["ts"],
            cs=row["cs"],
            ro=bool(row["ro"]),
            vault=bool(row["vault"]),
            we=we,
            ve=ve,
        )

    # Load chat
    for row in conn.execute("SELECT * FROM memory_chat WHERE uuid = ?", (workspace_uuid,)):
        mem._chat[row["key"]] = ChatMessage(
            from_name=row["from_name"],
            to_name=row["to_name"],
            msg=row["msg"],
        )

    # Load cursors
    for row in conn.execute("SELECT * FROM memory_cursors WHERE uuid = ?", (workspace_uuid,)):
        if row["agent_name"] not in mem._cursors:
            mem._cursors[row["agent_name"]] = {}
        mem._cursors[row["agent_name"]][row["message_key"]] = row["ack_level"]

    return mem


def save_memory(conn: sqlite3.Connection, workspace_uuid: str, mem: MemoryData) -> None:
    """Persist the full workspace state to SQLite."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        # Save data blob + pulse
        conn.execute(
            "INSERT OR REPLACE INTO memory_data (uuid, data_json, mutation_id) VALUES (?, ?, ?)",
            (workspace_uuid, json.dumps(mem._data), mem._ui.mutation_id),
        )

        # Save UI config
        conn.execute(
            """INSERT OR REPLACE INTO memory_ui
               (uuid, headless, agents_paused, chat_paused, ts, created_at, tier,
                global_revocation_ticker, invitation_ticker, user_token_uuid)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                workspace_uuid,
                int(mem._ui.headless),
                int(mem._ui.agents_paused),
                int(mem._ui.chat_paused),
                mem._ui.ts,
                mem._ui.created_at,
                mem._ui.tier,
                mem._ui.global_revocation_ticker,
                mem._ui.invitation_ticker,
                mem._ui.user_token_uuid,
            ),
        )

        # Clear and rebuild agents
        conn.execute("DELETE FROM memory_agents WHERE uuid = ?", (workspace_uuid,))
        for name, agent in mem._agents.items():
            profile_json = {}
            if agent.profile:
                profile_json = {k: v for k, v in {"role": agent.profile.role, "regex": agent.profile.regex, "model": agent.profile.model}.items() if v}
            conn.execute(
                """INSERT INTO memory_agents
                   (uuid, name, claimed, profile_json, session_id, last_ip, last_active_at,
                    revocation_ticker, invitation_id, permissions_json, revoked)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    workspace_uuid,
                    name,
                    agent.claimed,
                    json.dumps(profile_json),
                    agent.session_id,
                    agent.last_ip,
                    agent.last_active_at,
                    agent.revocation_ticker,
                    agent.invitation_id,
                    json.dumps(agent.permissions),
                    int(agent.revoked),
                ),
            )

        # Clear and rebuild journal
        conn.execute("DELETE FROM memory_journal WHERE uuid = ?", (workspace_uuid,))
        for path, entry in mem._journal.items():
            conn.execute(
                """INSERT INTO memory_journal (uuid, path, ts, cs, ro, vault, write_expiration, visibility_expiration)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (workspace_uuid, path, entry.ts, entry.cs, int(entry.ro), int(entry.vault), entry.we, entry.ve),
            )

        # Append queued audit snapshots (append-only)
        for snap in mem._pending_snapshots:
            insert_snapshot(conn, workspace_uuid, snap)

        # Clear and rebuild chat
        conn.execute("DELETE FROM memory_chat WHERE uuid = ?", (workspace_uuid,))
        for key, msg in mem._chat.items():
            conn.execute(
                "INSERT INTO memory_chat (uuid, key, ts, from_name, to_name, msg) VALUES (?, ?, ?, ?, ?, ?)",
                (workspace_uuid, key, get_timestamp(), msg.from_name, msg.to_name, msg.msg),
            )

        # Clear and rebuild cursors
        conn.execute("DELETE FROM memory_cursors WHERE uuid = ?", (workspace_uuid,))
        for agent_name, agent_cursors in mem._cursors.items():
            for msg_key, ack_level in agent_cursors.items():
                conn.execute(
                    "INSERT INTO memory_cursors (uuid, agent_name, message_key, ack_level) VALUES (?, ?, ?, ?)",
                    (workspace_uuid, agent_name, msg_key, ack_level),
                )

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def delete_workspace(conn: sqlite3.Connection, workspace_uuid: str) -> None:
    """Delete all data for a workspace."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        for table in ["memory_data", "memory_ui", "memory_agents", "memory_journal",
                       "memory_chat", "memory_cursors", "memory_ui_leases", "memory_snapshots"]:
            conn.execute(f"DELETE FROM {table} WHERE uuid = ?", (workspace_uuid,))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def insert_snapshot(conn: sqlite3.Connection, workspace_uuid: str, snap: dict) -> None:
    """Append an audit snapshot row for the workspace."""
    conn.execute(
        """INSERT INTO memory_snapshots
           (id, uuid, path, data_json, diff_b64, chain_hash, intent, agent_name,
            lines_added, lines_removed, ts, mutation_id, old_meta, new_meta,
            tool_call, secret_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            snap["id"],
            workspace_uuid,
            snap["path"],
            snap["data_json"],
            snap["diff_b64"],
            snap.get("chain_hash"),
            snap["intent"],
            snap.get("agent_name"),
            snap["lines_added"],
            snap["lines_removed"],
            snap["ts"],
            snap["mutation_id"],
            snap.get("old_meta"),
            snap.get("new_meta"),
            snap.get("tool_call"),
            snap.get("secret_version"),
        ),
    )


def get_snapshots(conn: sqlite3.Connection, workspace_uuid: str, path: str | None = None, limit: int = 10) -> list[dict]:
    """Get snapshots for a workspace, optionally filtered by path."""
    if path:
        rows = conn.execute(
            "SELECT * FROM memory_snapshots WHERE uuid = ? AND path = ? ORDER BY mutation_id DESC, ts DESC LIMIT ?",
            (workspace_uuid, path, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM memory_snapshots WHERE uuid = ? ORDER BY mutation_id DESC, ts DESC LIMIT ?",
            (workspace_uuid, limit),
        ).fetchall()
    return [dict(r) for r in rows]
