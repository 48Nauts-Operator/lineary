-- Add versioning support for projects and issues
CREATE TABLE IF NOT EXISTS versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,
    release_type VARCHAR(20) DEFAULT 'patch', -- major, minor, patch
    release_date DATE,
    release_notes TEXT,
    status VARCHAR(50) DEFAULT 'planned', -- planned, in_progress, released, archived
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, version_number)
);

-- Add version tracking to issues
ALTER TABLE issues ADD COLUMN IF NOT EXISTS target_version UUID REFERENCES versions(id);
ALTER TABLE issues ADD COLUMN IF NOT EXISTS fixed_in_version UUID REFERENCES versions(id);

-- Create index for performance
CREATE INDEX idx_versions_project ON versions(project_id);
CREATE INDEX idx_versions_status ON versions(status);
CREATE INDEX idx_issues_target_version ON issues(target_version);
CREATE INDEX idx_issues_fixed_version ON issues(fixed_in_version);

-- Auto-versioning configuration
CREATE TABLE IF NOT EXISTS version_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    auto_version BOOLEAN DEFAULT true,
    version_pattern VARCHAR(50) DEFAULT 'semver', -- semver, date, custom
    current_major INTEGER DEFAULT 0,
    current_minor INTEGER DEFAULT 1,
    current_patch INTEGER DEFAULT 0,
    prefix VARCHAR(10) DEFAULT 'v',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id)
);