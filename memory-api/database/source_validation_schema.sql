-- ABOUTME: Database schema for Source Validation & Verification System
-- ABOUTME: Comprehensive tables for validation results, audit trails, and compliance tracking

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Source validations table - stores validation results for each knowledge item
CREATE TABLE IF NOT EXISTS source_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    validation_id VARCHAR(255) UNIQUE NOT NULL,
    item_id UUID NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'validating', 'validated', 'failed', 'quarantined')),
    
    -- Validation scores (0.0 to 1.0)
    credibility_score DECIMAL(3,2) DEFAULT 0.0 CHECK (credibility_score >= 0.0 AND credibility_score <= 1.0),
    accuracy_score DECIMAL(3,2) DEFAULT 0.0 CHECK (accuracy_score >= 0.0 AND accuracy_score <= 1.0),
    security_score DECIMAL(3,2) DEFAULT 0.0 CHECK (security_score >= 0.0 AND security_score <= 1.0),
    freshness_score DECIMAL(3,2) DEFAULT 0.0 CHECK (freshness_score >= 0.0 AND freshness_score <= 1.0),
    overall_score DECIMAL(3,2) DEFAULT 0.0 CHECK (overall_score >= 0.0 AND overall_score <= 1.0),
    
    -- Performance metrics
    validation_time DECIMAL(10,6) DEFAULT 0.0,
    
    -- Validation details
    issues JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- Audit fields
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    validated_by VARCHAR(255) DEFAULT 'system',
    validation_version VARCHAR(50) DEFAULT '1.0',
    
    -- Indexes for performance
    CONSTRAINT fk_validation_item FOREIGN KEY (item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_source_validations_item_id ON source_validations(item_id);
CREATE INDEX IF NOT EXISTS idx_source_validations_source_name ON source_validations(source_name);
CREATE INDEX IF NOT EXISTS idx_source_validations_status ON source_validations(status);
CREATE INDEX IF NOT EXISTS idx_source_validations_timestamp ON source_validations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_source_validations_overall_score ON source_validations(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_source_validations_validation_id ON source_validations(validation_id);

-- GIN index for JSONB fields
CREATE INDEX IF NOT EXISTS idx_source_validations_issues_gin ON source_validations USING GIN(issues);
CREATE INDEX IF NOT EXISTS idx_source_validations_metadata_gin ON source_validations USING GIN(metadata);

-- Source credibility tracking table
CREATE TABLE IF NOT EXISTS source_credibility (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) UNIQUE NOT NULL,
    
    -- Credibility metrics
    base_credibility DECIMAL(3,2) DEFAULT 0.5 CHECK (base_credibility >= 0.0 AND base_credibility <= 1.0),
    historical_accuracy DECIMAL(3,2) DEFAULT 0.5 CHECK (historical_accuracy >= 0.0 AND historical_accuracy <= 1.0),
    community_validation DECIMAL(3,2) DEFAULT 0.5 CHECK (community_validation >= 0.0 AND community_validation <= 1.0),
    reputation_score DECIMAL(3,2) DEFAULT 0.5 CHECK (reputation_score >= 0.0 AND reputation_score <= 1.0),
    
    -- Statistics
    total_validations INTEGER DEFAULT 0,
    successful_validations INTEGER DEFAULT 0,
    failed_validations INTEGER DEFAULT 0,
    quarantined_items INTEGER DEFAULT 0,
    
    -- Performance metrics
    avg_validation_time DECIMAL(10,6) DEFAULT 0.0,
    last_validation TIMESTAMPTZ,
    
    -- Metadata
    source_config JSONB DEFAULT '{}',
    trust_indicators JSONB DEFAULT '{}',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_credibility_update TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_source_credibility_source_name ON source_credibility(source_name);
CREATE INDEX IF NOT EXISTS idx_source_credibility_reputation_score ON source_credibility(reputation_score DESC);
CREATE INDEX IF NOT EXISTS idx_source_credibility_updated_at ON source_credibility(updated_at DESC);

-- Security scan results table
CREATE TABLE IF NOT EXISTS security_scan_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    validation_id VARCHAR(255) NOT NULL,
    item_id UUID NOT NULL,
    
    -- Scan results
    is_safe BOOLEAN DEFAULT FALSE,
    risk_level VARCHAR(50) DEFAULT 'unknown' CHECK (risk_level IN ('low', 'medium', 'high', 'critical', 'unknown')),
    scan_time DECIMAL(10,6) DEFAULT 0.0,
    
    -- Threat details
    threats_detected JSONB DEFAULT '[]',
    suspicious_patterns JSONB DEFAULT '[]',
    url_analysis JSONB DEFAULT '{}',
    content_analysis JSONB DEFAULT '{}',
    
    -- Scanner metadata
    scanner_version VARCHAR(50) DEFAULT '1.0',
    scan_timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT fk_security_scan_validation FOREIGN KEY (validation_id) REFERENCES source_validations(validation_id) ON DELETE CASCADE,
    CONSTRAINT fk_security_scan_item FOREIGN KEY (item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_security_scan_validation_id ON security_scan_results(validation_id);
CREATE INDEX IF NOT EXISTS idx_security_scan_item_id ON security_scan_results(item_id);
CREATE INDEX IF NOT EXISTS idx_security_scan_risk_level ON security_scan_results(risk_level);
CREATE INDEX IF NOT EXISTS idx_security_scan_is_safe ON security_scan_results(is_safe);
CREATE INDEX IF NOT EXISTS idx_security_scan_timestamp ON security_scan_results(scan_timestamp DESC);

-- Content duplicate detection table
CREATE TABLE IF NOT EXISTS content_duplicates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    primary_item_id UUID NOT NULL,
    duplicate_item_id UUID NOT NULL,
    similarity_score DECIMAL(3,2) NOT NULL CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),
    
    -- Detection details
    detection_method VARCHAR(100) DEFAULT 'vector_similarity',
    similarity_metrics JSONB DEFAULT '{}',
    content_hash VARCHAR(255),
    
    -- Audit
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    validated_by VARCHAR(255) DEFAULT 'system',
    
    CONSTRAINT fk_duplicate_primary_item FOREIGN KEY (primary_item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE,
    CONSTRAINT fk_duplicate_duplicate_item FOREIGN KEY (duplicate_item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE,
    CONSTRAINT unique_duplicate_pair UNIQUE (primary_item_id, duplicate_item_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_content_duplicates_primary_item ON content_duplicates(primary_item_id);
CREATE INDEX IF NOT EXISTS idx_content_duplicates_duplicate_item ON content_duplicates(duplicate_item_id);
CREATE INDEX IF NOT EXISTS idx_content_duplicates_similarity_score ON content_duplicates(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_content_duplicates_detected_at ON content_duplicates(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_duplicates_content_hash ON content_duplicates(content_hash);

-- Validation audit log table for compliance tracking
CREATE TABLE IF NOT EXISTS validation_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Event identification
    event_type VARCHAR(100) NOT NULL,
    validation_id VARCHAR(255),
    item_id UUID,
    source_name VARCHAR(100),
    
    -- Event details
    event_data JSONB DEFAULT '{}',
    user_id VARCHAR(255),
    user_agent TEXT,
    ip_address INET,
    
    -- Compliance tracking
    gdpr_applicable BOOLEAN DEFAULT FALSE,
    data_retention_category VARCHAR(100) DEFAULT 'operational',
    anonymization_required BOOLEAN DEFAULT FALSE,
    
    -- Audit trail
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    correlation_id VARCHAR(255),
    trace_id VARCHAR(255),
    
    -- System information
    service_version VARCHAR(50) DEFAULT '1.0',
    environment VARCHAR(50) DEFAULT 'production'
);

-- Create indexes for audit log
CREATE INDEX IF NOT EXISTS idx_validation_audit_event_type ON validation_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_validation_audit_timestamp ON validation_audit_log(event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_validation_audit_validation_id ON validation_audit_log(validation_id);
CREATE INDEX IF NOT EXISTS idx_validation_audit_item_id ON validation_audit_log(item_id);
CREATE INDEX IF NOT EXISTS idx_validation_audit_correlation_id ON validation_audit_log(correlation_id);
CREATE INDEX IF NOT EXISTS idx_validation_audit_gdpr ON validation_audit_log(gdpr_applicable);

-- GIN index for audit event data
CREATE INDEX IF NOT EXISTS idx_validation_audit_event_data_gin ON validation_audit_log USING GIN(event_data);

-- Validation statistics materialized view for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS validation_statistics_mv AS
SELECT 
    source_name,
    DATE_TRUNC('hour', timestamp) as hour_bucket,
    COUNT(*) as total_validations,
    COUNT(CASE WHEN status = 'validated' THEN 1 END) as successful_validations,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_validations,
    COUNT(CASE WHEN status = 'quarantined' THEN 1 END) as quarantined_items,
    AVG(overall_score) as avg_overall_score,
    AVG(credibility_score) as avg_credibility_score,
    AVG(accuracy_score) as avg_accuracy_score,
    AVG(security_score) as avg_security_score,
    AVG(freshness_score) as avg_freshness_score,
    AVG(validation_time) as avg_validation_time,
    MIN(validation_time) as min_validation_time,
    MAX(validation_time) as max_validation_time,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY validation_time) as median_validation_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY validation_time) as p95_validation_time
FROM source_validations 
GROUP BY source_name, DATE_TRUNC('hour', timestamp);

-- Create indexes on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_validation_stats_mv_source_hour ON validation_statistics_mv(source_name, hour_bucket);
CREATE INDEX IF NOT EXISTS idx_validation_stats_mv_hour_bucket ON validation_statistics_mv(hour_bucket DESC);

-- Real-time monitoring alerts table
CREATE TABLE IF NOT EXISTS validation_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Alert identification
    alert_type VARCHAR(100) NOT NULL,
    alert_level VARCHAR(50) NOT NULL CHECK (alert_level IN ('info', 'warning', 'error', 'critical')),
    alert_title VARCHAR(255) NOT NULL,
    alert_message TEXT NOT NULL,
    
    -- Context
    source_name VARCHAR(100),
    validation_id VARCHAR(255),
    item_id UUID,
    
    -- Alert data
    metrics JSONB DEFAULT '{}',
    thresholds JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '[]',
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved', 'suppressed')),
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for alerts
CREATE INDEX IF NOT EXISTS idx_validation_alerts_alert_type ON validation_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_validation_alerts_alert_level ON validation_alerts(alert_level);
CREATE INDEX IF NOT EXISTS idx_validation_alerts_status ON validation_alerts(status);
CREATE INDEX IF NOT EXISTS idx_validation_alerts_source_name ON validation_alerts(source_name);
CREATE INDEX IF NOT EXISTS idx_validation_alerts_created_at ON validation_alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_validation_alerts_updated_at ON validation_alerts(updated_at DESC);

-- Performance monitoring table
CREATE TABLE IF NOT EXISTS validation_performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Time bucket
    time_bucket TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    
    -- Metric values
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50) DEFAULT 'count',
    
    -- Context
    source_name VARCHAR(100),
    validation_component VARCHAR(100), -- 'credibility', 'accuracy', 'security', 'freshness'
    
    -- Metadata
    tags JSONB DEFAULT '{}',
    
    -- Audit
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance metrics
CREATE INDEX IF NOT EXISTS idx_validation_perf_metrics_time_bucket ON validation_performance_metrics(time_bucket DESC);
CREATE INDEX IF NOT EXISTS idx_validation_perf_metrics_metric_name ON validation_performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_validation_perf_metrics_source_name ON validation_performance_metrics(source_name);
CREATE INDEX IF NOT EXISTS idx_validation_perf_metrics_component ON validation_performance_metrics(validation_component);

-- Composite index for time series queries
CREATE INDEX IF NOT EXISTS idx_validation_perf_metrics_composite ON validation_performance_metrics(metric_name, time_bucket DESC, source_name);

-- Data retention policy table
CREATE TABLE IF NOT EXISTS data_retention_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Policy identification
    policy_name VARCHAR(255) UNIQUE NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    
    -- Retention settings
    retention_period INTERVAL NOT NULL,
    retention_condition TEXT, -- SQL WHERE condition for selective retention
    
    -- Compliance requirements
    gdpr_compliant BOOLEAN DEFAULT FALSE,
    soc2_compliant BOOLEAN DEFAULT FALSE,
    custom_requirements JSONB DEFAULT '{}',
    
    -- Policy status
    is_active BOOLEAN DEFAULT TRUE,
    last_cleanup TIMESTAMPTZ,
    next_cleanup TIMESTAMPTZ,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255) DEFAULT 'system'
);

-- Function to automatically update the updated_at field
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at fields
CREATE TRIGGER update_source_credibility_updated_at BEFORE UPDATE ON source_credibility
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_validation_alerts_updated_at BEFORE UPDATE ON validation_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_retention_policies_updated_at BEFORE UPDATE ON data_retention_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default data retention policies
INSERT INTO data_retention_policies (policy_name, table_name, retention_period, gdpr_compliant, soc2_compliant) VALUES
('source_validations_7_year', 'source_validations', '7 years', TRUE, TRUE),
('security_scan_results_7_year', 'security_scan_results', '7 years', TRUE, TRUE),
('validation_audit_log_7_year', 'validation_audit_log', '7 years', TRUE, TRUE),
('validation_alerts_1_year', 'validation_alerts', '1 year', TRUE, TRUE),
('performance_metrics_2_year', 'validation_performance_metrics', '2 years', FALSE, TRUE),
('content_duplicates_2_year', 'content_duplicates', '2 years', FALSE, FALSE)
ON CONFLICT (policy_name) DO NOTHING;

-- Initialize default source credibility scores
INSERT INTO source_credibility (source_name, base_credibility, historical_accuracy, community_validation, reputation_score) VALUES
('stackoverflow', 0.80, 0.75, 0.85, 0.80),
('commandlinefu', 0.70, 0.70, 0.75, 0.72),
('owasp', 0.95, 0.90, 0.95, 0.93),
('exploit-db', 0.90, 0.85, 0.88, 0.88),
('hacktricks', 0.80, 0.82, 0.80, 0.81),
('kubernetes', 0.95, 0.92, 0.90, 0.92),
('terraform', 0.90, 0.88, 0.85, 0.88),
('hashicorp', 0.90, 0.89, 0.87, 0.89)
ON CONFLICT (source_name) DO NOTHING;

-- Create function for automatic materialized view refresh
CREATE OR REPLACE FUNCTION refresh_validation_statistics_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY validation_statistics_mv;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE source_validations IS 'Core validation results for all knowledge items with comprehensive scoring';
COMMENT ON TABLE source_credibility IS 'Source credibility tracking with historical performance metrics';
COMMENT ON TABLE security_scan_results IS 'Detailed security scan results for content validation';
COMMENT ON TABLE content_duplicates IS 'Duplicate content detection and similarity tracking';
COMMENT ON TABLE validation_audit_log IS 'Comprehensive audit log for GDPR/SOC2 compliance';
COMMENT ON TABLE validation_alerts IS 'Real-time monitoring alerts for validation system';
COMMENT ON TABLE validation_performance_metrics IS 'Performance metrics tracking for validation system';
COMMENT ON MATERIALIZED VIEW validation_statistics_mv IS 'Aggregated validation statistics for performance optimization';