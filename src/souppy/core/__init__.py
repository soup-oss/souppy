"""Core types and data structures for the SOUP protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


TIER_FREE = "free"
TIER_PRO = "pro"
TIER_ARCHITECT = "architect"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "")


def _now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class AgentProfile:
    role: str | None = None
    regex: str | None = None
    model: str | None = None


@dataclass
class AgentEntry:
    claimed: str
    profile: AgentProfile | None = None
    project_id: str | None = None
    epic_id: str | None = None
    session_id: str | None = None
    last_ip: str | None = None
    last_active_at: str | None = None
    revocation_ticker: int = 0
    invitation_id: str | None = None
    permissions: list[str] = field(default_factory=list)
    revoked: bool = False


@dataclass
class JournalEntry:
    ts: str
    cs: str
    ro: bool = False
    vault: bool = False
    we: str | None = None
    ve: str | None = None


@dataclass
class UILease:
    location_hash: str
    last_ip: str
    last_seen_at: str


@dataclass
class UIConfig:
    headless: bool = False
    agents_paused: bool = False
    chat_paused: bool = False
    ts: str = field(default_factory=_now_ts)
    created_at: str = field(default_factory=_now_ts)
    mutation_id: int = 0
    tier: str = TIER_FREE
    encryption_check: str | None = None
    global_revocation_ticker: int = 0
    invitation_ticker: int = 0
    user_token_uuid: str | None = None
    attestation_mode: bool = False


@dataclass
class ChatMessage:
    from_name: str
    to_name: str
    msg: str


@dataclass
class MemoryData:
    _ui: UIConfig = field(default_factory=UIConfig)
    _agents: dict[str, AgentEntry] = field(default_factory=dict)
    _journal: dict[str, JournalEntry] = field(default_factory=dict)
    _data: dict[str, Any] = field(default_factory=dict)
    _leases: dict[str, UILease] = field(default_factory=dict)
    _chat: dict[str, ChatMessage] = field(default_factory=dict)
    _cursors: dict[str, dict[str, int]] = field(default_factory=dict)
    _pending_snapshots: list[dict] = field(default_factory=list)


def empty_memory() -> MemoryData:
    return MemoryData(
        _ui=UIConfig(),
        _agents={},
        _journal={},
        _data={},
        _leases={},
        _chat={},
        _cursors={},
    )
