-- realm: soup
-- description: Cognitive Commits (Audit & Recovery) additions.

-- Update memory_ui for global revocation
ALTER TABLE memory_ui ADD COLUMN global_revocation_ticker INTEGER DEFAULT 0;

-- Update memory_agents to track invitation source
ALTER TABLE memory_agents ADD COLUMN invitation_id TEXT;

-- Update memory_snapshots for high-fidelity audit
ALTER TABLE memory_snapshots ADD COLUMN diff_b64 TEXT;
ALTER TABLE memory_snapshots ADD COLUMN chain_hash TEXT;
ALTER TABLE memory_snapshots ADD COLUMN invitation_id TEXT;
ALTER TABLE memory_snapshots ADD COLUMN provider_model TEXT;
ALTER TABLE memory_snapshots ADD COLUMN interface TEXT;
ALTER TABLE memory_snapshots ADD COLUMN mutation_id INTEGER DEFAULT 0;
ALTER TABLE memory_snapshots ADD COLUMN old_meta TEXT;
ALTER TABLE memory_snapshots ADD COLUMN new_meta TEXT;
