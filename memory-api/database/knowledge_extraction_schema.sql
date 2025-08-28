-- ABOUTME: Database schema for Multi-Source Knowledge Extraction Pipeline
-- ABOUTME: Tables for extraction tracking, processing pipeline, and real-time updates

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- EXTRACTION TRACKING TABLES
-- =====================================================

-- Table for tracking extraction statistics and results
CREATE TABLE IF NOT EXISTS extraction_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    total_extracted INTEGER NOT NULL DEFAULT 0,
    total_processed INTEGER NOT NULL DEFAULT 0,
    total_stored INTEGER NOT NULL DEFAULT 0,
    sources_active INTEGER NOT NULL DEFAULT 0,
    extraction_results JSONB,
    processing_time FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_extraction_stats_timestamp ON extraction_stats(timestamp);

-- Table for source configuration and status tracking
CREATE TABLE IF NOT EXISTS source_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'api', 'rss', 'scraping', etc.
    base_url TEXT,
    enabled BOOLEAN DEFAULT true,
    rate_limit FLOAT DEFAULT 1.0,
    timeout FLOAT DEFAULT 30.0,
    quality_weight FLOAT DEFAULT 1.0,
    last_extraction TIMESTAMP WITH TIME ZONE,
    consecutive_failures INTEGER DEFAULT 0,
    configuration JSONB, -- Flexible config storage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for source lookups
CREATE INDEX IF NOT EXISTS idx_source_configurations_name ON source_configurations(source_name);
CREATE INDEX IF NOT EXISTS idx_source_configurations_enabled ON source_configurations(enabled);

-- =====================================================
-- PROCESSING PIPELINE TABLES
-- =====================================================

-- Table for tracking processing tasks
CREATE TABLE IF NOT EXISTS processing_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES knowledge_items(id),
    processing_stage VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 0,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time FLOAT,
    classification JSONB,
    quality_scores JSONB,
    conflicts_detected TEXT[],
    conflicts_resolved BOOLEAN DEFAULT false,
    errors TEXT[],
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'pending' -- 'pending', 'processing', 'completed', 'failed'
);

-- Indexes for processing task queries
CREATE INDEX IF NOT EXISTS idx_processing_tasks_item_id ON processing_tasks(item_id);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_status ON processing_tasks(status);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_stage ON processing_tasks(processing_stage);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_submitted ON processing_tasks(submitted_at);

-- Table for conflict resolution records
CREATE TABLE IF NOT EXISTS conflict_resolutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conflict_type VARCHAR(50) NOT NULL,
    conflicting_items UUID[],
    resolution_strategy VARCHAR(100) NOT NULL,
    chosen_item UUID,
    confidence FLOAT,
    reasoning TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolver_version VARCHAR(20),
    metadata JSONB
);

-- Index for conflict analysis
CREATE INDEX IF NOT EXISTS idx_conflict_resolutions_type ON conflict_resolutions(conflict_type);
CREATE INDEX IF NOT EXISTS idx_conflict_resolutions_resolved ON conflict_resolutions(resolved_at);

-- =====================================================
-- REAL-TIME UPDATE TABLES
-- =====================================================

-- Table for tracking real-time update events
CREATE TABLE IF NOT EXISTS update_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL,
    update_type VARCHAR(50) NOT NULL, -- 'new_content', 'content_modified', etc.
    item_id UUID REFERENCES knowledge_items(id),
    source_url TEXT,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_result JSONB,
    conflicts TEXT[],
    metadata JSONB
);

-- Indexes for update tracking
CREATE INDEX IF NOT EXISTS idx_update_events_source ON update_events(source_name);
CREATE INDEX IF NOT EXISTS idx_update_events_type ON update_events(update_type);
CREATE INDEX IF NOT EXISTS idx_update_events_detected ON update_events(detected_at);
CREATE INDEX IF NOT EXISTS idx_update_events_processed ON update_events(processed);

-- Table for monitoring source status
CREATE TABLE IF NOT EXISTS source_monitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) UNIQUE NOT NULL,
    monitor_type VARCHAR(50) NOT NULL, -- 'api_polling', 'rss', 'scraping', 'webhook'
    check_interval FLOAT NOT NULL, -- seconds
    last_check TIMESTAMP WITH TIME ZONE,
    last_update TIMESTAMP WITH TIME ZONE,
    consecutive_failures INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT true,
    configuration JSONB,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'error'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for monitor management
CREATE INDEX IF NOT EXISTS idx_source_monitors_name ON source_monitors(source_name);
CREATE INDEX IF NOT EXISTS idx_source_monitors_enabled ON source_monitors(enabled);

-- Table for real-time conflict tracking
CREATE TABLE IF NOT EXISTS realtime_conflicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES knowledge_items(id),
    conflict_type VARCHAR(50) NOT NULL,
    conflicts TEXT[],
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolution_strategy VARCHAR(100),
    resolution_details JSONB,
    auto_resolved BOOLEAN DEFAULT true
);

-- Index for conflict analysis
CREATE INDEX IF NOT EXISTS idx_realtime_conflicts_item ON realtime_conflicts(item_id);
CREATE INDEX IF NOT EXISTS idx_realtime_conflicts_type ON realtime_conflicts(conflict_type);

-- =====================================================
-- ENHANCED KNOWLEDGE ITEMS TABLE UPDATES
-- =====================================================

-- Add new columns to existing knowledge_items table if they don't exist
DO $$
BEGIN
    -- Add status column for item lifecycle management
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'knowledge_items' AND column_name = 'status') THEN
        ALTER TABLE knowledge_items ADD COLUMN status VARCHAR(20) DEFAULT 'active';
        CREATE INDEX IF NOT EXISTS idx_knowledge_items_status ON knowledge_items(status);
    END IF;
    
    -- Add canonical_id for duplicate resolution
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'knowledge_items' AND column_name = 'canonical_id') THEN
        ALTER TABLE knowledge_items ADD COLUMN canonical_id UUID REFERENCES knowledge_items(id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_items_canonical ON knowledge_items(canonical_id);
    END IF;
    
    -- Add quality_score column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'knowledge_items' AND column_name = 'quality_score') THEN
        ALTER TABLE knowledge_items ADD COLUMN quality_score FLOAT DEFAULT 0.0;
        CREATE INDEX IF NOT EXISTS idx_knowledge_items_quality ON knowledge_items(quality_score);
    END IF;
    
    -- Add access_count for usage tracking
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'knowledge_items' AND column_name = 'access_count') THEN
        ALTER TABLE knowledge_items ADD COLUMN access_count INTEGER DEFAULT 0;
    END IF;
    
    -- Add last_accessed timestamp
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'knowledge_items' AND column_name = 'last_accessed') THEN
        ALTER TABLE knowledge_items ADD COLUMN last_accessed TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Add processing_version to track which version of the pipeline processed the item
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'knowledge_items' AND column_name = 'processing_version') THEN
        ALTER TABLE knowledge_items ADD COLUMN processing_version VARCHAR(20);
    END IF;
END
$$;

-- =====================================================
-- PATTERN RELATIONSHIPS TABLE UPDATES
-- =====================================================

-- Table for cross-source pattern relationships
CREATE TABLE IF NOT EXISTS cross_source_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_item_id UUID NOT NULL REFERENCES knowledge_items(id),
    to_item_id UUID NOT NULL REFERENCES knowledge_items(id),
    relationship_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    evidence TEXT[],
    detected_by VARCHAR(50), -- 'extraction_pipeline', 'pattern_intelligence', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated BOOLEAN DEFAULT false,
    validation_score FLOAT
);

-- Indexes for relationship queries
CREATE INDEX IF NOT EXISTS idx_cross_source_relationships_from ON cross_source_relationships(from_item_id);
CREATE INDEX IF NOT EXISTS idx_cross_source_relationships_to ON cross_source_relationships(to_item_id);
CREATE INDEX IF NOT EXISTS idx_cross_source_relationships_type ON cross_source_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_cross_source_relationships_confidence ON cross_source_relationships(confidence);

-- Unique constraint to prevent duplicate relationships
ALTER TABLE cross_source_relationships 
ADD CONSTRAINT unique_cross_source_relationship 
UNIQUE (from_item_id, to_item_id, relationship_type);

-- =====================================================
-- ANALYTICS AND PERFORMANCE TABLES
-- =====================================================

-- Table for tracking extraction performance metrics
CREATE TABLE IF NOT EXISTS extraction_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL,
    extraction_date DATE NOT NULL,
    items_attempted INTEGER DEFAULT 0,
    items_successful INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    average_quality FLOAT DEFAULT 0.0,
    processing_time FLOAT DEFAULT 0.0,
    error_rate FLOAT DEFAULT 0.0,
    throughput FLOAT DEFAULT 0.0, -- items per second
    metadata JSONB
);

-- Indexes for performance analysis
CREATE INDEX IF NOT EXISTS idx_extraction_performance_source ON extraction_performance(source_name);
CREATE INDEX IF NOT EXISTS idx_extraction_performance_date ON extraction_performance(extraction_date);

-- Table for quality score trending
CREATE TABLE IF NOT EXISTS quality_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    source_type VARCHAR(100),
    domain VARCHAR(100),
    average_quality FLOAT NOT NULL,
    median_quality FLOAT NOT NULL,
    quality_std_dev FLOAT,
    sample_size INTEGER NOT NULL,
    quality_distribution JSONB -- histogram data
);

-- Indexes for quality analysis
CREATE INDEX IF NOT EXISTS idx_quality_trends_date ON quality_trends(date);
CREATE INDEX IF NOT EXISTS idx_quality_trends_source ON quality_trends(source_type);
CREATE INDEX IF NOT EXISTS idx_quality_trends_domain ON quality_trends(domain);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
DROP TRIGGER IF EXISTS update_source_configurations_updated_at ON source_configurations;
CREATE TRIGGER update_source_configurations_updated_at 
    BEFORE UPDATE ON source_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_source_monitors_updated_at ON source_monitors;
CREATE TRIGGER update_source_monitors_updated_at 
    BEFORE UPDATE ON source_monitors 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically update access count and last accessed
CREATE OR REPLACE FUNCTION update_knowledge_access()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.access_count IS DISTINCT FROM OLD.access_count THEN
        NEW.last_accessed = NOW();
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for knowledge item access tracking
DROP TRIGGER IF EXISTS update_knowledge_access_trigger ON knowledge_items;
CREATE TRIGGER update_knowledge_access_trigger 
    BEFORE UPDATE ON knowledge_items 
    FOR EACH ROW EXECUTE FUNCTION update_knowledge_access();

-- =====================================================
-- VIEWS FOR ANALYTICS
-- =====================================================

-- View for extraction summary statistics
CREATE OR REPLACE VIEW extraction_summary AS
SELECT 
    source_name,
    COUNT(*) as total_extractions,
    SUM(total_extracted) as total_items_found,
    SUM(total_stored) as total_items_stored,
    AVG(total_stored::float / NULLIF(total_extracted, 0)) as storage_rate,
    MAX(timestamp) as last_extraction,
    AVG(processing_time) as avg_processing_time
FROM extraction_stats 
GROUP BY source_name;

-- View for quality score distribution
CREATE OR REPLACE VIEW quality_score_distribution AS
SELECT 
    source_type,
    COUNT(*) as total_items,
    AVG(quality_score) as avg_quality,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY quality_score) as median_quality,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY quality_score) as q1_quality,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY quality_score) as q3_quality,
    MIN(quality_score) as min_quality,
    MAX(quality_score) as max_quality
FROM knowledge_items 
WHERE quality_score IS NOT NULL
GROUP BY source_type;

-- View for processing pipeline performance
CREATE OR REPLACE VIEW processing_performance AS
SELECT 
    processing_stage,
    status,
    COUNT(*) as task_count,
    AVG(processing_time) as avg_processing_time,
    MIN(processing_time) as min_processing_time,
    MAX(processing_time) as max_processing_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time) as p95_processing_time
FROM processing_tasks 
WHERE processing_time IS NOT NULL
GROUP BY processing_stage, status;

-- View for real-time update activity
CREATE OR REPLACE VIEW update_activity_summary AS
SELECT 
    source_name,
    update_type,
    COUNT(*) as event_count,
    COUNT(CASE WHEN processed THEN 1 END) as processed_count,
    AVG(CASE WHEN processed AND processed_at IS NOT NULL 
             THEN EXTRACT(EPOCH FROM (processed_at - detected_at))
             ELSE NULL END) as avg_processing_delay
FROM update_events 
WHERE detected_at >= NOW() - INTERVAL '24 hours'
GROUP BY source_name, update_type;

-- =====================================================
-- INITIAL DATA AND CONFIGURATION
-- =====================================================

-- Insert initial source configurations
INSERT INTO source_configurations (source_name, source_type, base_url, enabled, rate_limit, quality_weight, configuration)
VALUES 
    ('stackoverflow', 'api', 'https://api.stackexchange.com/2.3', true, 0.33, 0.9, '{"site": "stackoverflow", "filter": "withbody"}'),
    ('commandlinefu', 'rss', 'https://www.commandlinefu.com', true, 0.5, 0.8, '{"feed_url": "https://www.commandlinefu.com/commands/browse/rss"}'),
    ('exploitdb', 'scraping', 'https://www.exploit-db.com', true, 0.2, 0.95, '{"search_endpoint": "/search?type=webapps"}'),
    ('hacktricks', 'scraping', 'https://book.hacktricks.xyz', true, 0.3, 0.85, '{"sections": ["pentesting-web", "linux-hardening"]}'),
    ('owasp', 'scraping', 'https://owasp.org', true, 0.5, 0.95, '{"resources": ["www-project-top-ten", "www-project-web-security-testing-guide"]}'),
    ('kubernetes', 'api', 'https://kubernetes.io/docs', true, 1.0, 0.9, '{"context7_integration": true}'),
    ('terraform', 'api', 'https://registry.terraform.io/v1', true, 0.5, 0.85, '{"modules_endpoint": "/modules", "providers_endpoint": "/providers"}'),
    ('hashicorp', 'api', 'https://discuss.hashicorp.com', true, 0.5, 0.8, '{"categories": ["terraform", "vault", "consul", "nomad", "packer"]}')
ON CONFLICT (source_name) DO NOTHING;

-- Insert initial source monitors
INSERT INTO source_monitors (source_name, monitor_type, check_interval, enabled, configuration)
VALUES 
    ('stackoverflow', 'api_polling', 300, true, '{"endpoint": "/questions", "params": {"sort": "activity", "order": "desc"}}'),
    ('commandlinefu', 'rss', 600, true, '{"feed_url": "https://www.commandlinefu.com/commands/browse/rss"}'),
    ('exploitdb', 'scraping', 3600, true, '{"check_interval": 3600, "content_hash": true}'),
    ('hacktricks', 'scraping', 1800, true, '{"sections": ["pentesting-web", "linux-hardening"], "content_hash": true}'),
    ('owasp', 'scraping', 1800, true, '{"resources": ["www-project-top-ten"], "content_hash": true}'),
    ('terraform', 'api_polling', 900, true, '{"endpoint": "/modules", "params": {"limit": 100}}'),
    ('hashicorp', 'api_polling', 900, true, '{"categories": ["terraform", "vault", "consul"]}')