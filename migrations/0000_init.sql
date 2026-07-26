-- realm: soup
-- description: Core protocol storage for deterministic context-as-files.

-- Memory data JSON blob per UUID (main content)
CREATE TABLE IF NOT EXISTS memory_data (
    uuid TEXT NOT NULL PRIMARY KEY,
    data_json TEXT NOT NULL DEFAULT '{}'
);

-- Agents table
CREATE TABLE IF NOT EXISTS memory_agents (
    uuid TEXT NOT NULL,
    name TEXT NOT NULL,
    claimed TEXT NOT NULL,
    profile_json TEXT,
    last_ip TEXT,
    last_active_at TEXT,
    session_id TEXT,
    revocation_ticker INTEGER DEFAULT 0,
    PRIMARY KEY (uuid, name)
    
    
);

-- Memory Leases (Active UI sessions)
CREATE TABLE IF NOT EXISTS memory_ui_leases (
    uuid TEXT NOT NULL,
    location_hash TEXT NOT NULL,
    last_ip TEXT,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (uuid, location_hash)
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS memory_chat (
    uuid TEXT NOT NULL,
    key TEXT NOT NULL,
    ts TEXT NOT NULL,
    from_name TEXT NOT NULL,
    to_name TEXT NOT NULL,
    msg TEXT NOT NULL,
    PRIMARY KEY (uuid, key)
);

-- Journal (path metadata) table
CREATE TABLE IF NOT EXISTS memory_journal (
    uuid TEXT NOT NULL,
    path TEXT NOT NULL,
    ts TEXT NOT NULL,
    cs TEXT NOT NULL,
    ro INTEGER DEFAULT 0,
    vault INTEGER DEFAULT 0,
    we TEXT, -- write expiration (timestamp)
    ve TEXT, -- visibility expiration (timestamp)
    PRIMARY KEY (uuid, path)
);

-- Cursors (inbox tracking) table
CREATE TABLE IF NOT EXISTS memory_cursors (
    uuid TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    message_key TEXT NOT NULL,
    ack_level INTEGER DEFAULT 0,
    PRIMARY KEY (uuid, agent_name, message_key)
);

-- UI state table
CREATE TABLE IF NOT EXISTS memory_ui (
    uuid TEXT NOT NULL PRIMARY KEY,
    headless INTEGER DEFAULT 0,
    agents_paused INTEGER DEFAULT 0,
    chat_paused INTEGER DEFAULT 0,
    ts TEXT,
    mutation_id INTEGER DEFAULT 0,
    tier TEXT DEFAULT 'free'
    
    
);

-- Memory snapshots for recovery and audit
CREATE TABLE IF NOT EXISTS memory_snapshots (
    id TEXT PRIMARY KEY,
    uuid TEXT NOT NULL,
    path TEXT NOT NULL,
    data_json TEXT, -- Zipped -> Base64
    intent TEXT,
    agent_name TEXT,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    session_id TEXT, -- core field
    ts TEXT
    
    
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agents_uuid ON memory_agents(uuid);
CREATE INDEX IF NOT EXISTS idx_chat_uuid ON memory_chat(uuid);
CREATE INDEX IF NOT EXISTS idx_journal_uuid ON memory_journal(uuid);
CREATE INDEX IF NOT EXISTS idx_journal_paths ON memory_journal(uuid, path);
CREATE INDEX IF NOT EXISTS idx_cursors_lookup ON memory_cursors(uuid, agent_name);
