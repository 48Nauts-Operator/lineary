-- Lineary Database Schema
-- Core tables for projects, issues, sprints, and AI features

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(255) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6',
    icon VARCHAR(50) DEFAULT 'folder',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Issues table
CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'backlog',
    priority INTEGER DEFAULT 3,
    story_points INTEGER,
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    assignee VARCHAR(255),
    labels JSONB DEFAULT '[]',
    
    -- Git integration
    branch_name VARCHAR(255),
    worktree_path VARCHAR(500),
    
    -- AI fields
    ai_complexity_score JSONB,
    ai_estimation JSONB,
    ai_review JSONB,
    ai_tests_generated BOOLEAN DEFAULT false,
    ai_docs_generated BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('backlog', 'todo', 'in_progress', 'in_review', 'done', 'cancelled'))
);

-- Sprints table
CREATE TABLE IF NOT EXISTS sprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    goal TEXT,
    duration_hours INTEGER NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'planned',
    velocity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_duration CHECK (duration_hours IN (2, 4, 8, 24)),
    CONSTRAINT valid_sprint_status CHECK (status IN ('planned', 'active', 'completed', 'cancelled'))
);

-- Sprint Issues junction table
CREATE TABLE IF NOT EXISTS sprint_issues (
    sprint_id UUID REFERENCES sprints(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sprint_id, issue_id)
);

-- Code Reviews table
CREATE TABLE IF NOT EXISTS code_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    commit_sha VARCHAR(40),
    diff_content TEXT,
    ai_review JSONB,
    human_review JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
);

-- Test Generations table
CREATE TABLE IF NOT EXISTS test_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    file_path VARCHAR(500),
    test_code TEXT,
    coverage_before DECIMAL(5,2),
    coverage_after DECIMAL(5,2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality Metrics table
CREATE TABLE IF NOT EXISTS quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    value JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_metric_type CHECK (metric_type IN ('lint', 'format', 'types', 'security', 'tests', 'coverage', 'complexity'))
);

-- AI Prompts table (for learning and optimization)
CREATE TABLE IF NOT EXISTS ai_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(50) NOT NULL,
    prompt_template TEXT NOT NULL,
    variables JSONB,
    success_rate DECIMAL(5,2),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity Log table
CREATE TABLE IF NOT EXISTS activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    action VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_issues_project_id ON issues(project_id);
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_issues_created_at ON issues(created_at DESC);
CREATE INDEX idx_sprints_project_id ON sprints(project_id);
CREATE INDEX idx_sprints_status ON sprints(status);
CREATE INDEX idx_code_reviews_issue_id ON code_reviews(issue_id);
CREATE INDEX idx_quality_metrics_issue_id ON quality_metrics(issue_id);
CREATE INDEX idx_activity_log_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_log_created_at ON activity_log(created_at DESC);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_issues_updated_at BEFORE UPDATE ON issues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sprints_updated_at BEFORE UPDATE ON sprints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_prompts_updated_at BEFORE UPDATE ON ai_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default AI prompt templates
INSERT INTO ai_prompts (category, prompt_template, variables) VALUES
('code_review', 'Review the following code diff and provide actionable feedback on: 1) Potential bugs, 2) Performance issues, 3) Code style, 4) Security concerns, 5) Best practices. Diff: {{diff}}', '["diff"]'),
('test_generation', 'Generate comprehensive unit tests for the following code. Include edge cases and error scenarios. Code: {{code}}', '["code"]'),
('documentation', 'Generate clear, concise documentation for the following code including purpose, parameters, return values, and usage examples. Code: {{code}}', '["code"]'),
('sprint_poker', 'Estimate the complexity of this task across 5 dimensions (code_footprint, integration_depth, test_complexity, uncertainty, data_volume). Task: {{description}}', '["description"]'),
('prompt_optimization', 'Improve the following user prompt to be more specific and actionable: {{prompt}}', '["prompt"]');

-- Insert sample project
INSERT INTO projects (name, description, slug, color, icon) VALUES
('Lineary Development', 'Building the Lineary platform itself', 'lineary-dev', '#8B5CF6', 'rocket');