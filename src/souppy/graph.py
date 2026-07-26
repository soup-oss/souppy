"""Logic for the hierarchical memory graph and path resolution."""

from __future__ import annotations

import re
from typing import Any

from .core.common import JOURNAL_LIMIT


def get_nested_value(obj: dict[str, Any], path: str) -> Any:
    """Get a value from a nested dict by slash-separated path."""
    parts = [p for p in path.split("/") if p]
    current: Any = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def set_nested_value(obj: dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a nested dict, creating intermediate dicts as needed."""
    parts = [p for p in path.split("/") if p]
    current: dict[str, Any] = obj
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def delete_nested_value(obj: dict[str, Any], path: str) -> bool:
    """Delete a value from a nested dict. Returns True if deleted."""
    parts = [p for p in path.split("/") if p]
    if not parts:
        return False
    stack: list[tuple[dict[str, Any], str]] = []
    current: Any = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            stack.append((current, part))
            current = current[part]
        else:
            return False
    if not stack:
        return False
    parent, key = stack.pop()
    del parent[key]
    # Clean up empty parent dicts
    while stack:
        parent, key = stack.pop()
        child = parent.get(key)
        if isinstance(child, dict) and not child:
            del parent[key]
    return True


def matches_glob(path: str, pattern: str) -> bool:
    """Check if a path matches a glob pattern."""
    regex = (
        pattern
        .replace(".", "\\.")
        .replace("**", "{{DOUBLE_STAR}}")
        .replace("*", "[^/]*")
        .replace("{{DOUBLE_STAR}}", ".*")
        .replace("?", ".")
    )
    return bool(re.match(f"^{regex}$", path))


def glob_match(paths: list[str], pattern: str) -> list[str]:
    """Filter paths by glob pattern."""
    return [p for p in paths if matches_glob(p, pattern)]


def generate_diff(old_val: str, new_val: str) -> tuple[str, int, int]:
    """Generate a unified diff. Returns (diff_string, lines_added, lines_removed)."""
    if old_val == new_val:
        return "", 0, 0
    old_lines = old_val.split("\n")
    new_lines = new_val.split("\n")
    diff_parts: list[str] = []
    added = 0
    removed = 0
    max_len = max(len(old_lines), len(new_lines))
    for i in range(max_len):
        old_line = old_lines[i] if i < len(old_lines) else None
        new_line = new_lines[i] if i < len(new_lines) else None
        if old_line != new_line:
            if old_line is not None:
                diff_parts.append(f"- {old_line}")
                removed += 1
            if new_line is not None:
                diff_parts.append(f"+ {new_line}")
                added += 1
    return "\n".join(diff_parts), added, removed


def prune_journal(journal: dict[str, Any]) -> list[str]:
    """Remove oldest journal entries if over limit. Returns removed paths."""
    if len(journal) <= JOURNAL_LIMIT:
        return []
    sorted_keys = sorted(journal.keys(), key=lambda k: journal[k].ts, reverse=True)
    to_remove = sorted_keys[JOURNAL_LIMIT:]
    for key in to_remove:
        del journal[key]
    return to_remove


def scan_for_backlinks(data: dict[str, Any], target_path: str) -> list[str]:
    """Find all paths that reference the target path via wiki or markdown links."""
    backlinks: list[str] = []

    def _scan(obj: Any, current_path: str) -> None:
        if not obj or not isinstance(obj, dict):
            return
        for key, val in obj.items():
            full_path = f"{current_path}/{key}" if current_path else key
            if isinstance(val, str):
                if f"[[{target_path}]]" in val or re.search(
                    rf"\[[^\]]*\]\({re.escape(target_path)}\)", val
                ):
                    backlinks.append(full_path)
            elif isinstance(val, dict):
                _scan(val, full_path)

    _scan(data, "")
    return [b for b in backlinks if b != target_path]
