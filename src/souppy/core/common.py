"""Generic stateless utilities."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any


JOURNAL_LIMIT = 5000
CHAT_LIMIT = 1000


def get_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_chat_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "")


def to_canonical_json(data: Any) -> str:
    """Deterministic JSON serialization with sorted keys."""
    if data is None:
        return "null"
    if isinstance(data, bool):
        return "true" if data else "false"
    if isinstance(data, (int, float)):
        return json.dumps(data)
    if isinstance(data, str):
        return json.dumps(data)
    if isinstance(data, list):
        return "[" + ",".join(to_canonical_json(i) for i in data) + "]"
    if isinstance(data, dict):
        keys = sorted(data.keys())
        items = ",".join(json.dumps(k) + ":" + to_canonical_json(data[k]) for k in keys)
        return "{" + items + "}"
    return json.dumps(data)


def validate_intent(intent: str) -> tuple[bool, str | None, str | None]:
    """Validate intent string. Returns (valid, error, feedback)."""
    if not intent or len(intent.strip()) < 5:
        return False, "intent_too_short", "Intent must be at least 5 characters long and describe the reason for the change."
    return True, None, None


def extract_internal_links(value: Any) -> list[str]:
    """Extract internal links from a value (wiki-style [[path]] and markdown [label](path))."""
    links: list[str] = []
    s = value if isinstance(value, str) else json.dumps(value)
    for m in re.finditer(r"\[\[([^\]]+)\]\]", s):
        links.append(m.group(1))
    for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", s):
        target = m.group(2)
        if not target.startswith("http://") and not target.startswith("https://"):
            links.append(target)
    return links
