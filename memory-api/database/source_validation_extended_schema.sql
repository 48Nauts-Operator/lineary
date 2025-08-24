-- ABOUTME: Extended database schema for Source Validation & Verification System
-- ABOUTME: Enterprise-grade tables supporting SOC2/GDPR compliance, audit trails, and security monitoring

-- Source Credibility Assessments Table
CREATE TABLE IF NOT EXISTS source_credibility_assessments (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(255) NOT NULL,
    reputation_score DECIMAL(5,4) NOT NULL CHECK (reputation_score BETWEEN 0 AND 1),
    uptime_percentage DECIMAL(5,2) NOT NULL CHECK (uptime_percentage BETWEEN 0 AND 100),
    historical_accuracy DECIMAL(5,2) NOT NULL CHECK (historical_accuracy BETWEEN 0 AND 100),
    community_rating DECIMAL(5,2) NOT NULL CHECK (community_rating BETWEEN 0 AND 100),
    ssl_validity BOOLEAN NOT NULL DEFAULT FALSE,
    domain_age INTEGER NOT NULL DEFAULT 0,
    threat_intelligence_score DECIMAL(5,4) NOT NULL CHECK (threat_intelligence_score BETWEEN 0 AND 1),
    assessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for efficient querying of source credibility
CREATE INDEX IF NOT EXISTS idx_source_credibility_source_id ON source_credibility_assessments(source_id);
CREATE INDEX IF NOT EXISTS idx_source_credibility_assessed_at ON source_credibility_assessments(assessed_at);
CREATE INDEX IF NOT EXISTS idx_source_credibility_reputation ON source_credibility_assessments(reputation_score DESC);

-- Source Validation Results Table (Enhanced)
CREATE TABLE IF NOT EXISTS source_validation_results (
    id VARCHAR(36) PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'validated', 'rejected', 'quarantined', 'monitoring')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    threat_types TEXT[] NOT NULL DEFAULT '{}',
    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    validation_time TIMESTAMP WITH TIME ZONE NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    compliance_flags JSONB NOT NULL DEFAULT '{}',
    audit_trail JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for validation results
CREATE INDEX IF NOT EXISTS idx_validation_results_source ON source_validation_results(source);
CREATE INDEX IF NOT EXISTS idx_validation_results_hash ON source_validation_results(content_hash);
CREATE INDEX IF NOT EXISTS idx_validation_results_status ON source_validation_results(status);
CREATE INDEX IF NOT EXISTS idx_validation_results_severity ON source_validation_results(severity);
CREATE INDEX IF NOT EXISTS idx_validation_results_validation_time ON source_validation_results(validation_time);
CREATE INDEX IF NOT EXISTS idx_validation_results_threat_types ON source_validation_results USING GIN(threat_types);
CREATE INDEX IF NOT EXISTS idx_validation_results_details ON source_validation_results USING GIN(details);

-- Source Health Monitoring Table
CREATE TABLE IF NOT EXISTS source_monitoring_results (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    sources_monitored INTEGER NOT NULL DEFAULT 0,
    healthy_sources INTEGER NOT NULL DEFAULT 0,
    degraded_sources INTEGER NOT NULL DEFAULT 0,
    failed_sources INTEGER NOT NULL DEFAULT 0,
    source_details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for monitoring results
CREATE INDEX IF NOT EXISTS idx_monitoring_results_timestamp ON source_monitoring_results(timestamp);

-- Data Integrity Verification Table
CREATE TABLE IF NOT EXISTS data_integrity_verifications (
    id SERIAL PRIMARY KEY,
    content_hash VARCHAR(64) NOT NULL,
    integrity_verified BOOLEAN NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    expected_hash VARCHAR(64),
    tamper_detected BOOLEAN NOT NULL DEFAULT FALSE,
    integrity_proof JSONB NOT NULL DEFAULT '{}',
    verification_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for integrity verifications
CREATE INDEX IF NOT EXISTS idx_integrity_content_hash ON data_integrity_verifications(content_hash);
CREATE INDEX IF NOT EXISTS idx_integrity_verification_time ON data_integrity_verifications(verification_time);
CREATE INDEX IF NOT EXISTS idx_integrity_tamper_detected ON data_integrity_verifications(tamper_detected);

-- Security Audit Events Table
CREATE TABLE IF NOT EXISTS security_audit_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL CHECK (event_category IN ('authentication', 'authorization', 'data_access', 'validation', 'monitoring', 'compliance')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    source_ip INET,
    user_id VARCHAR(255),
    resource VARCHAR(255),
    action VARCHAR(100),
    outcome VARCHAR(20) NOT NULL CHECK (outcome IN ('success', 'failure', 'blocked', 'monitored')),
    details JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    retention_period INTEGER NOT NULL DEFAULT 2555, -- 7 years in days for SOC2 compliance
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for audit events
CREATE INDEX IF NOT EXISTS idx_audit_events_event_id ON security_audit_events(event_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON security_audit_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_events_severity ON security_audit_events(severity);
CREATE INDEX IF NOT EXISTS idx_audit_events_category ON security_audit_events(event_category);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON security_audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_outcome ON security_audit_events(outcome);

-- Compliance Reports Table
CREATE TABLE IF NOT EXISTS compliance_reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(36) NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    validation_statistics JSONB NOT NULL DEFAULT '{}',
    threat_detection_summary JSONB NOT NULL DEFAULT '{}',
    performance_metrics JSONB NOT NULL DEFAULT '{}',
    compliance_status JSONB NOT NULL DEFAULT '{}',
    recommendations JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for compliance reports
CREATE INDEX IF NOT EXISTS idx_compliance_reports_report_id ON compliance_reports(report_id);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_generated_at ON compliance_reports(generated_at);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_period ON compliance_reports(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_type ON compliance_reports(report_type);

-- Threat Intelligence Table
CREATE TABLE IF NOT EXISTS threat_intelligence_indicators (
    id SERIAL PRIMARY KEY,
    indicator_id VARCHAR(36) NOT NULL,
    indicator_type VARCHAR(50) NOT NULL CHECK (indicator_type IN ('ip', 'domain', 'url', 'hash', 'pattern')),
    indicator_value TEXT NOT NULL,
    threat_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source VARCHAR(255) NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for threat intelligence
CREATE INDEX IF NOT EXISTS idx_threat_intelligence_indicator_id ON threat_intelligence_indicators(indicator_id);
CREATE INDEX IF NOT EXISTS idx_threat_intelligence_type ON threat_intelligence_indicators(indicator_type);
CREATE INDEX IF NOT EXISTS idx_threat_intelligence_value ON threat_intelligence_indicators(indicator_value);
CREATE INDEX IF NOT EXISTS idx_threat_intelligence_severity ON threat_intelligence_indicators(severity);
CREATE INDEX IF NOT EXISTS idx_threat_intelligence_active ON threat_intelligence_indicators(active);

-- Security Incident Response Table
CREATE TABLE IF NOT EXISTS security_incidents (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(36) NOT NULL,
    incident_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(30) NOT NULL CHECK (status IN ('open', 'investigating', 'contained', 'resolved', 'closed')),
    source VARCHAR(255),
    affected_systems TEXT[],
    description TEXT NOT NULL,
    impact_assessment TEXT,
    response_actions JSONB NOT NULL DEFAULT '[]',
    timeline JSONB NOT NULL DEFAULT '[]',
    evidence JSONB NOT NULL DEFAULT '{}',
    assigned_to VARCHAR(255),
    reported_at TIMESTAMP WITH TIME ZONE NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for incidents
CREATE INDEX IF NOT EXISTS idx_incidents_incident_id ON security_incidents(incident_id);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON security_incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_reported_at ON security_incidents(reported_at);

-- Validation Performance Metrics Table
CREATE TABLE IF NOT EXISTS validation_performance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    validations_processed INTEGER NOT NULL DEFAULT 0,
    threats_detected INTEGER NOT NULL DEFAULT 0,
    false_positives INTEGER NOT NULL DEFAULT 0,
    average_validation_time DECIMAL(8,4) NOT NULL DEFAULT 0,
    max_validation_time DECIMAL(8,4) NOT NULL DEFAULT 0,
    min_validation_time DECIMAL(8,4) NOT NULL DEFAULT 0,
    uptime_percentage DECIMAL(5,2) NOT NULL DEFAULT 100,
    memory_usage_mb INTEGER NOT NULL DEFAULT 0,
    cpu_usage_percentage DECIMAL(5,2) NOT NULL DEFAULT 0,
    api_response_time DECIMAL(8,4) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for performance metrics
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON validation_performance_metrics(timestamp);

-- Data Retention Policies Table (GDPR Compliance)
CREATE TABLE IF NOT EXISTS data_retention_policies (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    retention_period_days INTEGER NOT NULL,
    legal_basis VARCHAR(100),
    processing_purpose TEXT,
    data_categories TEXT[],
    deletion_method VARCHAR(50) NOT NULL CHECK (deletion_method IN ('hard_delete', 'soft_delete', 'anonymize', 'archive')),
    automated BOOLEAN NOT NULL DEFAULT TRUE,
    policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    effective_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for retention policies
CREATE INDEX IF NOT EXISTS idx_retention_policies_table_name ON data_retention_policies(table_name);
CREATE INDEX IF NOT EXISTS idx_retention_policies_effective_date ON data_retention_policies(effective_date);

-- Create functions for automated data retention (GDPR compliance)
CREATE OR REPLACE FUNCTION cleanup_expired_data() RETURNS void AS $$
DECLARE
    policy RECORD;
    cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
    FOR policy IN SELECT * FROM data_retention_policies WHERE automated = true
    LOOP
        cutoff_date := NOW() - (policy.retention_period_days || ' days')::INTERVAL;
        
        CASE policy.table_name
            WHEN 'source_validation_results' THEN
                DELETE FROM source_validation_results WHERE created_at < cutoff_date;
            WHEN 'security_audit_events' THEN
                DELETE FROM security_audit_events WHERE created_at < cutoff_date;
            WHEN 'source_monitoring_results' THEN
                DELETE FROM source_monitoring_results WHERE created_at < cutoff_date;
            WHEN 'data_integrity_verifications' THEN
                DELETE FROM data_integrity_verifications WHERE created_at < cutoff_date;
            ELSE
                -- Log unknown table
                INSERT INTO security_audit_events (
                    event_id, event_type, event_category, severity, 
                    action, outcome, details, timestamp
                ) VALUES (
                    gen_random_uuid()::text, 'data_retention', 'compliance', 'medium',
                    'cleanup_unknown_table', 'failure',
                    json_build_object('table_name', policy.table_name),
                    NOW()
                );
        END CASE;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for audit trail automation
CREATE OR REPLACE FUNCTION log_validation_audit() RETURNS trigger AS $$
BEGIN
    INSERT INTO security_audit_events (
        event_id, event_type, event_category, severity,
        resource, action, outcome, details, timestamp
    ) VALUES (
        gen_random_uuid()::text, 'source_validation', 'validation', 
        CASE WHEN NEW.severity = 'critical' THEN 'critical'
             WHEN NEW.severity = 'high' THEN 'high'
             ELSE 'medium' END,
        NEW.source, 'validate_content', 
        CASE WHEN NEW.status = 'validated' THEN 'success'
             WHEN NEW.status = 'rejected' THEN 'blocked'
             ELSE 'monitored' END,
        json_build_object(
            'validation_id', NEW.id,
            'content_hash', NEW.content_hash,
            'threat_types', NEW.threat_types,
            'confidence_score', NEW.confidence_score
        ),
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to validation results
DROP TRIGGER IF EXISTS tr_validation_audit ON source_validation_results;
CREATE TRIGGER tr_validation_audit
    AFTER INSERT ON source_validation_results
    FOR EACH ROW EXECUTE FUNCTION log_validation_audit();

-- Create materialized views for performance optimization
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_validation_summary AS
SELECT 
    DATE_TRUNC('hour', validation_time) as hour,
    COUNT(*) as total_validations,
    COUNT(*) FILTER (WHERE status = 'validated') as validated_count,
    COUNT(*) FILTER (WHERE status = 'rejected') as rejected_count,
    COUNT(*) FILTER (WHERE status = 'quarantined') as quarantined_count,
    AVG(confidence_score) as avg_confidence,
    COUNT(DISTINCT source) as unique_sources
FROM source_validation_results
GROUP BY DATE_TRUNC('hour', validation_time);

-- Index for validation summary view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_validation_summary_hour ON mv_validation_summary(hour);

-- Create materialized view for threat detection summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_threat_detection_summary AS
SELECT 
    unnest(threat_types) as threat_type,
    COUNT(*) as detection_count,
    AVG(confidence_score) as avg_confidence,
    DATE_TRUNC('day', validation_time) as detection_date
FROM source_validation_results
WHERE array_length(threat_types, 1) > 0
GROUP BY unnest(threat_types), DATE_TRUNC('day', validation_time);

-- Index for threat detection summary view
CREATE INDEX IF NOT EXISTS idx_mv_threat_detection_summary ON mv_threat_detection_summary(threat_type, detection_date);

-- Create view for compliance dashboard
CREATE OR REPLACE VIEW v_compliance_dashboard AS
SELECT 
    'validation_metrics' as metric_type,
    COUNT(*) as total_count,
    COUNT(*) FILTER (WHERE status = 'validated') as compliant_count,
    COUNT(*) FILTER (WHERE status IN ('rejected', 'quarantined')) as non_compliant_count,
    ROUND(COUNT(*) FILTER (WHERE status = 'validated') * 100.0 / COUNT(*), 2) as compliance_percentage
FROM source_validation_results
WHERE validation_time >= NOW() - INTERVAL '30 days'

UNION ALL

SELECT 
    'audit_completeness' as metric_type,
    COUNT(*) as total_count,
    COUNT(*) FILTER (WHERE audit_trail != '[]'::jsonb) as compliant_count,
    COUNT(*) FILTER (WHERE audit_trail = '[]'::jsonb) as non_compliant_count,
    ROUND(COUNT(*) FILTER (WHERE audit_trail != '[]'::jsonb) * 100.0 / COUNT(*), 2) as compliance_percentage
FROM source_validation_results
WHERE validation_time >= NOW() - INTERVAL '30 days';

-- Insert default data retention policies for GDPR compliance
INSERT INTO data_retention_policies (
    data_type, table_name, retention_period_days, legal_basis, 
    processing_purpose, data_categories, deletion_method, effective_date
) VALUES 
    ('validation_results', 'source_validation_results', 2555, 'Legitimate Interest', 
     'Security monitoring and threat detection', ARRAY['security', 'operational'], 'hard_delete', NOW()),
    ('audit_events', 'security_audit_events', 2555, 'Legal Obligation', 
     'Compliance monitoring and incident response', ARRAY['security', 'audit'], 'archive', NOW()),
    ('monitoring_data', 'source_monitoring_results', 1095, 'Legitimate Interest', 
     'System performance monitoring', ARRAY['operational'], 'hard_delete', NOW()),
    ('performance_metrics', 'validation_performance_metrics', 730, 'Legitimate Interest', 
     'System optimization and capacity planning', ARRAY['operational'], 'anonymize', NOW())
ON CONFLICT DO NOTHING;

-- Create indexes for updated_at columns to support change tracking
CREATE INDEX IF NOT EXISTS idx_source_credibility_updated_at ON source_credibility_assessments(updated_at);
CREATE INDEX IF NOT EXISTS idx_validation_results_updated_at ON source_validation_results(updated_at);
CREATE INDEX IF NOT EXISTS idx_threat_intelligence_updated_at ON threat_intelligence_indicators(updated_at);
CREATE INDEX IF NOT EXISTS idx_incidents_updated_at ON security_incidents(updated_at);
CREATE INDEX IF NOT EXISTS idx_retention_policies_updated_at ON data_retention_policies(updated_at);

-- Create function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_validation_views() RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_validation_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_threat_detection_summary;
END;
$$ LANGUAGE plpgsql;

-- Grant appropriate permissions (adjust as needed for your security model)
-- These would be customized based on your application's role-based access control

-- Create roles for different access levels
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'validation_admin') THEN
        CREATE ROLE validation_admin;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'validation_user') THEN
        CREATE ROLE validation_user;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'validation_readonly') THEN
        CREATE ROLE validation_readonly;
    END IF;
END $$;

-- Grant permissions to roles
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO validation_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO validation_admin;

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO validation_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO validation_user;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO validation_readonly;

-- Create function to generate validation statistics report
CREATE OR REPLACE FUNCTION get_validation_statistics(
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() - INTERVAL '30 days',
    end_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) RETURNS TABLE (
    metric_name TEXT,
    metric_value NUMERIC,
    metric_description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'total_validations'::TEXT,
        COUNT(*)::NUMERIC,
        'Total validation requests processed'::TEXT
    FROM source_validation_results 
    WHERE validation_time BETWEEN start_date AND end_date
    
    UNION ALL
    
    SELECT 
        'validation_success_rate'::TEXT,
        ROUND(COUNT(*) FILTER (WHERE status = 'validated') * 100.0 / COUNT(*), 2)::NUMERIC,
        'Percentage of validations that passed'::TEXT
    FROM source_validation_results 
    WHERE validation_time BETWEEN start_date AND end_date
    
    UNION ALL
    
    SELECT 
        'average_validation_time'::TEXT,
        ROUND(AVG(EXTRACT(EPOCH FROM (validation_time - created_at))), 4)::NUMERIC,
        'Average validation time in seconds'::TEXT
    FROM source_validation_results 
    WHERE validation_time BETWEEN start_date AND end_date
    
    UNION ALL
    
    SELECT 
        'threats_detected'::TEXT,
        COUNT(*)::NUMERIC,
        'Total number of threats detected'::TEXT
    FROM source_validation_results 
    WHERE validation_time BETWEEN start_date AND end_date
    AND array_length(threat_types, 1) > 0;
END;
$$ LANGUAGE plpgsql;

-- Create notification function for critical security events
CREATE OR REPLACE FUNCTION notify_critical_security_event() RETURNS trigger AS $$
BEGIN
    IF NEW.severity = 'critical' THEN
        PERFORM pg_notify('critical_security_event', json_build_object(
            'event_id', NEW.event_id,
            'event_type', NEW.event_type,
            'severity', NEW.severity,
            'timestamp', NEW.timestamp
        )::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply critical event notification trigger
DROP TRIGGER IF EXISTS tr_critical_security_notification ON security_audit_events;
CREATE TRIGGER tr_critical_security_notification
    AFTER INSERT ON security_audit_events
    FOR EACH ROW EXECUTE FUNCTION notify_critical_security_event();

-- Create cleanup job for old validation cache entries (performance optimization)
CREATE OR REPLACE FUNCTION cleanup_old_validation_cache() RETURNS void AS $$
BEGIN
    -- Delete validation results older than retention policy
    DELETE FROM source_validation_results 
    WHERE created_at < NOW() - INTERVAL '7 years';
    
    -- Delete old monitoring results
    DELETE FROM source_monitoring_results 
    WHERE created_at < NOW() - INTERVAL '3 years';
    
    -- Delete old performance metrics
    DELETE FROM validation_performance_metrics 
    WHERE created_at < NOW() - INTERVAL '2 years';
    
    -- Archive old security audit events
    UPDATE security_audit_events 
    SET details = details || json_build_object('archived', true)
    WHERE created_at < NOW() - INTERVAL '7 years';
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE source_credibility_assessments IS 'Stores real-time source credibility assessments with reputation scoring';
COMMENT ON TABLE source_validation_results IS 'Enhanced validation results with comprehensive threat detection and audit trails';
COMMENT ON TABLE security_audit_events IS 'SOC2-compliant audit trail for all security-related events';
COMMENT ON TABLE compliance_reports IS 'Generated compliance reports for SOC2/GDPR requirements';
COMMENT ON TABLE threat_intelligence_indicators IS 'Threat intelligence indicators for proactive threat detection';
COMMENT ON TABLE security_incidents IS 'Security incident tracking and response management';
COMMENT ON TABLE data_retention_policies IS 'GDPR-compliant data retention policy definitions';

-- Final validation of schema creation
SELECT 'Source Validation & Verification System schema created successfully' as status;