-- Tags and Test Cases Enhancement

-- Tags table for categorization and search
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) DEFAULT '#6B7280',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Issue tags many-to-many relationship
CREATE TABLE IF NOT EXISTS issue_tags (
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (issue_id, tag_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test cases table with Gherkin support
CREATE TABLE IF NOT EXISTS issue_test_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    test_type VARCHAR(50) DEFAULT 'functional' CHECK (test_type IN ('functional', 'integration', 'unit', 'e2e', 'performance', 'security')),
    gherkin_scenario TEXT,
    given_steps TEXT[],
    when_steps TEXT[],
    then_steps TEXT[],
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'passed', 'failed', 'skipped', 'blocked')),
    automated BOOLEAN DEFAULT false,
    automation_script TEXT,
    last_run_at TIMESTAMP,
    last_run_result VARCHAR(20),
    last_run_duration_ms INTEGER,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test execution history
CREATE TABLE IF NOT EXISTS test_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_case_id UUID NOT NULL REFERENCES issue_test_cases(id) ON DELETE CASCADE,
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    execution_status VARCHAR(20) NOT NULL CHECK (execution_status IN ('passed', 'failed', 'skipped', 'error')),
    duration_ms INTEGER,
    error_message TEXT,
    stack_trace TEXT,
    screenshots TEXT[],
    logs TEXT,
    executed_by VARCHAR(255),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    environment VARCHAR(50),
    metadata JSONB DEFAULT '{}'
);

-- Add tags column to issues for quick access
ALTER TABLE issues ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
ALTER TABLE issues ADD COLUMN IF NOT EXISTS test_coverage INTEGER DEFAULT 0 CHECK (test_coverage >= 0 AND test_coverage <= 100);
ALTER TABLE issues ADD COLUMN IF NOT EXISTS tests_passed INTEGER DEFAULT 0;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS tests_failed INTEGER DEFAULT 0;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS tests_total INTEGER DEFAULT 0;

-- Default tags
INSERT INTO tags (name, color, description) VALUES
('bug', '#EF4444', 'Bug or defect in the system'),
('feature', '#10B981', 'New feature or enhancement'),
('documentation', '#3B82F6', 'Documentation related'),
('performance', '#F59E0B', 'Performance optimization'),
('security', '#DC2626', 'Security related issue'),
('ux', '#8B5CF6', 'User experience improvement'),
('api', '#06B6D4', 'API related changes'),
('database', '#6366F1', 'Database related changes'),
('testing', '#EC4899', 'Testing and QA related'),
('deployment', '#84CC16', 'Deployment and DevOps'),
('ai', '#F97316', 'AI and ML related'),
('urgent', '#DC2626', 'Urgent priority'),
('blocked', '#991B1B', 'Blocked by dependency'),
('ready', '#059669', 'Ready to start')
ON CONFLICT (name) DO NOTHING;

-- Function to generate Gherkin test cases
CREATE OR REPLACE FUNCTION generate_gherkin_test_case(
    issue_uuid UUID,
    test_title TEXT,
    test_description TEXT
) RETURNS TEXT AS $$
DECLARE
    issue_record RECORD;
    gherkin_text TEXT;
BEGIN
    SELECT * INTO issue_record FROM issues WHERE id = issue_uuid;
    
    gherkin_text := 'Feature: ' || issue_record.title || E'\n\n';
    gherkin_text := gherkin_text || '  Scenario: ' || test_title || E'\n';
    gherkin_text := gherkin_text || '    Given the user is on the application' || E'\n';
    gherkin_text := gherkin_text || '    And the issue "' || issue_record.title || '" is being tested' || E'\n';
    gherkin_text := gherkin_text || '    When the user performs the action described in the test' || E'\n';
    gherkin_text := gherkin_text || '    Then the expected outcome should be observed' || E'\n';
    gherkin_text := gherkin_text || '    And no errors should occur' || E'\n';
    
    RETURN gherkin_text;
END;
$$ LANGUAGE plpgsql;

-- Function to auto-generate basic test cases for an issue
CREATE OR REPLACE FUNCTION auto_generate_test_cases(issue_uuid UUID)
RETURNS VOID AS $$
DECLARE
    issue_record RECORD;
BEGIN
    SELECT * INTO issue_record FROM issues WHERE id = issue_uuid;
    
    -- Generate happy path test
    INSERT INTO issue_test_cases (
        issue_id, title, test_type, gherkin_scenario,
        given_steps, when_steps, then_steps, priority
    ) VALUES (
        issue_uuid,
        'Happy Path - ' || issue_record.title,
        'functional',
        generate_gherkin_test_case(issue_uuid, 'Happy Path Test', 'Verify the main functionality works as expected'),
        ARRAY['User has valid permissions', 'System is in normal state'],
        ARRAY['User performs the main action', 'System processes the request'],
        ARRAY['Expected result is achieved', 'Success message is displayed'],
        1
    );
    
    -- Generate edge case test
    INSERT INTO issue_test_cases (
        issue_id, title, test_type, gherkin_scenario,
        given_steps, when_steps, then_steps, priority
    ) VALUES (
        issue_uuid,
        'Edge Case - ' || issue_record.title,
        'functional',
        generate_gherkin_test_case(issue_uuid, 'Edge Case Test', 'Verify edge cases are handled properly'),
        ARRAY['User is at system limits', 'Boundary conditions exist'],
        ARRAY['User attempts edge case action', 'System validates input'],
        ARRAY['Appropriate validation occurs', 'System remains stable'],
        2
    );
    
    -- Generate error handling test
    INSERT INTO issue_test_cases (
        issue_id, title, test_type, gherkin_scenario,
        given_steps, when_steps, then_steps, priority
    ) VALUES (
        issue_uuid,
        'Error Handling - ' || issue_record.title,
        'functional',
        generate_gherkin_test_case(issue_uuid, 'Error Handling Test', 'Verify errors are handled gracefully'),
        ARRAY['Invalid input is prepared', 'System is in error-prone state'],
        ARRAY['User provides invalid input', 'System attempts to process'],
        ARRAY['Error is caught gracefully', 'Helpful error message is shown', 'System recovers'],
        2
    );
END;
$$ LANGUAGE plpgsql;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_issue_tags_issue_id ON issue_tags(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_tags_tag_id ON issue_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_issue_test_cases_issue_id ON issue_test_cases(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_test_cases_status ON issue_test_cases(status);
CREATE INDEX IF NOT EXISTS idx_test_executions_test_case_id ON test_executions(test_case_id);
CREATE INDEX IF NOT EXISTS idx_test_executions_issue_id ON test_executions(issue_id);
CREATE INDEX IF NOT EXISTS idx_issues_tags ON issues USING GIN (tags);

-- View for issue test summary
CREATE OR REPLACE VIEW issue_test_summary AS
SELECT 
    i.id as issue_id,
    i.title as issue_title,
    COUNT(DISTINCT itc.id) as total_test_cases,
    COUNT(DISTINCT itc.id) FILTER (WHERE itc.status = 'passed') as passed_tests,
    COUNT(DISTINCT itc.id) FILTER (WHERE itc.status = 'failed') as failed_tests,
    COUNT(DISTINCT itc.id) FILTER (WHERE itc.automated = true) as automated_tests,
    CASE 
        WHEN COUNT(DISTINCT itc.id) > 0 
        THEN (COUNT(DISTINCT itc.id) FILTER (WHERE itc.status = 'passed')::FLOAT / COUNT(DISTINCT itc.id) * 100)::INTEGER
        ELSE 0 
    END as test_pass_rate,
    MAX(te.executed_at) as last_test_run
FROM issues i
LEFT JOIN issue_test_cases itc ON i.id = itc.issue_id
LEFT JOIN test_executions te ON itc.id = te.test_case_id
GROUP BY i.id, i.title;

-- Trigger to update issue test counts
CREATE OR REPLACE FUNCTION update_issue_test_counts()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE issues 
    SET 
        tests_total = (SELECT COUNT(*) FROM issue_test_cases WHERE issue_id = NEW.issue_id),
        tests_passed = (SELECT COUNT(*) FROM issue_test_cases WHERE issue_id = NEW.issue_id AND status = 'passed'),
        tests_failed = (SELECT COUNT(*) FROM issue_test_cases WHERE issue_id = NEW.issue_id AND status = 'failed'),
        test_coverage = CASE 
            WHEN (SELECT COUNT(*) FROM issue_test_cases WHERE issue_id = NEW.issue_id) > 0
            THEN ((SELECT COUNT(*) FROM issue_test_cases WHERE issue_id = NEW.issue_id AND status = 'passed')::FLOAT / 
                  (SELECT COUNT(*) FROM issue_test_cases WHERE issue_id = NEW.issue_id) * 100)::INTEGER
            ELSE 0
        END
    WHERE id = NEW.issue_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS test_case_update_trigger ON issue_test_cases;
CREATE TRIGGER test_case_update_trigger
AFTER INSERT OR UPDATE OR DELETE ON issue_test_cases
FOR EACH ROW
EXECUTE FUNCTION update_issue_test_counts();