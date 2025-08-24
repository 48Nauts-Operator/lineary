-- BETTY Memory System - Fix sessions table to match API models
-- Add missing columns for proper session management

-- Add missing columns to sessions table
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS title VARCHAR(200);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS parent_session_id UUID REFERENCES sessions(id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_title ON sessions(title);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_tags ON sessions USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_sessions_parent_session_id ON sessions(parent_session_id);

-- Migrate existing data if any (set title from session_title)
UPDATE sessions SET title = session_title WHERE title IS NULL AND session_title IS NOT NULL;

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES ('1.0.3', 'Added title, description, status, tags, parent_session_id columns to sessions table')
ON CONFLICT (version) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Successfully added missing columns to sessions table';
END $$;