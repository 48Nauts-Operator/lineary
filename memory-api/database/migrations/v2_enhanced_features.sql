-- BETTY Memory System v2.0 Database Migration
-- Enhanced features: batch operations, cross-project intelligence, advanced analytics

-- Create batch operations table for tracking long-running operations
CREATE TABLE IF NOT EXISTS batch_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    user_id UUID NOT NULL,
    
    -- Progress tracking
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4),
    
    -- Timing information
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    estimated_completion TIMESTAMP WITH TIME ZONE,
    
    -- Operation data
    request_data JSONB DEFAULT '{}',
    result_data JSONB,
    error_details JSONB,
    
    -- Configuration
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    CONSTRAINT batch_operations_status_check 
        CHECK (status IN ('queued', 'running', 'paused', 'completed', 'failed', 'cancelled')),
    CONSTRAINT batch_operations_type_check
        CHECK (operation_type IN ('knowledge_import', 'knowledge_export', 'session_merge', 
                                 'project_migration', 'vector_recompute', 'analytics_generation', 'cleanup'))
);

-- Create indexes for batch operations
CREATE INDEX IF NOT EXISTS idx_batch_operations_user_status ON batch_operations(user_id, status);
CREATE INDEX IF NOT EXISTS idx_batch_operations_type_created ON batch_operations(operation_type, created_at);
CREATE INDEX IF NOT EXISTS idx_batch_operations_status_priority ON batch_operations(status, priority DESC);

-- Create project connections table for cross-project intelligence
CREATE TABLE IF NOT EXISTS project_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_project_id UUID NOT NULL,
    target_project_id UUID NOT NULL,
    connection_type VARCHAR(30) NOT NULL,
    
    -- Access control
    permissions JSONB DEFAULT '{}',
    sharing_rules JSONB DEFAULT '{}',
    
    -- Connection metadata
    connection_strength DECIMAL(3,2) DEFAULT 1.0 CHECK (connection_strength BETWEEN 0 AND 1),
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    
    -- Status and tracking
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    
    CONSTRAINT project_connections_type_check
        CHECK (connection_type IN ('bidirectional', 'unidirectional', 'hierarchical', 'collaborative')),
    CONSTRAINT project_connections_unique_pair
        UNIQUE (source_project_id, target_project_id)
);

-- Create indexes for project connections
CREATE INDEX IF NOT EXISTS idx_project_connections_source ON project_connections(source_project_id);
CREATE INDEX IF NOT EXISTS idx_project_connections_target ON project_connections(target_project_id);
CREATE INDEX IF NOT EXISTS idx_project_connections_type ON project_connections(connection_type);
CREATE INDEX IF NOT EXISTS idx_project_connections_active ON project_connections(is_active, created_at);

-- Create knowledge transfer log table
CREATE TABLE IF NOT EXISTS knowledge_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_project_id UUID NOT NULL,
    target_project_id UUID NOT NULL,
    knowledge_item_id UUID NOT NULL,
    transfer_strategy VARCHAR(20) NOT NULL,
    
    -- Transfer metadata
    transfer_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    conflict_resolution VARCHAR(20),
    transformation_applied JSONB DEFAULT '{}',
    
    -- Tracking
    initiated_by UUID NOT NULL,
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    success BOOLEAN,
    error_message TEXT,
    new_item_id UUID, -- ID in target project
    
    CONSTRAINT knowledge_transfers_strategy_check
        CHECK (transfer_strategy IN ('copy', 'move', 'link', 'sync')),
    CONSTRAINT knowledge_transfers_status_check
        CHECK (transfer_status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled'))
);

-- Create indexes for knowledge transfers
CREATE INDEX IF NOT EXISTS idx_knowledge_transfers_source ON knowledge_transfers(source_project_id, initiated_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_transfers_target ON knowledge_transfers(target_project_id, initiated_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_transfers_item ON knowledge_transfers(knowledge_item_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_transfers_status ON knowledge_transfers(transfer_status, initiated_at);

-- Create pattern templates table for pattern sharing
CREATE TABLE IF NOT EXISTS pattern_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_project_id UUID NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(200) NOT NULL,
    
    -- Pattern definition
    pattern_definition JSONB NOT NULL,
    pattern_metadata JSONB DEFAULT '{}',
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2),
    
    -- Lifecycle
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Classification
    tags TEXT[] DEFAULT '{}',
    category VARCHAR(100),
    complexity_level INTEGER CHECK (complexity_level BETWEEN 1 AND 5)
);

-- Create indexes for pattern templates
CREATE INDEX IF NOT EXISTS idx_pattern_templates_project ON pattern_templates(source_project_id);
CREATE INDEX IF NOT EXISTS idx_pattern_templates_type ON pattern_templates(pattern_type);
CREATE INDEX IF NOT EXISTS idx_pattern_templates_category ON pattern_templates(category);
CREATE INDEX IF NOT EXISTS idx_pattern_templates_active ON pattern_templates(is_active, created_at);
CREATE INDEX IF NOT EXISTS idx_pattern_templates_usage ON pattern_templates(usage_count DESC);

-- Create pattern applications table for tracking pattern usage
CREATE TABLE IF NOT EXISTS pattern_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_template_id UUID NOT NULL REFERENCES pattern_templates(id),
    target_project_id UUID NOT NULL,
    applied_by UUID NOT NULL,
    
    -- Application details
    application_context JSONB DEFAULT '{}',
    adaptation_rules JSONB DEFAULT '{}',
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Results
    success BOOLEAN NOT NULL,
    impact_metrics JSONB DEFAULT '{}',
    feedback_score DECIMAL(3,2) CHECK (feedback_score BETWEEN 1 AND 5),
    notes TEXT
);

-- Create indexes for pattern applications
CREATE INDEX IF NOT EXISTS idx_pattern_applications_template ON pattern_applications(pattern_template_id);
CREATE INDEX IF NOT EXISTS idx_pattern_applications_project ON pattern_applications(target_project_id);
CREATE INDEX IF NOT EXISTS idx_pattern_applications_success ON pattern_applications(success, applied_at);

-- Create advanced analytics cache table for performance optimization
CREATE TABLE IF NOT EXISTS analytics_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(500) NOT NULL UNIQUE,
    metric_name VARCHAR(100) NOT NULL,
    
    -- Cache scope
    project_ids UUID[],
    user_ids UUID[],
    time_range_start TIMESTAMP WITH TIME ZONE,
    time_range_end TIMESTAMP WITH TIME ZONE,
    
    -- Cache data
    cached_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    
    -- Cache lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for analytics cache
CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_metric ON analytics_cache(metric_name);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires ON analytics_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_projects ON analytics_cache USING GIN(project_ids);

-- Create similarity matrices table for caching computed similarities
CREATE TABLE IF NOT EXISTS similarity_matrices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matrix_type VARCHAR(50) NOT NULL,
    similarity_metric VARCHAR(50) NOT NULL,
    
    -- Scope definition
    scope_filter JSONB NOT NULL,
    item_ids UUID[] NOT NULL,
    
    -- Matrix data (stored as compressed JSON)
    matrix_data JSONB NOT NULL,
    matrix_metadata JSONB DEFAULT '{}',
    dimensions INTEGER[] NOT NULL, -- [rows, cols]
    
    -- Matrix properties
    is_sparse BOOLEAN DEFAULT FALSE,
    threshold_applied DECIMAL(3,2),
    compression_ratio DECIMAL(5,2),
    
    -- Lifecycle
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    computation_time_ms INTEGER,
    
    CONSTRAINT similarity_matrices_type_check
        CHECK (matrix_type IN ('content', 'semantic', 'structural', 'behavioral', 'hybrid'))
);

-- Create indexes for similarity matrices  
CREATE INDEX IF NOT EXISTS idx_similarity_matrices_type ON similarity_matrices(matrix_type, similarity_metric);
CREATE INDEX IF NOT EXISTS idx_similarity_matrices_expires ON similarity_matrices(expires_at);
CREATE INDEX IF NOT EXISTS idx_similarity_matrices_computed ON similarity_matrices(computed_at);

-- Create knowledge clusters table for storing clustering results
CREATE TABLE IF NOT EXISTS knowledge_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clustering_algorithm VARCHAR(50) NOT NULL,
    
    -- Clustering parameters
    parameters JSONB NOT NULL,
    scope_filter JSONB NOT NULL,
    
    -- Cluster data
    cluster_data JSONB NOT NULL,
    cluster_count INTEGER NOT NULL,
    silhouette_score DECIMAL(4,3), -- Quality metric
    
    -- Items in clusters
    item_assignments JSONB NOT NULL, -- {item_id: cluster_id}
    cluster_metadata JSONB DEFAULT '{}',
    
    -- Lifecycle
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    computation_time_ms INTEGER,
    
    CONSTRAINT knowledge_clusters_algorithm_check
        CHECK (clustering_algorithm IN ('kmeans', 'hierarchical', 'dbscan', 'spectral', 'gaussian_mixture'))
);

-- Create indexes for knowledge clusters
CREATE INDEX IF NOT EXISTS idx_knowledge_clusters_algorithm ON knowledge_clusters(clustering_algorithm);
CREATE INDEX IF NOT EXISTS idx_knowledge_clusters_computed ON knowledge_clusters(computed_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_clusters_expires ON knowledge_clusters(expires_at);

-- Add new columns to existing knowledge_items table for v2 features
ALTER TABLE knowledge_items 
    ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100),
    ADD COLUMN IF NOT EXISTS embedding_version VARCHAR(20),
    ADD COLUMN IF NOT EXISTS quality_score DECIMAL(3,2) CHECK (quality_score BETWEEN 0 AND 1),
    ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'processed',
    ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0;

-- Create indexes for new knowledge_items columns
CREATE INDEX IF NOT EXISTS idx_knowledge_items_embedding_model ON knowledge_items(embedding_model);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_quality ON knowledge_items(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_processing_status ON knowledge_items(processing_status);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_last_accessed ON knowledge_items(last_accessed DESC);

-- Add new columns to existing sessions table for enhanced session management
ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS session_type VARCHAR(50) DEFAULT 'chat',
    ADD COLUMN IF NOT EXISTS merge_source_sessions UUID[],
    ADD COLUMN IF NOT EXISTS quality_metrics JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS topic_distribution JSONB DEFAULT '{}';

-- Create indexes for new sessions columns
CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_sessions_merge_sources ON sessions USING GIN(merge_source_sessions);

-- Create time series analytics table for temporal analysis
CREATE TABLE IF NOT EXISTS time_series_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    granularity VARCHAR(20) NOT NULL, -- 'hour', 'day', 'week', 'month'
    
    -- Scope
    project_id UUID,
    user_id UUID,
    
    -- Metric values
    value DECIMAL(15,4) NOT NULL,
    count INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    
    -- Aggregation info
    aggregation_type VARCHAR(20) DEFAULT 'sum', -- 'sum', 'avg', 'count', 'min', 'max'
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT time_series_granularity_check
        CHECK (granularity IN ('hour', 'day', 'week', 'month')),
    CONSTRAINT time_series_aggregation_check
        CHECK (aggregation_type IN ('sum', 'avg', 'count', 'min', 'max'))
);

-- Create indexes for time series analytics
CREATE INDEX IF NOT EXISTS idx_time_series_metric_bucket ON time_series_analytics(metric_name, time_bucket);
CREATE INDEX IF NOT EXISTS idx_time_series_project_time ON time_series_analytics(project_id, time_bucket);
CREATE INDEX IF NOT EXISTS idx_time_series_user_time ON time_series_analytics(user_id, time_bucket);
CREATE INDEX IF NOT EXISTS idx_time_series_granularity ON time_series_analytics(granularity, time_bucket);

-- Create performance monitoring table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    
    -- Performance data
    response_time_ms INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    user_id UUID,
    
    -- Request details
    request_size INTEGER,
    response_size INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    date DATE GENERATED ALWAYS AS (DATE(timestamp)) STORED,
    
    -- Additional context
    api_version VARCHAR(10),
    features_used TEXT[] DEFAULT '{}'
);

-- Create indexes for performance metrics
CREATE INDEX IF NOT EXISTS idx_performance_metrics_endpoint ON performance_metrics(endpoint, timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_response_time ON performance_metrics(response_time_ms);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_user ON performance_metrics(user_id, timestamp);

-- Create triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add update triggers to relevant tables
CREATE TRIGGER batch_operations_updated_at
    BEFORE UPDATE ON batch_operations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER project_connections_updated_at
    BEFORE UPDATE ON project_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER pattern_templates_updated_at
    BEFORE UPDATE ON pattern_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Create function for cleaning up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up expired analytics cache
    DELETE FROM analytics_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up expired similarity matrices
    DELETE FROM similarity_matrices WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    -- Clean up expired knowledge clusters
    DELETE FROM knowledge_clusters WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create materialized views for common analytics queries
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_activity_summary AS
SELECT 
    DATE(created_at) as activity_date,
    COUNT(*) as total_items,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(DISTINCT project_id) as active_projects,
    AVG(CASE WHEN quality_score IS NOT NULL THEN quality_score END) as avg_quality_score
FROM knowledge_items 
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(created_at)
ORDER BY activity_date DESC;

-- Create indexes on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_activity_date ON mv_daily_activity_summary(activity_date);

-- Create materialized view for project connection analytics  
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_project_connection_stats AS
SELECT 
    source_project_id as project_id,
    COUNT(*) as outbound_connections,
    AVG(connection_strength) as avg_connection_strength,
    SUM(usage_count) as total_usage,
    MAX(last_used) as last_connection_used
FROM project_connections 
WHERE is_active = TRUE
GROUP BY source_project_id
UNION ALL
SELECT 
    target_project_id as project_id,
    COUNT(*) as inbound_connections,
    AVG(connection_strength) as avg_connection_strength,
    SUM(usage_count) as total_usage,
    MAX(last_used) as last_connection_used  
FROM project_connections
WHERE is_active = TRUE
GROUP BY target_project_id;

-- Add comments for documentation
COMMENT ON TABLE batch_operations IS 'Tracks long-running batch operations with progress monitoring';
COMMENT ON TABLE project_connections IS 'Defines connections between projects for knowledge sharing';
COMMENT ON TABLE knowledge_transfers IS 'Logs knowledge transfer operations between projects';
COMMENT ON TABLE pattern_templates IS 'Stores reusable patterns for cross-project sharing';
COMMENT ON TABLE analytics_cache IS 'Caches computed analytics results for performance';
COMMENT ON TABLE similarity_matrices IS 'Stores computed similarity matrices for knowledge items';
COMMENT ON TABLE knowledge_clusters IS 'Stores clustering results for knowledge organization';
COMMENT ON TABLE time_series_analytics IS 'Stores time-series metrics for temporal analysis';
COMMENT ON TABLE performance_metrics IS 'Tracks API performance metrics for monitoring';

-- Update database version
INSERT INTO schema_migrations (version, applied_at) 
VALUES ('v2.0.0_enhanced_features', NOW())
ON CONFLICT (version) DO NOTHING;