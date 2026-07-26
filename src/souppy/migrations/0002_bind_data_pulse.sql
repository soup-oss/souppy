-- realm: soup
-- description: Bind mutation_id to data for atomic versioning.

ALTER TABLE memory_data ADD COLUMN mutation_id INTEGER DEFAULT 0;

-- Drop mutation_id from memory_ui as it is now centralized with the data blob
-- Note: SQLite does not support DROP COLUMN in older versions, but Cloudflare D1 does.
ALTER TABLE memory_ui DROP COLUMN mutation_id;
