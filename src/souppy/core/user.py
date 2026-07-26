"""Sovereignty user abstraction with tiered access and role-based verbs."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SoupUser(ABC):
    def __init__(
        self,
        user_id: str,
        tier: str = "free",
        token_uuid: str | None = None,
    ) -> None:
        self.id = user_id
        self.tier = tier
        self.token_uuid = token_uuid

    @abstractmethod
    def can_modify_structure(self) -> bool: ...

    @abstractmethod
    def can_modify_content(self) -> bool: ...

    def can_vault(self) -> bool:
        return self.can_modify_structure()

    @abstractmethod
    def can_manage_invites(self) -> bool: ...

    @abstractmethod
    def can_manage_agents(self) -> bool: ...

    def is_anonymous(self) -> bool:
        return False


class UIUser(SoupUser):
    """Human operator — manages vault/lock/structure, cannot edit content directly."""

    def can_modify_structure(self) -> bool:
        return True

    def can_modify_content(self) -> bool:
        return False

    def can_manage_invites(self) -> bool:
        return True

    def can_manage_agents(self) -> bool:
        return True


class AgentUser(SoupUser):
    """AI agent — writes content, cannot touch security metadata."""

    def __init__(self, user_id: str, agent_name: str, tier: str = "free", token_uuid: str | None = None) -> None:
        super().__init__(user_id, tier, token_uuid)
        self.agent_name = agent_name

    def can_modify_structure(self) -> bool:
        return False

    def can_modify_content(self) -> bool:
        return True

    def can_manage_invites(self) -> bool:
        return False

    def can_manage_agents(self) -> bool:
        return False


class AnonymousUser(SoupUser):
    """Unauthenticated — read-only with structure capability."""

    def __init__(self) -> None:
        super().__init__("anonymous", "free")

    def can_modify_structure(self) -> bool:
        return True

    def can_modify_content(self) -> bool:
        return False

    def can_manage_invites(self) -> bool:
        return False

    def can_manage_agents(self) -> bool:
        return False

    def is_anonymous(self) -> bool:
        return True
