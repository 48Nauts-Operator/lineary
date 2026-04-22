-- Runner-based autonomous dispatch
-- A "runner" is any machine the user owns that runs the lineary-runner daemon.
-- Dispatches pair auto_handle issues with a runner, stream stdout back, open a PR.

CREATE TABLE IF NOT EXISTS runners (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  hostname TEXT,
  runtime_preferences JSONB NOT NULL DEFAULT '["claude"]'::jsonb,
  status TEXT NOT NULL DEFAULT 'offline'
    CHECK (status IN ('offline', 'idle', 'busy')),
  last_seen_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_runners_user_status ON runners(user_id, status);

-- Token stored as sha256 hex; raw token shown to user only at creation time.
CREATE TABLE IF NOT EXISTS runner_tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  runner_id UUID NOT NULL REFERENCES runners(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  prefix TEXT NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_runner_tokens_hash ON runner_tokens(token_hash);

CREATE TABLE IF NOT EXISTS runner_dispatches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  runner_id UUID REFERENCES runners(id) ON DELETE SET NULL,
  issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  runtime TEXT NOT NULL CHECK (runtime IN ('claude', 'codex', 'opencode')),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'claimed', 'running', 'completed', 'failed', 'cancelled')),
  stdout_lines JSONB NOT NULL DEFAULT '[]'::jsonb,
  pr_number INTEGER,
  pr_url TEXT,
  error TEXT,
  claimed_at TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dispatches_runner_status ON runner_dispatches(runner_id, status);
CREATE INDEX IF NOT EXISTS idx_dispatches_issue ON runner_dispatches(issue_id);
CREATE INDEX IF NOT EXISTS idx_dispatches_pending ON runner_dispatches(status) WHERE status = 'pending';

-- Auto-handle flag on issues — set by humans in UI or by CI on failure.
ALTER TABLE issues ADD COLUMN IF NOT EXISTS auto_handle BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS runner_preference TEXT NOT NULL DEFAULT 'any'
  CHECK (runner_preference IN ('any', 'claude', 'codex', 'opencode'));
CREATE INDEX IF NOT EXISTS idx_issues_auto_handle ON issues(auto_handle, status) WHERE auto_handle = TRUE;
