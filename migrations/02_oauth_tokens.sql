CREATE TABLE IF NOT EXISTS oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL UNIQUE,
    access_token TEXT,
    refresh_token TEXT,
    expiry TIMESTAMPTZ,
    token_type TEXT,
    scope TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
