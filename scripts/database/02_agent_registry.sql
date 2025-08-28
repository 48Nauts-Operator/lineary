-- ABOUTME: SQL schema for BETTY Multi-Agent Registration System
-- ABOUTME: Creates tables for agent registration, credentials, configurations, and monitoring

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent types enumeration
CREATE TYPE agent_type AS ENUM ('api_based', 'local_process', 'custom');
CREATE TYPE agent_status AS ENUM ('active', 'inactive', 'failed', 'rate_limited');
CREATE TYPE credential_type AS ENUM ('api_key', 'oauth_token', 'certificate', 'custom');

-- Main agent registry table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    agent_type agent_type NOT NULL,
    provider VARCHAR(100) NOT NULL, -- 'claude', 'openai', 'gemini', 'devon', 'custom'
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',
    status agent_status DEFAULT 'inactive',
    capabilities JSONB NOT NULL DEFAULT '[]', -- Array of capability strings
    config JSONB NOT NULL DEFAULT '{}', -- Provider-specific configuration
    metadata JSONB DEFAULT '{}', -- Additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_status VARCHAR(50) DEFAULT 'unknown'
);

-- Agent credentials table (encrypted references to Vault)
CREATE TABLE agent_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    credential_type credential_type NOT NULL,
    vault_path VARCHAR(500) NOT NULL, -- Path in HashiCorp Vault
    vault_key VARCHAR(255) NOT NULL, -- Key within the Vault secret
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_id, credential_type, vault_key)
);

-- Agent configurations for different environments
CREATE TABLE agent_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    environment VARCHAR(50) NOT NULL DEFAULT 'production', -- 'development', 'staging', 'production'
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL,
    is_sensitive BOOLEAN DEFAULT false, -- If true, store in Vault
    vault_path VARCHAR(500), -- Path in Vault if is_sensitive = true
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_id, environment, config_key)
);

-- Rate limiting and cost tracking
CREATE TABLE agent_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    session_id UUID, -- Link to chat sessions if applicable
    request_count INTEGER DEFAULT 0,
    token_usage JSONB DEFAULT '{}', -- {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    cost_cents INTEGER DEFAULT 0, -- Cost in cents
    rate_limit_hits INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_date DATE DEFAULT CURRENT_DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_id, created_date)
);

-- Agent health monitoring
CREATE TABLE agent_health_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    status agent_status NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    health_data JSONB DEFAULT '{}', -- Additional health metrics
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX(agent_id, checked_at)
);

-- Local process management (for Devon AI, etc.)
CREATE TABLE local_processes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    process_id INTEGER, -- System PID
    container_id VARCHAR(255), -- Docker container ID if applicable
    port INTEGER, -- Service port
    working_directory VARCHAR(500),
    command_line TEXT,
    environment_vars JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'stopped', -- 'running', 'stopped', 'failed', 'starting'
    started_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE,
    restart_count INTEGER DEFAULT 0,
    max_restarts INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_id)
);

-- Agent capabilities definitions
CREATE TABLE capabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL, -- 'coding', 'analysis', 'writing', 'search', etc.
    description TEXT,
    parameters JSONB DEFAULT '{}', -- Expected parameters for this capability
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Junction table for agent-capability relationships
CREATE TABLE agent_capabilities (
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    capability_id UUID NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 1, -- 1-10, higher = better at this capability
    config JSONB DEFAULT '{}', -- Capability-specific configuration
    PRIMARY KEY (agent_id, capability_id)
);

-- Indexes for performance
CREATE INDEX idx_agents_provider ON agents(provider);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agent_usage_date ON agent_usage(created_date);
CREATE INDEX idx_agent_health_logs_checked_at ON agent_health_logs(checked_at);
CREATE INDEX idx_capabilities_category ON capabilities(category);

-- Update timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_credentials_updated_at BEFORE UPDATE ON agent_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_configurations_updated_at BEFORE UPDATE ON agent_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_usage_updated_at BEFORE UPDATE ON agent_usage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_local_processes_updated_at BEFORE UPDATE ON local_processes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default capabilities
INSERT INTO capabilities (name, category, description, parameters) VALUES
('code_analysis', 'coding', 'Analyze and review code for bugs, performance, and best practices', '{"languages": ["python", "javascript", "typescript"], "max_files": 50}'),
('code_generation', 'coding', 'Generate code based on specifications and requirements', '{"languages": ["python", "javascript", "typescript"], "frameworks": []}'),
('debugging', 'coding', 'Debug issues and provide solutions for code problems', '{"languages": ["python", "javascript", "typescript"], "error_types": []}'),
('test_writing', 'coding', 'Write comprehensive unit, integration, and end-to-end tests', '{"test_frameworks": ["pytest", "jest", "cypress"], "coverage_target": 80}'),
('security_audit', 'security', 'Perform security audits and vulnerability assessments', '{"scan_types": ["static", "dynamic"], "compliance_standards": []}'),
('performance_optimization', 'analysis', 'Optimize system performance and identify bottlenecks', '{"metrics": ["response_time", "throughput", "memory_usage"], "tools": []}'),
('documentation', 'writing', 'Generate technical documentation and user guides', '{"formats": ["markdown", "rst", "html"], "audience": ["technical", "end_user"]}'),
('data_analysis', 'analysis', 'Analyze data patterns and generate insights', '{"data_types": ["csv", "json", "sql"], "visualization": true}'),
('api_design', 'architecture', 'Design RESTful APIs and GraphQL schemas', '{"standards": ["openapi", "graphql"], "authentication": []}'),
('system_monitoring', 'operations', 'Monitor system health and performance metrics', '{"platforms": ["docker", "kubernetes"], "metrics": []}')