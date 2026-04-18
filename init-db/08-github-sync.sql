-- GitHub sync: project mode, installation link, issue mapping, outbox for reverse sync.
-- Runs on first postgres init. For an already-initialized DB, apply manually:
--   docker compose exec postgres psql -U lineary -d lineary_db -f /docker-entrypoint-initdb.d/08-github-sync.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Project mode: MCP-only (agents-only) or github (bidirectional sync to a repo).
ALTER TABLE projects
  ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'mcp_only';

ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_mode_check;
ALTER TABLE projects
  ADD CONSTRAINT projects_mode_check CHECK (mode IN ('mcp_only', 'github'));

-- GitHub App installation linked to a project.
CREATE TABLE IF NOT EXISTS project_github_installations (
  project_id UUID PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
  installation_id BIGINT NOT NULL,
  repo_owner TEXT NOT NULL,
  repo_name TEXT NOT NULL,
  repo_id BIGINT NOT NULL,
  default_branch TEXT,
  last_synced_at TIMESTAMPTZ,
  sync_status TEXT NOT NULL DEFAULT 'idle',
  sync_error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE project_github_installations DROP CONSTRAINT IF EXISTS pgi_sync_status_check;
ALTER TABLE project_github_installations
  ADD CONSTRAINT pgi_sync_status_check
  CHECK (sync_status IN ('idle','initial_syncing','live','error'));

CREATE INDEX IF NOT EXISTS idx_pgi_installation ON project_github_installations(installation_id);

-- Issue ↔ GitHub issue mapping.
ALTER TABLE issues ADD COLUMN IF NOT EXISTS github_issue_number INTEGER;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS github_issue_id BIGINT;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS github_issue_url TEXT;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'lineary';
ALTER TABLE issues ADD COLUMN IF NOT EXISTS sync_origin TEXT;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS last_github_synced_at TIMESTAMPTZ;

ALTER TABLE issues DROP CONSTRAINT IF EXISTS issues_source_check;
ALTER TABLE issues ADD CONSTRAINT issues_source_check
  CHECK (source IN ('lineary','github'));

CREATE UNIQUE INDEX IF NOT EXISTS idx_issues_github_num
  ON issues(project_id, github_issue_number)
  WHERE github_issue_number IS NOT NULL;

-- Comments mapping.
ALTER TABLE issue_comments ADD COLUMN IF NOT EXISTS github_comment_id BIGINT;
ALTER TABLE issue_comments ADD COLUMN IF NOT EXISTS sync_origin TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_comments_github_id
  ON issue_comments(github_comment_id) WHERE github_comment_id IS NOT NULL;

-- Outbox: durable queue for reverse sync (Lineary → GitHub).
-- Writes enqueue rows here; the drain worker fulfils them and retries on failure.
CREATE TABLE IF NOT EXISTS github_sync_outbox (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  payload JSONB NOT NULL,
  lineary_ref UUID,
  attempts INT NOT NULL DEFAULT 0,
  last_error TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  done_at TIMESTAMPTZ
);

ALTER TABLE github_sync_outbox DROP CONSTRAINT IF EXISTS outbox_status_check;
ALTER TABLE github_sync_outbox
  ADD CONSTRAINT outbox_status_check
  CHECK (status IN ('pending','in_flight','done','failed'));

CREATE INDEX IF NOT EXISTS idx_outbox_pending
  ON github_sync_outbox(project_id, status)
  WHERE status IN ('pending','in_flight');
