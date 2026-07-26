"""Tests for souppy config module."""

import pytest
from souppy.config import SoupConfig


def test_config_init(tmp_path):
    config = SoupConfig(tmp_path)
    assert config.exists() is False


def test_config_add_and_get(tmp_path):
    config = SoupConfig(tmp_path)
    config.add_soup("main", "./workspace.db", label="Test Workspace")
    soups = config.get_soups()
    assert "main" in soups
    assert soups["main"]["db"] == "./workspace.db"
    assert soups["main"]["label"] == "Test Workspace"


def test_config_save_and_load(tmp_path):
    config = SoupConfig(tmp_path)
    config.add_soup("main", "./workspace.db")
    config.save()
    
    config2 = SoupConfig(tmp_path)
    config2.load()
    soups = config2.get_soups()
    assert "main" in soups


def test_config_remove(tmp_path):
    config = SoupConfig(tmp_path)
    config.add_soup("main", "./workspace.db")
    config.add_soup("other", "./other.db")
    config.remove_soup("main")
    soups = config.get_soups()
    assert "main" not in soups
    assert "other" in soups


def test_config_resolve_db_path(tmp_path):
    config = SoupConfig(tmp_path)
    config.add_soup("main", "workspace.db")
    path = config.resolve_db_path("main")
    assert path == tmp_path / "workspace.db"


def test_config_resolve_db_path_not_found(tmp_path):
    config = SoupConfig(tmp_path)
    with pytest.raises(ValueError):
        config.resolve_db_path("nonexistent")


def test_config_add_with_boot_sequence(tmp_path):
    config = SoupConfig(tmp_path)
    boot = [
        "souppy status workspace.db",
        "souppy agents workspace.db",
    ]
    config.add_soup("main", "./workspace.db", boot_sequence=boot)
    soups = config.get_soups()
    assert soups["main"]["boot_sequence"] == boot


def test_config_get_boot_sequence(tmp_path):
    config = SoupConfig(tmp_path)
    boot = ["souppy status {db}", "souppy agents {db}"]
    config.add_soup("main", "./workspace.db", boot_sequence=boot)
    result = config.get_boot_sequence("main")
    assert result == boot


def test_config_get_boot_sequence_empty(tmp_path):
    config = SoupConfig(tmp_path)
    config.add_soup("main", "./workspace.db")
    result = config.get_boot_sequence("main")
    assert result == []


def test_config_get_boot_sequence_not_found(tmp_path):
    config = SoupConfig(tmp_path)
    result = config.get_boot_sequence("nonexistent")
    assert result == []


def test_config_render_boot_sequence(tmp_path):
    config = SoupConfig(tmp_path)
    boot = [
        "souppy status {db}",
        "souppy agents {db}",
        "souppy read {db} goals/",
    ]
    config.add_soup("main", "workspace.soup.db", agent_name="alice", boot_sequence=boot)
    rendered = config.render_boot_sequence("main")
    assert rendered == [
        "souppy status workspace.soup.db",
        "souppy agents workspace.soup.db",
        "souppy read workspace.soup.db goals/",
    ]


def test_config_render_boot_sequence_with_variables(tmp_path):
    config = SoupConfig(tmp_path)
    boot = ["echo {db} {custom}"]
    config.add_soup("main", "workspace.db", boot_sequence=boot)
    rendered = config.render_boot_sequence("main", variables={"custom": "hello"})
    assert rendered == ["echo workspace.db hello"]


def test_config_render_boot_sequence_empty(tmp_path):
    config = SoupConfig(tmp_path)
    config.add_soup("main", "./workspace.db")
    rendered = config.render_boot_sequence("main")
    assert rendered == []
