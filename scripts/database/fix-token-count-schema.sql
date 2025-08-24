-- BETTY Memory System - Add missing token_count column to messages
-- Fix for token counting functionality

-- Add token_count column to messages table
ALTER TABLE messages ADD COLUMN IF NOT EXISTS token_count INTEGER DEFAULT 0;

-- Create index for performance on token_count column
CREATE INDEX IF NOT EXISTS idx_messages_token_count ON messages(token_count);

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES ('1.0.2', 'Added token_count column to messages table')
ON CONFLICT (version) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Successfully added token_count column to messages table';
END $$;