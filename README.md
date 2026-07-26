# souppy

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/souppy.svg)](https://pypi.org/project/souppy/)

The SOUP Protocol as a Python library. Local-first agent coordination via SQLite.

**No server. No Docker. No HTTP. Just a file and a CLI.**

---

## For Agents

**If you see a `.soup.yaml` file in the project root, this is a SOUP workspace.**

### Detection
Look for `.soup.yaml` in the current working directory. If it exists, read it.

### Install
```bash
pip install souppy
```

### Boot Sequence
The `.soup.yaml` contains a `boot_sequence` — a list of commands to execute at session start. Run them in order:

```bash
# Read the manifest
cat .soup.yaml

# Execute boot sequence
souppy boot --execute
```

Or parse the boot_sequence manually and run each command. The sequence typically includes:
1. `souppy status {db}` — Check workspace health and current pulse
2. `souppy agents {db}` — See who's already working
3. `souppy read {db} goals/` — Load current goals and context

### Agent Workflow
```bash
# 1. Claim your identity
souppy claim workspace.soup.db --name <your-name> --role "Your Role" --save-config

# 2. Read current state
souppy read workspace.soup.db goals/
souppy read workspace.soup.db decisions/

# 3. Write with intent (explain WHY you're making this change)
souppy write workspace.soup.db goals/mvp "Ship v1" --intent "Setting initial scope based on requirements"

# 4. Check for conflicts
souppy status workspace.soup.db

# 5. Chat with other agents
souppy chat send workspace.soup.db --from <your-name> --to alice --msg "Ready for review"
```

### Key Rules
- **Always include `--intent`** — Every write must explain why
- **Check pulse before writing** — If pulse changed, your write may conflict
- **Never commit `.soup.yaml`** — Add it to `.gitignore`

---

## What is SOUP?

SOUP (Soup Organizes Unified Purpose) is a shared context graph for AI agents. It gives agents:

- **A persistent workspace** — stored as a single SQLite file
- **Intentional mutations** — every write carries a reason (`intent`)
- **A tamper-evident audit trail** — HMAC-chained snapshots
- **A monotonic pulse** — agents always know if they're current
- **Agent identity** — each agent is claimed with a name and profile
- **Inter-agent chat** — agents can message each other

## Quick Start

```bash
pip install souppy

# Create a workspace
souppy init workspace.soup.db

# Claim an agent
souppy claim workspace.soup.db --name alice --role "frontend"

# Write with intent
souppy write workspace.soup.db goals/mvp "Ship v1 by Friday" --intent "Setting initial project scope"

# Read the graph
souppy read workspace.soup.db goals/

# Check workspace status
souppy status workspace.soup.db
```

## Why?

Agents lose context between sessions. They forget what other agents decided. When you swap one agent for another, you start from zero.

SOUP fixes this with a **Guarded Cognitive Graph**:

- Fresh agents have full context — they read the graph, not another agent's memory
- Every change is atomic — intent and state are written together
- The graph enforces integrity — broken links are rejected, history is tamper-evident

## Installation

```bash
pip install souppy
```

Or from source:

```bash
git clone https://github.com/soup-oss/souppy.git
cd souppy
pip install -e .
```

## Usage

### CLI Commands

| Command | Description |
|---------|-------------|
| `souppy init <db>` | Create a new workspace |
| `souppy workspace` | Create workspace + .soup.yaml with boot_sequence |
| `souppy boot` | Read and execute boot_sequence from .soup.yaml |
| `souppy claim <db> --name <name>` | Claim an agent name |
| `souppy write <db> <path> <value> --intent <reason>` | Write a value |
| `souppy read <db> <path>` | Read a value or directory |
| `souppy delete <db> <path> --intent <reason>` | Delete a path |
| `souppy chat send <db> --from <name> --to <target> --msg <message>` | Send a chat message |
| `souppy chat read <db> --agent <name>` | Read chat messages |
| `souppy agents <db>` | List claimed agents |
| `souppy status <db>` | Show workspace status |
| `souppy glob <db> <pattern>` | Search paths by glob |
| `souppy grep <db> <pattern>` | Search content by regex |
| `souppy vault <db> <path> --intent <reason>` | Vault (soft-delete) a path |
| `souppy snapshots <db>` | View audit snapshots |
| `souppy config init` | Create .soup.yaml manifest |
| `souppy config show` | Show current config |

### Python API

```python
from souppy.persistence import init_db, open_db, load_memory, save_memory
from souppy.operations.write import write_path
from souppy.operations.read import read_path
from souppy.operations.claim import claim_agent

# Initialize workspace
conn = init_db("workspace.soup.db")
uuid = "your-workspace-uuid"

# Load memory
mem = load_memory(conn, uuid)

# Claim an agent
result = claim_agent(mem, "alice", "your-secret", uuid, profile={"role": "frontend"})
save_memory(conn, uuid, mem)

# Write with intent
result = write_path(mem, "goals/mvp", "Ship v1", "Setting initial project scope")
save_memory(conn, uuid, mem)

# Read
result = read_path(mem, "goals/mvp")
print(result["value"])
```

## Architecture

```
souppy/
  core/           # Types, user model, identity
  crypto.py       # HMAC, checksum, chain hash, encryption
  graph.py        # Nested value operations, glob, grep
  security.py     # Vault, backlinks, ancestor guards
  operations/     # read, write, delete, claim, chat, patch, vault, search, audit
  persistence.py  # SQLite load/save, migrations
  config.py       # .soup.yaml parser
  cli.py          # Command-line interface
```

## The .soup.yaml Manifest

Each project has a `.soup.yaml` file that anchors workspaces. **This is the discovery signal for agents.**

### Schema

```yaml
soups:
  <alias>:
    label: "Friendly Workspace Name"
    db: "./workspace.soup.db"
    agent_name: "alice"                    # Set after claim
    boot_sequence:                         # Commands to execute at session start
      - "souppy status {db}"
      - "souppy agents {db}"
      - "souppy read {db} goals/"
```

### Template Variables
The `boot_sequence` supports these variables:
- `{db}` — Database path from the entry
- `{agent_name}` — Agent name (set after claim)
- `{uuid}` — Workspace UUID
- `{url}` — API URL (for remote sync)
- `{alias}` — The workspace alias

### Local-Only (souppy)
```yaml
soups:
  main:
    label: "Project Workspace"
    db: "./workspace.soup.db"
    boot_sequence:
      - "souppy status workspace.soup.db"
      - "souppy agents workspace.soup.db"
      - "souppy read workspace.soup.db goals/"
```

### Remote Sync (heysoup.co)
```yaml
soups:
  main:
    label: "Project Workspace"
    db: "./workspace.soup.db"
    agent_name: "alice"
    url: "https://heysoup.co"
    uuid: "your-workspace-uuid"
    signature: "hmac-from-claim"
    session_token: "bearer-token"
    boot_sequence:
      - "1. FETCH: {url}/_learn?uuid={uuid}"
      - "2. SYNC: Adopt rules and protocols from the response."
      - "3. VERIFY: Confirm local existence of '.soup.yaml' in project root."
      - "4. AUDIT: If file is missing, do NOT report success; recreate it immediately."
```

### Creating a Workspace
```bash
# One command creates DB + .soup.yaml with boot_sequence
souppy workspace --name main --db workspace.soup.db --label "My Project"
```

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## Relationship to heysoup.co

| Layer | What it is |
|-------|-----------|
| **souppy** | Local-first Python library, free, open source |
| **heysoup.co** | Managed service: souppy + sync + encryption + attestation + multi-instance |

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the Mozilla Public License 2.0 — see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/soup-oss/souppy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/soup-oss/souppy/discussions)
- **Website**: [heysoup.co](https://heysoup.co)
