"""Write operation — write values to the workspace graph."""

from __future__ import annotations

import json
from typing import Any

from ..core import JournalEntry, MemoryData
from ..core.common import get_timestamp, validate_intent, extract_internal_links, to_canonical_json
from ..crypto import compute_checksum
from ..graph import (
    get_nested_value,
    set_nested_value,
    delete_nested_value,
    prune_journal,
    generate_diff,
)
from ..security import check_ancestor_vault


def write_path(
    memory: MemoryData,
    path: str,
    value: Any,
    intent: str,
    checksum: str | None = None,
) -> dict:
    """Write a value to the workspace. Returns {pulse, journal_pruned}."""
    # Validate intent
    valid, error, feedback = validate_intent(intent)
    if not valid:
        return {"error": error, "feedback": feedback, "status": 400}

    # Check ancestor vault
    vaulted = check_ancestor_vault(memory, path)
    if vaulted:
        return {"error": "forbidden", "detail": "vault_anchor_violation", "path": vaulted, "status": 403}

    # Check write expiration on existing entry
    existing_entry = memory._journal.get(path)
    if existing_entry and existing_entry.we and existing_entry.we < get_timestamp():
        return {"error": "forbidden", "detail": "write_expired", "status": 403}

    # Check read-only lock
    if existing_entry and existing_entry.ro:
        return {"error": "forbidden", "detail": "read_only", "status": 403}

    # Check optimistic concurrency (checksum)
    if checksum and existing_entry:
        current_checksum = existing_entry.cs
        if checksum != current_checksum:
            return {"error": "conflict", "detail": "checksum_mismatch", "status": 409}

    # Deep no-op detection
    old_value = get_nested_value(memory._data, path)
    if old_value is not None:
        if isinstance(old_value, str) and old_value == value:
            return {"pulse": memory._ui.mutation_id, "noop": True}
        elif not isinstance(old_value, str) and to_canonical_json(old_value) == to_canonical_json(value):
            return {"pulse": memory._ui.mutation_id, "noop": True}

    # Generate diff for snapshots
    old_str = json.dumps(old_value) if old_value is not None else ""
    new_str = json.dumps(value) if not isinstance(value, str) else value
    diff_str, added, removed = generate_diff(old_str, new_str)

    # Compute new checksum
    new_checksum = compute_checksum(value)

    # Increment pulse
    mutation_id = memory._ui.mutation_id + 1
    memory._ui.mutation_id = mutation_id

    # Set the value
    set_nested_value(memory._data, path, value)

    # Handle parent-to-node conversion: if writing a/b/c, remove a/b if it exists as a leaf
    parts = [p for p in path.split("/") if p]
    for i in range(1, len(parts)):
        parent = "/".join(parts[:i])
        if parent in memory._journal and parent != path:
            # Check if parent has descendants
            prefix = parent + "/"
            has_descendants = any(p.startswith(prefix) for p in memory._journal if p != parent)
            if not has_descendants:
                # Parent is a leaf being replaced by a child
                del memory._journal[parent]

    # Update journal
    ts = get_timestamp()
    memory._journal[path] = JournalEntry(ts=ts, cs=new_checksum)

    # Prune journal if over limit
    pruned = prune_journal(memory._journal)

    # Check for broken outbound links
    links = extract_internal_links(value)
    broken = [link for link in links if link not in memory._journal and link != path]

    return {
        "pulse": mutation_id,
        "lines_added": added,
        "lines_removed": removed,
        "broken_links": broken,
        "journal_pruned": pruned,
    }
