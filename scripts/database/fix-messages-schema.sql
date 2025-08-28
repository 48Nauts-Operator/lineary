-- BETTY Memory System - Add missing columns to messages table
-- Fix for message creation functionality

-- Add missing columns to messages table
ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_type VARCHAR(50) DEFAULT 'text';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS function_name VARCHAR(100);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS function_args JSONB;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS attachments JSONB DEFAULT '[]'::jsonb;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS parent_message_id UUID REFERENCES messages(id);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS context_window JSONB DEFAULT '[]'::jsonb;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER DEFAULT 0;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS completion_tokens INTEGER DEFAULT 0;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Create indexes for performance on new columns
CREATE INDEX IF NOT EXISTS idx_messages_message_type ON messages(message_type);
CREATE INDEX IF NOT EXISTS idx_messages_function_name ON messages(function_name);
CREATE INDEX IF NOT EXISTS idx_messages_parent_message_id ON messages(parent_message_id);
CREATE INDEX IF NOT EXISTS idx_messages_prompt_tokens ON messages(prompt_tokens);
CREATE INDEX IF NOT EXISTS idx_messages_completion_tokens ON messages(completion_tokens);
CREATE INDEX IF NOT EXISTS idx_messages_updated_at ON messages(updated_at);

-- Add trigger for updated_at column
CREATE TRIGGER update_messages_updated_at 
    BEFORE UPDATE ON messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES ('1.0.5', 'Added missing columns to messages table for full API compatibility')
ON CONFLICT (version) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Successfully added missing columns to messages table:';
    RAISE NOTICE '- message_type';
    RAISE NOTICE '- function_name';
    RAISE NOTICE '- function_args';
    RAISE NOTICE '- attachments';
    RAISE NOTICE '- parent_message_id';
    RAISE NOTICE '- context_window';
    RAISE NOTICE '- prompt_tokens';
    RAISE NOTICE '- completion_tokens';
    RAISE NOTICE '- updated_at';
    RAISE NOTICE '============================================================';
END $$;