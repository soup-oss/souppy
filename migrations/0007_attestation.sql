-- realm: soup
-- description: Tool Call Attestation fields for MCP integration.

ALTER TABLE memory_snapshots ADD COLUMN tool_call TEXT;
ALTER TABLE memory_snapshots ADD COLUMN secret_version TEXT;
