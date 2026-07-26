-- realm: soup
-- description: Enable attestation mode per workspace.

ALTER TABLE memory_ui ADD COLUMN attestation_mode INTEGER DEFAULT 0;
