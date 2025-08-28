-- ABOUTME: Database schema for BETTY Memory System ingestion features
-- ABOUTME: Tables for batch tracking, session management, and knowledge ingestion

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For trigram search

-- Batch ingestion status tracking
CREATE TABLE IF NOT EXISTS batch_ingestion_status (
    batch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    total_items INTEGER NOT NULL DEFAULT 0,
    successful_items INTEGER NOT NULL DEFAULT 0,
    failed_items INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'processing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_batch_ingestion_session_id (session_id),
    INDEX idx_batch_ingestion_project_id (project_id),
    INDEX idx_batch_ingestion_user_id (user_id),
    INDEX idx_batch_ingestion_status (status),
    INDEX idx_batch_ingestion_created_at (created_at)
);

-- Claude session tracking
CREATE TABLE IF NOT EXISTS claude_sessions (
    session_id UUID PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    session_title VARCHAR(500),
    session_status VARCHAR(50) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    claude_version VARCHAR(100),
    environment VARCHAR(100),
    total_messages INTEGER DEFAULT 0,
    total_tool_calls INTEGER DEFAULT 0,
    outcome VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_claude_sessions_project_id (project_id),
    INDEX idx_claude_sessions_user_id (user_id),
    INDEX idx_claude_sessions_status (session_status),
    INDEX idx_claude_sessions_started_at (started_at)
);

-- Knowledge ingestion logs for tracking all ingestion operations
CREATE TABLE IF NOT EXISTS knowledge_ingestion_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES claude_sessions(session_id),
    batch_id UUID REFERENCES batch_ingestion_status(batch_id),
    project_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    ingestion_type VARCHAR(50) NOT NULL, -- conversation, code_change, decision, etc.
    knowledge_item_id UUID, -- References to knowledge_items table
    success BOOLEAN NOT NULL DEFAULT false,
    processing_time_ms FLOAT,
    entities_extracted INTEGER DEFAULT 0,
    relationships_created INTEGER DEFAULT 0,
    embeddings_generated INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_knowledge_ingestion_session_id (session_id),
    INDEX idx_knowledge_ingestion_batch_id (batch_id),
    INDEX idx_knowledge_ingestion_project_id (project_id),
    INDEX idx_knowledge_ingestion_type (ingestion_type),
    INDEX idx_knowledge_ingestion_success (success),
    INDEX idx_knowledge_ingestion_created_at (created_at)
);

-- Project knowledge statistics
CREATE TABLE IF NOT EXISTS project_knowledge_stats (
    project_id VARCHAR(255) PRIMARY KEY,
    total_knowledge_items INTEGER DEFAULT 0,
    total_conversations INTEGER DEFAULT 0,
    total_code_changes INTEGER DEFAULT 0,
    total_decisions INTEGER DEFAULT 0,
    total_problem_solutions INTEGER DEFAULT 0,
    total_tool_usages INTEGER DEFAULT 0,
    total_entities INTEGER DEFAULT 0,
    total_relationships INTEGER DEFAULT 0,
    avg_processing_time_ms FLOAT DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_ingestion_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_project_stats_last_activity (last_activity_at),
    INDEX idx_project_stats_last_ingestion (last_ingestion_at)
);

-- Tool usage patterns for analysis
CREATE TABLE IF NOT EXISTS tool_usage_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(255) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_execution_time_ms FLOAT DEFAULT 0,
    common_parameters JSONB DEFAULT '{}',
    common_contexts JSONB DEFAULT '{}',
    first_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    UNIQUE (project_id, tool_name),
    INDEX idx_tool_usage_patterns_project (project_id),
    INDEX idx_tool_usage_patterns_tool (tool_name),
    INDEX idx_tool_usage_patterns_usage_count (usage_count),
    INDEX idx_tool_usage_patterns_last_used (last_used_at)
);

-- Decision impact tracking
CREATE TABLE IF NOT EXISTS decision_impacts (
    impact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_knowledge_id UUID NOT NULL, -- References knowledge_items
    project_id VARCHAR(255) NOT NULL,
    decision_type VARCHAR(50) NOT NULL,
    impact_type VARCHAR(50) NOT NULL, -- positive, negative, neutral
    impact_description TEXT,
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    impact_score FLOAT, -- -1.0 to 1.0
    verification_method VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_decision_impacts_decision_id (decision_knowledge_id),
    INDEX idx_decision_impacts_project_id (project_id),
    INDEX idx_decision_impacts_type (decision_type),
    INDEX idx_decision_impacts_impact_type (impact_type),
    INDEX idx_decision_impacts_measured_at (measured_at)
);

-- Problem-solution effectiveness tracking
CREATE TABLE IF NOT EXISTS solution_effectiveness (
    effectiveness_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    problem_knowledge_id UUID NOT NULL, -- References knowledge_items for problem
    solution_knowledge_id UUID NOT NULL, -- References knowledge_items for solution
    project_id VARCHAR(255) NOT NULL,
    problem_category VARCHAR(50) NOT NULL,
    effectiveness_score FLOAT, -- 0.0 to 1.0
    resolution_time_minutes INTEGER,
    recurrence_count INTEGER DEFAULT 0,
    last_recurrence_at TIMESTAMP WITH TIME ZONE,
    prevention_success BOOLEAN DEFAULT true,
    feedback_score INTEGER, -- 1-5 rating
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_solution_effectiveness_problem_id (problem_knowledge_id),
    INDEX idx_solution_effectiveness_solution_id (solution_knowledge_id),
    INDEX idx_solution_effectiveness_project_id (project_id),
    INDEX idx_solution_effectiveness_category (problem_category),
    INDEX idx_solution_effectiveness_score (effectiveness_score),
    INDEX idx_solution_effectiveness_recurrence (recurrence_count)
);

-- Conversation context tracking
CREATE TABLE IF NOT EXISTS conversation_contexts (
    context_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES claude_sessions(session_id),
    conversation_knowledge_id UUID NOT NULL, -- References knowledge_items
    project_id VARCHAR(255) NOT NULL,
    context_type VARCHAR(50) NOT NULL, -- user_intent, problem_solving, feature_development, etc.
    primary_intent VARCHAR(255),
    secondary_intents TEXT[],
    technologies_mentioned TEXT[],
    files_mentioned TEXT[],
    entities_mentioned TEXT[],
    outcome_achieved BOOLEAN DEFAULT false,
    outcome_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_conversation_contexts_session_id (session_id),
    INDEX idx_conversation_contexts_conversation_id (conversation_knowledge_id),
    INDEX idx_conversation_contexts_project_id (project_id),
    INDEX idx_conversation_contexts_type (context_type),
    INDEX idx_conversation_contexts_intent (primary_intent),
    INDEX idx_conversation_contexts_outcome (outcome_achieved)
);

-- Code change impact tracking
CREATE TABLE IF NOT EXISTS code_change_impacts (
    impact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code_change_knowledge_id UUID NOT NULL, -- References knowledge_items
    session_id UUID REFERENCES claude_sessions(session_id),
    project_id VARCHAR(255) NOT NULL,
    files_affected TEXT[] NOT NULL,
    lines_added INTEGER DEFAULT 0,
    lines_modified INTEGER DEFAULT 0,
    lines_deleted INTEGER DEFAULT 0,
    change_category VARCHAR(50),
    impact_scope VARCHAR(50), -- local, module, system, architecture
    risk_level VARCHAR(50), -- low, medium, high, critical
    validation_status VARCHAR(50) DEFAULT 'pending', -- pending, passed, failed
    deployment_status VARCHAR(50) DEFAULT 'not_deployed',
    rollback_available BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_code_change_impacts_change_id (code_change_knowledge_id),
    INDEX idx_code_change_impacts_session_id (session_id),
    INDEX idx_code_change_impacts_project_id (project_id),
    INDEX idx_code_change_impacts_category (change_category),
    INDEX idx_code_change_impacts_scope (impact_scope),
    INDEX idx_code_change_impacts_risk (risk_level),
    INDEX idx_code_change_impacts_validation (validation_status)
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_batch_ingestion_status_updated_at 
    BEFORE UPDATE ON batch_ingestion_status 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_knowledge_stats_updated_at 
    BEFORE UPDATE ON project_knowledge_stats 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_solution_effectiveness_updated_at 
    BEFORE UPDATE ON solution_effectiveness 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create functions for statistics updates
CREATE OR REPLACE FUNCTION increment_project_stats(
    p_project_id VARCHAR(255),
    p_ingestion_type VARCHAR(50),
    p_entities_count INTEGER DEFAULT 0,
    p_relationships_count INTEGER DEFAULT 0,
    p_processing_time_ms FLOAT DEFAULT 0
) RETURNS VOID AS $$
BEGIN
    INSERT INTO project_knowledge_stats (
        project_id, 
        total_knowledge_items,
        total_conversations,
        total_code_changes,
        total_decisions,
        total_problem_solutions,
        total_tool_usages,
        total_entities,
        total_relationships,
        avg_processing_time_ms,
        last_activity_at,
        last_ingestion_at
    ) VALUES (
        p_project_id,
        1,
        CASE WHEN p_ingestion_type = 'conversation' THEN 1 ELSE 0 END,
        CASE WHEN p_ingestion_type = 'code_change' THEN 1 ELSE 0 END,
        CASE WHEN p_ingestion_type = 'decision' THEN 1 ELSE 0 END,
        CASE WHEN p_ingestion_type = 'problem_solution' THEN 1 ELSE 0 END,
        CASE WHEN p_ingestion_type = 'tool_usage' THEN 1 ELSE 0 END,
        p_entities_count,
        p_relationships_count,
        p_processing_time_ms,
        NOW(),
        NOW()
    )
    ON CONFLICT (project_id) DO UPDATE SET
        total_knowledge_items = project_knowledge_stats.total_knowledge_items + 1,
        total_conversations = project_knowledge_stats.total_conversations + 
            CASE WHEN p_ingestion_type = 'conversation' THEN 1 ELSE 0 END,
        total_code_changes = project_knowledge_stats.total_code_changes + 
            CASE WHEN p_ingestion_type = 'code_change' THEN 1 ELSE 0 END,
        total_decisions = project_knowledge_stats.total_decisions + 
            CASE WHEN p_ingestion_type = 'decision' THEN 1 ELSE 0 END,
        total_problem_solutions = project_knowledge_stats.total_problem_solutions + 
            CASE WHEN p_ingestion_type = 'problem_solution' THEN 1 ELSE 0 END,
        total_tool_usages = project_knowledge_stats.total_tool_usages + 
            CASE WHEN p_ingestion_type = 'tool_usage' THEN 1 ELSE 0 END,
        total_entities = project_knowledge_stats.total_entities + p_entities_count,
        total_relationships = project_knowledge_stats.total_relationships + p_relationships_count,
        avg_processing_time_ms = (
            (project_knowledge_stats.avg_processing_time_ms * project_knowledge_stats.total_knowledge_items + p_processing_time_ms) /
            (project_knowledge_stats.total_knowledge_items + 1)
        ),
        last_activity_at = NOW(),
        last_ingestion_at = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Create function for updating tool usage patterns
CREATE OR REPLACE FUNCTION update_tool_usage_pattern(
    p_project_id VARCHAR(255),
    p_tool_name VARCHAR(100),
    p_success BOOLEAN,
    p_execution_time_ms FLOAT DEFAULT NULL,
    p_parameters JSONB DEFAULT '{}',
    p_context JSONB DEFAULT '{}'
) RETURNS VOID AS $$
BEGIN
    INSERT INTO tool_usage_patterns (
        project_id,
        tool_name,
        usage_count,
        success_count,
        failure_count,
        avg_execution_time_ms,
        common_parameters,
        common_contexts,
        first_used_at,
        last_used_at
    ) VALUES (
        p_project_id,
        p_tool_name,
        1,
        CASE WHEN p_success THEN 1 ELSE 0 END,
        CASE WHEN p_success THEN 0 ELSE 1 END,
        COALESCE(p_execution_time_ms, 0),
        p_parameters,
        p_context,
        NOW(),
        NOW()
    )
    ON CONFLICT (project_id, tool_name) DO UPDATE SET
        usage_count = tool_usage_patterns.usage_count + 1,
        success_count = tool_usage_patterns.success_count + 
            CASE WHEN p_success THEN 1 ELSE 0 END,
        failure_count = tool_usage_patterns.failure_count + 
            CASE WHEN p_success THEN 0 ELSE 1 END,
        avg_execution_time_ms = CASE 
            WHEN p_execution_time_ms IS NOT NULL THEN
                (tool_usage_patterns.avg_execution_time_ms * tool_usage_patterns.usage_count + p_execution_time_ms) /
                (tool_usage_patterns.usage_count + 1)
            ELSE tool_usage_patterns.avg_execution_time_ms
        END,
        last_used_at = NOW();
END;
$$ LANGUAGE plpgsql;