-- Create table for storing Git provider connections
CREATE TABLE IF NOT EXISTS project_git_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  provider VARCHAR(20) NOT NULL CHECK (provider IN ('github', 'gitlab')),
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  expires_at TIMESTAMP,
  user_id VARCHAR(255),
  username VARCHAR(255),
  email VARCHAR(255),
  repositories JSONB DEFAULT '[]',
  selected_repository_id VARCHAR(255),
  webhook_id VARCHAR(255),
  webhook_secret VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(project_id, provider)
);

-- Create table for webhook events
CREATE TABLE IF NOT EXISTS git_webhook_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  provider VARCHAR(20) NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  event_id VARCHAR(255),
  payload JSONB,
  processed BOOLEAN DEFAULT false,
  processed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(provider, event_id)
);

-- Create table for commit-issue links
CREATE TABLE IF NOT EXISTS issue_commits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  commit_sha VARCHAR(255) NOT NULL,
  commit_message TEXT,
  commit_author VARCHAR(255),
  commit_date TIMESTAMP,
  commit_url TEXT,
  repository_id VARCHAR(255),
  branch VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(issue_id, commit_sha)
);

-- Create table for PR-issue links
CREATE TABLE IF NOT EXISTS issue_pull_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  pr_number INTEGER NOT NULL,
  pr_title TEXT,
  pr_url TEXT,
  pr_state VARCHAR(20),
  pr_author VARCHAR(255),
  pr_created_at TIMESTAMP,
  pr_merged_at TIMESTAMP,
  pr_closed_at TIMESTAMP,
  repository_id VARCHAR(255),
  provider VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(issue_id, pr_number, repository_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_git_connections_project ON project_git_connections(project_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_project ON git_webhook_events(project_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON git_webhook_events(processed);
CREATE INDEX IF NOT EXISTS idx_issue_commits_issue ON issue_commits(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_commits_project ON issue_commits(project_id);
CREATE INDEX IF NOT EXISTS idx_issue_prs_issue ON issue_pull_requests(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_prs_project ON issue_pull_requests(project_id);