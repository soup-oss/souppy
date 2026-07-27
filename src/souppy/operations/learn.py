"""Learn operation — returns a self-describing payload for agent onboarding."""

from __future__ import annotations

from typing import Any

from .. import __version__
from ..core import MemoryData


def get_learn_payload(
    memory: MemoryData,
    uuid: str,
    *,
    agent_name: str | None = None,
    db_path: str = "workspace.soup.db",
) -> dict[str, Any]:
    """Return a self-describing payload that teaches agents how to use this workspace.

    This is the local equivalent of heysoup.co's /_learn endpoint.
    Any agent that reads this payload knows everything it needs to operate.

    For the full protocol specification, mental models, and paradigm,
    visit https://heysoup.co/knowledge
    """
    agents = [
        {"name": name, "claimed": entry.claimed, "profile": _profile(entry)}
        for name, entry in memory._agents.items()
    ]

    return {
        "protocol": "SOUP",
        "version": __version__,
        "uuid": uuid,
        "description": (
            "SOUP (Soup Organizes Unified Purpose) is a shared context graph "
            "for AI agents. It gives agents a persistent workspace, intentional "
            "mutations, and a tamper-evident audit trail. This is souppy — "
            "the local-first implementation. A single SQLite file and a CLI."
        ),
        "reference": {
            "url": "https://heysoup.co/knowledge",
            "description": (
                "The full protocol specification and mental models. "
                "Covers: The Agent's Map, Dual Anchors (Local vs Soup), "
                "Intent & Transparency, Safety Guardrails, and the Pulse Loop. "
                "Read this to understand the 'why' behind the primitives below."
            ),
        },
        "install": "pip install souppy",
        "relationship": {
            "souppy": "Local-first Python library. SQLite + CLI. No server. Free.",
            "heysoup": "Managed service. Sync, encryption, attestation, dashboard.",
            "protocol": "Both implement the same SOUP protocol. Data is portable between them.",
        },
        "next_steps": [
            "1. Claim your identity: souppy claim {db} --name <your-name> --role <your-role>",
            "2. Read the workspace state: souppy read {db} goals/",
            "3. Check who else is working: souppy agents {db}",
            "4. Write with intent: souppy write {db} goals/mvp \"Ship v1\" --intent \"Setting initial scope\"",
        ],
        "workspace": {
            "db": db_path,
            "pulse": memory._ui.mutation_id,
            "agents": len(memory._agents),
            "journal_entries": len(memory._journal),
            "data_keys": len(memory._data),
            "chat_messages": len(memory._chat),
        },
        "agents": agents,
        "rules": [
            "Every write must include --intent explaining WHY you are making this change.",
            "Check pulse before writing. If pulse changed since your last read, re-read first.",
            "Read souppy agents to see who else is working in this workspace.",
            "Use chat for coordination with other agents. Use write for state.",
            "Never commit .soup.yaml to version control. It contains workspace secrets.",
            "Respect vaulted paths. Do not write to descendants of vaulted ancestors.",
            "Path names should be descriptive and hierarchical (e.g., goals/mvp, decisions/arch).",
        ],
        "patterns": {
            "path_structure": {
                "description": "Use hierarchical slash-separated paths to organize state.",
                "examples": [
                    "goals/mvp",
                    "goals/stack/backend",
                    "decisions/architecture/database",
                    "status/readiness",
                ],
            },
            "intent_quality": {
                "description": "Intent should explain the reasoning, not just describe the action.",
                "good": [
                    "Setting initial project scope based on stakeholder alignment",
                    "Updating database choice after benchmark results showed Postgres is 3x faster",
                    "Archiving old goal after sprint review confirmed it is no longer relevant",
                ],
                "bad": [
                    "write",
                    "update",
                    "change",
                    "fix",
                ],
            },
            "conflict_resolution": {
                "description": "If pulse changed between your read and write, your context may be stale.",
                "steps": [
                    "Re-read the path and any related paths",
                    "Check souppy agents to see if another agent was active",
                    "Re-evaluate your intent with fresh context",
                    "Write again with updated intent if still needed",
                ],
            },
            "link_integrity": {
                "description": "Values can reference other paths using [[wiki-style]] or [markdown](path) links.",
                "rule": "Broken links are reported on write. Vaulted paths check backlinks before deletion.",
            },
        },
        "commands": {
            "claim": "souppy claim {db} --name <name> --role <role>",
            "read": "souppy read {db} <path>",
            "write": "souppy write {db} <path> <value> --intent <reason>",
            "delete": "souppy delete {db} <path> --intent <reason>",
            "chat_send": "souppy chat send {db} --from <name> --to <target> --msg <message>",
            "chat_read": "souppy chat read {db} --agent <name>",
            "glob": "souppy glob {db} <pattern>",
            "grep": "souppy grep {db} <pattern>",
            "vault": "souppy vault {db} <path> --intent <reason>",
            "snapshots": "souppy snapshots {db} [--path <path>]",
            "agents": "souppy agents {db}",
            "status": "souppy status {db}",
            "boot": "souppy boot",
            "learn": "souppy learn {db}",
        },
        "authority": {
            "description": (
                "SOUP enforces separation of concerns. Agents modify content. "
                "Humans (UI) modify security metadata (vaults, locks, invites). "
                "This prevents agents from escalating their own permissions."
            ),
            "agent_can": [
                "Read any non-vaulted path",
                "Write to non-vaulted, non-locked paths",
                "Send and read chat messages",
                "Claim an agent name",
            ],
            "agent_cannot": [
                "Vault or unvault paths",
                "Lock or unlock paths",
                "Manage other agents",
                "Modify workspace configuration",
            ],
        },
        "concepts": {
            "pulse": {
                "description": (
                    "A monotonic counter that increments on every mutation. "
                    "Agents read the pulse, write, then check if pulse changed. "
                    "If it did, another agent mutated the workspace during the write."
                ),
            },
            "journal": {
                "description": (
                    "Every tracked path has a journal entry with timestamp, checksum, "
                    "vault state, read-only lock, and optional expiration timestamps. "
                    "The journal is the security boundary."
                ),
            },
            "vault": {
                "description": (
                    "Soft-delete that hides paths from agents while keeping them "
                    "for humans. Vaulted paths cannot be written to by agents. "
                    "Ancestors of vaulted paths are also protected."
                ),
            },
            "intent": {
                "description": (
                    "A mandatory string (minimum 5 characters) explaining why "
                    "a mutation is being made. Creates an audit trail of "
                    "human-readable reasoning behind each change."
                ),
            },
        },
        "paradigm": {
            "description": (
                "SOUP is built on the Guarded Cognitive Graph paradigm. "
                "Agents are stateless and swappable — a fresh session reads the "
                "last few mutations and has full situational awareness."
            ),
            "mental_models": {
                "dual_anchors": {
                    "description": (
                        "Local Anchor (your hard drive, source files, Git) vs "
                        "Soup Anchor (shared coordination layer, intent, plans, sync signals). "
                        "Agents must not confuse the two."
                    ),
                },
                "pulse_loop": {
                    "description": (
                        "For long-running tasks, agents should operate in pulses: "
                        "wake, sync (read .soup.yaml and boot), work, exit. "
                        "Each pulse starts with zero context decay."
                    ),
                },
                "presence_latch": {
                    "description": (
                        "By default, agents can only modify workspace while a human "
                        "is watching. Headless mode can be explicitly delegated."
                    ),
                },
            },
        },
        "links": {
            "knowledge": "https://heysoup.co/knowledge",
            "github": "https://github.com/soup-oss/souppy",
            "issues": "https://github.com/soup-oss/souppy/issues",
        },
    }


def _profile(entry: Any) -> dict[str, str | None]:
    """Extract agent profile as a simple dict."""
    if not entry.profile:
        return {}
    return {
        "role": entry.profile.role,
        "regex": entry.profile.regex,
        "model": entry.profile.model,
    }
