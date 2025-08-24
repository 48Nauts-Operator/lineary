-- ABOUTME: Data provenance tracking schema for BETTY Memory System
-- ABOUTME: Comprehensive audit trail for knowledge pattern sources and transformations

-- Enable required extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- DATA PROVENANCE CORE TABLES
-- =============================================================================

-- Data Sources Registry - Track all external sources Betty ingests from
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source identification
    source_name VARCHAR(255) NOT NULL UNIQUE, -- 'Context7', 'Stack Overflow', 'OWASP', '137docs'
    source_type VARCHAR(100) NOT NULL, -- 'documentation', 'qa_site', 'security_framework', 'internal_patterns'
    base_url TEXT, -- https://context7.ai, https://stackoverflow.com
    
    -- Source metadata
    description TEXT,
    reliability_score REAL DEFAULT 0.8, -- 0.0-1.0 how reliable is this source
    update_frequency VARCHAR(50), -- 'daily', 'weekly', 'monthly', 'on_demand'
    access_method VARCHAR(100), -- 'api', 'web_scraping', 'manual_export', 'webhook'
    
    -- Authentication and access
    requires_auth BOOLEAN DEFAULT false,
    auth_config JSONB DEFAULT '{}'::jsonb, -- API keys, credentials (encrypted)
    rate_limits JSONB DEFAULT '{}'::jsonb, -- {'requests_per_minute': 60, 'daily_limit': 1000}
    
    -- Quality and validation
    validation_rules JSONB DEFAULT '[]'::jsonb, -- Validation rules for data from this source
    content_standards JSONB DEFAULT '{}'::jsonb, -- Expected content format, quality requirements
    
    -- Status tracking
    is_active BOOLEAN DEFAULT true,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    last_successful_extraction TIMESTAMP WITH TIME ZONE,
    consecutive_failures INTEGER DEFAULT 0,
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Extraction Jobs - Track each extraction/ingestion operation
CREATE TABLE extraction_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Job identification
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL, -- 'full_sync', 'incremental', 'targeted_extraction', 'manual_import'
    data_source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    
    -- Extraction parameters
    extraction_method VARCHAR(100) NOT NULL, -- 'api_fetch', 'web_scrape', 'file_import', 'direct_input'
    extraction_version VARCHAR(50) NOT NULL, -- Version of extraction logic used
    extraction_parameters JSONB NOT NULL DEFAULT '{}'::jsonb, -- Specific parameters used
    
    -- Target information
    target_url TEXT, -- Specific URL or endpoint extracted from
    target_query TEXT, -- Search query or filter criteria
    date_range_start TIMESTAMP WITH TIME ZONE, -- For time-bounded extractions
    date_range_end TIMESTAMP WITH TIME ZONE,
    
    -- Job execution
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'
    
    -- Results summary
    items_discovered INTEGER DEFAULT 0,
    items_processed INTEGER DEFAULT 0,
    items_successful INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    items_duplicated INTEGER DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    
    -- Quality metrics
    avg_processing_time_ms REAL,
    data_quality_score REAL, -- 0.0-1.0 overall quality of extracted data
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Knowledge Provenance - Detailed provenance for each knowledge item
CREATE TABLE knowledge_provenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_item_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    
    -- Source attribution
    extraction_job_id UUID NOT NULL REFERENCES extraction_jobs(id) ON DELETE RESTRICT,
    data_source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
    original_source_url TEXT NOT NULL, -- Exact URL where this knowledge came from
    source_timestamp TIMESTAMP WITH TIME ZONE, -- When the original content was created/modified
    
    -- Content identification
    original_content_id VARCHAR(500), -- ID from source system (SO question ID, Context7 pattern ID)
    original_content_hash VARCHAR(64) NOT NULL, -- SHA-256 of original raw content
    processed_content_hash VARCHAR(64) NOT NULL, -- SHA-256 of processed content
    
    -- Extraction metadata
    extraction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    extraction_method_version VARCHAR(50) NOT NULL,
    extraction_parameters JSONB DEFAULT '{}'::jsonb,
    
    -- Content transformations
    raw_content TEXT, -- Original content before any processing
    processing_steps JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of processing steps applied
    transformation_log JSONB DEFAULT '[]'::jsonb, -- Detailed log of each transformation
    
    -- Quality and validation
    validation_results JSONB DEFAULT '{}'::jsonb, -- Results of validation checks
    quality_metrics JSONB DEFAULT '{}'::jsonb, -- Quality scores and metrics
    validation_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'passed', 'failed', 'warning'
    validated_by VARCHAR(255), -- Who/what validated this data
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Update tracking
    is_current_version BOOLEAN DEFAULT true,
    superseded_by UUID REFERENCES knowledge_provenance(id),
    superseded_at TIMESTAMP WITH TIME ZONE,
    version_number INTEGER DEFAULT 1,
    
    -- Internal development notes (not user-visible)
    internal_notes TEXT,
    development_flags JSONB DEFAULT '{}'::jsonb, -- Flags for development team
    debugging_info JSONB DEFAULT '{}'::jsonb, -- Debug information
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one current version per knowledge item
    UNIQUE(knowledge_item_id) WHERE is_current_version = true,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Transformation Steps - Detailed tracking of content transformations
CREATE TABLE transformation_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_provenance_id UUID NOT NULL REFERENCES knowledge_provenance(id) ON DELETE CASCADE,
    
    -- Step identification
    step_name VARCHAR(255) NOT NULL, -- 'html_cleanup', 'markdown_conversion', 'entity_extraction'
    step_order INTEGER NOT NULL, -- Order in transformation pipeline
    processor_name VARCHAR(255) NOT NULL, -- Name of processor/function that performed step
    processor_version VARCHAR(50) NOT NULL, -- Version of processor
    
    -- Step execution
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'completed', -- 'completed', 'failed', 'skipped'
    
    -- Content transformation
    input_content TEXT, -- Content before this step
    output_content TEXT, -- Content after this step
    input_hash VARCHAR(64), -- SHA-256 of input content
    output_hash VARCHAR(64), -- SHA-256 of output content
    
    -- Step parameters and results
    parameters JSONB DEFAULT '{}'::jsonb, -- Parameters passed to this step
    results JSONB DEFAULT '{}'::jsonb, -- Results/metrics from this step
    changes_made JSONB DEFAULT '[]'::jsonb, -- Specific changes applied
    
    -- Error handling
    error_message TEXT,
    error_details JSONB,
    warnings JSONB DEFAULT '[]'::jsonb,
    
    -- Quality metrics
    quality_impact_score REAL, -- How this step affected content quality
    validation_results JSONB DEFAULT '{}'::jsonb,
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique step per provenance
    UNIQUE(knowledge_provenance_id, step_order),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Quality Lineage - Track quality assessments and approvals
CREATE TABLE quality_lineage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_provenance_id UUID NOT NULL REFERENCES knowledge_provenance(id) ON DELETE CASCADE,
    
    -- Quality assessment
    assessment_type VARCHAR(100) NOT NULL, -- 'automated', 'manual_review', 'peer_review', 'expert_approval'
    assessor_name VARCHAR(255), -- Who performed the assessment
    assessor_type VARCHAR(50), -- 'system', 'developer', 'domain_expert', 'ai_model'
    
    -- Quality scores and metrics
    overall_quality_score REAL NOT NULL, -- 0.0-1.0 overall quality
    accuracy_score REAL, -- 0.0-1.0 accuracy assessment
    completeness_score REAL, -- 0.0-1.0 completeness
    relevance_score REAL, -- 0.0-1.0 relevance to domain
    freshness_score REAL, -- 0.0-1.0 how current/fresh is the content
    
    -- Detailed assessment
    quality_criteria JSONB NOT NULL DEFAULT '{}'::jsonb, -- Specific criteria checked
    assessment_results JSONB NOT NULL DEFAULT '{}'::jsonb, -- Detailed results
    issues_found JSONB DEFAULT '[]'::jsonb, -- List of issues identified
    recommendations JSONB DEFAULT '[]'::jsonb, -- Recommendations for improvement
    
    -- Approval workflow
    approval_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'needs_revision'
    approval_reason TEXT, -- Reason for approval/rejection
    approved_by VARCHAR(255),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Review notes (internal)
    reviewer_notes TEXT,
    internal_flags JSONB DEFAULT '{}'::jsonb,
    follow_up_required BOOLEAN DEFAULT false,
    
    -- Temporal tracking
    assessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Internal Annotations - Development team notes and annotations
CREATE TABLE internal_annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Target identification (can reference multiple entity types)
    target_type VARCHAR(100) NOT NULL, -- 'knowledge_item', 'extraction_job', 'data_source', 'transformation_step'
    target_id UUID NOT NULL, -- ID of the target entity
    
    -- Annotation details
    annotation_type VARCHAR(100) NOT NULL, -- 'note', 'flag', 'todo', 'investigation', 'quality_concern'
    title VARCHAR(500),
    content TEXT NOT NULL,
    priority VARCHAR(50) DEFAULT 'normal', -- 'low', 'normal', 'high', 'critical'
    
    -- Attribution
    created_by VARCHAR(255) NOT NULL, -- Developer name
    assigned_to VARCHAR(255), -- If it's an action item
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'resolved', 'archived'
    resolution_notes TEXT,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Categorization
    tags JSONB DEFAULT '[]'::jsonb, -- ['data_quality', 'extraction_bug', 'needs_review']
    visibility VARCHAR(50) DEFAULT 'internal', -- 'internal', 'team', 'public'
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Update History - Track changes to knowledge items over time
CREATE TABLE knowledge_update_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_item_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    
    -- Update identification
    update_type VARCHAR(100) NOT NULL, -- 'content_refresh', 'quality_improvement', 'source_update', 'manual_edit'
    update_source VARCHAR(255), -- What triggered this update
    update_reason TEXT, -- Why was this updated
    
    -- Change details
    fields_changed JSONB NOT NULL DEFAULT '[]'::jsonb, -- List of fields that changed
    old_values JSONB DEFAULT '{}'::jsonb, -- Previous values
    new_values JSONB DEFAULT '{}'::jsonb, -- New values
    change_summary TEXT, -- Human-readable summary of changes
    
    -- Update context
    updated_by VARCHAR(255) NOT NULL, -- Who made the update
    update_method VARCHAR(100), -- 'automated', 'manual', 'batch_process'
    batch_job_id UUID REFERENCES extraction_jobs(id), -- If part of batch update
    
    -- Provenance linkage
    new_provenance_id UUID REFERENCES knowledge_provenance(id), -- New provenance record if applicable
    
    -- Impact assessment
    impact_level VARCHAR(50) DEFAULT 'low', -- 'low', 'medium', 'high', 'breaking'
    affects_relationships BOOLEAN DEFAULT false,
    relationship_updates JSONB DEFAULT '[]'::jsonb, -- Changes to relationships
    
    -- Temporal tracking
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- PERFORMANCE INDEXES FOR PROVENANCE TABLES
-- =============================================================================

-- Data Sources indexes
CREATE INDEX idx_data_sources_source_name ON data_sources(source_name);
CREATE INDEX idx_data_sources_source_type ON data_sources(source_type);
CREATE INDEX idx_data_sources_is_active ON data_sources(is_active);
CREATE INDEX idx_data_sources_last_accessed ON data_sources(last_accessed_at);
CREATE INDEX idx_data_sources_reliability ON data_sources(reliability_score);

-- Extraction Jobs indexes
CREATE INDEX idx_extraction_jobs_data_source ON extraction_jobs(data_source_id);
CREATE INDEX idx_extraction_jobs_status ON extraction_jobs(status);
CREATE INDEX idx_extraction_jobs_started_at ON extraction_jobs(started_at);
CREATE INDEX idx_extraction_jobs_job_type ON extraction_jobs(job_type);
CREATE INDEX idx_extraction_jobs_completed_at ON extraction_jobs(completed_at);

-- Knowledge Provenance indexes
CREATE INDEX idx_knowledge_provenance_knowledge_item ON knowledge_provenance(knowledge_item_id);
CREATE INDEX idx_knowledge_provenance_extraction_job ON knowledge_provenance(extraction_job_id);
CREATE INDEX idx_knowledge_provenance_data_source ON knowledge_provenance(data_source_id);
CREATE INDEX idx_knowledge_provenance_current_version ON knowledge_provenance(is_current_version);
CREATE INDEX idx_knowledge_provenance_source_url ON knowledge_provenance(original_source_url);
CREATE INDEX idx_knowledge_provenance_content_hash ON knowledge_provenance(original_content_hash);
CREATE INDEX idx_knowledge_provenance_validation_status ON knowledge_provenance(validation_status);
CREATE INDEX idx_knowledge_provenance_extraction_timestamp ON knowledge_provenance(extraction_timestamp);

-- Transformation Steps indexes
CREATE INDEX idx_transformation_steps_provenance ON transformation_steps(knowledge_provenance_id);
CREATE INDEX idx_transformation_steps_order ON transformation_steps(knowledge_provenance_id, step_order);
CREATE INDEX idx_transformation_steps_processor ON transformation_steps(processor_name);
CREATE INDEX idx_transformation_steps_status ON transformation_steps(status);
CREATE INDEX idx_transformation_steps_started_at ON transformation_steps(started_at);

-- Quality Lineage indexes
CREATE INDEX idx_quality_lineage_provenance ON quality_lineage(knowledge_provenance_id);
CREATE INDEX idx_quality_lineage_assessment_type ON quality_lineage(assessment_type);
CREATE INDEX idx_quality_lineage_approval_status ON quality_lineage(approval_status);
CREATE INDEX idx_quality_lineage_quality_score ON quality_lineage(overall_quality_score);
CREATE INDEX idx_quality_lineage_assessed_at ON quality_lineage(assessed_at);
CREATE INDEX idx_quality_lineage_approved_by ON quality_lineage(approved_by);

-- Internal Annotations indexes
CREATE INDEX idx_internal_annotations_target ON internal_annotations(target_type, target_id);
CREATE INDEX idx_internal_annotations_type ON internal_annotations(annotation_type);
CREATE INDEX idx_internal_annotations_status ON internal_annotations(status);
CREATE INDEX idx_internal_annotations_created_by ON internal_annotations(created_by);
CREATE INDEX idx_internal_annotations_assigned_to ON internal_annotations(assigned_to);
CREATE INDEX idx_internal_annotations_priority ON internal_annotations(priority);
CREATE INDEX idx_internal_annotations_tags ON internal_annotations USING GIN(tags);
CREATE INDEX idx_internal_annotations_created_at ON internal_annotations(created_at);

-- Update History indexes
CREATE INDEX idx_knowledge_update_history_knowledge_item ON knowledge_update_history(knowledge_item_id);
CREATE INDEX idx_knowledge_update_history_update_type ON knowledge_update_history(update_type);
CREATE INDEX idx_knowledge_update_history_updated_by ON knowledge_update_history(updated_by);
CREATE INDEX idx_knowledge_update_history_batch_job ON knowledge_update_history(batch_job_id);
CREATE INDEX idx_knowledge_update_history_impact_level ON knowledge_update_history(impact_level);
CREATE INDEX idx_knowledge_update_history_updated_at ON knowledge_update_history(updated_at);

-- =============================================================================
-- TRIGGERS FOR PROVENANCE TRACKING
-- =============================================================================

-- Apply updated_at trigger to provenance tables
CREATE TRIGGER update_data_sources_updated_at 
    BEFORE UPDATE ON data_sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_provenance_updated_at 
    BEFORE UPDATE ON knowledge_provenance 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_internal_annotations_updated_at 
    BEFORE UPDATE ON internal_annotations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Automatically create provenance tracking when knowledge items are inserted
CREATE OR REPLACE FUNCTION create_knowledge_provenance_placeholder()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create placeholder if no provenance exists yet
    IF NOT EXISTS (SELECT 1 FROM knowledge_provenance WHERE knowledge_item_id = NEW.id) THEN
        INSERT INTO knowledge_provenance (
            knowledge_item_id,
            extraction_job_id,
            data_source_id,
            original_source_url,
            original_content_hash,
            processed_content_hash,
            extraction_method_version,
            raw_content,
            processing_steps,
            validation_status,
            internal_notes
        ) VALUES (
            NEW.id,
            -- Use a default/placeholder extraction job (will need to be created)
            '00000000-0000-0000-0000-000000000000'::uuid,
            -- Use a default/placeholder data source (will need to be created) 
            '00000000-0000-0000-0000-000000000000'::uuid,
            COALESCE(NEW.metadata->>'source_url', 'unknown'),
            encode(sha256(NEW.content::bytea), 'hex'),
            encode(sha256(NEW.content::bytea), 'hex'),
            'legacy_import',
            NEW.content,
            '[]'::jsonb,
            'needs_review',
            'Auto-created provenance record for existing knowledge item'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic provenance creation
CREATE TRIGGER create_knowledge_provenance_trigger
    AFTER INSERT ON knowledge_items
    FOR EACH ROW EXECUTE FUNCTION create_knowledge_provenance_placeholder();

-- Automatically track knowledge item updates
CREATE OR REPLACE FUNCTION track_knowledge_item_updates()
RETURNS TRIGGER AS $$
DECLARE
    changed_fields jsonb := '[]'::jsonb;
    old_vals jsonb := '{}'::jsonb;
    new_vals jsonb := '{}'::jsonb;
    field_name text;
BEGIN
    -- Compare fields and track changes
    FOR field_name IN SELECT jsonb_object_keys(to_jsonb(NEW)) LOOP
        IF to_jsonb(OLD)->>field_name IS DISTINCT FROM to_jsonb(NEW)->>field_name THEN
            changed_fields := changed_fields || jsonb_build_array(field_name);
            old_vals := old_vals || jsonb_build_object(field_name, to_jsonb(OLD)->>field_name);
            new_vals := new_vals || jsonb_build_object(field_name, to_jsonb(NEW)->>field_name);
        END IF;
    END LOOP;
    
    -- Only create history record if there were actual changes
    IF jsonb_array_length(changed_fields) > 0 THEN
        INSERT INTO knowledge_update_history (
            knowledge_item_id,
            update_type,
            update_source,
            update_reason,
            fields_changed,
            old_values,
            new_values,
            change_summary,
            updated_by,
            update_method
        ) VALUES (
            NEW.id,
            'content_update',
            'system_trigger',
            'Knowledge item updated',
            changed_fields,
            old_vals,
            new_vals,
            format('%s fields changed', jsonb_array_length(changed_fields)),
            CURRENT_USER,
            'automated'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for knowledge item update tracking
CREATE TRIGGER track_knowledge_item_updates_trigger
    AFTER UPDATE ON knowledge_items
    FOR EACH ROW EXECUTE FUNCTION track_knowledge_item_updates();

-- =============================================================================
-- VIEWS FOR PROVENANCE QUERIES
-- =============================================================================

-- Complete provenance view with full lineage
CREATE VIEW knowledge_provenance_complete AS
SELECT 
    ki.id as knowledge_item_id,
    ki.title,
    ki.knowledge_type,
    ki.domain,
    ki.quality_score,
    
    -- Source information
    ds.source_name,
    ds.source_type,
    ds.reliability_score as source_reliability,
    kp.original_source_url,
    kp.source_timestamp,
    
    -- Extraction details
    ej.job_name as extraction_job,
    ej.extraction_method,
    ej.extraction_version,
    kp.extraction_timestamp,
    
    -- Quality information
    kp.validation_status,
    kp.validated_by,
    kp.validated_at,
    ql.overall_quality_score as provenance_quality_score,
    ql.approval_status,
    ql.approved_by,
    
    -- Processing information
    jsonb_array_length(kp.processing_steps) as processing_step_count,
    kp.version_number,
    kp.is_current_version,
    
    -- Internal notes (for development team)
    kp.internal_notes,
    
    -- Timing information
    ki.created_at as knowledge_created_at,
    kp.created_at as provenance_created_at,
    ki.last_used_at as knowledge_last_used
    
FROM knowledge_items ki
LEFT JOIN knowledge_provenance kp ON ki.id = kp.knowledge_item_id AND kp.is_current_version = true
LEFT JOIN data_sources ds ON kp.data_source_id = ds.id
LEFT JOIN extraction_jobs ej ON kp.extraction_job_id = ej.id
LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id AND ql.approval_status = 'approved'
WHERE ki.system_time_until IS NULL; -- Only current knowledge items

-- Data source summary view
CREATE VIEW data_source_summary AS
SELECT 
    ds.*,
    COUNT(DISTINCT ej.id) as total_extraction_jobs,
    COUNT(DISTINCT kp.knowledge_item_id) as total_knowledge_items,
    AVG(ql.overall_quality_score) as avg_quality_score,
    MAX(ej.completed_at) as last_extraction,
    SUM(ej.items_successful) as total_items_extracted,
    SUM(ej.items_failed) as total_items_failed
FROM data_sources ds
LEFT JOIN extraction_jobs ej ON ds.id = ej.data_source_id
LEFT JOIN knowledge_provenance kp ON ej.id = kp.extraction_job_id
LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
GROUP BY ds.id;

-- =============================================================================
-- FUNCTIONS FOR PROVENANCE MANAGEMENT
-- =============================================================================

-- Function to get complete provenance for a knowledge item
CREATE OR REPLACE FUNCTION get_knowledge_provenance(knowledge_item_uuid UUID)
RETURNS TABLE (
    source_name TEXT,
    original_url TEXT,
    extraction_method TEXT,
    extraction_timestamp TIMESTAMP WITH TIME ZONE,
    processing_steps JSONB,
    quality_score REAL,
    validation_status TEXT,
    internal_notes TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ds.source_name::TEXT,
        kp.original_source_url::TEXT,
        ej.extraction_method::TEXT,
        kp.extraction_timestamp,
        kp.processing_steps,
        ql.overall_quality_score,
        kp.validation_status::TEXT,
        kp.internal_notes::TEXT
    FROM knowledge_provenance kp
    JOIN data_sources ds ON kp.data_source_id = ds.id
    JOIN extraction_jobs ej ON kp.extraction_job_id = ej.id
    LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
    WHERE kp.knowledge_item_id = knowledge_item_uuid 
    AND kp.is_current_version = true;
END;
$$ LANGUAGE plpgsql;

-- Function to add internal annotation
CREATE OR REPLACE FUNCTION add_internal_annotation(
    target_entity_type VARCHAR(100),
    target_entity_id UUID,
    annotation_type_param VARCHAR(100),
    title_param VARCHAR(500),
    content_param TEXT,
    created_by_param VARCHAR(255),
    priority_param VARCHAR(50) DEFAULT 'normal',
    tags_param JSONB DEFAULT '[]'::jsonb
)
RETURNS UUID AS $$
DECLARE
    annotation_id UUID;
BEGIN
    INSERT INTO internal_annotations (
        target_type,
        target_id,
        annotation_type,
        title,
        content,
        created_by,
        priority,
        tags
    ) VALUES (
        target_entity_type,
        target_entity_id,
        annotation_type_param,
        title_param,
        content_param,
        created_by_param,
        priority_param,
        tags_param
    ) RETURNING id INTO annotation_id;
    
    RETURN annotation_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- INITIAL DATA SETUP
-- =============================================================================

-- Create default/placeholder data source for legacy data
INSERT INTO data_sources (
    id,
    source_name,
    source_type,
    description,
    reliability_score,
    is_active
) VALUES (
    '00000000-0000-0000-0000-000000000000'::uuid,
    'Legacy/Unknown',
    'internal_patterns',
    'Placeholder for knowledge items without clear provenance',
    0.5,
    false
) ON CONFLICT (source_name) DO NOTHING;

-- Create default/placeholder extraction job
INSERT INTO extraction_jobs (
    id,
    job_name,
    job_type,
    data_source_id,
    extraction_method,
    extraction_version,
    status,
    started_at,
    completed_at,
    items_successful
) VALUES (
    '00000000-0000-0000-0000-000000000000'::uuid,
    'Legacy Import',
    'manual_import',
    '00000000-0000-0000-0000-000000000000'::uuid,
    'legacy_import',
    '1.0.0',
    'completed',
    CURRENT_TIMESTAMP - INTERVAL '1 year',
    CURRENT_TIMESTAMP - INTERVAL '1 year',
    0
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE data_sources IS 'Registry of all external data sources that Betty ingests knowledge from';
COMMENT ON TABLE extraction_jobs IS 'Detailed tracking of each extraction/ingestion operation from external sources';
COMMENT ON TABLE knowledge_provenance IS 'Complete provenance tracking for each knowledge item including source attribution and transformations';
COMMENT ON TABLE transformation_steps IS 'Detailed audit trail of content transformation steps during ingestion';
COMMENT ON TABLE quality_lineage IS 'Quality assessment and approval workflow tracking';
COMMENT ON TABLE internal_annotations IS 'Development team notes and annotations not visible to end users';
COMMENT ON TABLE knowledge_update_history IS 'Complete history of changes made to knowledge items over time';

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES ('1.1.0', 'Added comprehensive data provenance tracking system')
ON CONFLICT (version) DO NOTHING;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'BETTY Data Provenance System Schema Added Successfully';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'New Tables: 7 provenance tracking tables';
    RAISE NOTICE 'New Views: 2 provenance summary views';  
    RAISE NOTICE 'New Functions: 3 provenance management functions';
    RAISE NOTICE 'New Triggers: 3 automatic tracking triggers';
    RAISE NOTICE 'Features: Source attribution, transformation history, quality lineage';
    RAISE NOTICE 'Internal: Development annotations, update tracking, debugging info';
    RAISE NOTICE '============================================================';
END $$;