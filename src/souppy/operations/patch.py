"""Patch operation — surgically update part of a markdown file."""

from __future__ import annotations

from ..core import MemoryData
from .write import write_path


def patch_path(memory: MemoryData, path: str, intent: str, diff: str) -> dict:
    """Apply a line-level patch to a value. Diff format: '- old' / '+ new' lines."""
    from ..graph import get_nested_value

    current = get_nested_value(memory._data, path)
    if current is None:
        return {"error": "not_found", "status": 404}

    if not isinstance(current, str):
        return {"error": "invalid_type", "detail": "Can only patch string values", "status": 400}

    # Parse diff lines
    removals: list[str] = []
    additions: list[str] = []
    for line in diff.split("\n"):
        if line.startswith("- "):
            removals.append(line[2:])
        elif line.startswith("+ "):
            additions.append(line[2:])

    if not removals:
        return {"error": "invalid_diff", "detail": "No removal lines found", "status": 400}

    # Find the removal block in the current value
    current_lines = current.split("\n")
    removal_text = "\n".join(removals)
    idx = current.find(removal_text)

    if idx == -1:
        # Try line-by-line matching
        for i, line in enumerate(current_lines):
            if line == removals[0]:
                match = True
                for j, rem in enumerate(removals):
                    if i + j >= len(current_lines) or current_lines[i + j] != rem:
                        match = False
                        break
                if match:
                    # Replace this block
                    new_lines = current_lines[:i] + additions + current_lines[i + len(removals):]
                    new_value = "\n".join(new_lines)
                    return write_path(memory, path, new_value, intent)

        return {
            "error": "patch_not_found",
            "detail": "Removal lines not found in current value",
            "status": 409,
        }

    # Apply patch
    new_value = current[:idx] + "\n".join(additions) + current[idx + len(removal_text):]
    return write_path(memory, path, new_value, intent)
