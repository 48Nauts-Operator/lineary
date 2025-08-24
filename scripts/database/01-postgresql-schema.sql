-- BETTY Memory System - PostgreSQL Schema
-- Database: betty_memory
-- Purpose: Source of truth for structured data in BETTY's cross-project memory system
-- 
-- Architecture:
-- - PostgreSQL as source of truth for all structured data
-- - Graphiti uses Neo4j for temporal knowledge graphs 
-- - Qdrant stores vector embeddings for semantic search
-- - Redis provides caching layer for performance

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- CORE SYSTEM TABLES
-- =============================================================================

-- Projects table - Define project boundaries and configuration
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    domain VARCHAR(255), -- e.g., 'rufus.blockonauts.io'
    repository_url TEXT,
    
    -- Privacy and sharing configuration
    privacy_level VARCHAR(50) NOT NULL DEFAULT 'private', -- private, shared, public
    knowledge_sharing_enabled BOOLEAN NOT NULL DEFAULT true,
    cross_project_learning BOOLEAN NOT NULL DEFAULT true,
    
    -- Project metadata
    technology_stack JSONB DEFAULT '[]'::jsonb, -- ['Python', 'FastAPI', 'PostgreSQL']
    project_type VARCHAR(100), -- 'web_api', 'cli_tool', 'library', 'memory_system'
    business_domain VARCHAR(100), -- 'fintech', 'ai_systems', 'memory_management'
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Users table - Track user behavior patterns and preferences
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    email VARCHAR(255),
    
    -- User preferences for BETTY system
    preferences JSONB DEFAULT '{
        "context_loading_depth": 10,
        "cross_project_suggestions": true,
        "memory_retention_days": 365,
        "privacy_level": "private"
    }'::jsonb,
    
    -- Behavioral patterns (learned over time)
    behavior_patterns JSONB DEFAULT '{
        "preferred_technologies": [],
        "common_problem_domains": [],
        "working_hours": null,
        "session_duration_avg": null
    }'::jsonb,
    
    -- Activity tracking
    last_active_at TIMESTAMP WITH TIME ZONE,
    total_sessions INTEGER DEFAULT 0,
    total_knowledge_items INTEGER DEFAULT 0,
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Sessions table - Claude interaction sessions with context
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session identification
    session_title VARCHAR(500),
    session_context TEXT, -- What was Claude working on?
    
    -- Session metrics
    message_count INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    tools_used JSONB DEFAULT '[]'::jsonb, -- ['Read', 'Edit', 'Bash', 'WebSearch']
    files_modified JSONB DEFAULT '[]'::jsonb, -- ['/path/to/file1.py', '/path/to/file2.js']
    
    -- Outcomes and results
    session_outcome VARCHAR(100), -- 'completed', 'interrupted', 'failed', 'ongoing'
    achievements JSONB DEFAULT '[]'::jsonb, -- ['implemented_auth', 'fixed_bug', 'added_tests']
    problems_solved JSONB DEFAULT '[]'::jsonb, -- Problems solved in this session
    
    -- Knowledge graph integration
    graphiti_session_id VARCHAR(255), -- Link to Graphiti temporal graph
    
    -- Temporal tracking
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Messages table - Individual conversation messages in sessions
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    content_hash VARCHAR(64), -- SHA-256 hash for deduplication
    
    -- Message context
    message_index INTEGER NOT NULL, -- Order within session (0, 1, 2, ...)
    tool_calls JSONB DEFAULT '[]'::jsonb, -- Tools used in this message
    tool_results JSONB DEFAULT '[]'::jsonb, -- Results from tool calls
    
    -- Message analysis
    intent VARCHAR(100), -- 'question', 'request', 'clarification', 'information'
    complexity_score REAL, -- 0.0-1.0 complexity of the message
    knowledge_density REAL, -- 0.0-1.0 how much knowledge this contains
    
    -- Vector embeddings reference
    embedding_id VARCHAR(255), -- Reference to Qdrant vector
    
    -- Temporal tracking
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- KNOWLEDGE MANAGEMENT TABLES
-- =============================================================================

-- Knowledge Items table - Core knowledge storage with rich metadata
CREATE TABLE knowledge_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Knowledge identification
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for deduplication
    knowledge_type VARCHAR(100) NOT NULL, -- 'solution', 'pattern', 'decision', 'error_fix', 'architecture'
    
    -- Categorization
    domain VARCHAR(100), -- 'authentication', 'database', 'frontend', 'deployment'
    subdomain VARCHAR(100), -- 'jwt_auth', 'postgres_optimization', 'react_hooks'
    technologies JSONB DEFAULT '[]'::jsonb, -- ['Python', 'FastAPI', 'PostgreSQL']
    patterns JSONB DEFAULT '[]'::jsonb, -- ['middleware', 'factory_pattern', 'singleton']
    
    -- Content analysis
    quality_score REAL DEFAULT 0.5, -- 0.0-1.0 quality assessment
    reusability_score REAL DEFAULT 0.5, -- 0.0-1.0 how reusable is this knowledge
    complexity_level VARCHAR(50) DEFAULT 'medium', -- 'simple', 'medium', 'complex', 'expert'
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    success_rate REAL DEFAULT 0.0, -- 0.0-1.0 success rate when applied
    
    -- Relationships
    related_knowledge_ids UUID[] DEFAULT ARRAY[]::UUID[], -- Related knowledge items
    prerequisite_knowledge_ids UUID[] DEFAULT ARRAY[]::UUID[], -- Required knowledge
    
    -- Context information
    problem_description TEXT, -- What problem did this solve?
    solution_description TEXT, -- How was it solved?
    outcome_description TEXT, -- What was the result?
    lessons_learned TEXT, -- Key takeaways
    
    -- Vector embeddings reference
    embedding_id VARCHAR(255), -- Reference to Qdrant vector
    
    -- Graphiti integration
    graphiti_entity_id VARCHAR(255), -- Link to Graphiti knowledge graph
    
    -- Temporal validity (bi-temporal support)
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE, -- NULL means still valid
    system_time_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    system_time_until TIMESTAMP WITH TIME ZONE, -- NULL means current version
    
    -- Standard temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Ensure content hash uniqueness per project
    UNIQUE(project_id, content_hash)
);

-- Knowledge Relationships table - Explicit relationships between knowledge items
CREATE TABLE knowledge_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_knowledge_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    target_knowledge_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    
    -- Relationship definition
    relationship_type VARCHAR(100) NOT NULL, -- 'similar_to', 'prerequisite_of', 'evolved_from', 'conflicts_with'
    strength REAL NOT NULL DEFAULT 0.5, -- 0.0-1.0 relationship strength
    confidence REAL NOT NULL DEFAULT 0.5, -- 0.0-1.0 confidence in relationship
    
    -- Context
    description TEXT,
    detected_by VARCHAR(100), -- 'graphiti', 'manual', 'semantic_similarity'
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate relationships
    UNIQUE(source_knowledge_id, target_knowledge_id, relationship_type)
);

-- =============================================================================
-- CLAUDE TOOL INTEGRATION TABLES
-- =============================================================================

-- Tool Usage table - Track all Claude Code tool usage for knowledge capture
CREATE TABLE tool_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Tool identification
    tool_name VARCHAR(100) NOT NULL, -- 'Read', 'Edit', 'Bash', 'WebSearch', etc.
    tool_operation VARCHAR(100), -- 'read_file', 'edit_file', 'execute_command'
    
    -- Tool parameters and results
    parameters JSONB NOT NULL, -- Tool input parameters
    results JSONB, -- Tool output/results
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    
    -- File operations tracking
    file_path TEXT, -- For file-based operations
    file_content_before TEXT, -- For Edit operations
    file_content_after TEXT, -- For Edit operations
    
    -- Context and impact
    purpose TEXT, -- Why was this tool used?
    impact_description TEXT, -- What did this accomplish?
    
    -- Performance metrics
    execution_time_ms INTEGER,
    
    -- Temporal tracking
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- AUDIT AND MONITORING TABLES
-- =============================================================================

-- Audit Log table - Comprehensive audit trail for all system actions
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Action identification
    action VARCHAR(100) NOT NULL, -- 'knowledge_created', 'session_started', 'search_performed'
    entity_type VARCHAR(100) NOT NULL, -- 'knowledge_item', 'session', 'project'
    entity_id UUID, -- ID of the affected entity
    
    -- Actor information
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    
    -- Action details
    action_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    before_state JSONB, -- State before the action
    after_state JSONB, -- State after the action
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    
    -- Results
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    
    -- Performance
    execution_time_ms INTEGER,
    
    -- Temporal tracking
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- System Metrics table - Track system performance and usage patterns
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(100) NOT NULL, -- 'performance', 'usage', 'quality', 'intelligence'
    
    -- Metric values
    value REAL NOT NULL,
    unit VARCHAR(50), -- 'ms', 'count', 'percentage', 'ratio'
    
    -- Context
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    
    -- Temporal tracking
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Projects indexes
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_privacy_level ON projects(privacy_level);
CREATE INDEX idx_projects_technology_stack ON projects USING GIN(technology_stack);
CREATE INDEX idx_projects_created_at ON projects(created_at);

-- Users indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_last_active_at ON users(last_active_at);
CREATE INDEX idx_users_preferences ON users USING GIN(preferences);

-- Sessions indexes
CREATE INDEX idx_sessions_project_id ON sessions(project_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_started_at ON sessions(started_at);
CREATE INDEX idx_sessions_session_outcome ON sessions(session_outcome);
CREATE INDEX idx_sessions_tools_used ON sessions USING GIN(tools_used);
CREATE INDEX idx_sessions_graphiti_session_id ON sessions(graphiti_session_id);

-- Messages indexes
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_message_index ON messages(session_id, message_index);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_messages_content_hash ON messages(content_hash);
CREATE INDEX idx_messages_embedding_id ON messages(embedding_id);

-- Full-text search on message content
CREATE INDEX idx_messages_content_search ON messages USING GIN(to_tsvector('english', content));

-- Knowledge Items indexes
CREATE INDEX idx_knowledge_items_project_id ON knowledge_items(project_id);
CREATE INDEX idx_knowledge_items_session_id ON knowledge_items(session_id);
CREATE INDEX idx_knowledge_items_user_id ON knowledge_items(user_id);
CREATE INDEX idx_knowledge_items_knowledge_type ON knowledge_items(knowledge_type);
CREATE INDEX idx_knowledge_items_domain ON knowledge_items(domain, subdomain);
CREATE INDEX idx_knowledge_items_technologies ON knowledge_items USING GIN(technologies);
CREATE INDEX idx_knowledge_items_patterns ON knowledge_items USING GIN(patterns);
CREATE INDEX idx_knowledge_items_quality_score ON knowledge_items(quality_score);
CREATE INDEX idx_knowledge_items_usage_count ON knowledge_items(usage_count);
CREATE INDEX idx_knowledge_items_last_used_at ON knowledge_items(last_used_at);
CREATE INDEX idx_knowledge_items_content_hash ON knowledge_items(project_id, content_hash);
CREATE INDEX idx_knowledge_items_embedding_id ON knowledge_items(embedding_id);
CREATE INDEX idx_knowledge_items_graphiti_entity_id ON knowledge_items(graphiti_entity_id);

-- Temporal indexes for bi-temporal support
CREATE INDEX idx_knowledge_items_valid_time ON knowledge_items(valid_from, valid_until);
CREATE INDEX idx_knowledge_items_system_time ON knowledge_items(system_time_from, system_time_until);

-- Full-text search on knowledge content
CREATE INDEX idx_knowledge_items_title_search ON knowledge_items USING GIN(to_tsvector('english', title));
CREATE INDEX idx_knowledge_items_content_search ON knowledge_items USING GIN(to_tsvector('english', content));
CREATE INDEX idx_knowledge_items_combined_search ON knowledge_items USING GIN(to_tsvector('english', title || ' ' || content || ' ' || COALESCE(problem_description, '') || ' ' || COALESCE(solution_description, '')));

-- Knowledge Relationships indexes
CREATE INDEX idx_knowledge_relationships_source ON knowledge_relationships(source_knowledge_id);
CREATE INDEX idx_knowledge_relationships_target ON knowledge_relationships(target_knowledge_id);
CREATE INDEX idx_knowledge_relationships_type ON knowledge_relationships(relationship_type);
CREATE INDEX idx_knowledge_relationships_strength ON knowledge_relationships(strength);

-- Tool Usage indexes
CREATE INDEX idx_tool_usage_session_id ON tool_usage(session_id);
CREATE INDEX idx_tool_usage_message_id ON tool_usage(message_id);
CREATE INDEX idx_tool_usage_tool_name ON tool_usage(tool_name);
CREATE INDEX idx_tool_usage_executed_at ON tool_usage(executed_at);
CREATE INDEX idx_tool_usage_success ON tool_usage(success);
CREATE INDEX idx_tool_usage_file_path ON tool_usage(file_path);

-- Audit Log indexes
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_session_id ON audit_log(session_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_success ON audit_log(success);

-- System Metrics indexes
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_category ON system_metrics(metric_category);
CREATE INDEX idx_system_metrics_recorded_at ON system_metrics(recorded_at);
CREATE INDEX idx_system_metrics_project_id ON system_metrics(project_id);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC MAINTENANCE
-- =============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_items_updated_at BEFORE UPDATE ON knowledge_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_relationships_updated_at BEFORE UPDATE ON knowledge_relationships FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Automatically update message count in sessions
CREATE OR REPLACE FUNCTION update_session_message_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE sessions 
        SET message_count = message_count + 1
        WHERE id = NEW.session_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE sessions 
        SET message_count = message_count - 1
        WHERE id = OLD.session_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_session_message_count_trigger 
    AFTER INSERT OR DELETE ON messages 
    FOR EACH ROW EXECUTE FUNCTION update_session_message_count();

-- Automatically update knowledge item usage tracking
CREATE OR REPLACE FUNCTION update_knowledge_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- This will be called when knowledge is retrieved/used
    -- Implementation will be added when usage tracking is implemented
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =============================================================================
-- INITIAL DATA SETUP
-- =============================================================================

-- Create default user (Claude/Andre)
INSERT INTO users (id, username, display_name, preferences)
VALUES (
    uuid_generate_v4(),
    'andre',
    'Andre',
    '{
        "context_loading_depth": 15,
        "cross_project_suggestions": true,
        "memory_retention_days": -1,
        "privacy_level": "private",
        "intelligent_suggestions": true,
        "background_processing": true
    }'::jsonb
) ON CONFLICT (username) DO NOTHING;

-- Create BETTY system project
INSERT INTO projects (id, name, description, domain, technology_stack, project_type, business_domain, privacy_level)
VALUES (
    uuid_generate_v4(),
    'BETTY',
    'Cross-project memory system providing unlimited context awareness for Claude',
    'localhost',
    '["Python", "FastAPI", "PostgreSQL", "Neo4j", "Qdrant", "Redis", "Graphiti"]'::jsonb,
    'memory_system',
    'ai_systems',
    'private'
) ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for active knowledge items with relationship counts
CREATE VIEW knowledge_items_enriched AS
SELECT 
    ki.*,
    COUNT(kr_out.id) as outgoing_relationships,
    COUNT(kr_in.id) as incoming_relationships,
    AVG(kr_out.strength) as avg_outgoing_strength,
    AVG(kr_in.strength) as avg_incoming_strength,
    p.name as project_name,
    u.username as created_by_username
FROM knowledge_items ki
LEFT JOIN knowledge_relationships kr_out ON ki.id = kr_out.source_knowledge_id
LEFT JOIN knowledge_relationships kr_in ON ki.id = kr_in.target_knowledge_id
LEFT JOIN projects p ON ki.project_id = p.id
LEFT JOIN users u ON ki.user_id = u.id
WHERE ki.system_time_until IS NULL -- Only current versions
GROUP BY ki.id, p.name, u.username;

-- View for session summaries with metrics
CREATE VIEW session_summaries AS
SELECT 
    s.*,
    p.name as project_name,
    u.username as user_name,
    COUNT(m.id) as actual_message_count,
    COUNT(tu.id) as tool_usage_count,
    COUNT(DISTINCT tu.tool_name) as unique_tools_used,
    MIN(m.timestamp) as first_message_at,
    MAX(m.timestamp) as last_message_at,
    EXTRACT(EPOCH FROM (MAX(m.timestamp) - MIN(m.timestamp))) as duration_seconds_calculated
FROM sessions s
LEFT JOIN messages m ON s.id = m.session_id
LEFT JOIN tool_usage tu ON s.id = tu.session_id
LEFT JOIN projects p ON s.project_id = p.id
LEFT JOIN users u ON s.user_id = u.id
GROUP BY s.id, p.name, u.username;

-- =============================================================================
-- PERFORMANCE MONITORING FUNCTIONS
-- =============================================================================

-- Function to get knowledge item statistics
CREATE OR REPLACE FUNCTION get_knowledge_stats()
RETURNS TABLE (
    total_items BIGINT,
    items_by_type JSONB,
    items_by_domain JSONB,
    avg_quality_score REAL,
    avg_reusability_score REAL,
    most_used_technologies JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_items,
        jsonb_object_agg(knowledge_type, type_count) as items_by_type,
        jsonb_object_agg(domain, domain_count) as items_by_domain,
        AVG(quality_score) as avg_quality_score,
        AVG(reusability_score) as avg_reusability_score,
        (
            SELECT jsonb_object_agg(tech, tech_count)
            FROM (
                SELECT tech, COUNT(*) as tech_count
                FROM knowledge_items, jsonb_array_elements_text(technologies) as tech
                WHERE system_time_until IS NULL
                GROUP BY tech
                ORDER BY tech_count DESC
                LIMIT 10
            ) t
        ) as most_used_technologies
    FROM (
        SELECT 
            knowledge_type,
            domain,
            quality_score,
            reusability_score,
            COUNT(*) OVER (PARTITION BY knowledge_type) as type_count,
            COUNT(*) OVER (PARTITION BY domain) as domain_count
        FROM knowledge_items
        WHERE system_time_until IS NULL
    ) stats;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old audit logs (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_log 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup action
    INSERT INTO audit_log (action, entity_type, action_details, success)
    VALUES (
        'audit_cleanup',
        'audit_log',
        jsonb_build_object(
            'retention_days', retention_days,
            'deleted_count', deleted_count
        ),
        true
    );
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON DATABASE betty_memory IS 'BETTY Memory System - Cross-project intelligence and temporal knowledge management for Claude';

COMMENT ON TABLE projects IS 'Project definitions with privacy controls and knowledge sharing configuration';
COMMENT ON TABLE users IS 'User profiles with preferences and behavioral patterns for personalized memory';
COMMENT ON TABLE sessions IS 'Claude interaction sessions with context and outcome tracking';
COMMENT ON TABLE messages IS 'Individual conversation messages with tool usage and analysis';
COMMENT ON TABLE knowledge_items IS 'Core knowledge storage with rich metadata and temporal validity';
COMMENT ON TABLE knowledge_relationships IS 'Explicit relationships between knowledge items with strength scoring';
COMMENT ON TABLE tool_usage IS 'Complete audit trail of Claude Code tool usage for knowledge capture';
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all system actions and changes';
COMMENT ON TABLE system_metrics IS 'Performance and usage metrics for system monitoring and optimization';

-- Schema version tracking
CREATE TABLE schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial BETTY Memory System schema with full Graphiti integration support');

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'BETTY Memory System PostgreSQL Schema Initialized Successfully';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Database: betty_memory';
    RAISE NOTICE 'Schema Version: 1.0.0';
    RAISE NOTICE 'Tables Created: 9 core tables + 2 views';
    RAISE NOTICE 'Indexes Created: 50+ performance indexes';
    RAISE NOTICE 'Features: Full-text search, temporal tracking, audit logging';
    RAISE NOTICE 'Integration: Neo4j/Graphiti, Qdrant vectors, Redis caching';
    RAISE NOTICE '============================================================';
END $$;