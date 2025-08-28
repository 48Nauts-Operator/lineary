-- Fix time_tracking table schema
-- Drop the old table if it exists with wrong schema
DROP TABLE IF EXISTS time_tracking CASCADE;

-- Create time_tracking with correct schema
CREATE TABLE time_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,
    user_id VARCHAR(255),
    time_spent_minutes INTEGER DEFAULT 0,
    ai_time_saved_minutes INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance
CREATE INDEX idx_time_tracking_project ON time_tracking(project_id, created_at);

-- Insert sample time tracking data
INSERT INTO time_tracking (project_id, issue_id, time_spent_minutes, ai_time_saved_minutes)
SELECT 
    p.id,
    i.id,
    (random() * 120 + 30)::INTEGER, -- 30-150 minutes spent
    (random() * 60 + 10)::INTEGER   -- 10-70 minutes saved
FROM projects p
CROSS JOIN LATERAL (
    SELECT id FROM issues WHERE project_id = p.id LIMIT 5
) i
ON CONFLICT DO NOTHING;