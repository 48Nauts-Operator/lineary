-- ABOUTME: Database schema for BETTY's Cross-Domain Pattern Intelligence system
-- ABOUTME: Stores abstract patterns, domain ontologies, cross-domain matches, and adaptation strategies

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Abstract Patterns table - stores domain-agnostic pattern templates
CREATE TABLE abstract_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    abstract_description TEXT NOT NULL,
    conceptual_structure JSONB NOT NULL,
    invariant_properties TEXT[] NOT NULL DEFAULT '{}',
    variable_components JSONB NOT NULL,
    applicability_conditions TEXT[] NOT NULL DEFAULT '{}',
    expected_outcomes TEXT[] NOT NULL DEFAULT '{}',
    source_domains VARCHAR(100)[] NOT NULL DEFAULT '{}',
    abstraction_level DECIMAL(3,2) NOT NULL CHECK (abstraction_level >= 0.0 AND abstraction_level <= 1.0),
    quality_score DECIMAL(3,2) NOT NULL DEFAULT 0.5 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    usage_count INTEGER NOT NULL DEFAULT 0,
    success_rate DECIMAL(3,2) DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT abstract_patterns_title_check CHECK (length(title) > 0),
    CONSTRAINT abstract_patterns_description_check CHECK (length(abstract_description) > 0)
);

-- Domain Ontologies table - stores knowledge domain structures
CREATE TABLE domain_ontologies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(100) NOT NULL UNIQUE,
    core_concepts TEXT[] NOT NULL DEFAULT '{}',
    concept_relationships JSONB NOT NULL DEFAULT '{}',
    technical_vocabulary TEXT[] NOT NULL DEFAULT '{}',
    common_patterns TEXT[] NOT NULL DEFAULT '{}',
    tools_and_technologies TEXT[] NOT NULL DEFAULT '{}',
    typical_problems TEXT[] NOT NULL DEFAULT '{}',
    success_metrics TEXT[] NOT NULL DEFAULT '{}',
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 0.5 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    pattern_count INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT domain_ontologies_domain_check CHECK (length(domain) > 0)
);

-- Cross-Domain Matches table - stores pattern similarity relationships
CREATE TABLE cross_domain_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_pattern_id UUID NOT NULL,
    target_pattern_id UUID NOT NULL,
    source_domain VARCHAR(100) NOT NULL,
    target_domain VARCHAR(100) NOT NULL,
    similarity_score DECIMAL(4,3) NOT NULL CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),
    conceptual_overlap TEXT[] NOT NULL DEFAULT '{}',
    structural_similarity DECIMAL(4,3) NOT NULL CHECK (structural_similarity >= 0.0 AND structural_similarity <= 1.0),
    adaptation_strategy VARCHAR(100) NOT NULL,
    confidence_level DECIMAL(4,3) NOT NULL CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0),
    evidence TEXT[] NOT NULL DEFAULT '{}',
    validation_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    validation_result JSONB DEFAULT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    -- Foreign key references (would reference patterns table if it exists)
    CONSTRAINT cross_domain_matches_different_patterns CHECK (source_pattern_id != target_pattern_id),
    CONSTRAINT cross_domain_matches_different_domains CHECK (source_domain != target_domain),
    CONSTRAINT cross_domain_matches_strategy_check CHECK (
        adaptation_strategy IN ('direct_transfer', 'conceptual_mapping', 'structural_analogy', 
                               'abstraction_refinement', 'hybrid_approach')
    ),
    CONSTRAINT cross_domain_matches_validation_check CHECK (
        validation_status IN ('pending', 'validated', 'rejected', 'needs_review')
    )
);

-- Domain Adaptations table - stores successful pattern adaptations
CREATE TABLE domain_adaptations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_pattern_id UUID NOT NULL,
    abstract_pattern_id UUID NOT NULL,
    adapted_pattern_id UUID NOT NULL,
    source_domain VARCHAR(100) NOT NULL,
    target_domain VARCHAR(100) NOT NULL,
    adaptation_strategy VARCHAR(100) NOT NULL,
    concept_mappings JSONB NOT NULL DEFAULT '{}',
    technology_substitutions JSONB NOT NULL DEFAULT '{}',
    structural_modifications TEXT[] NOT NULL DEFAULT '{}',
    validation_criteria TEXT[] NOT NULL DEFAULT '{}',
    success_probability VARCHAR(20) NOT NULL DEFAULT 'medium',
    risk_factors TEXT[] NOT NULL DEFAULT '{}',
    mitigation_strategies TEXT[] NOT NULL DEFAULT '{}',
    actual_success BOOLEAN DEFAULT NULL,
    success_metrics JSONB DEFAULT NULL,
    user_feedback JSONB DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    -- Foreign key references
    CONSTRAINT fk_abstract_pattern FOREIGN KEY (abstract_pattern_id) 
        REFERENCES abstract_patterns(id) ON DELETE CASCADE,
    
    CONSTRAINT domain_adaptations_different_domains CHECK (source_domain != target_domain),
    CONSTRAINT domain_adaptations_success_prob_check CHECK (
        success_probability IN ('very_low', 'low', 'medium', 'high', 'very_high')
    ),
    CONSTRAINT domain_adaptations_strategy_check CHECK (
        adaptation_strategy IN ('direct_transfer', 'conceptual_mapping', 'structural_analogy', 
                               'abstraction_refinement', 'hybrid_approach')
    )
);

-- Cross-Domain Usage Analytics table - tracks pattern usage across domains
CREATE TABLE cross_domain_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL,
    original_domain VARCHAR(100) NOT NULL,
    used_in_domain VARCHAR(100) NOT NULL,
    usage_type VARCHAR(50) NOT NULL, -- 'direct_use', 'adapted_use', 'inspiration'
    adaptation_id UUID DEFAULT NULL,
    user_id UUID DEFAULT NULL,
    project_context VARCHAR(500) DEFAULT NULL,
    success_rating INTEGER CHECK (success_rating >= 1 AND success_rating <= 5),
    feedback TEXT DEFAULT NULL,
    metadata JSONB DEFAULT '{}',
    used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign key references
    CONSTRAINT fk_adaptation FOREIGN KEY (adaptation_id) 
        REFERENCES domain_adaptations(id) ON DELETE SET NULL,
    
    CONSTRAINT cross_domain_usage_type_check CHECK (
        usage_type IN ('direct_use', 'adapted_use', 'inspiration', 'reference')
    ),
    CONSTRAINT cross_domain_usage_different_domains CHECK (original_domain != used_in_domain)
);

-- Domain Relationship Strength table - tracks relationships between domains
CREATE TABLE domain_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_domain VARCHAR(100) NOT NULL,
    target_domain VARCHAR(100) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'similarity',
    strength_score DECIMAL(4,3) NOT NULL CHECK (strength_score >= 0.0 AND strength_score <= 1.0),
    shared_concepts INTEGER NOT NULL DEFAULT 0,
    successful_adaptations INTEGER NOT NULL DEFAULT 0,
    total_adaptation_attempts INTEGER NOT NULL DEFAULT 0,
    average_success_rate DECIMAL(4,3) DEFAULT NULL,
    last_calculated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Ensure unique domain pairs (bidirectional)
    CONSTRAINT domain_relationships_unique UNIQUE (source_domain, target_domain),
    CONSTRAINT domain_relationships_different_domains CHECK (source_domain != target_domain),
    CONSTRAINT domain_relationships_type_check CHECK (
        relationship_type IN ('similarity', 'complementary', 'analogous', 'hierarchical')
    )
);

-- Pattern Concept Embeddings table - for semantic similarity calculations
CREATE TABLE pattern_concept_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL,
    domain VARCHAR(100) NOT NULL,
    concepts TEXT[] NOT NULL DEFAULT '{}',
    embedding_vector DECIMAL[] DEFAULT NULL, -- Store as array of decimals
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'sentence-transformers',
    embedding_dimension INTEGER DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT pattern_concept_embeddings_concepts_check CHECK (array_length(concepts, 1) > 0)
);

-- Indexes for optimal performance

-- Abstract Patterns indexes
CREATE INDEX idx_abstract_patterns_domains ON abstract_patterns USING GIN (source_domains);
CREATE INDEX idx_abstract_patterns_abstraction_level ON abstract_patterns (abstraction_level);
CREATE INDEX idx_abstract_patterns_quality_score ON abstract_patterns (quality_score);
CREATE INDEX idx_abstract_patterns_usage_count ON abstract_patterns (usage_count);
CREATE INDEX idx_abstract_patterns_created_at ON abstract_patterns (created_at);

-- Domain Ontologies indexes  
CREATE INDEX idx_domain_ontologies_domain ON domain_ontologies (domain);
CREATE INDEX idx_domain_ontologies_confidence ON domain_ontologies (confidence_score);
CREATE INDEX idx_domain_ontologies_pattern_count ON domain_ontologies (pattern_count);

-- Cross-Domain Matches indexes
CREATE INDEX idx_cross_domain_matches_source_pattern ON cross_domain_matches (source_pattern_id);
CREATE INDEX idx_cross_domain_matches_target_pattern ON cross_domain_matches (target_pattern_id);
CREATE INDEX idx_cross_domain_matches_domains ON cross_domain_matches (source_domain, target_domain);
CREATE INDEX idx_cross_domain_matches_similarity ON cross_domain_matches (similarity_score);
CREATE INDEX idx_cross_domain_matches_confidence ON cross_domain_matches (confidence_level);
CREATE INDEX idx_cross_domain_matches_strategy ON cross_domain_matches (adaptation_strategy);
CREATE INDEX idx_cross_domain_matches_validation ON cross_domain_matches (validation_status);
CREATE INDEX idx_cross_domain_matches_discovered_at ON cross_domain_matches (discovered_at);

-- Domain Adaptations indexes
CREATE INDEX idx_domain_adaptations_source_pattern ON domain_adaptations (source_pattern_id);
CREATE INDEX idx_domain_adaptations_abstract_pattern ON domain_adaptations (abstract_pattern_id);
CREATE INDEX idx_domain_adaptations_adapted_pattern ON domain_adaptations (adapted_pattern_id);
CREATE INDEX idx_domain_adaptations_domains ON domain_adaptations (source_domain, target_domain);
CREATE INDEX idx_domain_adaptations_strategy ON domain_adaptations (adaptation_strategy);
CREATE INDEX idx_domain_adaptations_success ON domain_adaptations (success_probability);
CREATE INDEX idx_domain_adaptations_actual_success ON domain_adaptations (actual_success) WHERE actual_success IS NOT NULL;

-- Cross-Domain Usage indexes
CREATE INDEX idx_cross_domain_usage_pattern ON cross_domain_usage (pattern_id);
CREATE INDEX idx_cross_domain_usage_domains ON cross_domain_usage (original_domain, used_in_domain);
CREATE INDEX idx_cross_domain_usage_type ON cross_domain_usage (usage_type);
CREATE INDEX idx_cross_domain_usage_rating ON cross_domain_usage (success_rating) WHERE success_rating IS NOT NULL;
CREATE INDEX idx_cross_domain_usage_user ON cross_domain_usage (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_cross_domain_usage_used_at ON cross_domain_usage (used_at);

-- Domain Relationships indexes
CREATE INDEX idx_domain_relationships_source ON domain_relationships (source_domain);
CREATE INDEX idx_domain_relationships_target ON domain_relationships (target_domain);
CREATE INDEX idx_domain_relationships_strength ON domain_relationships (strength_score);
CREATE INDEX idx_domain_relationships_type ON domain_relationships (relationship_type);
CREATE INDEX idx_domain_relationships_success_rate ON domain_relationships (average_success_rate) WHERE average_success_rate IS NOT NULL;

-- Pattern Concept Embeddings indexes
CREATE INDEX idx_pattern_concept_embeddings_pattern ON pattern_concept_embeddings (pattern_id);
CREATE INDEX idx_pattern_concept_embeddings_domain ON pattern_concept_embeddings (domain);
CREATE INDEX idx_pattern_concept_embeddings_concepts ON pattern_concept_embeddings USING GIN (concepts);
CREATE INDEX idx_pattern_concept_embeddings_model ON pattern_concept_embeddings (embedding_model);

-- GIN indexes for JSONB columns
CREATE INDEX idx_abstract_patterns_conceptual_structure ON abstract_patterns USING GIN (conceptual_structure);
CREATE INDEX idx_abstract_patterns_variable_components ON abstract_patterns USING GIN (variable_components);
CREATE INDEX idx_domain_ontologies_concept_relationships ON domain_ontologies USING GIN (concept_relationships);
CREATE INDEX idx_domain_adaptations_concept_mappings ON domain_adaptations USING GIN (concept_mappings);
CREATE INDEX idx_domain_adaptations_tech_substitutions ON domain_adaptations USING GIN (technology_substitutions);
CREATE INDEX idx_cross_domain_usage_metadata ON cross_domain_usage USING GIN (metadata);

-- Triggers for updating timestamps

-- Update abstract_patterns updated_at
CREATE OR REPLACE FUNCTION update_abstract_patterns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_abstract_patterns_updated_at
    BEFORE UPDATE ON abstract_patterns
    FOR EACH ROW EXECUTE FUNCTION update_abstract_patterns_updated_at();

-- Update pattern_concept_embeddings updated_at
CREATE OR REPLACE FUNCTION update_pattern_concept_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_pattern_concept_embeddings_updated_at
    BEFORE UPDATE ON pattern_concept_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_pattern_concept_embeddings_updated_at();

-- Views for common queries

-- View for successful cross-domain adaptations
CREATE VIEW successful_cross_domain_adaptations AS
SELECT 
    da.id,
    da.source_domain,
    da.target_domain,
    da.adaptation_strategy,
    da.success_probability,
    da.actual_success,
    da.created_at,
    ap.title as abstract_pattern_title,
    ap.abstraction_level,
    cdu.success_rating as user_rating,
    cdu.feedback as user_feedback
FROM domain_adaptations da
JOIN abstract_patterns ap ON da.abstract_pattern_id = ap.id
LEFT JOIN cross_domain_usage cdu ON da.id = cdu.adaptation_id
WHERE da.actual_success = true;

-- View for domain relationship summary
CREATE VIEW domain_relationship_summary AS
SELECT 
    dr.source_domain,
    dr.target_domain,
    dr.strength_score,
    dr.shared_concepts,
    dr.successful_adaptations,
    dr.total_adaptation_attempts,
    dr.average_success_rate,
    COUNT(cdm.id) as pattern_matches,
    AVG(cdm.similarity_score) as avg_similarity
FROM domain_relationships dr
LEFT JOIN cross_domain_matches cdm ON 
    (dr.source_domain = cdm.source_domain AND dr.target_domain = cdm.target_domain) OR
    (dr.source_domain = cdm.target_domain AND dr.target_domain = cdm.source_domain)
GROUP BY dr.id, dr.source_domain, dr.target_domain, dr.strength_score, 
         dr.shared_concepts, dr.successful_adaptations, dr.total_adaptation_attempts, dr.average_success_rate;

-- View for pattern cross-domain usage statistics
CREATE VIEW pattern_cross_domain_stats AS
SELECT 
    cdu.pattern_id,
    cdu.original_domain,
    COUNT(*) as total_cross_domain_uses,
    COUNT(DISTINCT cdu.used_in_domain) as domains_used_in,
    AVG(cdu.success_rating::DECIMAL) as avg_success_rating,
    COUNT(CASE WHEN cdu.usage_type = 'adapted_use' THEN 1 END) as adapted_uses,
    COUNT(CASE WHEN cdu.usage_type = 'direct_use' THEN 1 END) as direct_uses
FROM cross_domain_usage cdu
GROUP BY cdu.pattern_id, cdu.original_domain;

-- Comments for documentation
COMMENT ON TABLE abstract_patterns IS 'Stores domain-agnostic pattern templates that can be reused across different domains';
COMMENT ON TABLE domain_ontologies IS 'Contains the conceptual structure and knowledge base for each domain';
COMMENT ON TABLE cross_domain_matches IS 'Records similarities between patterns from different domains';
COMMENT ON TABLE domain_adaptations IS 'Tracks successful adaptations of patterns from one domain to another';
COMMENT ON TABLE cross_domain_usage IS 'Analytics for how patterns are used across different domains';
COMMENT ON TABLE domain_relationships IS 'Quantifies relationships and compatibility between domains';
COMMENT ON TABLE pattern_concept_embeddings IS 'Stores vector embeddings for semantic similarity calculations';

-- Grant permissions (adjust as needed for your security model)
-- These would typically be more restrictive in production
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO betty_api_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO betty_api_user;

-- Success! Cross-Domain Pattern Intelligence database schema is now ready
-- This enables Betty to store and analyze patterns across different knowledge domains
-- enabling revolutionary cross-domain pattern transfer and adaptation capabilities