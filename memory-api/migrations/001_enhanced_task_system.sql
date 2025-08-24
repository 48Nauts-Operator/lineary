-- ABOUTME: Database migration for enhanced task management system with Git integration
-- ABOUTME: Adds task descriptions, sprint poker estimation, workflow states, and Git integration fields

-- Migration: Enhanced Task Management System
-- Version: 001
-- Date: 2025-08-14
-- Purpose: Transform basic task system into full development workflow management

BEGIN;

-- Create task_descriptions table for detailed task information
CREATE TABLE IF NOT EXISTS task_descriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    acceptance_criteria TEXT[],
    technical_notes TEXT,
    dependencies TEXT[],
    estimated_story_points INTEGER,
    estimated_hours DECIMAL(5,2),
    estimated_tokens INTEGER,
    estimated_cost DECIMAL(10,4),
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    risk_factors TEXT[],
    similar_tasks UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(task_id)
);

-- Create task_states table for workflow state management
CREATE TABLE IF NOT EXISTS task_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    state VARCHAR(50) NOT NULL DEFAULT 'planning',
    previous_state VARCHAR(50),
    changed_by VARCHAR(255),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    metadata JSONB,
    
    -- Workflow states: planning, implementing, validating, pushing, testing, merging, closing
    CONSTRAINT valid_states CHECK (state IN (
        'planning', 'implementing', 'validating', 'pushing', 'testing', 'merging', 'closing', 'done'
    ))
);

-- Create git_integration table for Git workflow tracking
CREATE TABLE IF NOT EXISTS git_integration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    branch_name VARCHAR(255),
    worktree_path VARCHAR(500),
    commit_hashes TEXT[],
    pr_url VARCHAR(500),
    pr_number INTEGER,
    base_branch VARCHAR(255) DEFAULT 'develop',
    merge_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_merge_status CHECK (merge_status IN (
        'pending', 'mergeable', 'conflicts', 'merged', 'closed'
    )),
    UNIQUE(task_id)
);

-- Create sprint_estimates table for AI Sprint Poker results
CREATE TABLE IF NOT EXISTS sprint_estimates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    complexity_score INTEGER NOT NULL, -- 1-13 Fibonacci scale
    story_points INTEGER NOT NULL,
    estimated_hours DECIMAL(5,2) NOT NULL,
    estimated_tokens INTEGER NOT NULL,
    estimated_cost DECIMAL(10,4) NOT NULL,
    confidence_level DECIMAL(3,2) NOT NULL, -- 0.00 to 1.00
    model_used VARCHAR(100),
    analysis_factors JSONB,
    similar_tasks JSONB,
    reusability_score DECIMAL(3,2), -- 0.00 to 1.00
    optimization_suggestions TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    estimator_version VARCHAR(50) DEFAULT '1.0',
    
    UNIQUE(task_id)
);

-- Create task_validation table for testing and validation tracking
CREATE TABLE IF NOT EXISTS task_validation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    validation_type VARCHAR(100) NOT NULL, -- 'unit_tests', 'integration_tests', 'lint', 'type_check', etc.
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    result_url VARCHAR(500),
    coverage_percentage DECIMAL(5,2),
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    error_messages TEXT[],
    validation_data JSONB,
    validated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_validation_status CHECK (status IN (
        'pending', 'running', 'passed', 'failed', 'skipped'
    ))
);

-- Create task_dependencies table for dependency management
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'blocks', -- 'blocks', 'related', 'subtask'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_dependency_type CHECK (dependency_type IN (
        'blocks', 'related', 'subtask', 'duplicate'
    )),
    CONSTRAINT no_self_dependency CHECK (task_id != depends_on_task_id),
    UNIQUE(task_id, depends_on_task_id)
);

-- Create task_metrics table for performance tracking
CREATE TABLE IF NOT EXISTS task_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    actual_hours DECIMAL(5,2),
    actual_tokens INTEGER,
    actual_cost DECIMAL(10,4),
    actual_story_points INTEGER,
    lines_of_code INTEGER,
    files_modified INTEGER,
    commits_count INTEGER,
    reused_code_percentage DECIMAL(5,2),
    efficiency_score DECIMAL(5,2),
    velocity_points DECIMAL(5,2),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(task_id)
);

-- Create workflow_automation table for automated actions
CREATE TABLE IF NOT EXISTS workflow_automation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    trigger_event VARCHAR(100) NOT NULL, -- 'state_change', 'git_push', 'test_pass', etc.
    action_type VARCHAR(100) NOT NULL, -- 'create_branch', 'run_tests', 'create_pr', etc.
    action_data JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    executed_at TIMESTAMP WITH TIME ZONE,
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_automation_status CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    ))
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_task_descriptions_task_id ON task_descriptions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_states_task_id ON task_states(task_id);
CREATE INDEX IF NOT EXISTS idx_task_states_state ON task_states(state);
CREATE INDEX IF NOT EXISTS idx_git_integration_task_id ON git_integration(task_id);
CREATE INDEX IF NOT EXISTS idx_git_integration_branch ON git_integration(branch_name);
CREATE INDEX IF NOT EXISTS idx_sprint_estimates_task_id ON sprint_estimates(task_id);
CREATE INDEX IF NOT EXISTS idx_task_validation_task_id ON task_validation(task_id);
CREATE INDEX IF NOT EXISTS idx_task_validation_type ON task_validation(validation_type);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_task_metrics_task_id ON task_metrics(task_id);
CREATE INDEX IF NOT EXISTS idx_workflow_automation_task_id ON workflow_automation(task_id);
CREATE INDEX IF NOT EXISTS idx_workflow_automation_trigger ON workflow_automation(trigger_event);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_task_descriptions_updated_at BEFORE UPDATE ON task_descriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_git_integration_updated_at BEFORE UPDATE ON git_integration FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add initial task state for existing tasks
INSERT INTO task_states (task_id, state, changed_by, notes)
SELECT id, 'planning', 'system_migration', 'Initial state assignment during migration'
FROM tasks
WHERE id NOT IN (SELECT task_id FROM task_states);

-- Update task priorities to include new enhanced priority system
-- Keep existing priorities but add descriptions for sprint poker integration
COMMENT ON COLUMN tasks.priority IS 'Task priority: 1=P0 Critical, 2=P1 High, 3=P2 Normal, 4=P3 Low, 5=P4 Backlog';

COMMIT;