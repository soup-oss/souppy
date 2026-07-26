"""Delete operation — remove paths from the workspace graph."""

from __future__ import annotations

from ..core import MemoryData
from ..core.common import validate_intent
from ..graph import delete_nested_value
from ..security import check_ancestor_vault


def delete_path(memory: MemoryData, path: str, intent: str) -> dict:
    """Delete a path and all descendants. Returns {pulse, deleted_count}."""
    valid, error, feedback = validate_intent(intent)
    if not valid:
        return {"error": error, "feedback": feedback, "status": 400}

    # Find all paths to delete (target + descendants)
    prefix = path + "/"
    targets = [p for p in memory._journal if p == path or p.startswith(prefix)]

    if not targets:
        return {"error": "not_found", "status": 404}

    # Check read-only locks
    for t in targets:
        entry = memory._journal.get(t)
        if entry and entry.ro:
            return {"error": "forbidden", "detail": "read_only", "path": t, "status": 403}

    # Increment pulse
    mutation_id = memory._ui.mutation_id + 1
    memory._ui.mutation_id = mutation_id

    # Delete from data
    delete_nested_value(memory._data, path)

    # Delete from journal
    for t in targets:
        if t in memory._journal:
            del memory._journal[t]

    return {
        "pulse": mutation_id,
        "deleted_count": len(targets),
        "deleted_paths": targets,
    }
