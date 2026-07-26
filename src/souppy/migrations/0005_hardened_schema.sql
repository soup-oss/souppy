-- realm: soup
-- description: Add missing agent fields and standardize journal expiration column names.

-- 1. Patch memory_agents for permissions and revocation status
ALTER TABLE memory_agents ADD COLUMN permissions_json TEXT;
ALTER TABLE memory_agents ADD COLUMN revoked INTEGER DEFAULT 0;

-- 2. Standardize memory_journal (Renaming shorthand to full descriptors)
-- Note: D1 supports RENAME COLUMN. If running locally on older SQLite, this might need table recreation.
ALTER TABLE memory_journal RENAME COLUMN we TO write_expiration;
ALTER TABLE memory_journal RENAME COLUMN ve TO visibility_expiration;
