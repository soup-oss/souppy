"""Tests for souppy CLI."""

import pytest
import json
from souppy.cli import main


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.soup.db")


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0


def test_cli_init(db_path, capsys):
    main(["init", db_path])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert "uuid" in result
    assert result["created"] is True


def test_cli_claim(db_path, capsys):
    main(["init", db_path])
    capsys.readouterr()
    main(["claim", db_path, "--name", "alice", "--role", "frontend"])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["agent"]["name"] == "alice"


def test_cli_write_and_read(db_path, capsys):
    main(["init", db_path])
    main(["write", db_path, "goals/mvp", "Ship v1", "--intent", "Setting scope"])
    capsys.readouterr()
    main(["read", db_path, "goals/mvp"])
    captured = capsys.readouterr()
    assert "Ship v1" in captured.out


def test_cli_status(db_path, capsys):
    main(["init", db_path])
    capsys.readouterr()
    main(["status", db_path])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert "pulse" in result
    assert result["pulse"] == 0


def test_cli_agents(db_path, capsys):
    main(["init", db_path])
    main(["claim", db_path, "--name", "alice", "--role", "frontend"])
    capsys.readouterr()
    main(["agents", db_path])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["name"] == "alice"
