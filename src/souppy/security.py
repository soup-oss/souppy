"""State gating and security rules (Vaulting, Expiration)."""

from __future__ import annotations

from .core import MemoryData
from .core.common import get_timestamp, validate_intent, extract_internal_links
from .graph import get_nested_value, scan_for_backlinks


def is_vaulted(entry: dict | None) -> bool:
    """Check if a journal entry is vaulted (soft-deleted)."""
    if not entry:
        return False
    if entry.get("vault"):
        return True
    ve = entry.get("ve")
    if ve and ve < get_timestamp():
        return True
    return False


def is_write_expired(entry: dict | None) -> bool:
    """Check if a write has expired."""
    if not entry:
        return False
    we = entry.get("we")
    if we and we < get_timestamp():
        return True
    return False


def check_ancestor_vault(memory: MemoryData, path: str) -> str | None:
    """Check if any ancestor path is vaulted. Returns the vaulted path or None."""
    parts = [p for p in path.split("/") if p]
    for i in range(1, len(parts)):
        parent_path = "/".join(parts[:i])
        entry = memory._journal.get(parent_path)
        if entry and entry.vault:
            return parent_path
    return None


def check_leaf_vault(memory: MemoryData, path: str) -> bool:
    """Check if the path has descendants (not a leaf)."""
    prefix = path + "/"
    return any(p.startswith(prefix) for p in memory._journal)
