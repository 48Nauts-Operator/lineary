-- Add comprehensive bug reporting system
CREATE TABLE IF NOT EXISTS bug_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium', -- critical, high, medium, low
    status VARCHAR(50) DEFAULT 'new', -- new, confirmed, in_progress, resolved, closed, won't_fix
    reporter_email VARCHAR(255),
    reporter_name VARCHAR(255),
    environment TEXT, -- browser, OS, version info
    steps_to_reproduce TEXT,
    expected_behavior TEXT,
    actual_behavior TEXT,
    error_message TEXT,
    stack_trace TEXT,
    screenshot_url TEXT,
    browser_info JSONB,
    system_info JSONB,
    assigned_to VARCHAR(255),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_bug_reports_project ON bug_reports(project_id);
CREATE INDEX idx_bug_reports_status ON bug_reports(status);
CREATE INDEX idx_bug_reports_severity ON bug_reports(severity);
CREATE INDEX idx_bug_reports_created ON bug_reports(created_at);

-- Bug report comments
CREATE TABLE IF NOT EXISTS bug_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bug_report_id UUID NOT NULL REFERENCES bug_reports(id) ON DELETE CASCADE,
    author VARCHAR(255),
    comment TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bug_comments_report ON bug_comments(bug_report_id);