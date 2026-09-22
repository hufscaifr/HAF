CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(36) PRIMARY KEY,
    external_id VARCHAR(200) UNIQUE,
    title VARCHAR(300) NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    content TEXT,
    thumbnail_url TEXT,
    file_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'published', 'rejected')),
    created_by VARCHAR(100) NOT NULL DEFAULT 'n8n',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_reports_status_published_at
    ON reports (status, published_at DESC);
