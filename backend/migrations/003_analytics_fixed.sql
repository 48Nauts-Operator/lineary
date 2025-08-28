-- Analytics tables for tracking project metrics

-- Project activity tracking (GitHub-style heatmap)
CREATE TABLE IF NOT EXISTS project_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    activity_type VARCHAR(50) NOT NULL, -- 'issue_created', 'issue_completed', 'commit', 'comment', etc.
    activity_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, activity_date, activity_type)
);

-- Token usage tracking
CREATE TABLE IF NOT EXISTS token_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,
    model_name VARCHAR(100),
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Time tracking (for AI time saved)
CREATE TABLE IF NOT EXISTS time_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,
    user_id VARCHAR(255),
    hours_estimated DECIMAL(10, 2) DEFAULT 0,
    hours_actual DECIMAL(10, 2) DEFAULT 0,
    hours_saved DECIMAL(10, 2) DEFAULT 0, -- AI time saved
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily analytics aggregation
CREATE TABLE IF NOT EXISTS daily_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    issues_created INTEGER DEFAULT 0,
    issues_completed INTEGER DEFAULT 0,
    story_points_completed INTEGER DEFAULT 0,
    commits_count INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    ai_interactions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, date)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_project_activity_date ON project_activity(project_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_token_usage_project ON token_usage(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_time_tracking_project ON time_tracking(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(project_id, date);

-- Add completed_at column to issues if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'issues' AND column_name = 'completed_at') THEN
        ALTER TABLE issues ADD COLUMN completed_at TIMESTAMP;
    END IF;
END $$;

-- Add story_points column to issues if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'issues' AND column_name = 'story_points') THEN
        ALTER TABLE issues ADD COLUMN story_points INTEGER DEFAULT 0;
    END IF;
END $$;

-- Add token_cost column to issues if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'issues' AND column_name = 'token_cost') THEN
        ALTER TABLE issues ADD COLUMN token_cost DECIMAL(10, 6) DEFAULT 0;
    END IF;
END $$;

-- Insert some sample data for testing (only if tables are empty)
INSERT INTO project_activity (project_id, activity_date, activity_type, activity_count)
SELECT 
    p.id,
    CURRENT_DATE - (n || ' days')::INTERVAL,
    CASE (random() * 4)::INT
        WHEN 0 THEN 'issue_created'
        WHEN 1 THEN 'issue_completed'
        WHEN 2 THEN 'commit'
        WHEN 3 THEN 'comment'
        ELSE 'review'
    END,
    (random() * 10 + 1)::INT
FROM projects p
CROSS JOIN generate_series(0, 30) n
WHERE NOT EXISTS (SELECT 1 FROM project_activity WHERE project_id = p.id)
ON CONFLICT (project_id, activity_date, activity_type) DO NOTHING;

-- Add sample token usage
INSERT INTO token_usage (project_id, model_name, prompt_tokens, completion_tokens, total_tokens, cost)
SELECT 
    p.id,
    'gpt-4',
    (random() * 1000 + 100)::INT,
    (random() * 500 + 50)::INT,
    (random() * 1500 + 150)::INT,
    (random() * 5 + 0.5)::DECIMAL
FROM projects p
CROSS JOIN generate_series(1, 10) n
WHERE NOT EXISTS (SELECT 1 FROM token_usage WHERE project_id = p.id)
ON CONFLICT DO NOTHING;

-- Add sample time tracking (AI time saved)
INSERT INTO time_tracking (project_id, hours_estimated, hours_actual, hours_saved)
SELECT 
    p.id,
    (random() * 8 + 2)::DECIMAL,
    (random() * 6 + 1)::DECIMAL,
    (random() * 4 + 0.5)::DECIMAL
FROM projects p
CROSS JOIN generate_series(1, 5) n
WHERE NOT EXISTS (SELECT 1 FROM time_tracking WHERE project_id = p.id)
ON CONFLICT DO NOTHING;