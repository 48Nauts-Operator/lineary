-- Add file attachments support for issues
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100),
    size_bytes BIGINT,
    storage_path TEXT NOT NULL,
    uploaded_by VARCHAR(255),
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance
CREATE INDEX idx_attachments_issue ON attachments(issue_id);
CREATE INDEX idx_attachments_uploaded_at ON attachments(uploaded_at);

-- Add attachment_count to issues for quick reference
ALTER TABLE issues ADD COLUMN IF NOT EXISTS attachment_count INTEGER DEFAULT 0;