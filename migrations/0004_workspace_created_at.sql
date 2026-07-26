-- Add created_at to track workspace longevity (24h limit for free tier)
ALTER TABLE memory_ui ADD COLUMN created_at TEXT;
