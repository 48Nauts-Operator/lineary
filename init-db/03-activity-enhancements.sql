-- Enhanced activity tracking for AI and human interactions

-- Extend issue_activities table for better tracking
ALTER TABLE issue_activities 
ADD COLUMN IF NOT EXISTS user_type VARCHAR(20) DEFAULT 'human' CHECK (user_type IN ('human', 'ai', 'system')),
ADD COLUMN IF NOT EXISTS token_cost INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS execution_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS ai_model VARCHAR(100),
ADD COLUMN IF NOT EXISTS parent_activity_id UUID REFERENCES issue_activities(id),
ADD COLUMN IF NOT EXISTS is_request BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS request_status VARCHAR(20) CHECK (request_status IN ('pending', 'processing', 'completed', 'failed'));

-- Documentation links table
CREATE TABLE IF NOT EXISTS issue_documentation_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    link_type VARCHAR(50) NOT NULL CHECK (link_type IN ('documentation', 'git', 'pr', 'design', 'reference', 'external')),
    description TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Git integration tracking
CREATE TABLE IF NOT EXISTS issue_git_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    repository_url TEXT NOT NULL,
    branch_name VARCHAR(255),
    commit_hash VARCHAR(40),
    pull_request_url TEXT,
    pr_status VARCHAR(20) CHECK (pr_status IN ('draft', 'open', 'merged', 'closed')),
    files_changed INTEGER DEFAULT 0,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI execution details
CREATE TABLE IF NOT EXISTS ai_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES issue_activities(id),
    prompt TEXT NOT NULL,
    response TEXT,
    model VARCHAR(100) NOT NULL,
    token_input INTEGER NOT NULL DEFAULT 0,
    token_output INTEGER NOT NULL DEFAULT 0,
    token_total INTEGER GENERATED ALWAYS AS (token_input + token_output) STORED,
    cost_usd NUMERIC(10,6),
    execution_time_ms INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Comments and requests
CREATE TABLE IF NOT EXISTS issue_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES issue_comments(id),
    user_id VARCHAR(255) NOT NULL,
    user_type VARCHAR(20) NOT NULL DEFAULT 'human' CHECK (user_type IN ('human', 'ai')),
    comment_type VARCHAR(20) NOT NULL DEFAULT 'comment' CHECK (comment_type IN ('comment', 'request', 'question', 'review')),
    content TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255),
    sub_ticket_id UUID REFERENCES issues(id),
    reactions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_issue_activities_user_type ON issue_activities(user_type);
CREATE INDEX IF NOT EXISTS idx_issue_activities_token_cost ON issue_activities(token_cost);
CREATE INDEX IF NOT EXISTS idx_issue_documentation_links_issue_id ON issue_documentation_links(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_git_links_issue_id ON issue_git_links(issue_id);
CREATE INDEX IF NOT EXISTS idx_ai_executions_issue_id ON ai_executions(issue_id);
CREATE INDEX IF NOT EXISTS idx_ai_executions_status ON ai_executions(status);
CREATE INDEX IF NOT EXISTS idx_issue_comments_issue_id ON issue_comments(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_comments_comment_type ON issue_comments(comment_type);

-- Function to calculate total token cost for an issue
CREATE OR REPLACE FUNCTION calculate_issue_token_cost(issue_uuid UUID)
RETURNS TABLE(
    total_tokens INTEGER,
    total_cost_usd NUMERIC,
    execution_count INTEGER,
    avg_tokens_per_execution INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(token_total), 0)::INTEGER as total_tokens,
        COALESCE(SUM(cost_usd), 0.0) as total_cost_usd,
        COUNT(*)::INTEGER as execution_count,
        CASE 
            WHEN COUNT(*) > 0 THEN (SUM(token_total) / COUNT(*))::INTEGER
            ELSE 0
        END as avg_tokens_per_execution
    FROM ai_executions
    WHERE issue_id = issue_uuid
    AND status = 'completed';
END;
$$ LANGUAGE plpgsql;

-- Function to create sub-ticket from request
CREATE OR REPLACE FUNCTION create_sub_ticket_from_request(
    parent_issue_uuid UUID,
    request_content TEXT,
    request_comment_id UUID
) RETURNS UUID AS $$
DECLARE
    new_issue_id UUID;
    parent_issue RECORD;
BEGIN
    -- Get parent issue details
    SELECT * INTO parent_issue FROM issues WHERE id = parent_issue_uuid;
    
    -- Create sub-ticket
    INSERT INTO issues (
        project_id,
        parent_issue_id,
        title,
        description,
        priority,
        status,
        ai_prompt
    ) VALUES (
        parent_issue.project_id,
        parent_issue_uuid,
        'Request: ' || LEFT(request_content, 100),
        'Generated from request: ' || request_content,
        parent_issue.priority,
        'backlog',
        request_content
    ) RETURNING id INTO new_issue_id;
    
    -- Update comment with sub-ticket reference
    UPDATE issue_comments 
    SET sub_ticket_id = new_issue_id 
    WHERE id = request_comment_id;
    
    -- Log activity
    INSERT INTO issue_activities (
        issue_id,
        activity_type,
        description,
        user_type,
        metadata
    ) VALUES (
        parent_issue_uuid,
        'sub_ticket_created',
        'Sub-ticket created from request',
        'system',
        jsonb_build_object('sub_ticket_id', new_issue_id, 'comment_id', request_comment_id)
    );
    
    RETURN new_issue_id;
END;
$$ LANGUAGE plpgsql;

-- View for issue activity summary
CREATE OR REPLACE VIEW issue_activity_summary AS
SELECT 
    i.id as issue_id,
    i.title as issue_title,
    COUNT(DISTINCT ia.id) as total_activities,
    COUNT(DISTINCT ia.id) FILTER (WHERE ia.user_type = 'ai') as ai_activities,
    COUNT(DISTINCT ia.id) FILTER (WHERE ia.user_type = 'human') as human_activities,
    SUM(ia.token_cost) as total_token_cost,
    COUNT(DISTINCT ic.id) as total_comments,
    COUNT(DISTINCT ic.id) FILTER (WHERE ic.comment_type = 'request') as total_requests,
    COUNT(DISTINCT ic.id) FILTER (WHERE ic.comment_type = 'request' AND ic.sub_ticket_id IS NOT NULL) as requests_converted,
    COUNT(DISTINCT idl.id) as documentation_links,
    COUNT(DISTINCT igl.id) as git_links,
    MAX(ia.created_at) as last_activity
FROM issues i
LEFT JOIN issue_activities ia ON i.id = ia.issue_id
LEFT JOIN issue_comments ic ON i.id = ic.issue_id
LEFT JOIN issue_documentation_links idl ON i.id = idl.issue_id
LEFT JOIN issue_git_links igl ON i.id = igl.issue_id
GROUP BY i.id, i.title;

-- Sample data for activity types
INSERT INTO issue_activities (issue_id, activity_type, description, user_type, token_cost, ai_model, metadata)
SELECT 
    i.id,
    'ai_analysis',
    'AI analyzed issue and generated implementation plan',
    'ai',
    1250,
    'gpt-4',
    jsonb_build_object(
        'actions', ARRAY['analyzed_requirements', 'generated_plan', 'estimated_complexity'],
        'confidence', 0.92
    )
FROM issues i
LIMIT 1
ON CONFLICT DO NOTHING;