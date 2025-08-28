-- Add repository settings to projects table
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS github_repo VARCHAR(500),
ADD COLUMN IF NOT EXISTS gitlab_repo VARCHAR(500),
ADD COLUMN IF NOT EXISTS repo_type VARCHAR(20) DEFAULT 'github' CHECK (repo_type IN ('github', 'gitlab', 'both')),
ADD COLUMN IF NOT EXISTS repo_access_token TEXT,
ADD COLUMN IF NOT EXISTS webhook_secret VARCHAR(255),
ADD COLUMN IF NOT EXISTS auto_create_issues BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS auto_sync_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';

-- Create project settings history table
CREATE TABLE IF NOT EXISTS project_settings_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  changed_by VARCHAR(255),
  changes JSONB,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_projects_repo_type ON projects(repo_type);
CREATE INDEX IF NOT EXISTS idx_project_settings_history_project ON project_settings_history(project_id);