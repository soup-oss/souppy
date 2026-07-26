"""Search operations — glob and grep across the workspace."""

from __future__ import annotations

import re
from typing import Any

from ..core import MemoryData
from ..graph import glob_match, get_nested_value


def glob_search(memory: MemoryData, pattern: str, limit: int = 100) -> list[dict]:
    """Search journal paths by glob pattern."""
    paths = list(memory._journal.keys())
    matches = glob_match(paths, pattern)
    results = []
    for path in sorted(matches)[:limit]:
        entry = memory._journal[path]
        results.append({
            "path": path,
            "ts": entry.ts,
            "cs": entry.cs,
        })
    return results


def grep_search(
    memory: MemoryData,
    pattern: str,
    include: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Search content by regex pattern."""
    results = []
    regex = re.compile(pattern, re.IGNORECASE)
    for path in sorted(memory._journal.keys()):
        if include and not glob_match([path], include):
            continue
        value = get_nested_value(memory._data, path)
        if value is None:
            continue
        text = value if isinstance(value, str) else str(value)
        if regex.search(text):
            results.append({
                "path": path,
                "match": text[:200],
            })
            if len(results) >= limit:
                break
    return results
