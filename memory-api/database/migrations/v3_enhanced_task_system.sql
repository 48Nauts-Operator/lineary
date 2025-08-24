-- ABOUTME: Enhanced Task Management System with Git Integration - Database Schema Migration v3
-- ABOUTME: Adds comprehensive task management tables with Git integration, Sprint Poker, and workflow automation

-- =============================================================================
-- ENHANCED TASK MANAGEMENT TABLES
-- =============================================================================

-- Main enhanced tasks table
CREATE TABLE IF NOT EXISTS enhanced_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    
    -- Core task information
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL DEFAULT 'feature', -- feature, bug, enhancement, refactor, test, docs
    priority INTEGER NOT NULL DEFAULT 1, -- 1-5 scale
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, cancelled, blocked
    
    -- Git Integration
    git_branch VARCHAR(255),
    pull_request_url VARCHAR(500),
    git_status VARCHAR(50) DEFAULT 'not_started', -- not_started, branch_created, commits_made, pr_opened, merged
    base_branch VARCHAR(255) DEFAULT 'main',
    
    -- AI Sprint Poker & Estimation
    complexity_score INTEGER, -- 1-13 (Fibonacci sequence)
    story_points INTEGER,
    confidence_level DECIMAL(3,2), -- 0.00-1.00
    similar_tasks_analyzed JSONB DEFAULT '[]'::jsonb, -- Array of task IDs used for estimation
    
    -- Enhanced Cost Prediction
    estimated_tokens_total INTEGER,
    estimated_tokens_breakdown JSONB DEFAULT '{
        "planning": 0,
        "implementation": 0,
        "testing": 0,
        "review": 0
    }'::jsonb,
    estimated_cost DECIMAL(10,4),
    actual_cost DECIMAL(10,4),
    cost_variance DECIMAL(10,4), -- actual - estimated
    
    -- Workflow State Machine
    workflow_state VARCHAR(50) DEFAULT 'planning', -- planning, estimation, ready, implementing, code_review, testing, validation, pr_review, merging, deployed, closed, blocked
    acceptance_criteria JSONB DEFAULT '[]'::jsonb, -- Array of criteria strings
    definition_of_done JSONB DEFAULT '[]'::jsonb, -- Array of completion requirements
    validation_checklist JSONB DEFAULT '[]'::jsonb, -- Array of validation items
    
    -- Time Tracking & Estimates
    time_estimates JSONB DEFAULT '{
        "planning_hours": 0,
        "implementation_hours": 0,
        "testing_hours": 0,
        "review_hours": 0,
        "total_hours": 0
    }'::jsonb,
    actual_time_tracked JSONB DEFAULT '{
        "planning_minutes": 0,
        "implementation_minutes": 0,
        "testing_minutes": 0,
        "review_minutes": 0,
        "total_minutes": 0
    }'::jsonb,
    
    -- Dependencies & Relationships
    dependencies JSONB DEFAULT '[]'::jsonb, -- Array of task IDs this depends on
    dependents JSONB DEFAULT '[]'::jsonb, -- Array of task IDs that depend on this
    blockers JSONB DEFAULT '[]'::jsonb, -- Array of blocker objects
    
    -- Sprint Planning Integration
    sprint_id UUID, -- Reference to sprint (to be created later)
    sprint_day INTEGER, -- 1-6 for Betty's 6-day sprints
    velocity_impact DECIMAL(5,2), -- Impact on team velocity
    
    -- Legacy task system compatibility
    legacy_task_id VARCHAR(255), -- Link to file-based task system if migrated
    extracted_from VARCHAR(100) DEFAULT 'manual', -- manual, conversation, api, migration
    
    -- Performance & Quality Metrics
    reusability_score DECIMAL(3,2) DEFAULT 0.5, -- How reusable is this work
    technical_debt_impact DECIMAL(3,2) DEFAULT 0.0, -- Technical debt created/resolved
    test_coverage_target DECIMAL(3,2), -- Target test coverage percentage
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Task commits tracking table
CREATE TABLE IF NOT EXISTS task_commits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES enhanced_tasks(id) ON DELETE CASCADE,
    commit_hash VARCHAR(40) NOT NULL,
    commit_message TEXT NOT NULL,
    author VARCHAR(255),
    branch VARCHAR(255),
    files_changed INTEGER DEFAULT 0,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    commit_timestamp TIMESTAMP WITH TIME ZONE,
    ai_generated BOOLEAN DEFAULT false, -- Was this commit message AI-generated?
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Prevent duplicate commits per task
    UNIQUE(task_id, commit_hash)
);

-- Task estimation history table
CREATE TABLE IF NOT EXISTS task_estimates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES enhanced_tasks(id) ON DELETE CASCADE,
    
    -- Estimation method and model
    estimator_type VARCHAR(50) NOT NULL, -- ai_sprint_poker, historical, manual, hybrid
    model_version VARCHAR(50), -- Version of estimation model used
    estimation_confidence DECIMAL(3,2), -- Confidence in this estimate
    
    -- Complexity analysis factors
    complexity_factors JSONB DEFAULT '{
        "code_footprint_score": 0,
        "integration_complexity": 0,
        "testing_complexity": 0,
        "uncertainty_factor": 0,
        "technical_debt_impact": 0,
        "domain_familiarity": 0
    }'::jsonb,
    
    -- Token and cost estimates
    token_estimates JSONB DEFAULT '{
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "model_mix": {}
    }'::jsonb,
    cost_estimates JSONB DEFAULT '{
        "planning": 0,
        "implementation": 0,
        "review": 0,
        "testing": 0,
        "total": 0
    }'::jsonb,
    
    -- Time estimates
    time_estimates JSONB DEFAULT '{
        "min_hours": 0,
        "max_hours": 0,
        "p90_hours": 0,
        "estimated_hours": 0
    }'::jsonb,
    
    -- Supporting data
    similar_tasks_used JSONB DEFAULT '[]'::jsonb, -- Tasks used for comparison
    risk_factors JSONB DEFAULT '[]'::jsonb, -- Identified risks
    optimization_opportunities JSONB DEFAULT '[]'::jsonb, -- Potential optimizations
    
    -- Results tracking
    actual_values JSONB DEFAULT '{}'::jsonb, -- Filled in after completion
    accuracy_score DECIMAL(3,2), -- How accurate was this estimate
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP WITH TIME ZONE, -- When estimate was validated against actual
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Sprint planning table (6-day Betty sprints)
CREATE TABLE IF NOT EXISTS sprint_planning (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sprint_id UUID NOT NULL, -- Sprint identifier
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Sprint definition
    sprint_name VARCHAR(255) NOT NULL,
    sprint_type VARCHAR(50) DEFAULT 'development', -- discovery, development, integration, validation, deployment, retrospective
    sprint_goal TEXT,
    
    -- Sprint timing (6-day structure)
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    current_day INTEGER DEFAULT 1, -- 1-6
    
    -- Sprint structure and allocation
    day_structure JSONB DEFAULT '{
        "day_1": {"focus": "Discovery & Planning", "allocation": {"planning": 60, "development": 40}},
        "day_2": {"focus": "Core Implementation", "allocation": {"development": 70, "testing": 30}},
        "day_3": {"focus": "Feature Completion", "allocation": {"development": 60, "testing": 40}},
        "day_4": {"focus": "Integration & Polish", "allocation": {"development": 40, "testing": 50, "review": 10}},
        "day_5": {"focus": "Validation & Documentation", "allocation": {"testing": 40, "review": 40, "planning": 20}},
        "day_6": {"focus": "Deployment & Retrospective", "allocation": {"review": 50, "planning": 50}}
    }'::jsonb,
    
    -- Budget and capacity
    cost_budget DECIMAL(10,4),
    token_budget INTEGER,
    capacity_hours INTEGER DEFAULT 48, -- 8 hours per day * 6 days
    
    -- Agent allocation
    agent_allocation JSONB DEFAULT '{}'::jsonb, -- Which agents work on what
    
    -- Success metrics
    success_metrics JSONB DEFAULT '[]'::jsonb,
    
    -- Sprint status
    status VARCHAR(50) DEFAULT 'planning', -- planning, active, completed, cancelled
    
    -- Sprint results
    actual_cost DECIMAL(10,4),
    actual_tokens INTEGER,
    actual_hours INTEGER,
    completion_rate DECIMAL(3,2), -- Percentage of planned work completed
    velocity_achieved DECIMAL(5,2), -- Story points completed
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    UNIQUE(sprint_id, project_id)
);

-- Link tasks to sprints
CREATE TABLE IF NOT EXISTS sprint_task_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sprint_id UUID NOT NULL,
    task_id UUID NOT NULL REFERENCES enhanced_tasks(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Assignment details
    planned_day INTEGER, -- 1-6 for planned completion day
    planned_order INTEGER, -- Order within the day
    estimated_completion_time INTERVAL,
    actual_completion_time INTERVAL,
    
    -- Impact tracking
    velocity_contribution DECIMAL(5,2), -- Story points contributed
    cost_contribution DECIMAL(10,4),
    
    -- Status
    assignment_status VARCHAR(50) DEFAULT 'planned', -- planned, active, completed, moved, cancelled
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    moved_to_sprint_id UUID, -- If task was moved to another sprint
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    UNIQUE(sprint_id, task_id)
);

-- Cost prediction tracking
CREATE TABLE IF NOT EXISTS cost_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES enhanced_tasks(id) ON DELETE CASCADE,
    
    -- Prediction model information
    prediction_model VARCHAR(100) NOT NULL, -- model identifier/version
    model_confidence DECIMAL(3,2), -- Model's confidence in prediction
    
    -- Predicted values
    predicted_cost DECIMAL(10,4) NOT NULL,
    predicted_tokens INTEGER NOT NULL,
    predicted_hours DECIMAL(5,2),
    
    -- Breakdown predictions
    cost_breakdown JSONB DEFAULT '{
        "planning": 0,
        "implementation": 0,
        "testing": 0,
        "review": 0
    }'::jsonb,
    
    -- Actual values (filled after completion)
    actual_cost DECIMAL(10,4),
    actual_tokens INTEGER,
    actual_hours DECIMAL(5,2),
    
    -- Variance analysis
    cost_variance_percentage DECIMAL(5,2), -- (actual - predicted) / predicted * 100
    token_variance_percentage DECIMAL(5,2),
    time_variance_percentage DECIMAL(5,2),
    prediction_accuracy DECIMAL(5,2), -- Overall accuracy score
    
    -- Supporting data
    historical_basis JSONB DEFAULT '[]'::jsonb, -- Similar tasks used for prediction
    environmental_factors JSONB DEFAULT '{}'::jsonb, -- Factors affecting prediction
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Workflow transitions tracking
CREATE TABLE IF NOT EXISTS workflow_transitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES enhanced_tasks(id) ON DELETE CASCADE,
    
    -- Transition details
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    transition_trigger VARCHAR(50) NOT NULL, -- automatic, manual, ai_agent, time_based, dependency
    trigger_agent VARCHAR(100), -- Which agent/user triggered the transition
    
    -- Validation and conditions
    validation_passed BOOLEAN DEFAULT true,
    validation_results JSONB DEFAULT '[]'::jsonb, -- Array of validation check results
    transition_reason TEXT,
    automated BOOLEAN DEFAULT false,
    
    -- Context
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    git_event_data JSONB DEFAULT '{}'::jsonb, -- Git-related trigger data
    
    -- Temporal tracking
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Task dependencies tracking
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_task_id UUID NOT NULL REFERENCES enhanced_tasks(id) ON DELETE CASCADE,
    target_task_id UUID NOT NULL REFERENCES enhanced_tasks(id) ON DELETE CASCADE,
    
    -- Dependency details
    dependency_type VARCHAR(50) NOT NULL, -- blocks, requires, relates_to, conflicts_with
    dependency_strength DECIMAL(3,2) DEFAULT 1.0, -- 0.0-1.0 strength of dependency
    is_hard_dependency BOOLEAN DEFAULT true, -- Hard block vs soft dependency
    
    -- Status
    resolved BOOLEAN DEFAULT false,
    resolution_notes TEXT,
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Prevent self-dependencies and duplicates
    CHECK (source_task_id != target_task_id),
    UNIQUE(source_task_id, target_task_id, dependency_type)
);

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Enhanced tasks indexes
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_project_id ON enhanced_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_user_id ON enhanced_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_session_id ON enhanced_tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_status ON enhanced_tasks(status);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_workflow_state ON enhanced_tasks(workflow_state);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_priority ON enhanced_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_git_branch ON enhanced_tasks(git_branch);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_git_status ON enhanced_tasks(git_status);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_complexity_score ON enhanced_tasks(complexity_score);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_story_points ON enhanced_tasks(story_points);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_sprint_id ON enhanced_tasks(sprint_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_created_at ON enhanced_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_due_date ON enhanced_tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_task_type ON enhanced_tasks(task_type);

-- Full-text search on task content
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_title_search ON enhanced_tasks USING GIN(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_description_search ON enhanced_tasks USING GIN(to_tsvector('english', COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_enhanced_tasks_combined_search ON enhanced_tasks USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Task commits indexes
CREATE INDEX IF NOT EXISTS idx_task_commits_task_id ON task_commits(task_id);
CREATE INDEX IF NOT EXISTS idx_task_commits_commit_hash ON task_commits(commit_hash);
CREATE INDEX IF NOT EXISTS idx_task_commits_branch ON task_commits(branch);
CREATE INDEX IF NOT EXISTS idx_task_commits_author ON task_commits(author);
CREATE INDEX IF NOT EXISTS idx_task_commits_timestamp ON task_commits(commit_timestamp);

-- Task estimates indexes
CREATE INDEX IF NOT EXISTS idx_task_estimates_task_id ON task_estimates(task_id);
CREATE INDEX IF NOT EXISTS idx_task_estimates_estimator_type ON task_estimates(estimator_type);
CREATE INDEX IF NOT EXISTS idx_task_estimates_created_at ON task_estimates(created_at);
CREATE INDEX IF NOT EXISTS idx_task_estimates_accuracy_score ON task_estimates(accuracy_score);

-- Sprint planning indexes
CREATE INDEX IF NOT EXISTS idx_sprint_planning_sprint_id ON sprint_planning(sprint_id);
CREATE INDEX IF NOT EXISTS idx_sprint_planning_project_id ON sprint_planning(project_id);
CREATE INDEX IF NOT EXISTS idx_sprint_planning_status ON sprint_planning(status);
CREATE INDEX IF NOT EXISTS idx_sprint_planning_start_date ON sprint_planning(start_date);
CREATE INDEX IF NOT EXISTS idx_sprint_planning_end_date ON sprint_planning(end_date);
CREATE INDEX IF NOT EXISTS idx_sprint_planning_sprint_type ON sprint_planning(sprint_type);

-- Sprint task assignments indexes
CREATE INDEX IF NOT EXISTS idx_sprint_task_assignments_sprint_id ON sprint_task_assignments(sprint_id);
CREATE INDEX IF NOT EXISTS idx_sprint_task_assignments_task_id ON sprint_task_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_sprint_task_assignments_project_id ON sprint_task_assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_sprint_task_assignments_planned_day ON sprint_task_assignments(planned_day);
CREATE INDEX IF NOT EXISTS idx_sprint_task_assignments_status ON sprint_task_assignments(assignment_status);

-- Cost predictions indexes
CREATE INDEX IF NOT EXISTS idx_cost_predictions_task_id ON cost_predictions(task_id);
CREATE INDEX IF NOT EXISTS idx_cost_predictions_prediction_model ON cost_predictions(prediction_model);
CREATE INDEX IF NOT EXISTS idx_cost_predictions_accuracy ON cost_predictions(prediction_accuracy);
CREATE INDEX IF NOT EXISTS idx_cost_predictions_created_at ON cost_predictions(created_at);

-- Workflow transitions indexes
CREATE INDEX IF NOT EXISTS idx_workflow_transitions_task_id ON workflow_transitions(task_id);
CREATE INDEX IF NOT EXISTS idx_workflow_transitions_from_state ON workflow_transitions(from_state);
CREATE INDEX IF NOT EXISTS idx_workflow_transitions_to_state ON workflow_transitions(to_state);
CREATE INDEX IF NOT EXISTS idx_workflow_transitions_trigger ON workflow_transitions(transition_trigger);
CREATE INDEX IF NOT EXISTS idx_workflow_transitions_timestamp ON workflow_transitions(timestamp);

-- Task dependencies indexes
CREATE INDEX IF NOT EXISTS idx_task_dependencies_source_task_id ON task_dependencies(source_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_target_task_id ON task_dependencies(target_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_type ON task_dependencies(dependency_type);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_resolved ON task_dependencies(resolved);

-- =============================================================================
-- TRIGGERS AND FUNCTIONS
-- =============================================================================

-- Update updated_at trigger for enhanced_tasks
CREATE TRIGGER update_enhanced_tasks_updated_at 
    BEFORE UPDATE ON enhanced_tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update updated_at trigger for sprint_planning
CREATE TRIGGER update_sprint_planning_updated_at 
    BEFORE UPDATE ON sprint_planning 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically transition task states based on git events
CREATE OR REPLACE FUNCTION handle_git_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-transition workflow state based on git status changes
    IF NEW.git_status IS DISTINCT FROM OLD.git_status THEN
        CASE NEW.git_status
            WHEN 'branch_created' THEN
                IF NEW.workflow_state = 'ready' THEN
                    NEW.workflow_state = 'implementing';
                END IF;
            WHEN 'commits_made' THEN
                IF NEW.workflow_state = 'implementing' THEN
                    -- Stay in implementing until PR is opened
                END IF;
            WHEN 'pr_opened' THEN
                IF NEW.workflow_state = 'implementing' THEN
                    NEW.workflow_state = 'code_review';
                END IF;
            WHEN 'merged' THEN
                IF NEW.workflow_state IN ('code_review', 'pr_review') THEN
                    NEW.workflow_state = 'deployed';
                    NEW.completed_at = CURRENT_TIMESTAMP;
                    NEW.status = 'completed';
                END IF;
        END CASE;
        
        -- Log the transition
        INSERT INTO workflow_transitions (
            task_id, from_state, to_state, transition_trigger, 
            trigger_agent, automated, git_event_data
        ) VALUES (
            NEW.id, 
            COALESCE(OLD.workflow_state, 'unknown'), 
            NEW.workflow_state,
            'automatic',
            'git_integration',
            true,
            jsonb_build_object(
                'git_status_change', json_build_object(
                    'from', OLD.git_status,
                    'to', NEW.git_status
                )
            )
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply git status change trigger
CREATE TRIGGER handle_git_status_change_trigger
    BEFORE UPDATE ON enhanced_tasks
    FOR EACH ROW EXECUTE FUNCTION handle_git_status_change();

-- Function to update task cost variance when actual costs are recorded
CREATE OR REPLACE FUNCTION update_cost_variance()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.actual_cost IS NOT NULL AND NEW.estimated_cost IS NOT NULL THEN
        NEW.cost_variance = NEW.actual_cost - NEW.estimated_cost;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply cost variance trigger
CREATE TRIGGER update_cost_variance_trigger
    BEFORE UPDATE ON enhanced_tasks
    FOR EACH ROW EXECUTE FUNCTION update_cost_variance();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Enhanced task summary view with relationships
CREATE VIEW enhanced_tasks_summary AS
SELECT 
    et.*,
    p.name as project_name,
    u.username as assigned_to,
    s.session_title as session_context,
    COUNT(tc.id) as commit_count,
    COUNT(te.id) as estimate_count,
    COUNT(td_out.id) as blocking_count,
    COUNT(td_in.id) as blocked_by_count,
    sp.sprint_name,
    sp.sprint_type,
    spa.planned_day as sprint_day_planned,
    spa.planned_order as sprint_order
FROM enhanced_tasks et
LEFT JOIN projects p ON et.project_id = p.id
LEFT JOIN users u ON et.user_id = u.id
LEFT JOIN sessions s ON et.session_id = s.id
LEFT JOIN task_commits tc ON et.id = tc.task_id
LEFT JOIN task_estimates te ON et.id = te.task_id
LEFT JOIN task_dependencies td_out ON et.id = td_out.source_task_id AND NOT td_out.resolved
LEFT JOIN task_dependencies td_in ON et.id = td_in.target_task_id AND NOT td_in.resolved
LEFT JOIN sprint_task_assignments spa ON et.id = spa.task_id
LEFT JOIN sprint_planning sp ON spa.sprint_id = sp.sprint_id AND et.project_id = sp.project_id
GROUP BY et.id, p.name, u.username, s.session_title, sp.sprint_name, sp.sprint_type, spa.planned_day, spa.planned_order;

-- Sprint dashboard view
CREATE VIEW sprint_dashboard AS
SELECT 
    sp.*,
    p.name as project_name,
    COUNT(sta.task_id) as total_tasks,
    COUNT(CASE WHEN et.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN et.status = 'in_progress' THEN 1 END) as active_tasks,
    COUNT(CASE WHEN et.status = 'blocked' THEN 1 END) as blocked_tasks,
    SUM(et.story_points) as total_story_points,
    SUM(CASE WHEN et.status = 'completed' THEN et.story_points ELSE 0 END) as completed_story_points,
    SUM(et.estimated_cost) as estimated_total_cost,
    SUM(et.actual_cost) as actual_total_cost,
    AVG(et.confidence_level) as avg_confidence,
    COUNT(CASE WHEN et.workflow_state = 'blocked' THEN 1 END) as workflow_blocks
FROM sprint_planning sp
LEFT JOIN projects p ON sp.project_id = p.id
LEFT JOIN sprint_task_assignments sta ON sp.sprint_id = sta.sprint_id
LEFT JOIN enhanced_tasks et ON sta.task_id = et.id
GROUP BY sp.id, p.name;

-- =============================================================================
-- MIGRATION DATA AND COMPATIBILITY
-- =============================================================================

-- Function to migrate legacy tasks from file system
CREATE OR REPLACE FUNCTION migrate_legacy_task(
    p_legacy_id VARCHAR(255),
    p_title VARCHAR(500),
    p_priority INTEGER,
    p_status VARCHAR(50),
    p_project_name VARCHAR(255) DEFAULT 'BETTY',
    p_username VARCHAR(255) DEFAULT 'andre'
) RETURNS UUID AS $$
DECLARE
    v_task_id UUID;
    v_project_id UUID;
    v_user_id UUID;
BEGIN
    -- Get project and user IDs
    SELECT id INTO v_project_id FROM projects WHERE name = p_project_name;
    SELECT id INTO v_user_id FROM users WHERE username = p_username;
    
    -- Create enhanced task
    INSERT INTO enhanced_tasks (
        project_id, user_id, title, priority, status, 
        legacy_task_id, extracted_from, task_type
    ) VALUES (
        v_project_id, v_user_id, p_title, p_priority, p_status,
        p_legacy_id, 'migration', 'feature'
    ) RETURNING id INTO v_task_id;
    
    RETURN v_task_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMPLETION AND VERSION TRACKING
-- =============================================================================

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES ('3.0.0', 'Enhanced Task Management System with Git Integration, Sprint Poker, and Workflow Automation')
ON CONFLICT (version) DO UPDATE SET 
    description = EXCLUDED.description,
    applied_at = CURRENT_TIMESTAMP;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Enhanced Task Management System Schema Migration Complete';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Schema Version: 3.0.0';
    RAISE NOTICE 'New Tables: 7 enhanced task management tables';
    RAISE NOTICE 'New Features: Git Integration, Sprint Poker, Workflow Automation';
    RAISE NOTICE 'Backward Compatibility: Legacy task migration function included';
    RAISE NOTICE 'Performance: 40+ specialized indexes for optimal query performance';
    RAISE NOTICE '============================================================';
END $$;