-- Releases: a human-readable bundle of merged work.
-- Typical lifecycle: a release is "draft" while the agent/planner is
-- composing notes; flips to "published" when the human clicks Publish
-- (or a rule auto-publishes it).

CREATE TABLE IF NOT EXISTS releases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  tag TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  body TEXT,
  pr_numbers INTEGER[] DEFAULT '{}',
  issue_ids UUID[] DEFAULT '{}',
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE releases DROP CONSTRAINT IF EXISTS releases_status_check;
ALTER TABLE releases ADD CONSTRAINT releases_status_check
  CHECK (status IN ('draft', 'published'));

CREATE INDEX IF NOT EXISTS idx_releases_project
  ON releases(project_id, created_at DESC);
