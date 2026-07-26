"""Audit operations — snapshots, chain hash, inertia."""

from __future__ import annotations

from ..core import MemoryData
from ..persistence import get_snapshots


def get_inertia(memory: MemoryData, path: str | None = None) -> dict:
    """Get the last mutations for context (inertia)."""
    result = {"local": [], "global": []}

    # Local inertia: last 3 snapshots for the specific path
    if path:
        local = get_inertia_for_path(memory, path, limit=3)
        result["local"] = local

    # Global inertia: last 3 snapshots across the workspace
    global_inertia = get_inertia_global(memory, limit=3)
    result["global"] = global_inertia

    return result


def get_inertia_for_path(memory: MemoryData, path: str, limit: int = 3) -> list[dict]:
    """Get recent snapshots for a specific path (from journal metadata)."""
    # Use journal entries as a lightweight proxy for inertia
    entry = memory._journal.get(path)
    if not entry:
        return []
    return [{
        "path": path,
        "ts": entry.ts,
        "mutation_id": memory._ui.mutation_id,
    }]


def get_inertia_global(memory: MemoryData, limit: int = 3) -> list[dict]:
    """Get the most recently modified paths across the workspace."""
    sorted_paths = sorted(
        memory._journal.keys(),
        key=lambda p: memory._journal[p].ts,
        reverse=True,
    )[:limit]
    return [{
        "path": p,
        "ts": memory._journal[p].ts,
        "mutation_id": memory._ui.mutation_id,
    } for p in sorted_paths]
