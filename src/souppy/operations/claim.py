"""Claim operation — register agents in the workspace."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from ..core import AgentEntry, AgentProfile, MemoryData
from ..core.common import get_timestamp
from ..crypto import compute_signature


def claim_agent(
    memory: MemoryData,
    name: str,
    secret: str,
    workspace_uuid: str,
    profile: dict | None = None,
    signature: str | None = None,
) -> dict:
    """Claim an agent name in the workspace. Returns {signature, agent}."""
    # Validate name
    if name.lower() == "all":
        return {"error": "invalid_name", "detail": "'all' is reserved", "status": 400}
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return {"error": "invalid_name", "detail": "Name must be alphanumeric with dashes/underscores", "status": 400}

    # Check if already claimed
    if name in memory._agents:
        existing = memory._agents[name]
        # Re-claim: verify existing signature
        if signature:
            expected = compute_signature(secret, workspace_uuid, name)
            if signature != expected:
                return {"error": "invalid_signature", "status": 401}
            # Update last active
            existing.last_active_at = get_timestamp()
            return {
                "signature": signature,
                "agent": {"name": name, "claimed": existing.claimed, "profile": _profile_to_dict(existing.profile)},
                "reclaimed": True,
            }
        return {"error": "already_claimed", "status": 409}

    # Claim new
    ts = get_timestamp()
    agent_profile = None
    if profile:
        agent_profile = AgentProfile(
            role=profile.get("role"),
            regex=profile.get("regex"),
            model=profile.get("model"),
        )

    agent = AgentEntry(
        claimed=ts,
        profile=agent_profile,
        last_active_at=ts,
    )
    memory._agents[name] = agent

    # Compute signature
    sig = compute_signature(secret, workspace_uuid, name)

    return {
        "signature": sig,
        "agent": {"name": name, "claimed": ts, "profile": profile or {}},
        "reclaimed": False,
    }


def list_agents(memory: MemoryData) -> list[dict]:
    """List all claimed agents."""
    agents = []
    for name, entry in memory._agents.items():
        agents.append({
            "name": name,
            "claimed": entry.claimed,
            "profile": _profile_to_dict(entry.profile),
            "last_active_at": entry.last_active_at,
        })
    return agents


def _profile_to_dict(profile: AgentProfile | None) -> dict:
    if not profile:
        return {}
    d = {}
    if profile.role:
        d["role"] = profile.role
    if profile.regex:
        d["regex"] = profile.regex
    if profile.model:
        d["model"] = profile.model
    return d
