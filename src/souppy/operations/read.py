"""Read operation — read values from the workspace graph."""

from __future__ import annotations

from ..core import MemoryData
from ..graph import get_nested_value


def read_path(
    memory: MemoryData,
    path: str,
    offset: int | None = None,
    limit: int | None = None,
) -> dict:
    """Read a value from the workspace. Returns {value, total_length, pulse}."""
    value = get_nested_value(memory._data, path)

    if value is None:
        # Try reading as a directory (return subtree)
        if path.endswith("/"):
            dir_path = path.rstrip("/")
            value = get_nested_value(memory._data, dir_path)
            if value is None:
                return {"value": None, "total_length": 0, "pulse": memory._ui.mutation_id}

    if isinstance(value, str):
        total = len(value)
        if offset is not None and limit is not None:
            value = value[offset : offset + limit]
        elif limit is not None:
            value = value[:limit]
        return {"value": value, "total_length": total, "pulse": memory._ui.mutation_id}

    return {"value": value, "total_length": 0, "pulse": memory._ui.mutation_id}
