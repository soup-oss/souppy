"""Audit operations — snapshots (intent + state) and read inertia.

Every mutation queues a snapshot carrying the intent (the "why") alongside
the previous state and a diff. Snapshots are persisted to the memory_snapshots
table and surfaced on reads as inertia, matching heysoup.co's audit trail.
The HMAC chain is a heysoup.co platform feature; locally chain_hash stays null.
"""

from __future__ import annotations

import base64
import gzip
import sqlite3
import uuid
from typing import Any

from ..core import MemoryData
from ..core.common import get_timestamp, to_canonical_json
from ..graph import generate_diff

_INERTIA_COLS = "id, path, intent, agent_name, mutation_id, lines_added, lines_removed, ts"


def _compress_b64(data: str) -> str:
    """Compress a string to gzip->base64 (prefix 'gz:' like heysoup.co)."""
    return "gz:" + base64.b64encode(gzip.compress(data.encode("utf-8"))).decode("ascii")


def queue_snapshot(
    memory: MemoryData,
    path: str,
    old_value: Any,
    new_value: Any,
    intent: str,
    mutation_id: int,
    old_meta: dict | None = None,
    new_meta: dict | None = None,
    agent_name: str | None = None,
) -> None:
    """Append an audit snapshot for a mutation to the pending list.

    The snapshot captures the previous state (data_json), the diff, and the
    intent. It is persisted by save_memory() alongside the workspace state.
    """
    ts = get_timestamp()
    old_json = to_canonical_json(old_value)
    new_json = to_canonical_json(new_value)
    diff_str, added, removed = generate_diff(old_json, new_json)

    memory._pending_snapshots.append({
        "id": uuid.uuid4().hex,
        "path": path,
        "data_json": _compress_b64(old_json),
        "diff_b64": _compress_b64(diff_str),
        "chain_hash": None,
        "intent": intent,
        "agent_name": agent_name,
        "lines_added": added,
        "lines_removed": removed,
        "ts": ts,
        "mutation_id": mutation_id,
        "old_meta": to_canonical_json(old_meta or {}),
        "new_meta": to_canonical_json(new_meta or {}),
        "tool_call": None,
        "secret_version": None,
    })


def _snap_rows(conn: sqlite3.Connection, workspace_uuid: str, path: str | None, limit: int) -> list[dict]:
    if path:
        rows = conn.execute(
            f"SELECT {_INERTIA_COLS} FROM memory_snapshots "
            "WHERE uuid = ? AND path = ? ORDER BY mutation_id DESC, ts DESC LIMIT ?",
            (workspace_uuid, path, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT {_INERTIA_COLS} FROM memory_snapshots "
            "WHERE uuid = ? ORDER BY mutation_id DESC, ts DESC LIMIT ?",
            (workspace_uuid, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_inertia(conn: sqlite3.Connection, workspace_uuid: str, path: str) -> dict:
    """Get the last 3 mutations for the path (local) and workspace (global).

    Mirrors heysoup.co's read inertia: recent mutations with intents so a
    reader can see what happened and why without reading all content.
    """
    try:
        return {
            "local": _snap_rows(conn, workspace_uuid, path=path, limit=3),
            "global": _snap_rows(conn, workspace_uuid, path=None, limit=3),
        }
    except Exception:
        return {"local": [], "global": []}
