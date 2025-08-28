-- ABOUTME: Database schema for GitHub App integration and Claude code reviews
-- ABOUTME: Stores PR links, review insights, and project GitHub configurations

-- Add GitHub PR tracking columns to issues table
ALTER TABLE issues ADD COLUMN IF NOT EXISTS github_pr_url TEXT;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS github_pr_number INTEGER;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS github_pr_status VARCHAR(50);

-- Code reviews table
CREATE TABLE IF NOT EXISTS code_reviews (
    id SERIAL PRIMARY KEY,
    pr_number INTEGER NOT NULL,
    pr_url TEXT,
    repository TEXT NOT NULL,
    review_text TEXT,
    insights JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_code_reviews_pr_number ON code_reviews(pr_number);
CREATE INDEX IF NOT EXISTS idx_code_reviews_repository ON code_reviews(repository);

-- Review comments table
CREATE TABLE IF NOT EXISTS review_comments (
    id SERIAL PRIMARY KEY,
    pr_number INTEGER NOT NULL,
    comment_text TEXT,
    author VARCHAR(255),
    line_number INTEGER,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_comments_pr ON review_comments(pr_number);

-- Project GitHub configuration
CREATE TABLE IF NOT EXISTS project_github_config (
    id SERIAL PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    repository TEXT NOT NULL,
    installation_id BIGINT,
    webhook_secret TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id)
);

-- Project metrics table for tracking code quality over time
CREATE TABLE IF NOT EXISTS project_metrics (
    id SERIAL PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL, -- 'code_quality', 'security_score', etc.
    value NUMERIC,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_project_metrics_project ON project_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_project_metrics_type ON project_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_project_metrics_created ON project_metrics(created_at);

-- AI feedback loop table
CREATE TABLE IF NOT EXISTS ai_feedback_loop (
    id SERIAL PRIMARY KEY,
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    estimated_hours NUMERIC,
    actual_hours NUMERIC,
    ai_accuracy_score NUMERIC,
    review_quality_score NUMERIC,
    feedback_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_feedback_issue ON ai_feedback_loop(issue_id);