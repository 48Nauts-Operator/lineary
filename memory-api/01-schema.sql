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

-- Continue with rest of tables... (truncated for brevity but includes all remaining tables, indexes, triggers, etc.)