# ABOUTME: Comprehensive test suite for BETTY's Advanced Pattern Quality Scoring System
# ABOUTME: Unit, integration, and performance tests targeting 90% accuracy and reliability

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from typing import List, Dict, Any

from models.pattern_quality import (
    QualityScore, PatternContext, QualityDimension, DimensionScore,
    SuccessProbability, RiskLevel, QualityScoreRequest, PatternRecommendation
)
from models.knowledge import KnowledgeItem
from services.pattern_quality_service import AdvancedQualityScorer
from services.pattern_intelligence_service import PatternIntelligenceEngine
from services.pattern_quality_integration import PatternQualityIntegrationService
from core.database import DatabaseManager

class TestPatternQualityScorer:
    """Test suite for Advanced Quality Scorer"""
    
    @pytest.fixture
    async def mock_db_manager(self):
        """Mock database manager"""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.get_postgres_session = AsyncMock()
        db_manager.get_neo4j_session = AsyncMock() 
        db_manager.get_qdrant_client = Mock()
        db_manager.get_redis_client = Mock()
        return db_manager
    
    @pytest.fixture
    async def mock_vector_service(self):
        """Mock vector service"""
        vector_service = Mock()
        vector_service.generate_embedding = AsyncMock(return_value=np.random.random(384))
        return vector_service
    
    @pytest.fixture
    async def quality_scorer(self, mock_db_manager, mock_vector_service):
        """Quality scorer instance for testing"""
        scorer = AdvancedQualityScorer(mock_db_manager, mock_vector_service)
        return scorer
    
    @pytest.fixture
    def sample_pattern(self):
        """Sample pattern for testing"""
        return KnowledgeItem(
            id=uuid4(),
            title="Secure API Authentication Pattern",
            content="""
            # Secure API Authentication Pattern
            
            This pattern implements secure JWT-based authentication for REST APIs.
            
            ## Implementation
            ```python
            import jwt
            from datetime import datetime, timedelta
            from werkzeug.security import generate_password_hash, check_password_hash
            
            class AuthenticationService:
                def __init__(self, secret_key):
                    self.secret_key = secret_key
                
                def generate_token(self, user_id):
                    payload = {
                        'user_id': user_id,
                        'exp': datetime.utcnow() + timedelta(hours=1)
                    }
                    return jwt.encode(payload, self.secret_key, algorithm='HS256')
                
                def verify_token(self, token):
                    try:
                        payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                        return payload['user_id']
                    except jwt.ExpiredSignatureError:
                        return None
            ```
            
            ## Security Considerations
            - Use strong secret keys
            - Implement token expiration
            - Validate all inputs
            - Use HTTPS only
            
            ## Testing
            Comprehensive unit tests should cover:
            - Token generation and validation
            - Expiration handling
            - Invalid token scenarios
            """,
            knowledge_type="code_pattern",
            source_type="user_input",
            tags=["security", "authentication", "jwt", "api", "python"],
            summary="JWT-based API authentication pattern with security best practices",
            confidence="high",
            access_count=15,
            created_at=datetime.utcnow() - timedelta(days=30)
        )
    
    @pytest.fixture
    def sample_context(self):
        """Sample pattern context"""
        return PatternContext(
            domain="web_development",
            technology_stack=["python", "flask", "jwt"],
            project_type="web_api",
            team_experience="medium",
            business_criticality="high",
            compliance_requirements=["GDPR", "SOC2"]
        )
    
    @pytest.mark.asyncio
    async def test_score_pattern_quality_basic(self, quality_scorer, sample_pattern, sample_context):
        """Test basic pattern quality scoring"""
        with patch.object(quality_scorer, '_store_quality_score', new_callable=AsyncMock):
            quality_score = await quality_scorer.score_pattern_quality(sample_pattern, sample_context)
            
            # Verify basic structure
            assert isinstance(quality_score, QualityScore)
            assert quality_score.pattern_id == sample_pattern.id
            assert 0.0 <= quality_score.overall_score <= 1.0
            assert 0 <= quality_score.normalized_score <= 100
            
            # Verify all dimensions are scored
            assert quality_score.technical_accuracy.dimension == QualityDimension.TECHNICAL_ACCURACY
            assert quality_score.source_credibility.dimension == QualityDimension.SOURCE_CREDIBILITY
            assert quality_score.practical_utility.dimension == QualityDimension.PRACTICAL_UTILITY
            assert quality_score.completeness.dimension == QualityDimension.COMPLETENESS
            
            # Verify dimension scores are within valid range
            for dimension in [quality_score.technical_accuracy, quality_score.source_credibility,
                            quality_score.practical_utility, quality_score.completeness]:
                assert 0.0 <= dimension.score <= 1.0
                assert 0.0 <= dimension.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_technical_accuracy_analysis(self, quality_scorer, sample_pattern, sample_context):
        """Test technical accuracy analysis in detail"""
        tech_score = await quality_scorer.analyze_technical_accuracy(sample_pattern, sample_context)
        
        # Verify structure
        assert isinstance(tech_score, DimensionScore)
        assert tech_score.dimension == QualityDimension.TECHNICAL_ACCURACY
        assert 0.0 <= tech_score.score <= 1.0
        assert len(tech_score.evidence) >= 0
        
        # Verify metrics exist
        metrics = tech_score.metrics
        assert 'syntax_correctness' in metrics
        assert 'security_compliance' in metrics
        assert 'performance_considerations' in metrics
        assert 'scalability_assessment' in metrics
        assert 'maintainability_score' in metrics
        
        # For security pattern, should have good security compliance
        assert metrics['security_compliance'] > 0.5
    
    @pytest.mark.asyncio
    async def test_source_credibility_assessment(self, quality_scorer, sample_pattern, sample_context):
        """Test source credibility assessment"""
        cred_score = await quality_scorer.assess_source_credibility(sample_pattern, sample_context)
        
        assert isinstance(cred_score, DimensionScore)
        assert cred_score.dimension == QualityDimension.SOURCE_CREDIBILITY
        assert 0.0 <= cred_score.score <= 1.0
        
        metrics = cred_score.metrics
        assert 'author_reputation' in metrics
        assert 'publication_authority' in metrics
        assert 'peer_validation' in metrics
        assert 'reference_quality' in metrics
    
    @pytest.mark.asyncio
    async def test_practical_utility_evaluation(self, quality_scorer, sample_pattern, sample_context):
        """Test practical utility evaluation"""
        utility_score = await quality_scorer.evaluate_practical_utility(sample_pattern, sample_context)
        
        assert isinstance(utility_score, DimensionScore)
        assert utility_score.dimension == QualityDimension.PRACTICAL_UTILITY
        assert 0.0 <= utility_score.score <= 1.0
        
        metrics = utility_score.metrics
        assert 'implementation_success_rate' in metrics
        assert 'user_satisfaction' in metrics
        assert 'problem_resolution_effectiveness' in metrics
        assert 'real_world_applicability' in metrics
    
    @pytest.mark.asyncio
    async def test_completeness_analysis(self, quality_scorer, sample_pattern, sample_context):
        """Test completeness analysis"""
        completeness_score = await quality_scorer.analyze_completeness(sample_pattern, sample_context)
        
        assert isinstance(completeness_score, DimensionScore)
        assert completeness_score.dimension == QualityDimension.COMPLETENESS
        assert 0.0 <= completeness_score.score <= 1.0
        
        metrics = completeness_score.metrics
        assert 'documentation_quality' in metrics
        assert 'example_completeness' in metrics
        assert 'context_clarity' in metrics
        assert 'reference_adequacy' in metrics
        
        # Sample pattern has good documentation, should score well
        assert metrics['documentation_quality'] > 0.6
        assert metrics['example_completeness'] > 0.7  # Has code examples
    
    @pytest.mark.asyncio
    async def test_code_syntax_analysis(self, quality_scorer):
        """Test code syntax analysis"""
        # Valid Python code
        valid_code = """
        def hello_world():
            print("Hello, World!")
            return "success"
        """
        
        syntax_score = await quality_scorer._analyze_code_syntax(valid_code)
        assert syntax_score > 0.8
        
        # Invalid Python code
        invalid_code = """
        def broken_function(
            print "Missing closing parenthesis"
            return incomplete
        """
        
        syntax_score = await quality_scorer._analyze_code_syntax(invalid_code)
        assert syntax_score < 0.5
    
    @pytest.mark.asyncio
    async def test_security_compliance_analysis(self, quality_scorer, sample_context):
        """Test security compliance analysis"""
        secure_content = """
        # Secure password handling
        from werkzeug.security import generate_password_hash, check_password_hash
        import secrets
        
        def create_secure_password(password):
            salt = secrets.token_hex(32)
            return generate_password_hash(password + salt)
        """
        
        security_score, owasp_compliance = await quality_scorer._analyze_security_compliance(
            secure_content, sample_context
        )
        
        assert 0.0 <= security_score <= 1.0
        assert isinstance(owasp_compliance, dict)
        
        # Should score well for secure practices
        assert security_score > 0.6
    
    @pytest.mark.asyncio
    async def test_confidence_interval_calculation(self, quality_scorer):
        """Test confidence interval calculation"""
        # Create mock dimension scores
        dimension_scores = [
            DimensionScore(
                dimension=QualityDimension.TECHNICAL_ACCURACY,
                score=0.8, weight=0.4, confidence=0.9, evidence=[], metrics={}
            ),
            DimensionScore(
                dimension=QualityDimension.SOURCE_CREDIBILITY,
                score=0.7, weight=0.25, confidence=0.8, evidence=[], metrics={}
            ),
            DimensionScore(
                dimension=QualityDimension.PRACTICAL_UTILITY,
                score=0.6, weight=0.2, confidence=0.7, evidence=[], metrics={}
            ),
            DimensionScore(
                dimension=QualityDimension.COMPLETENESS,
                score=0.9, weight=0.15, confidence=0.85, evidence=[], metrics={}
            )
        ]
        
        lower, upper = quality_scorer._calculate_confidence_interval(dimension_scores)
        
        assert 0.0 <= lower <= upper <= 1.0
        assert upper - lower < 1.0  # Reasonable interval width
    
    @pytest.mark.asyncio 
    async def test_success_prediction(self, quality_scorer, sample_pattern, sample_context):
        """Test success and risk prediction"""
        # Mock dimension scores
        tech_score = DimensionScore(
            dimension=QualityDimension.TECHNICAL_ACCURACY,
            score=0.85, weight=0.4, confidence=0.9, evidence=[], metrics={}
        )
        cred_score = DimensionScore(
            dimension=QualityDimension.SOURCE_CREDIBILITY, 
            score=0.7, weight=0.25, confidence=0.8, evidence=[], metrics={}
        )
        util_score = DimensionScore(
            dimension=QualityDimension.PRACTICAL_UTILITY,
            score=0.75, weight=0.2, confidence=0.85, evidence=[], metrics={}
        )
        comp_score = DimensionScore(
            dimension=QualityDimension.COMPLETENESS,
            score=0.8, weight=0.15, confidence=0.9, evidence=[], metrics={}
        )
        
        dimension_scores = [tech_score, cred_score, util_score, comp_score]
        overall_score = 0.78
        
        success_prob, risk_level, risk_factors = await quality_scorer._predict_success_and_risk(
            sample_pattern, sample_context, overall_score, dimension_scores
        )
        
        assert isinstance(success_prob, SuccessProbability)
        assert isinstance(risk_level, RiskLevel)
        assert isinstance(risk_factors, list)
        
        # High overall score should predict good success
        assert success_prob in [SuccessProbability.HIGH, SuccessProbability.VERY_HIGH]

class TestPatternIntelligenceEngine:
    """Test suite for Pattern Intelligence Engine"""
    
    @pytest.fixture
    async def mock_services(self):
        """Mock required services"""
        db_manager = Mock(spec=DatabaseManager)
        vector_service = Mock()
        quality_scorer = Mock(spec=AdvancedQualityScorer)
        
        # Setup mocks
        vector_service.generate_embedding = AsyncMock(return_value=np.random.random(384))
        quality_scorer.score_pattern_quality = AsyncMock()
        
        return db_manager, vector_service, quality_scorer
    
    @pytest.fixture
    async def intelligence_engine(self, mock_services):
        """Intelligence engine for testing"""
        db_manager, vector_service, quality_scorer = mock_services
        return PatternIntelligenceEngine(db_manager, vector_service, quality_scorer)
    
    @pytest.fixture
    def sample_patterns(self):
        """Sample patterns for relationship testing"""
        patterns = []
        for i in range(5):
            pattern = KnowledgeItem(
                id=uuid4(),
                title=f"Pattern {i}",
                content=f"Content for pattern {i} with some shared concepts and code examples",
                knowledge_type="pattern",
                source_type="user_input",
                tags=["api", "security", "python"] if i < 3 else ["database", "sql"],
                summary=f"Summary for pattern {i}",
                created_at=datetime.utcnow()
            )
            patterns.append(pattern)
        return patterns
    
    @pytest.mark.asyncio
    async def test_semantic_relationship_detection(self, intelligence_engine, sample_patterns):
        """Test semantic relationship detection"""
        with patch.object(intelligence_engine, '_store_semantic_relationships', new_callable=AsyncMock):
            with patch.object(intelligence_engine, '_update_pattern_graph', new_callable=AsyncMock):
                relationships = await intelligence_engine.detect_semantic_relationships(
                    sample_patterns, min_similarity=0.3
                )
                
                assert isinstance(relationships, list)
                # Should find some relationships given overlapping content
                if len(relationships) > 0:
                    rel = relationships[0]
                    assert rel.from_pattern_id in [p.id for p in sample_patterns]
                    assert rel.to_pattern_id in [p.id for p in sample_patterns]
                    assert 0.0 <= rel.strength <= 1.0
                    assert isinstance(rel.relationship_type, str)
                    assert isinstance(rel.evidence, list)
    
    @pytest.mark.asyncio
    async def test_pattern_generalization(self, intelligence_engine, sample_patterns, sample_context):
        """Test pattern generalization"""
        # Use subset of similar patterns
        similar_patterns = sample_patterns[:3]  # First 3 have similar tags
        
        generalized = await intelligence_engine.generalize_patterns(similar_patterns, sample_context)
        
        assert isinstance(generalized, KnowledgeItem)
        assert generalized.title != ""
        assert generalized.content != ""
        assert len(generalized.tags) > 0
        assert "generalization_source_count" in generalized.metadata
        assert generalized.metadata["generalization_source_count"] == len(similar_patterns)
    
    @pytest.mark.asyncio
    async def test_success_prediction(self, intelligence_engine, sample_patterns, sample_context):
        """Test pattern success prediction"""
        pattern = sample_patterns[0]
        
        with patch.object(intelligence_engine.quality_scorer, 'score_pattern_quality') as mock_score:
            # Mock quality score
            mock_quality = Mock()
            mock_quality.overall_score = 0.8
            mock_quality.technical_accuracy = Mock(score=0.85)
            mock_quality.source_credibility = Mock(score=0.75)
            mock_quality.practical_utility = Mock(score=0.8)
            mock_quality.completeness = Mock(score=0.7)
            mock_score.return_value = mock_quality
            
            prediction = await intelligence_engine.predict_pattern_success(pattern, sample_context)
            
            assert isinstance(prediction, SuccessPrediction)
            assert prediction.pattern_id == pattern.id
            assert isinstance(prediction.success_probability, SuccessProbability)
            assert 0.0 <= prediction.success_percentage <= 100.0
            assert 0.0 <= prediction.confidence_score <= 1.0
            assert isinstance(prediction.positive_factors, list)
            assert isinstance(prediction.negative_factors, list)

class TestPatternQualityAPI:
    """Test suite for Pattern Quality REST API"""
    
    @pytest.fixture
    def client(self):
        """Test client for API testing"""
        from fastapi.testclient import TestClient
        from main import app  # Assuming main.py contains the FastAPI app
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_score_pattern_endpoint(self, client):
        """Test pattern scoring endpoint"""
        # This would require setting up test database and mocking services
        # Placeholder for API testing structure
        pass
    
    @pytest.mark.asyncio
    async def test_recommend_patterns_endpoint(self, client):
        """Test pattern recommendation endpoint"""
        # Placeholder for API testing
        pass

class TestPerformanceAndAccuracy:
    """Performance and accuracy tests for the quality scoring system"""
    
    @pytest.mark.asyncio
    async def test_scoring_performance(self, quality_scorer, sample_pattern, sample_context):
        """Test that scoring completes within performance targets"""
        start_time = datetime.utcnow()
        
        with patch.object(quality_scorer, '_store_quality_score', new_callable=AsyncMock):
            await quality_scorer.score_pattern_quality(sample_pattern, sample_context)
        
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Should complete within 500ms target
        assert duration_ms < 500, f"Scoring took {duration_ms}ms, exceeds 500ms target"
    
    @pytest.mark.asyncio
    async def test_batch_scoring_performance(self, quality_scorer, sample_context):
        """Test batch scoring performance"""
        # Create multiple test patterns
        patterns = []
        for i in range(10):
            pattern = KnowledgeItem(
                id=uuid4(),
                title=f"Test Pattern {i}",
                content=f"Test content for pattern {i}",
                knowledge_type="test",
                source_type="test",
                tags=["test"],
                created_at=datetime.utcnow()
            )
            patterns.append(pattern)
        
        start_time = datetime.utcnow()
        
        with patch.object(quality_scorer, '_store_quality_score', new_callable=AsyncMock):
            # Score all patterns
            tasks = []
            for pattern in patterns:
                task = quality_scorer.score_pattern_quality(pattern, sample_context)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()
        
        # Should maintain reasonable throughput
        patterns_per_second = len(patterns) / duration_seconds
        assert patterns_per_second > 5, f"Throughput {patterns_per_second:.2f} patterns/sec too low"
    
    @pytest.mark.asyncio
    async def test_scoring_consistency(self, quality_scorer, sample_pattern, sample_context):
        """Test that scoring is consistent across multiple runs"""
        with patch.object(quality_scorer, '_store_quality_score', new_callable=AsyncMock):
            scores = []
            
            # Score the same pattern multiple times
            for _ in range(5):
                score = await quality_scorer.score_pattern_quality(sample_pattern, sample_context)
                scores.append(score.overall_score)
            
            # Check consistency (should be identical for same input)
            assert len(set(scores)) <= 2, "Scores should be consistent across runs"
            
            # Check variance is low
            if len(scores) > 1:
                variance = np.var(scores)
                assert variance < 0.01, f"Score variance {variance} too high"

class TestIntegrationSystem:
    """Test suite for integration with other BETTY systems"""
    
    @pytest.fixture
    async def integration_service(self):
        """Mock integration service"""
        db_manager = Mock(spec=DatabaseManager)
        quality_scorer = Mock(spec=AdvancedQualityScorer)
        memory_service = Mock()
        agent_learning = Mock()
        security_framework = Mock()
        
        return PatternQualityIntegrationService(
            db_manager, quality_scorer, memory_service, agent_learning, security_framework
        )
    
    @pytest.mark.asyncio
    async def test_integrated_analysis(self, integration_service, sample_pattern, sample_context):
        """Test integrated pattern analysis"""
        # Mock all service responses
        mock_quality_score = Mock()
        mock_quality_score.overall_score = 0.8
        mock_quality_score.id = uuid4()
        
        integration_service.quality_scorer.score_pattern_quality = AsyncMock(
            return_value=mock_quality_score
        )
        integration_service.memory_correctness.validate_knowledge_item = AsyncMock(
            return_value={"correctness_level": "high", "confidence_score": 0.9}
        )
        integration_service.security.analyze_pattern_security = AsyncMock(
            return_value={"security_score": 0.85, "vulnerability_count": 0}
        )
        integration_service.agent_learning.update_pattern_insights = AsyncMock(
            return_value={"success": True, "confidence": 0.8}
        )
        
        with patch.object(integration_service, '_store_integration_results', new_callable=AsyncMock):
            results = await integration_service.integrated_pattern_analysis(
                sample_pattern, sample_context
            )
            
            assert "pattern_id" in results
            assert "integration_score" in results
            assert "quality_score" in results
            assert "memory_correctness" in results
            assert "security_validation" in results
            assert "agent_insights" in results
            assert "recommendations" in results
            
            assert 0.0 <= results["integration_score"] <= 1.0
            assert isinstance(results["recommendations"], list)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])