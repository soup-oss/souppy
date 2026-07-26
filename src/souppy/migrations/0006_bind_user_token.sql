-- realm: soup
-- description: Add user_token_uuid to bind workspaces to subscriptions.

ALTER TABLE memory_ui ADD COLUMN user_token_uuid TEXT;
