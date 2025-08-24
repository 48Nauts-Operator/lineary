-- BETTY Memory System - Add missing deleted_at columns
-- Fix for soft delete functionality

-- Add deleted_at column to sessions table
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Add deleted_at column to messages table  
ALTER TABLE messages ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Create indexes for performance on deleted_at columns
CREATE INDEX IF NOT EXISTS idx_sessions_deleted_at ON sessions(deleted_at);
CREATE INDEX IF NOT EXISTS idx_messages_deleted_at ON messages(deleted_at);

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES ('1.0.1', 'Added deleted_at columns for soft delete functionality')
ON CONFLICT (version) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Successfully added deleted_at columns to sessions and messages tables';
END $$;