-- BETTY Memory System - Add missing access_count columns
-- Fix for access tracking functionality

-- Add access_count and last_accessed_at columns to sessions table
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE;

-- Add access_count and last_accessed_at columns to knowledge_items table
-- Note: knowledge_items already has usage_count and last_used_at, but the code expects access_count
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0;
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE;

-- Migrate existing data from usage_count to access_count
UPDATE knowledge_items 
SET access_count = COALESCE(usage_count, 0),
    last_accessed_at = last_used_at
WHERE access_count = 0 OR access_count IS NULL;

-- Create indexes for performance on new columns
CREATE INDEX IF NOT EXISTS idx_sessions_access_count ON sessions(access_count);
CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed_at ON sessions(last_accessed_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_access_count ON knowledge_items(access_count);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_last_accessed_at ON knowledge_items(last_accessed_at);

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES ('1.0.4', 'Added access_count and last_accessed_at columns for access tracking')
ON CONFLICT (version) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Successfully added access tracking columns:';
    RAISE NOTICE '- sessions.access_count';
    RAISE NOTICE '- sessions.last_accessed_at';
    RAISE NOTICE '- knowledge_items.access_count';
    RAISE NOTICE '- knowledge_items.last_accessed_at';
    RAISE NOTICE 'Migrated usage_count data to access_count for knowledge_items';
    RAISE NOTICE '============================================================';
END $$;