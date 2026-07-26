"""Identity type definitions for SoupUser resolution."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IdentityClaims:
    type: str  # 'ui' or 'agent'
    id: str
    tier: str = "free"
    token_uuid: str | None = None
    token_ticker: int | None = None
    token_ts: int | None = None
    global_token_ticker: int | None = None
    invitation_id: str | None = None
    provider_model: str | None = None
    permissions: list[str] = field(default_factory=list)
