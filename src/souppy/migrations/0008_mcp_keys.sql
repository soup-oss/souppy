-- realm: soup
-- description: MCP Server public key registry for credential wrapping.

CREATE TABLE IF NOT EXISTS memory_mcp_keys (
    uuid TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    pubkey_encrypted TEXT NOT NULL,
    label TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (uuid, fingerprint)
);
