"""Tests for souppy graph module."""

import pytest
from souppy.graph import (
    get_nested_value,
    set_nested_value,
    delete_nested_value,
    matches_glob,
    glob_match,
    generate_diff,
    prune_journal,
    scan_for_backlinks,
)
from souppy.core import JournalEntry


def test_get_nested_value():
    obj = {"a": {"b": {"c": "hello"}}}
    assert get_nested_value(obj, "a/b/c") == "hello"
    assert get_nested_value(obj, "a/b") == {"c": "hello"}
    assert get_nested_value(obj, "a/x") is None


def test_set_nested_value():
    obj = {}
    set_nested_value(obj, "a/b/c", "hello")
    assert obj == {"a": {"b": {"c": "hello"}}}


def test_set_nested_value_overwrite():
    obj = {"a": {"b": {"c": "old"}}}
    set_nested_value(obj, "a/b/c", "new")
    assert obj["a"]["b"]["c"] == "new"


def test_delete_nested_value():
    obj = {"a": {"b": {"c": "hello"}, "d": "keep"}}
    assert delete_nested_value(obj, "a/b/c") is True
    assert "b" not in obj["a"]
    assert obj["a"]["d"] == "keep"


def test_delete_nested_value_cleans_empty():
    obj = {"a": {"b": {}}}
    delete_nested_value(obj, "a/b")
    assert "a" not in obj


def test_delete_nested_value_nonexistent():
    obj = {"a": 1}
    assert delete_nested_value(obj, "b") is False


def test_matches_glob():
    assert matches_glob("goals/mvp", "goals/*") is True
    assert matches_glob("goals/mvp", "goals/**") is True
    assert matches_glob("goals/mvp/v2", "goals/**") is True
    assert matches_glob("goals/mvp", "other/*") is False


def test_glob_match():
    paths = ["goals/mvp", "goals/stack", "config/db"]
    assert glob_match(paths, "goals/*") == ["goals/mvp", "goals/stack"]
    assert glob_match(paths, "*/*") == paths


def test_generate_diff():
    diff, added, removed = generate_diff("hello\nworld", "hello\nthere\nworld")
    assert added == 2
    assert removed == 1
    assert "- world" in diff
    assert "+ there" in diff
    assert "+ world" in diff


def test_generate_diff_same():
    diff, added, removed = generate_diff("hello", "hello")
    assert diff == ""
    assert added == 0
    assert removed == 0


def test_prune_journal():
    journal = {}
    for i in range(5010):
        journal[f"path/{i}"] = JournalEntry(ts=f"2024-01-01 {i:06d}", cs=f"cs{i}")
    pruned = prune_journal(journal)
    assert len(pruned) == 10
    assert len(journal) == 5000


def test_prune_journal_under_limit():
    journal = {}
    for i in range(10):
        journal[f"path/{i}"] = JournalEntry(ts=f"2024-01-01 {i:06d}", cs=f"cs{i}")
    pruned = prune_journal(journal)
    assert pruned == []
    assert len(journal) == 10


def test_scan_for_backlinks():
    data = {
        "goals": {"mvp": "see [[config/db]] for details"},
        "config": {"db": "PostgreSQL"},
    }
    backlinks = scan_for_backlinks(data, "config/db")
    assert "goals/mvp" in backlinks
