"""Configuration parser for .soup.yaml manifests."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


_SOUPS_FIELD = "soups"
_DEFAULT_DB = "workspace.soup.db"


class SoupConfig:
    """Parser for .soup.yaml manifest files."""

    def __init__(self, project_dir: str | Path | None = None) -> None:
        if project_dir is None:
            project_dir = Path.cwd()
        self.project_dir = Path(project_dir)
        self.config_path = self.project_dir / ".soup.yaml"
        self._data: dict[str, Any] = {}

    def exists(self) -> bool:
        return self.config_path.exists()

    def load(self) -> dict[str, Any]:
        """Load the .soup.yaml file."""
        if not self.exists():
            return {}
        if yaml is None:
            raise ImportError("pyyaml is required for .soup.yaml support. Install with: pip install souppy")
        with open(self.config_path) as f:
            self._data = yaml.safe_load(f) or {}
        return self._data

    def save(self) -> None:
        """Save the current config to .soup.yaml."""
        if yaml is None:
            raise ImportError("pyyaml is required for .soup.yaml support. Install with: pip install souppy")
        with open(self.config_path, "w") as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False)

    def get_soups(self) -> dict[str, dict]:
        """Get all soup workspace entries."""
        return self._data.get(_SOUPS_FIELD, {})

    def get_soup(self, alias: str) -> dict | None:
        """Get a specific soup workspace entry."""
        return self.get_soups().get(alias)

    def add_soup(
        self,
        alias: str,
        db: str,
        label: str | None = None,
        agent_name: str | None = None,
        boot_sequence: list[str] | None = None,
        **extra: Any,
    ) -> None:
        """Add a soup workspace entry."""
        if _SOUPS_FIELD not in self._data:
            self._data[_SOUPS_FIELD] = {}
        entry: dict[str, Any] = {"db": db}
        if label:
            entry["label"] = label
        if agent_name:
            entry["agent_name"] = agent_name
        if boot_sequence:
            entry["boot_sequence"] = boot_sequence
        entry.update(extra)
        self._data[_SOUPS_FIELD][alias] = entry

    def remove_soup(self, alias: str) -> bool:
        """Remove a soup workspace entry. Returns True if removed."""
        soups = self.get_soups()
        if alias in soups:
            del soups[alias]
            return True
        return False

    def resolve_db_path(self, alias: str) -> Path:
        """Resolve the database path for a soup alias."""
        soup = self.get_soup(alias)
        if not soup:
            raise ValueError(f"No soup found with alias '{alias}'")
        db = soup.get("db", _DEFAULT_DB)
        db_path = Path(db)
        if not db_path.is_absolute():
            db_path = self.project_dir / db_path
        return db_path

    def get_boot_sequence(self, alias: str) -> list[str]:
        """Get the raw boot_sequence for a soup alias."""
        soup = self.get_soup(alias)
        if not soup:
            return []
        return soup.get("boot_sequence", [])

    def render_boot_sequence(self, alias: str, variables: dict[str, str] | None = None) -> list[str]:
        """Get boot_sequence with template variables substituted.

        Supported variables: {db}, {agent_name}, {uuid}, {url}, {alias}
        Any key in the variables dict is also available.
        """
        raw = self.get_boot_sequence(alias)
        if not raw:
            return []

        soup = self.get_soup(alias) or {}
        substitutions = {
            "db": soup.get("db", _DEFAULT_DB),
            "agent_name": soup.get("agent_name", ""),
            "uuid": soup.get("uuid", ""),
            "url": soup.get("url", ""),
            "alias": alias,
        }
        if variables:
            substitutions.update(variables)

        rendered = []
        for cmd in raw:
            for key, value in substitutions.items():
                cmd = cmd.replace("{" + key + "}", value)
            rendered.append(cmd)
        return rendered
