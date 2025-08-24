-- ABOUTME: Database schema for BETTY's Advanced Pattern Quality Scoring System
-- ABOUTME: PostgreSQL tables for quality scores, predictions, and pattern intelligence data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Quality Scores table
CREATE TABLE IF NOT EXISTS quality_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    
    -- Context information
    context_domain VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL DEFAULT '{}',
    
    -- Dimension scores
    technical_accuracy_score DECIMAL(3,2) NOT NULL CHECK (technical_accuracy_score >= 0 AND technical_accuracy_score <= 1),
    technical_accuracy_confidence DECIMAL(3,2) NOT NULL CHECK (technical_accuracy_confidence >= 0 AND technical_accuracy_confidence <= 1),
    technical_accuracy_metrics JSONB NOT NULL DEFAULT '{}',
    
    source_credibility_score DECIMAL(3,2) NOT NULL CHECK (source_credibility_score >= 0 AND source_credibility_score <= 1),
    source_credibility_confidence DECIMAL(3,2) NOT NULL CHECK (source_credibility_confidence >= 0 AND source_credibility_confidence <= 1),
    source_credibility_metrics JSONB NOT NULL DEFAULT '{}',
    
    practical_utility_score DECIMAL(3,2) NOT NULL CHECK (practical_utility_score >= 0 AND practical_utility_score <= 1),
    practical_utility_confidence DECIMAL(3,2) NOT NULL CHECK (practical_utility_confidence >= 0 AND practical_utility_confidence <= 1),
    practical_utility_metrics JSONB NOT NULL DEFAULT '{}',
    
    completeness_score DECIMAL(3,2) NOT NULL CHECK (completeness_score >= 0 AND completeness_score <= 1),
    completeness_confidence DECIMAL(3,2) NOT NULL CHECK (completeness_confidence >= 0 AND completeness_confidence <= 1),
    completeness_metrics JSONB NOT NULL DEFAULT '{}',
    
    -- Overall scoring
    overall_score DECIMAL(3,2) NOT NULL CHECK (overall_score >= 0 AND overall_score <= 1),
    normalized_score INTEGER NOT NULL CHECK (normalized_score >= 0 AND normalized_score <= 100),
    confidence_interval_lower DECIMAL(3,2) NOT NULL CHECK (confidence_interval_lower >= 0 AND confidence_interval_lower <= 1),
    confidence_interval_upper DECIMAL(3,2) NOT NULL CHECK (confidence_interval_upper >= 0 AND confidence_interval_upper <= 1),
    
    -- Predictions
    success_probability VARCHAR(20) NOT NULL CHECK (success_probability IN ('very_low', 'low', 'medium', 'high', 'very_high')),
    success_percentage DECIMAL(5,2) NOT NULL CHECK (success_percentage >= 0 AND success_percentage <= 100),
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('minimal', 'low', 'moderate', 'high', 'critical')),
    risk_factors TEXT[] DEFAULT '{}',
    
    -- Evidence and metadata
    evidence TEXT[] DEFAULT '{}',
    scoring_algorithm_version VARCHAR(10) NOT NULL DEFAULT '1.0.0',
    scorer_metadata JSONB NOT NULL DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(pattern_id, context_domain, scoring_algorithm_version)
);

-- Success Predictions table
CREATE TABLE IF NOT EXISTS success_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    
    -- Context
    context_domain VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL DEFAULT '{}',
    
    -- Prediction results
    success_probability VARCHAR(20) NOT NULL CHECK (success_probability IN ('very_low', 'low', 'medium', 'high', 'very_high')),
    success_percentage DECIMAL(5,2) NOT NULL CHECK (success_percentage >= 0 AND success_percentage <= 100),
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Factors
    positive_factors TEXT[] DEFAULT '{}',
    negative_factors TEXT[] DEFAULT '{}',
    risk_mitigation_suggestions TEXT[] DEFAULT '{}',
    
    -- Historical analysis
    similar_patterns_outcomes JSONB DEFAULT '[]',
    success_rate_trend DECIMAL(3,2),
    
    -- Model information
    model_version VARCHAR(10) NOT NULL DEFAULT '1.0.0',
    prediction_features DECIMAL[] DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Pattern Relationships table (for semantic relationships)
CREATE TABLE IF NOT EXISTS pattern_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    to_pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    
    -- Relationship details
    relationship_type VARCHAR(50) NOT NULL,
    strength DECIMAL(3,2) NOT NULL CHECK (strength >= 0 AND strength <= 1),
    bidirectional BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Evidence and metadata
    evidence TEXT[] DEFAULT '{}',
    discovery_method VARCHAR(50) NOT NULL DEFAULT 'semantic_analysis',
    validation_score DECIMAL(3,2) DEFAULT 0.5,
    
    -- Timestamps
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_validated_at TIMESTAMPTZ,
    
    -- Constraints
    UNIQUE(from_pattern_id, to_pattern_id, relationship_type),
    CHECK (from_pattern_id != to_pattern_id)
);

-- Pattern Recommendations table
CREATE TABLE IF NOT EXISTS pattern_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Query and context
    query_text TEXT NOT NULL,
    query_embedding_id VARCHAR(100),  -- Reference to vector in Qdrant
    context_domain VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL DEFAULT '{}',
    
    -- Recommended pattern
    pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    quality_score_id UUID REFERENCES quality_scores(id),
    
    -- Recommendation scoring
    relevance_score DECIMAL(3,2) NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    composite_score DECIMAL(3,2) NOT NULL CHECK (composite_score >= 0 AND composite_score <= 1),
    recommendation_rank INTEGER NOT NULL,
    
    -- Recommendation details
    recommendation_reason TEXT NOT NULL,
    implementation_notes TEXT[] DEFAULT '{}',
    alternative_patterns UUID[] DEFAULT '{}',
    
    -- Feedback tracking
    user_feedback_rating INTEGER CHECK (user_feedback_rating >= 1 AND user_feedback_rating <= 5),
    user_feedback_text TEXT,
    implementation_outcome VARCHAR(20) CHECK (implementation_outcome IN ('success', 'partial', 'failure', 'unknown')),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    feedback_at TIMESTAMPTZ
);

-- Technical Accuracy Metrics table
CREATE TABLE IF NOT EXISTS technical_accuracy_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    quality_score_id UUID REFERENCES quality_scores(id),
    
    -- Core metrics
    syntax_correctness DECIMAL(3,2) NOT NULL DEFAULT 0,
    security_compliance DECIMAL(3,2) NOT NULL DEFAULT 0,
    performance_considerations DECIMAL(3,2) NOT NULL DEFAULT 0,
    scalability_assessment DECIMAL(3,2) NOT NULL DEFAULT 0,
    maintainability_score DECIMAL(3,2) NOT NULL DEFAULT 0,
    
    -- Security specific
    owasp_compliance JSONB DEFAULT '{}',
    vulnerability_count INTEGER DEFAULT 0,
    security_best_practices DECIMAL(3,2) DEFAULT 0,
    
    -- Code quality metrics
    cyclomatic_complexity DECIMAL(5,2),
    code_coverage DECIMAL(3,2),
    test_quality DECIMAL(3,2),
    lines_of_code INTEGER,
    
    -- Analysis metadata
    analysis_tools_used TEXT[] DEFAULT '{}',
    analysis_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    analysis_version VARCHAR(10) DEFAULT '1.0.0',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Source Credibility Metrics table
CREATE TABLE IF NOT EXISTS source_credibility_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    quality_score_id UUID REFERENCES quality_scores(id),
    
    -- Core metrics
    author_reputation DECIMAL(3,2) NOT NULL DEFAULT 0,
    publication_authority DECIMAL(3,2) NOT NULL DEFAULT 0,
    peer_validation DECIMAL(3,2) NOT NULL DEFAULT 0,
    reference_quality DECIMAL(3,2) NOT NULL DEFAULT 0,
    
    -- Author metrics
    author_name VARCHAR(200),
    author_email VARCHAR(200),
    author_contributions INTEGER DEFAULT 0,
    author_expertise_score DECIMAL(3,2) DEFAULT 0,
    author_citation_count INTEGER DEFAULT 0,
    
    -- Publication metrics
    source_url TEXT,
    source_domain VARCHAR(200),
    source_domain_authority DECIMAL(3,2) DEFAULT 0,
    publication_date TIMESTAMPTZ,
    publication_recency DECIMAL(3,2) DEFAULT 0,
    cross_references INTEGER DEFAULT 0,
    
    -- Validation data
    peer_reviews INTEGER DEFAULT 0,
    community_upvotes INTEGER DEFAULT 0,
    community_downvotes INTEGER DEFAULT 0,
    external_citations INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Pattern Usage Analytics table
CREATE TABLE IF NOT EXISTS pattern_usage_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    
    -- Usage metrics
    total_views INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    implementation_attempts INTEGER DEFAULT 0,
    successful_implementations INTEGER DEFAULT 0,
    failed_implementations INTEGER DEFAULT 0,
    
    -- Time-based metrics
    views_last_30_days INTEGER DEFAULT 0,
    implementations_last_30_days INTEGER DEFAULT 0,
    avg_time_to_implement_hours DECIMAL(8,2),
    
    -- Outcome tracking
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2) CHECK (average_rating >= 1 AND average_rating <= 5),
    
    -- Success indicators
    problem_resolution_rate DECIMAL(3,2) DEFAULT 0,
    user_satisfaction_score DECIMAL(3,2) DEFAULT 0,
    recommendation_acceptance_rate DECIMAL(3,2) DEFAULT 0,
    
    -- ROI and business metrics
    estimated_time_saved_hours INTEGER DEFAULT 0,
    estimated_cost_saved_usd DECIMAL(10,2) DEFAULT 0,
    business_value_score DECIMAL(3,2) DEFAULT 0,
    
    -- Timestamps
    last_updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Pattern Quality History table (for tracking score changes over time)
CREATE TABLE IF NOT EXISTS quality_score_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    quality_score_id UUID NOT NULL REFERENCES quality_scores(id) ON DELETE CASCADE,
    
    -- Score snapshot
    overall_score DECIMAL(3,2) NOT NULL,
    technical_accuracy DECIMAL(3,2) NOT NULL,
    source_credibility DECIMAL(3,2) NOT NULL,
    practical_utility DECIMAL(3,2) NOT NULL,
    completeness DECIMAL(3,2) NOT NULL,
    
    -- Change tracking
    score_change_reason VARCHAR(200),
    previous_score DECIMAL(3,2),
    score_delta DECIMAL(4,3),
    
    -- Context
    algorithm_version VARCHAR(10) NOT NULL,
    scoring_context JSONB DEFAULT '{}',
    
    -- Timestamps
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_quality_scores_pattern_id ON quality_scores(pattern_id);
CREATE INDEX IF NOT EXISTS idx_quality_scores_overall_score ON quality_scores(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_quality_scores_context_domain ON quality_scores(context_domain);
CREATE INDEX IF NOT EXISTS idx_quality_scores_created_at ON quality_scores(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_success_predictions_pattern_id ON success_predictions(pattern_id);
CREATE INDEX IF NOT EXISTS idx_success_predictions_success_probability ON success_predictions(success_probability);
CREATE INDEX IF NOT EXISTS idx_success_predictions_confidence ON success_predictions(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_pattern_relationships_from_pattern ON pattern_relationships(from_pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_relationships_to_pattern ON pattern_relationships(to_pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_relationships_type ON pattern_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_pattern_relationships_strength ON pattern_relationships(strength DESC);

CREATE INDEX IF NOT EXISTS idx_pattern_recommendations_pattern_id ON pattern_recommendations(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_recommendations_relevance ON pattern_recommendations(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_pattern_recommendations_context ON pattern_recommendations(context_domain);
CREATE INDEX IF NOT EXISTS idx_pattern_recommendations_query_embedding ON pattern_recommendations(query_embedding_id);

CREATE INDEX IF NOT EXISTS idx_usage_analytics_pattern_id ON pattern_usage_analytics(pattern_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_success_rate ON pattern_usage_analytics(problem_resolution_rate DESC);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_satisfaction ON pattern_usage_analytics(user_satisfaction_score DESC);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_quality_scores_pattern_context ON quality_scores(pattern_id, context_domain);
CREATE INDEX IF NOT EXISTS idx_recommendations_context_score ON pattern_recommendations(context_domain, composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_relationships_patterns ON pattern_relationships(from_pattern_id, to_pattern_id);

-- Triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER update_quality_scores_updated_at BEFORE UPDATE ON quality_scores
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_success_predictions_updated_at BEFORE UPDATE ON success_predictions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_technical_metrics_updated_at BEFORE UPDATE ON technical_accuracy_metrics
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_credibility_metrics_updated_at BEFORE UPDATE ON source_credibility_metrics
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW pattern_quality_summary AS
SELECT 
    ki.id as pattern_id,
    ki.title as pattern_title,
    ki.knowledge_type,
    qs.overall_score,
    qs.normalized_score,
    qs.success_probability,
    qs.success_percentage,
    qs.risk_level,
    qs.context_domain,
    ua.total_views,
    ua.successful_implementations,
    ua.user_satisfaction_score,
    qs.created_at as scored_at
FROM knowledge_items ki
LEFT JOIN quality_scores qs ON ki.id = qs.pattern_id
LEFT JOIN pattern_usage_analytics ua ON ki.id = ua.pattern_id
WHERE qs.id IS NOT NULL
ORDER BY qs.overall_score DESC;

CREATE OR REPLACE VIEW top_quality_patterns AS
SELECT 
    pattern_id,
    pattern_title,
    overall_score,
    success_probability,
    context_domain,
    total_views,
    successful_implementations
FROM pattern_quality_summary
WHERE overall_score >= 0.8
ORDER BY overall_score DESC, successful_implementations DESC
LIMIT 100;

CREATE OR REPLACE VIEW pattern_improvement_opportunities AS
SELECT 
    pattern_id,
    pattern_title,
    overall_score,
    CASE 
        WHEN technical_accuracy_score < 0.6 THEN 'Technical Accuracy'
        WHEN source_credibility_score < 0.6 THEN 'Source Credibility'
        WHEN practical_utility_score < 0.6 THEN 'Practical Utility'
        WHEN completeness_score < 0.6 THEN 'Completeness'
        ELSE 'General Quality'
    END as improvement_area,
    context_domain
FROM quality_scores qs
JOIN knowledge_items ki ON qs.pattern_id = ki.id
WHERE qs.overall_score < 0.7
ORDER BY qs.overall_score ASC;

-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO betty_api;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO betty_api;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO betty_api;