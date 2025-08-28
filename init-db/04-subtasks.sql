-- Migration: Add sub-tasks support to issues
-- Adds parent-child relationships and issue types

-- Add parent_issue_id column to support sub-tasks
ALTER TABLE issues ADD COLUMN IF NOT EXISTS parent_issue_id UUID REFERENCES issues(id) ON DELETE CASCADE;

-- Add issue_type to distinguish between different issue types
ALTER TABLE issues ADD COLUMN IF NOT EXISTS issue_type VARCHAR(20) DEFAULT 'issue';

-- Add constraint for issue types
ALTER TABLE issues DROP CONSTRAINT IF EXISTS valid_issue_type;
ALTER TABLE issues ADD CONSTRAINT valid_issue_type 
  CHECK (issue_type IN ('epic', 'issue', 'subtask', 'bug'));

-- Add index for faster parent-child queries
CREATE INDEX IF NOT EXISTS idx_parent_issue ON issues(parent_issue_id);

-- Add completion_percentage column if not exists
ALTER TABLE issues ADD COLUMN IF NOT EXISTS completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100);

-- Add dependency tracking
ALTER TABLE issues ADD COLUMN IF NOT EXISTS dependencies UUID[] DEFAULT '{}';
ALTER TABLE issues ADD COLUMN IF NOT EXISTS blocked_by UUID[] DEFAULT '{}';

-- Add dates for better tracking
ALTER TABLE issues ADD COLUMN IF NOT EXISTS start_date DATE;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS end_date DATE;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS due_date DATE;

-- Add AI-related columns
ALTER TABLE issues ADD COLUMN IF NOT EXISTS ai_prompt TEXT;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS token_cost INTEGER DEFAULT 0;

-- Function to calculate parent issue completion based on sub-tasks
CREATE OR REPLACE FUNCTION update_parent_completion()
RETURNS TRIGGER AS $$
DECLARE
    parent_id UUID;
    avg_completion DECIMAL;
BEGIN
    -- Get the parent issue ID
    parent_id := COALESCE(NEW.parent_issue_id, OLD.parent_issue_id);
    
    -- If there's a parent, recalculate its completion
    IF parent_id IS NOT NULL THEN
        SELECT AVG(
            CASE 
                WHEN status = 'done' THEN 100
                WHEN status = 'cancelled' THEN 100
                ELSE COALESCE(completion_percentage, 0)
            END
        )::INTEGER
        INTO avg_completion
        FROM issues
        WHERE parent_issue_id = parent_id;
        
        -- Update parent's completion percentage
        UPDATE issues 
        SET completion_percentage = COALESCE(avg_completion, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = parent_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trigger_update_parent_completion ON issues;

-- Create trigger to update parent completion when sub-task changes
CREATE TRIGGER trigger_update_parent_completion
AFTER INSERT OR UPDATE OF status, completion_percentage OR DELETE
ON issues
FOR EACH ROW
EXECUTE FUNCTION update_parent_completion();

-- View to get issues with sub-task counts
CREATE OR REPLACE VIEW issues_with_subtasks AS
SELECT 
    i.*,
    COUNT(s.id) as subtask_count,
    COUNT(CASE WHEN s.status = 'done' THEN 1 END) as completed_subtasks
FROM issues i
LEFT JOIN issues s ON s.parent_issue_id = i.id
GROUP BY i.id;

-- Sample data for testing (optional - comment out in production)
-- INSERT INTO issues (project_id, title, description, issue_type, priority)
-- SELECT 
--     (SELECT id FROM projects LIMIT 1),
--     'Epic: Implement User Authentication',
--     'Complete user authentication system with OAuth support',
--     'epic',
--     2
-- WHERE NOT EXISTS (
--     SELECT 1 FROM issues WHERE title = 'Epic: Implement User Authentication'
-- );