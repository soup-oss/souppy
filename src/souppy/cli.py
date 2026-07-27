"""Command-line interface for souppy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import SoupConfig
from .core.common import get_timestamp
from .crypto import generate_uuid, compute_signature
from .persistence import init_db, open_db, load_memory, save_memory, delete_workspace, get_snapshots
from .operations.read import read_path
from .operations.write import write_path
from .operations.delete import delete_path
from .operations.claim import claim_agent, list_agents
from .operations.chat import chat_send, chat_read
from .operations.patch import patch_path
from .operations.search import glob_search, grep_search
from .operations.vault import vault_path
from .operations.audit import get_inertia
from .operations.learn import get_learn_payload
from .graph import get_nested_value


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="souppy",
        description="The SOUP Protocol — local-first agent coordination via SQLite",
    )
    parser.add_argument("--version", action="version", version=f"souppy {__version__}")
    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="Create a new SOUP workspace")
    p_init.add_argument("db", help="Path to the SQLite database file")
    p_init.add_argument("--uuid", help="Workspace UUID (auto-generated if omitted)")

    # claim
    p_claim = sub.add_parser("claim", help="Claim an agent name")
    p_claim.add_argument("db", help="Path to the SQLite database file")
    p_claim.add_argument("--name", required=True, help="Agent name")
    p_claim.add_argument("--role", help="Agent role description")
    p_claim.add_argument("--secret", default="dev-secret", help="HMAC secret for signing")
    p_claim.add_argument("--save-config", action="store_true", help="Persist claim to .soup.yaml")

    # write
    p_write = sub.add_parser("write", help="Write a value to the workspace")
    p_write.add_argument("db", help="Path to the SQLite database file")
    p_write.add_argument("path", help="Path to write to (e.g. goals/mvp)")
    p_write.add_argument("value", help="Value to write")
    p_write.add_argument("--intent", required=True, help="Why this change is being made")
    p_write.add_argument("--secret", default="dev-secret", help="HMAC secret")

    # read
    p_read = sub.add_parser("read", help="Read a value from the workspace")
    p_read.add_argument("db", help="Path to the SQLite database file")
    p_read.add_argument("path", help="Path to read (use trailing / for directory)")

    # delete
    p_delete = sub.add_parser("delete", help="Delete a path from the workspace")
    p_delete.add_argument("db", help="Path to the SQLite database file")
    p_delete.add_argument("path", help="Path to delete")
    p_delete.add_argument("--intent", required=True, help="Why this deletion is being made")

    # chat
    p_chat = sub.add_parser("chat", help="Inter-agent messaging")
    chat_sub = p_chat.add_subparsers(dest="chat_command")
    p_chat_send = chat_sub.add_parser("send", help="Send a chat message")
    p_chat_send.add_argument("db", help="Path to the SQLite database file")
    p_chat_send.add_argument("--from", dest="from_name", required=True, help="Sender agent name")
    p_chat_send.add_argument("--to", dest="to_name", required=True, help="Recipient (agent name or 'all')")
    p_chat_send.add_argument("--msg", required=True, help="Message content")
    p_chat_send.add_argument("--secret", default="dev-secret", help="HMAC secret")
    p_chat_read = chat_sub.add_parser("read", help="Read chat messages")
    p_chat_read.add_argument("db", help="Path to the SQLite database file")
    p_chat_read.add_argument("--agent", required=True, help="Agent name to read for")
    p_chat_read.add_argument("--limit", type=int, default=50, help="Max messages to return")

    # agents
    p_agents = sub.add_parser("agents", help="List claimed agents")
    p_agents.add_argument("db", help="Path to the SQLite database file")

    # status
    p_status = sub.add_parser("status", help="Show workspace status")
    p_status.add_argument("db", help="Path to the SQLite database file")

    # boot
    p_boot = sub.add_parser("boot", help="Execute boot_sequence from .soup.yaml")
    p_boot.add_argument("--alias", default="main", help="Workspace alias (default: main)")
    p_boot.add_argument("--project-dir", help="Project directory (default: cwd)")
    p_boot.add_argument("--execute", action="store_true", help="Execute commands instead of printing them")

    # learn
    p_learn = sub.add_parser("learn", help="Return self-describing payload for agent onboarding")
    p_learn.add_argument("db", help="Path to the SQLite database file")
    p_learn.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    # glob
    p_glob = sub.add_parser("glob", help="Search paths by glob pattern")
    p_glob.add_argument("db", help="Path to the SQLite database file")
    p_glob.add_argument("pattern", help="Glob pattern (e.g. goals/*)")

    # grep
    p_grep = sub.add_parser("grep", help="Search content by regex")
    p_grep.add_argument("db", help="Path to the SQLite database file")
    p_grep.add_argument("pattern", help="Regex pattern")
    p_grep.add_argument("--include", help="Glob pattern to filter paths")

    # snapshots
    p_snap = sub.add_parser("snapshots", help="View audit snapshots")
    p_snap.add_argument("db", help="Path to the SQLite database file")
    p_snap.add_argument("--path", help="Filter by path")
    p_snap.add_argument("--limit", type=int, default=10, help="Max snapshots")

    # vault
    p_vault = sub.add_parser("vault", help="Vault (soft-delete) a path")
    p_vault.add_argument("db", help="Path to the SQLite database file")
    p_vault.add_argument("path", help="Path to vault")
    p_vault.add_argument("--intent", required=True, help="Why this vault is being made")
    p_vault.add_argument("--unvault", action="store_true", help="Unvault instead of vault")

    # config
    p_config = sub.add_parser("config", help="Manage .soup.yaml manifest")
    config_sub = p_config.add_subparsers(dest="config_command")
    p_config_init = config_sub.add_parser("init", help="Create a new .soup.yaml")
    p_config_init.add_argument("--alias", default="main", help="Workspace alias")
    p_config_init.add_argument("--db", default="workspace.soup.db", help="Database path")
    p_config_init.add_argument("--label", help="Friendly workspace name")
    p_config_show = config_sub.add_parser("show", help="Show current config")

    # workspace (create with config)
    p_workspace = sub.add_parser("workspace", help="Create workspace + config in one step")
    p_workspace.add_argument("--name", default="main", help="Workspace alias")
    p_workspace.add_argument("--db", default="workspace.soup.db", help="Database path")
    p_workspace.add_argument("--label", help="Friendly workspace name")
    p_workspace.add_argument("--no-boot-sequence", action="store_true", help="Skip generating default boot_sequence")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    try:
        _dispatch(args)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _dispatch(args: argparse.Namespace) -> None:
    cmd = args.command

    if cmd == "init":
        secret = getattr(args, "secret", "dev-secret")
        uuid = args.uuid or generate_uuid(secret)
        conn = init_db(args.db)
        mem = load_memory(conn, uuid)
        mem._ui.ts = get_timestamp()
        mem._ui.created_at = get_timestamp()
        save_memory(conn, uuid, mem)
        conn.close()
        print(json.dumps({"uuid": uuid, "db": args.db, "created": True}, indent=2))

    elif cmd == "claim":
        secret = getattr(args, "secret", "dev-secret")
        # Try to find UUID from existing DB
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found. Run 'souppy init' first.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        result = claim_agent(mem, args.name, secret, uuid, profile={"role": args.role} if args.role else None)
        if "error" in result:
            print(json.dumps(result, indent=2))
            sys.exit(1)
        save_memory(conn, uuid, mem)
        conn.close()

        # Persist to .soup.yaml if requested
        if getattr(args, "save_config", False):
            config = SoupConfig()
            if not config.exists():
                # Auto-create config with default boot_sequence
                default_boot = [
                    f"souppy status {args.db}",
                    f"souppy agents {args.db}",
                    f"souppy read {args.db} goals/",
                ]
                config.add_soup("main", args.db, agent_name=args.name, boot_sequence=default_boot)
            else:
                config.load()
                soup = config.get_soup("main")
                if soup:
                    soup["agent_name"] = args.name
            config.save()
            result["config_updated"] = True

        print(json.dumps(result, indent=2))

    elif cmd == "write":
        secret = getattr(args, "secret", "dev-secret")
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        result = write_path(mem, args.path, args.value, args.intent)
        if "error" in result:
            print(json.dumps(result, indent=2))
            sys.exit(1)
        save_memory(conn, uuid, mem)
        conn.close()
        print(json.dumps(result, indent=2))

    elif cmd == "read":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        result = read_path(mem, args.path)
        conn.close()
        if result["value"] is None:
            print(f"Path not found: {args.path}")
        elif isinstance(result["value"], dict):
            print(json.dumps(result["value"], indent=2))
        else:
            print(result["value"])

    elif cmd == "delete":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        result = delete_path(mem, args.path, args.intent)
        if "error" in result:
            print(json.dumps(result, indent=2))
            sys.exit(1)
        save_memory(conn, uuid, mem)
        conn.close()
        print(json.dumps(result, indent=2))

    elif cmd == "chat":
        if not args.chat_command:
            print("Usage: souppy chat [send|read]", file=sys.stderr)
            sys.exit(1)
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        if args.chat_command == "send":
            result = chat_send(mem, args.from_name, args.to_name, args.msg)
        else:
            result = chat_read(mem, args.agent, args.limit)
        save_memory(conn, uuid, mem)
        conn.close()
        print(json.dumps(result, indent=2))

    elif cmd == "agents":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        agents = list_agents(mem)
        conn.close()
        print(json.dumps(agents, indent=2))

    elif cmd == "status":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        conn.close()
        status = {
            "uuid": uuid,
            "pulse": mem._ui.mutation_id,
            "tier": mem._ui.tier,
            "created_at": mem._ui.created_at,
            "agents": len(mem._agents),
            "journal_entries": len(mem._journal),
            "chat_messages": len(mem._chat),
            "data_keys": len(mem._data),
        }
        print(json.dumps(status, indent=2))

    elif cmd == "learn":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        conn.close()
        payload = get_learn_payload(mem, uuid, db_path=args.db)
        indent = 2 if getattr(args, "pretty", False) else None
        print(json.dumps(payload, indent=indent))

    elif cmd == "glob":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        results = glob_search(mem, args.pattern)
        conn.close()
        print(json.dumps(results, indent=2))

    elif cmd == "grep":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        results = grep_search(mem, args.pattern, include=getattr(args, "include", None))
        conn.close()
        print(json.dumps(results, indent=2))

    elif cmd == "snapshots":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        snapshots = get_snapshots(conn, uuid, path=getattr(args, "path", None), limit=args.limit)
        conn.close()
        print(json.dumps(snapshots, indent=2))

    elif cmd == "vault":
        conn = open_db(args.db)
        uuid = _find_uuid(conn)
        if not uuid:
            print("Error: No workspace found.", file=sys.stderr)
            sys.exit(1)
        mem = load_memory(conn, uuid)
        result = vault_path(mem, args.path, args.intent, vault=not args.unvault)
        if "error" in result:
            print(json.dumps(result, indent=2))
            sys.exit(1)
        save_memory(conn, uuid, mem)
        conn.close()
        print(json.dumps(result, indent=2))

    elif cmd == "config":
        if not args.config_command:
            print("Usage: souppy config [init|show]", file=sys.stderr)
            sys.exit(1)
        config = SoupConfig()
        if args.config_command == "init":
            config.add_soup(args.alias, args.db, label=getattr(args, "label", None))
            config.save()
            print(f"Created .soup.yaml with alias '{args.alias}'")
        elif args.config_command == "show":
            if config.exists():
                data = config.load()
                print(json.dumps(data, indent=2))
            else:
                print("No .soup.yaml found in current directory")

    elif cmd == "workspace":
        # Create workspace + config
        secret = "dev-secret"
        uuid = generate_uuid(secret)
        conn = init_db(args.db)
        mem = load_memory(conn, uuid)
        mem._ui.ts = get_timestamp()
        mem._ui.created_at = get_timestamp()
        save_memory(conn, uuid, mem)
        conn.close()

        # Default boot_sequence for local-only usage
        boot_sequence = None
        if not getattr(args, "no_boot_sequence", False):
            boot_sequence = [
                f"souppy status {args.db}",
                f"souppy agents {args.db}",
                f"souppy read {args.db} goals/",
            ]

        config = SoupConfig()
        config.add_soup(
            args.name,
            args.db,
            label=getattr(args, "label", None),
            boot_sequence=boot_sequence,
        )
        config.save()

        print(json.dumps({
            "uuid": uuid,
            "db": args.db,
            "alias": args.name,
            "config": ".soup.yaml",
            "boot_sequence": boot_sequence,
        }, indent=2))


    elif cmd == "boot":
        project_dir = getattr(args, "project_dir", None)
        config = SoupConfig(project_dir)
        if not config.exists():
            print("Error: No .soup.yaml found. Run 'souppy workspace' first.", file=sys.stderr)
            sys.exit(1)
        config.load()
        alias = args.alias
        soup = config.get_soup(alias)
        if not soup:
            print(f"Error: No workspace found with alias '{alias}'.", file=sys.stderr)
            sys.exit(1)

        rendered = config.render_boot_sequence(alias)
        if not rendered:
            print(f"Error: No boot_sequence found for alias '{alias}'.", file=sys.stderr)
            sys.exit(1)

        if getattr(args, "execute", False):
            import subprocess
            for cmd_line in rendered:
                print(f"$ {cmd_line}")
                result = subprocess.run(cmd_line, shell=True, capture_output=False)
                if result.returncode != 0:
                    print(f"Warning: Command exited with code {result.returncode}", file=sys.stderr)
        else:
            # Print as JSON for agents to parse
            output = {
                "alias": alias,
                "db": soup.get("db", "workspace.soup.db"),
                "agent_name": soup.get("agent_name", ""),
                "boot_sequence": rendered,
            }
            print(json.dumps(output, indent=2))


def _find_uuid(conn) -> str | None:
    """Find the first workspace UUID in the database."""
    row = conn.execute("SELECT uuid FROM memory_data LIMIT 1").fetchone()
    return row["uuid"] if row else None


if __name__ == "__main__":
    main()
