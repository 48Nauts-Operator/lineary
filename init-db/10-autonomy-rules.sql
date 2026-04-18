-- Autonomy rules per project — which proposals the agents may auto-act on
-- without human sign-off. The evaluator inside server.js consults these
-- at proposal creation time; if any rule matches, the proposal is
-- auto-approved immediately instead of landing in the Review queue.

CREATE TABLE IF NOT EXISTS autonomy_rules (
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  rule_key TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT false,
  config JSONB NOT NULL DEFAULT '{}',
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (project_id, rule_key)
);

-- A small audit trail — every auto-approval is recorded so humans can
-- scroll through what was done without asking them.
CREATE TABLE IF NOT EXISTS autonomy_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  proposal_id UUID REFERENCES proposals(id) ON DELETE SET NULL,
  rule_key TEXT NOT NULL,
  agent_slug TEXT,
  kind TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_autonomy_audit_project_time
  ON autonomy_audit(project_id, created_at DESC);
