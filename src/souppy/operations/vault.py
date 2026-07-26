"""Vault operation — soft-delete paths with structural integrity."""

from __future__ import annotations

from ..core import MemoryData
from ..core.common import get_timestamp
from ..core.common import validate_intent
from ..graph import get_nested_value, scan_for_backlinks


def vault_path(
    memory: MemoryData,
    path: str,
    intent: str,
    vault: bool = True,
    we: str | None = None,
    ve: str | None = None,
) -> dict:
    """Vault or unvault a path. Only structure managers can do this."""
    valid, error, feedback = validate_intent(intent)
    if not valid:
        return {"error": error, "feedback": feedback, "status": 400}

    entry = memory._journal.get(path)
    if not entry:
        return {"error": "not_found", "status": 404}

    # Leaf-level guard: cannot vault a branch
    if vault:
        prefix = path + "/"
        has_descendants = any(p.startswith(prefix) for p in memory._journal)
        if has_descendants:
            return {"error": "forbidden", "detail": "vault_branch_prohibited", "status": 403}

        # Backlink check
        backlinks = scan_for_backlinks(memory._data, path)
        if backlinks:
            return {"error": "conflict", "detail": "vault_target_referenced", "backlinks": backlinks, "status": 409}

    # Increment pulse
    mutation_id = memory._ui.mutation_id + 1
    memory._ui.mutation_id = mutation_id

    # Apply vault state
    entry.vault = vault
    if we is not None:
        entry.we = we
    if ve is not None:
        entry.ve = ve

    return {"path": path, "vault": entry.vault, "pulse": mutation_id}
