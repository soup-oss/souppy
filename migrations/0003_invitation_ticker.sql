-- Add invitation_ticker to support universal revocation of all L3 invite links
ALTER TABLE memory_ui ADD COLUMN invitation_ticker INTEGER DEFAULT 0;
