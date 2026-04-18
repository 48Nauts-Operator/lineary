-- AI-first Review layer: agents, proposals, live presence.
-- Runs on fresh init-db; for existing DBs, apply manually:
--   docker compose exec -T postgres psql -U lineary -d lineary_db -f /docker-entrypoint-initdb.d/09-agents-proposals.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  slug TEXT NOT NULL,
  display_name TEXT NOT NULL,
  model TEXT,
  specialty TEXT,
  color TEXT DEFAULT '#6EA0F5',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ,
  UNIQUE(user_id, slug)
);

CREATE TABLE IF NOT EXISTS proposals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
  kind TEXT NOT NULL,
  target_issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
  target_label TEXT,
  payload JSONB NOT NULL DEFAULT '{}',
  reasoning TEXT,
  confidence NUMERIC(5,4),
  blast_radius TEXT DEFAULT 'low',
  urgency TEXT DEFAULT 'normal',
  status TEXT DEFAULT 'pending',
  auto_approve_at TIMESTAMPTZ,
  human_response TEXT,
  resolved_by UUID REFERENCES users(id),
  resolved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE proposals DROP CONSTRAINT IF EXISTS proposals_status_check;
ALTER TABLE proposals ADD CONSTRAINT proposals_status_check
  CHECK (status IN ('pending','approved','intervened','expired','cancelled'));

ALTER TABLE proposals DROP CONSTRAINT IF EXISTS proposals_blast_check;
ALTER TABLE proposals ADD CONSTRAINT proposals_blast_check
  CHECK (blast_radius IN ('low','medium','high'));

ALTER TABLE proposals DROP CONSTRAINT IF EXISTS proposals_urgency_check;
ALTER TABLE proposals ADD CONSTRAINT proposals_urgency_check
  CHECK (urgency IN ('urgent','normal','low'));

CREATE INDEX IF NOT EXISTS idx_proposals_pending
  ON proposals(project_id, status) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS agent_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  status TEXT NOT NULL,
  current_task TEXT,
  current_target TEXT,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at TIMESTAMPTZ
);

ALTER TABLE agent_sessions DROP CONSTRAINT IF EXISTS sessions_status_check;
ALTER TABLE agent_sessions ADD CONSTRAINT sessions_status_check
  CHECK (status IN ('active','idle','waiting','finished'));

CREATE INDEX IF NOT EXISTS idx_sessions_active
  ON agent_sessions(project_id, status) WHERE status IN ('active','waiting');
