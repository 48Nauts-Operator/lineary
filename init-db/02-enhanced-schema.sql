-- Enhanced schema for Lineary advanced features

-- Add new columns to existing issues table
ALTER TABLE issues ADD COLUMN IF NOT EXISTS parent_issue_id UUID REFERENCES issues(id);
ALTER TABLE issues ADD COLUMN IF NOT EXISTS depends_on UUID[] DEFAULT '{}';
ALTER TABLE issues ADD COLUMN IF NOT EXISTS start_date TIMESTAMP;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS end_date TIMESTAMP;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS duration_hours NUMERIC(8,2) GENERATED ALWAYS AS (
    CASE 
        WHEN start_date IS NOT NULL AND end_date IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (end_date - start_date)) / 3600
        ELSE NULL
    END
) STORED;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS token_cost INTEGER DEFAULT 0;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS completion_scope INTEGER DEFAULT 0 CHECK (completion_scope >= 0 AND completion_scope <= 100);
ALTER TABLE issues ADD COLUMN IF NOT EXISTS ai_prompt TEXT;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS sprint_id UUID REFERENCES sprints(id);

-- Activity timeline for issues
CREATE TABLE IF NOT EXISTS issue_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    activity_type VARCHAR(50) NOT NULL, -- 'status_change', 'comment', 'code_commit', 'review', 'test_run', etc.
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project documentation
CREATE TABLE IF NOT EXISTS project_documentation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    section VARCHAR(100), -- 'overview', 'architecture', 'requirements', 'api', etc.
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sprint enhancements
ALTER TABLE sprints ADD COLUMN IF NOT EXISTS burndown_data JSONB DEFAULT '[]';
ALTER TABLE sprints ADD COLUMN IF NOT EXISTS velocity NUMERIC(5,2);
ALTER TABLE sprints ADD COLUMN IF NOT EXISTS planned_story_points INTEGER DEFAULT 0;
ALTER TABLE sprints ADD COLUMN IF NOT EXISTS completed_story_points INTEGER DEFAULT 0;

-- Analytics data
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    metric_type VARCHAR(50) NOT NULL, -- 'velocity', 'burndown', 'cycle_time', 'lead_time', etc.
    metric_value JSONB NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI prompt templates for better issue descriptions
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100), -- 'feature', 'bug', 'refactor', 'documentation', etc.
    template TEXT NOT NULL,
    variables JSONB DEFAULT '[]', -- List of variables to fill in
    example_output TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default prompt templates
INSERT INTO prompt_templates (name, category, template, variables) VALUES
('Feature Implementation', 'feature', 
'Implement a {feature_type} that {main_functionality}. 
Requirements:
- {requirement_1}
- {requirement_2}
- {requirement_3}
Acceptance Criteria:
- {acceptance_1}
- {acceptance_2}
Technical Considerations:
- {tech_consideration}
Testing: {testing_approach}',
'["feature_type", "main_functionality", "requirement_1", "requirement_2", "requirement_3", "acceptance_1", "acceptance_2", "tech_consideration", "testing_approach"]'::jsonb),

('Bug Fix', 'bug',
'Fix the issue where {bug_description}.
Steps to Reproduce:
1. {step_1}
2. {step_2}
3. {step_3}
Expected: {expected_behavior}
Actual: {actual_behavior}
Impact: {impact_level}
Root Cause Analysis: {potential_cause}',
'["bug_description", "step_1", "step_2", "step_3", "expected_behavior", "actual_behavior", "impact_level", "potential_cause"]'::jsonb),

('AI Integration', 'ai',
'Integrate AI capabilities for {ai_feature}.
Model Requirements: {model_type}
Input Data: {input_format}
Expected Output: {output_format}
Performance Targets:
- Latency: {latency_target}
- Accuracy: {accuracy_target}
- Token Budget: {token_budget}
Integration Points: {integration_points}',
'["ai_feature", "model_type", "input_format", "output_format", "latency_target", "accuracy_target", "token_budget", "integration_points"]'::jsonb);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_issue_activities_issue_id ON issue_activities(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_activities_created_at ON issue_activities(created_at);
CREATE INDEX IF NOT EXISTS idx_issues_parent_issue_id ON issues(parent_issue_id);
CREATE INDEX IF NOT EXISTS idx_issues_sprint_id ON issues(sprint_id);
CREATE INDEX IF NOT EXISTS idx_project_documentation_project_id ON project_documentation(project_id);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_project_id ON analytics_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_period ON analytics_metrics(period_start, period_end);

-- Function to calculate sprint burndown
CREATE OR REPLACE FUNCTION calculate_sprint_burndown(sprint_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    burndown JSONB;
    sprint_record RECORD;
    daily_points JSONB;
BEGIN
    SELECT * INTO sprint_record FROM sprints WHERE id = sprint_uuid;
    
    -- Calculate daily story points remaining
    WITH daily_progress AS (
        SELECT 
            DATE(ia.created_at) as day,
            SUM(CASE 
                WHEN ia.activity_type = 'status_change' 
                AND ia.metadata->>'new_status' = 'done' 
                THEN i.story_points 
                ELSE 0 
            END) as points_completed
        FROM issue_activities ia
        JOIN issues i ON ia.issue_id = i.id
        WHERE i.sprint_id = sprint_uuid
        GROUP BY DATE(ia.created_at)
        ORDER BY day
    )
    SELECT jsonb_agg(
        jsonb_build_object(
            'date', day,
            'points_remaining', sprint_record.planned_story_points - SUM(points_completed) OVER (ORDER BY day)
        )
    ) INTO daily_points
    FROM daily_progress;
    
    RETURN COALESCE(daily_points, '[]'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update activity timeline
CREATE OR REPLACE FUNCTION log_issue_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- Log status changes
        IF OLD.status != NEW.status THEN
            INSERT INTO issue_activities (issue_id, activity_type, description, metadata)
            VALUES (
                NEW.id, 
                'status_change',
                'Status changed from ' || OLD.status || ' to ' || NEW.status,
                jsonb_build_object('old_status', OLD.status, 'new_status', NEW.status)
            );
        END IF;
        
        -- Log completion changes
        IF OLD.completion_scope != NEW.completion_scope THEN
            INSERT INTO issue_activities (issue_id, activity_type, description, metadata)
            VALUES (
                NEW.id,
                'progress_update',
                'Progress updated to ' || NEW.completion_scope || '%',
                jsonb_build_object('old_progress', OLD.completion_scope, 'new_progress', NEW.completion_scope)
            );
        END IF;
        
        -- Log sprint assignment
        IF OLD.sprint_id IS DISTINCT FROM NEW.sprint_id THEN
            INSERT INTO issue_activities (issue_id, activity_type, description, metadata)
            VALUES (
                NEW.id,
                'sprint_assignment',
                CASE 
                    WHEN NEW.sprint_id IS NULL THEN 'Removed from sprint'
                    ELSE 'Added to sprint'
                END,
                jsonb_build_object('old_sprint_id', OLD.sprint_id, 'new_sprint_id', NEW.sprint_id)
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for activity logging
DROP TRIGGER IF EXISTS issue_activity_trigger ON issues;
CREATE TRIGGER issue_activity_trigger
AFTER UPDATE ON issues
FOR EACH ROW
EXECUTE FUNCTION log_issue_activity();

-- View for issue hierarchy
CREATE OR REPLACE VIEW issue_hierarchy AS
WITH RECURSIVE issue_tree AS (
    -- Base case: top-level issues
    SELECT 
        i.*,
        0 as depth,
        ARRAY[i.id] as path,
        i.id as root_id
    FROM issues i
    WHERE i.parent_issue_id IS NULL
    
    UNION ALL
    
    -- Recursive case: sub-issues
    SELECT 
        i.*,
        it.depth + 1,
        it.path || i.id,
        it.root_id
    FROM issues i
    JOIN issue_tree it ON i.parent_issue_id = it.id
)
SELECT * FROM issue_tree;

-- View for sprint statistics
CREATE OR REPLACE VIEW sprint_statistics AS
SELECT 
    s.id,
    s.name,
    s.project_id,
    s.status,
    s.start_date,
    s.end_date,
    COUNT(DISTINCT i.id) as total_issues,
    SUM(i.story_points) as total_story_points,
    SUM(CASE WHEN i.status = 'done' THEN i.story_points ELSE 0 END) as completed_story_points,
    AVG(i.completion_scope) as average_completion,
    SUM(i.token_cost) as total_token_cost
FROM sprints s
LEFT JOIN issues i ON i.sprint_id = s.id
GROUP BY s.id;