"""Tests for souppy security module."""

import pytest
from souppy.core import MemoryData, empty_memory, JournalEntry
from souppy.security import is_vaulted, is_write_expired, check_ancestor_vault, check_leaf_vault
from souppy.core.common import get_timestamp


def test_is_vaulted_true():
    entry = {"vault": True}
    assert is_vaulted(entry) is True


def test_is_vaulted_false():
    entry = {"vault": False}
    assert is_vaulted(entry) is False


def test_is_vaulted_none():
    assert is_vaulted(None) is False


def test_is_write_expired():
    entry = {"we": "2020-01-01 00:00:00"}
    assert is_write_expired(entry) is True


def test_is_write_not_expired():
    entry = {"we": "2099-12-31 23:59:59"}
    assert is_write_expired(entry) is False


def test_check_ancestor_vault():
    mem = empty_memory()
    mem._journal["goals"] = JournalEntry(ts="2024-01-01", cs="abc", vault=True)
    result = check_ancestor_vault(mem, "goals/mvp")
    assert result == "goals"


def test_check_ancestor_no_vault():
    mem = empty_memory()
    mem._journal["goals"] = JournalEntry(ts="2024-01-01", cs="abc", vault=False)
    result = check_ancestor_vault(mem, "goals/mvp")
    assert result is None


def test_check_leaf_vault():
    mem = empty_memory()
    mem._journal["goals/mvp"] = JournalEntry(ts="2024-01-01", cs="abc")
    mem._journal["goals/mvp/v2"] = JournalEntry(ts="2024-01-01", cs="abc")
    assert check_leaf_vault(mem, "goals/mvp") is True


def test_check_leaf_no_descendants():
    mem = empty_memory()
    mem._journal["goals/mvp"] = JournalEntry(ts="2024-01-01", cs="abc")
    assert check_leaf_vault(mem, "goals/mvp") is False
