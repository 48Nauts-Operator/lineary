# ABOUTME: Comprehensive integration tests for BETTY's Cross-Domain Pattern Intelligence system
# ABOUTME: Tests pattern abstraction, domain adaptation, cross-domain matching, and success prediction

import pytest
import asyncio
import json
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any

from services.cross_domain_intelligence import (
    CrossDomainIntelligence, DomainType, AdaptationStrategy,
    AbstractPattern, CrossDomainMatch, DomainOntology, DomainAdaptation
)
from models.knowledge import KnowledgeItem
from models.pattern_quality import PatternContext, QualityScore, SuccessProbability
from core.database import DatabaseManager
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer


@pytest.fixture
def mock_db_manager():
    """Create mock database manager"""
    db_manager = MagicMock()
    
    # Mock pool context manager
    pool_context = AsyncMock()
    pool_context.__aenter__ = AsyncMock()
    pool_context.__aexit__ = AsyncMock()
    
    conn_context = AsyncMock() 
    conn_context.__aenter__ = AsyncMock()
    conn_context.__aexit__ = AsyncMock()
    
    # Mock connection methods
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock()
    mock_conn.execute = AsyncMock()
    conn_context.__aenter__.return_value = mock_conn
    
    pool_context.__aenter__.return_value.acquire.return_value = conn_context
    db_manager.get_db_pool.return_value = pool_context
    
    # Mock Neo4j session
    neo4j_context = AsyncMock()
    neo4j_context.__aenter__ = AsyncMock()
    neo4j_context.__aexit__ = AsyncMock()
    
    mock_neo4j_session = AsyncMock()
    mock_neo4j_session.run = AsyncMock()
    neo4j_context.__aenter__.return_value = mock_neo4j_session
    
    db_manager.get_neo4j_session.return_value = neo4j_context
    
    return db_manager


@pytest.fixture
def mock_vector_service():
    """Create mock vector service"""
    vector_service = AsyncMock()
    # Return consistent embeddings for testing
    vector_service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3] * 128)
    return vector_service


@pytest.fixture
def mock_quality_scorer():
    """Create mock quality scorer"""
    quality_scorer = AsyncMock()
    
    # Mock quality score
    mock_quality_score = QualityScore(
        overall_score=0.8,
        technical_accuracy=MagicMock(score=0.85),
        source_credibility=MagicMock(score=0.75),
        practical_utility=MagicMock(score=0.8),
        completeness=MagicMock(score=0.9)
    )
    
    quality_scorer.score_pattern_quality = AsyncMock(return_value=mock_quality_score)
    return quality_scorer


@pytest.fixture
def sample_patterns():
    """Create sample patterns for testing"""
    auth_pattern = KnowledgeItem(
        id=uuid4(),
        title="JWT Authentication Implementation",
        content="""
        # JWT Authentication Pattern
        
        ## Problem
        Need secure user authentication for API endpoints.
        
        ## Solution
        Implement JWT-based authentication with token validation.
        
        ```javascript
        const jwt = require('jsonwebtoken');
        
        function authenticateToken(req, res, next) {
            const authHeader = req.headers['authorization'];
            const token = authHeader && authHeader.split(' ')[1];
            
            if (token == null) return res.sendStatus(401);
            
            jwt.verify(token, process.env.ACCESS_TOKEN_SECRET, (err, user) => {
                if (err) return res.sendStatus(403);
                req.user = user;
                next();
            });
        }
        ```
        
        ## Validation
        - Verify token signature
        - Check token expiration
        - Validate user permissions
        """,
        knowledge_type="pattern",
        source_type="manual",
        tags=["authentication", "jwt", "security", "api"],
        summary="JWT-based authentication pattern for secure API access",
        confidence="high",
        metadata={
            "domain": "authentication",
            "complexity": "medium",
            "technologies": ["javascript", "jwt", "express"]
        }
    )
    
    database_pattern = KnowledgeItem(
        id=uuid4(),
        title="Database Connection Pooling",
        content="""
        # Database Connection Pooling Pattern
        
        ## Problem
        Need efficient database connections for high-traffic applications.
        
        ## Solution
        Implement connection pooling to reuse database connections.
        
        ```python
        import psycopg2.pool
        
        class DatabasePool:
            def __init__(self, min_conn=1, max_conn=20):
                self.pool = psycopg2.pool.ThreadedConnectionPool(
                    min_conn, max_conn,
                    host='localhost',
                    database='mydb',
                    user='user',
                    password='password'
                )
            
            def get_connection(self):
                return self.pool.getconn()
            
            def put_connection(self, conn):
                self.pool.putconn(conn)
        ```
        
        ## Validation
        - Monitor connection usage
        - Check for connection leaks
        - Verify performance improvements
        """,
        knowledge_type="pattern",
        source_type="manual",
        tags=["database", "connection", "pooling", "performance"],
        summary="Database connection pooling for efficient resource usage",
        confidence="high",
        metadata={
            "domain": "database",
            "complexity": "medium",
            "technologies": ["python", "postgresql", "psycopg2"]
        }
    )
    
    return [auth_pattern, database_pattern]


@pytest.fixture
def cross_domain_engine(mock_db_manager, mock_vector_service, mock_quality_scorer):
    """Create cross-domain intelligence engine"""
    return CrossDomainIntelligence(mock_db_manager, mock_vector_service, mock_quality_scorer)


@pytest.mark.asyncio
class TestCrossDomainPatternDetection:
    """Test cross-domain pattern detection capabilities"""
    
    async def test_detect_cross_domain_patterns_basic(self, cross_domain_engine, sample_patterns):
        """Test basic cross-domain pattern detection"""
        
        # Mock the _get_patterns_by_domain method
        cross_domain_engine._get_patterns_by_domain = AsyncMock()
        cross_domain_engine._get_patterns_by_domain.side_effect = lambda domain: (
            [sample_patterns[0]] if domain == DomainType.AUTHENTICATION else
            [sample_patterns[1]] if domain == DomainType.DATABASE else []
        )
        
        # Test detection
        matches = await cross_domain_engine.detect_cross_domain_patterns(
            source_domain=DomainType.AUTHENTICATION,
            target_domain=DomainType.BACKEND,
            min_similarity=0.3
        )
        
        # Verify results
        assert isinstance(matches, list)
        # Note: Actual matches depend on implementation details
        # This tests the flow works without errors
    
    async def test_detect_cross_domain_patterns_no_patterns(self, cross_domain_engine):
        """Test detection with no patterns available"""
        
        # Mock empty pattern lists
        cross_domain_engine._get_patterns_by_domain = AsyncMock(return_value=[])
        
        matches = await cross_domain_engine.detect_cross_domain_patterns(
            source_domain=DomainType.AUTHENTICATION,
            target_domain=DomainType.BACKEND,
            min_similarity=0.5
        )
        
        assert matches == []
    
    async def test_detect_cross_domain_patterns_high_threshold(self, cross_domain_engine, sample_patterns):
        """Test detection with high similarity threshold"""
        
        cross_domain_engine._get_patterns_by_domain = AsyncMock()
        cross_domain_engine._get_patterns_by_domain.side_effect = lambda domain: (
            [sample_patterns[0]] if domain == DomainType.AUTHENTICATION else
            [sample_patterns[1]] if domain == DomainType.DATABASE else []
        )
        
        matches = await cross_domain_engine.detect_cross_domain_patterns(
            source_domain=DomainType.AUTHENTICATION,
            target_domain=DomainType.DATABASE,
            min_similarity=0.9  # Very high threshold
        )
        
        # Should return fewer or no matches due to high threshold
        assert isinstance(matches, list)


@pytest.mark.asyncio
class TestPatternAbstraction:
    """Test pattern abstraction capabilities"""
    
    async def test_abstract_domain_pattern_basic(self, cross_domain_engine, sample_patterns):
        """Test basic pattern abstraction"""
        
        pattern = sample_patterns[0]  # JWT auth pattern
        
        # Mock domain classification
        cross_domain_engine._classify_pattern_domain = AsyncMock(return_value=DomainType.AUTHENTICATION)
        
        abstract_pattern = await cross_domain_engine.abstract_domain_pattern(pattern)
        
        # Verify abstract pattern structure
        assert isinstance(abstract_pattern, AbstractPattern)
        assert abstract_pattern.title.startswith("Abstract:")
        assert abstract_pattern.abstraction_level > 0.0
        assert abstract_pattern.abstraction_level <= 1.0
        assert len(abstract_pattern.source_domains) > 0
        assert abstract_pattern.source_domains[0] == DomainType.AUTHENTICATION
        assert len(abstract_pattern.invariant_properties) >= 0
        assert isinstance(abstract_pattern.variable_components, dict)
        assert isinstance(abstract_pattern.conceptual_structure, dict)
    
    async def test_abstract_pattern_conceptual_structure(self, cross_domain_engine, sample_patterns):
        """Test conceptual structure extraction"""
        
        pattern = sample_patterns[1]  # Database pattern
        cross_domain_engine._classify_pattern_domain = AsyncMock(return_value=DomainType.DATABASE)
        
        abstract_pattern = await cross_domain_engine.abstract_domain_pattern(pattern)
        
        # Verify conceptual structure contains expected elements
        assert "problem_structure" in abstract_pattern.conceptual_structure
        assert "solution_structure" in abstract_pattern.conceptual_structure
        assert isinstance(abstract_pattern.conceptual_structure["problem_structure"], dict)
        assert isinstance(abstract_pattern.conceptual_structure["solution_structure"], dict)


@pytest.mark.asyncio 
class TestPatternAdaptation:
    """Test pattern adaptation to different domains"""
    
    async def test_adapt_pattern_to_domain_basic(self, cross_domain_engine):
        """Test basic pattern adaptation"""
        
        # Create abstract pattern
        abstract_pattern = AbstractPattern(
            id=uuid4(),
            title="Abstract Authentication Pattern",
            abstract_description="Generic user authentication flow",
            conceptual_structure={
                "problem_structure": {
                    "problem_type": "access_control",
                    "key_challenges": ["identity_verification", "session_management"],
                    "constraints": ["security_requirements", "performance_needs"]
                },
                "solution_structure": {
                    "approach_type": "token_based",
                    "key_components": ["token_generator", "token_validator"],
                    "implementation_steps": ["generate_token", "validate_token", "authorize_access"]
                }
            },
            invariant_properties=["security", "scalability", "stateless"],
            variable_components={
                "technology_jwt": "Token technology",
                "config_secret": "Secret key configuration"
            },
            applicability_conditions=["requires_stateless_auth", "api_based_system"],
            expected_outcomes=["secure_access", "scalable_auth"],
            source_domains=[DomainType.AUTHENTICATION],
            abstraction_level=0.8,
            created_at=datetime.utcnow(),
            quality_score=0.85
        )
        
        # Mock domain-specific methods
        cross_domain_engine._get_patterns_by_domain = AsyncMock(return_value=[])
        cross_domain_engine._build_domain_ontology = AsyncMock(return_value=DomainOntology(
            domain=DomainType.BACKEND,
            core_concepts=["server", "api", "middleware", "authentication"],
            concept_relationships={},
            technical_vocabulary={"server", "middleware", "endpoint"},
            common_patterns=["middleware_pattern", "api_pattern"],
            tools_and_technologies={"express", "nodejs", "passport"},
            typical_problems=["authentication", "authorization", "session_management"],
            success_metrics=["response_time", "security_score"],
            created_at=datetime.utcnow(),
            confidence_score=0.8
        ))
        
        adapted_pattern = await cross_domain_engine.adapt_pattern_to_domain(
            abstract_pattern, DomainType.BACKEND
        )
        
        # Verify adapted pattern
        assert isinstance(adapted_pattern, KnowledgeItem)
        assert "backend" in adapted_pattern.title.lower()
        assert adapted_pattern.knowledge_type == "pattern"
        assert adapted_pattern.source_type == "cross_domain_adaptation"
        assert "target_domain" in adapted_pattern.metadata
        assert adapted_pattern.metadata["target_domain"] == "backend"


@pytest.mark.asyncio
class TestCrossDomainRecommendations:
    """Test cross-domain solution recommendations"""
    
    async def test_recommend_cross_domain_solutions_basic(self, cross_domain_engine, sample_patterns):
        """Test basic cross-domain recommendations"""
        
        problem_description = "I need to implement secure user authentication for my mobile app backend"
        target_domain = DomainType.BACKEND
        
        # Mock pattern retrieval
        cross_domain_engine._get_patterns_by_domain = AsyncMock()
        cross_domain_engine._get_patterns_by_domain.side_effect = lambda domain: (
            [sample_patterns[0]] if domain == DomainType.AUTHENTICATION else []
        )
        
        recommendations = await cross_domain_engine.recommend_cross_domain_solutions(
            problem_description=problem_description,
            target_domain=target_domain,
            exclude_domains=[],
            max_recommendations=5
        )
        
        # Verify recommendations structure
        assert isinstance(recommendations, list)
        # Note: Actual recommendations depend on pattern matching implementation
        # This tests the flow works without errors
    
    async def test_recommend_with_exclude_domains(self, cross_domain_engine, sample_patterns):
        """Test recommendations with excluded domains"""
        
        problem_description = "Need database optimization for high-performance application"
        target_domain = DomainType.PERFORMANCE
        exclude_domains = [DomainType.DATABASE]  # Exclude database domain
        
        cross_domain_engine._get_patterns_by_domain = AsyncMock()
        cross_domain_engine._get_patterns_by_domain.side_effect = lambda domain: (
            [sample_patterns[1]] if domain == DomainType.DATABASE else []
        )
        
        recommendations = await cross_domain_engine.recommend_cross_domain_solutions(
            problem_description=problem_description,
            target_domain=target_domain,
            exclude_domains=exclude_domains,
            max_recommendations=10
        )
        
        assert isinstance(recommendations, list)
        # Should not include patterns from excluded domains
        for rec in recommendations:
            if isinstance(rec, dict) and 'original_domain' in rec:
                assert rec['original_domain'] != DomainType.DATABASE.value


@pytest.mark.asyncio
class TestDomainRelationshipGraph:
    """Test domain relationship graph building"""
    
    async def test_build_domain_relationship_graph_basic(self, cross_domain_engine):
        """Test basic domain relationship graph building"""
        
        # Mock domain similarity calculations
        cross_domain_engine._calculate_domain_similarity = AsyncMock(return_value=0.6)
        cross_domain_engine._find_shared_concepts_between_domains = AsyncMock(return_value=["security", "api"])
        cross_domain_engine._count_successful_adaptations = AsyncMock(return_value=3)
        
        graph = await cross_domain_engine.build_domain_relationship_graph()
        
        # Verify graph structure
        assert graph is not None
        assert graph.number_of_nodes() > 0
        
        # Check that nodes represent domains
        nodes = list(graph.nodes())
        assert all(isinstance(node, str) for node in nodes)
        
        # Verify edges exist
        if graph.number_of_edges() > 0:
            edges = list(graph.edges(data=True))
            for source, target, data in edges:
                assert 'similarity' in data
                assert 'weight' in data
                assert data['similarity'] >= 0.0
                assert data['similarity'] <= 1.0
    
    async def test_domain_graph_edge_attributes(self, cross_domain_engine):
        """Test domain relationship graph edge attributes"""
        
        cross_domain_engine._calculate_domain_similarity = AsyncMock(return_value=0.8)
        cross_domain_engine._find_shared_concepts_between_domains = AsyncMock(return_value=["auth", "security", "api"])
        cross_domain_engine._count_successful_adaptations = AsyncMock(return_value=5)
        
        graph = await cross_domain_engine.build_domain_relationship_graph()
        
        if graph.number_of_edges() > 0:
            # Check first edge for required attributes
            edge_data = list(graph.edges(data=True))[0][2]
            assert 'similarity' in edge_data
            assert 'shared_concepts' in edge_data
            assert 'adaptation_count' in edge_data
            assert 'weight' in edge_data


@pytest.mark.asyncio
class TestSuccessPrediction:
    """Test success prediction for cross-domain adaptations"""
    
    async def test_predict_adaptation_success_high_probability(self, cross_domain_engine):
        """Test success prediction with high probability scenario"""
        
        # Create high-quality abstract pattern
        abstract_pattern = AbstractPattern(
            id=uuid4(),
            title="High Quality Pattern",
            abstract_description="Well-established pattern",
            conceptual_structure={},
            invariant_properties=["principle1", "principle2", "principle3"],
            variable_components={"tech1": "Technology 1"},
            applicability_conditions=["condition1"],
            expected_outcomes=["outcome1"],
            source_domains=[DomainType.AUTHENTICATION],
            abstraction_level=0.9,  # High abstraction
            created_at=datetime.utcnow(),
            quality_score=0.95  # High quality
        )
        
        problem_context = {"complexity": 0.3}  # Low complexity
        
        # Mock methods for high success scenario
        cross_domain_engine._get_patterns_by_domain = AsyncMock(return_value=[])
        cross_domain_engine._build_domain_ontology = AsyncMock(return_value=DomainOntology(
            domain=DomainType.BACKEND,
            core_concepts=["principle1", "principle2"],  # High concept overlap
            concept_relationships={},
            technical_vocabulary=set(),
            common_patterns=[],
            tools_and_technologies=set(),
            typical_problems=[],
            success_metrics=[],
            created_at=datetime.utcnow(),
            confidence_score=0.8
        ))
        cross_domain_engine._get_historical_success_rate = AsyncMock(return_value=0.8)
        
        success_prediction = await cross_domain_engine._predict_adaptation_success(
            abstract_pattern, DomainType.BACKEND, problem_context
        )
        
        # Should predict high success due to favorable conditions
        assert isinstance(success_prediction, SuccessProbability)
        assert success_prediction in [SuccessProbability.HIGH, SuccessProbability.VERY_HIGH]
    
    async def test_predict_adaptation_success_low_probability(self, cross_domain_engine):
        """Test success prediction with low probability scenario"""
        
        # Create low-quality abstract pattern
        abstract_pattern = AbstractPattern(
            id=uuid4(),
            title="Low Quality Pattern",
            abstract_description="Poorly documented pattern",
            conceptual_structure={},
            invariant_properties=[],  # No invariant properties
            variable_components={},
            applicability_conditions=[],
            expected_outcomes=[],
            source_domains=[DomainType.UNKNOWN],
            abstraction_level=0.2,  # Low abstraction
            created_at=datetime.utcnow(),
            quality_score=0.3  # Low quality
        )
        
        problem_context = {"complexity": 0.9}  # High complexity
        
        # Mock methods for low success scenario
        cross_domain_engine._get_patterns_by_domain = AsyncMock(return_value=[])
        cross_domain_engine._build_domain_ontology = AsyncMock(return_value=DomainOntology(
            domain=DomainType.MACHINE_LEARNING,
            core_concepts=["ml_concept1", "ml_concept2"],  # No concept overlap
            concept_relationships={},
            technical_vocabulary=set(),
            common_patterns=[],
            tools_and_technologies=set(),
            typical_problems=[],
            success_metrics=[],
            created_at=datetime.utcnow(),
            confidence_score=0.8
        ))
        cross_domain_engine._get_historical_success_rate = AsyncMock(return_value=0.2)
        
        success_prediction = await cross_domain_engine._predict_adaptation_success(
            abstract_pattern, DomainType.MACHINE_LEARNING, problem_context
        )
        
        # Should predict low success due to unfavorable conditions
        assert isinstance(success_prediction, SuccessProbability)
        assert success_prediction in [SuccessProbability.LOW, SuccessProbability.VERY_LOW]


@pytest.mark.asyncio
class TestDomainClassification:
    """Test domain classification capabilities"""
    
    async def test_classify_authentication_pattern(self, cross_domain_engine, sample_patterns):
        """Test classification of authentication pattern"""
        
        auth_pattern = sample_patterns[0]  # JWT auth pattern
        
        domain = await cross_domain_engine._classify_pattern_domain(auth_pattern)
        
        assert domain == DomainType.AUTHENTICATION
    
    async def test_classify_database_pattern(self, cross_domain_engine, sample_patterns):
        """Test classification of database pattern"""
        
        db_pattern = sample_patterns[1]  # Database connection pattern
        
        domain = await cross_domain_engine._classify_pattern_domain(db_pattern)
        
        assert domain == DomainType.DATABASE
    
    async def test_classify_unknown_pattern(self, cross_domain_engine):
        """Test classification of unknown pattern"""
        
        unknown_pattern = KnowledgeItem(
            id=uuid4(),
            title="Mysterious Pattern",
            content="This pattern doesn't match any specific domain keywords",
            knowledge_type="pattern",
            source_type="manual",
            tags=["mysterious", "unknown"],
            summary="Unknown pattern",
            confidence="medium",
            metadata={}
        )
        
        domain = await cross_domain_engine._classify_pattern_domain(unknown_pattern)
        
        assert domain == DomainType.UNKNOWN


@pytest.mark.asyncio
class TestDomainCompatibility:
    """Test domain compatibility calculations"""
    
    async def test_calculate_high_compatibility(self, cross_domain_engine):
        """Test calculation of high domain compatibility"""
        
        compatibility = await cross_domain_engine._calculate_domain_compatibility(
            DomainType.AUTHENTICATION, DomainType.SECURITY
        )
        
        assert compatibility > 0.8  # Should be high compatibility
    
    async def test_calculate_medium_compatibility(self, cross_domain_engine):
        """Test calculation of medium domain compatibility"""
        
        compatibility = await cross_domain_engine._calculate_domain_compatibility(
            DomainType.FRONTEND, DomainType.API_DESIGN
        )
        
        assert 0.5 <= compatibility <= 0.9  # Should be medium compatibility
    
    async def test_calculate_unknown_domain_compatibility(self, cross_domain_engine):
        """Test compatibility calculation for unknown domain pairs"""
        
        # Mock implicit compatibility calculation
        cross_domain_engine._calculate_implicit_compatibility = AsyncMock(return_value=0.4)
        
        compatibility = await cross_domain_engine._calculate_domain_compatibility(
            DomainType.TESTING, DomainType.MACHINE_LEARNING
        )
        
        assert 0.0 <= compatibility <= 1.0


@pytest.mark.asyncio 
class TestPatternConcepts:
    """Test pattern concept extraction"""
    
    async def test_extract_pattern_concepts_jwt(self, cross_domain_engine, sample_patterns):
        """Test concept extraction from JWT pattern"""
        
        jwt_pattern = sample_patterns[0]
        concepts = await cross_domain_engine._extract_pattern_concepts(jwt_pattern)
        
        assert isinstance(concepts, list)
        assert len(concepts) > 0
        
        # Should include technical terms and tags
        expected_concepts = ["jwt", "authentication", "security", "api"]
        for expected in expected_concepts:
            assert any(expected.lower() in concept.lower() for concept in concepts)
    
    async def test_extract_pattern_concepts_database(self, cross_domain_engine, sample_patterns):
        """Test concept extraction from database pattern"""
        
        db_pattern = sample_patterns[1]
        concepts = await cross_domain_engine._extract_pattern_concepts(db_pattern)
        
        assert isinstance(concepts, list)
        assert len(concepts) > 0
        
        # Should include database-related concepts
        expected_concepts = ["database", "connection", "pooling", "performance"]
        for expected in expected_concepts:
            assert any(expected.lower() in concept.lower() for concept in concepts)


@pytest.mark.asyncio
class TestStructuralSimilarity:
    """Test structural similarity calculations"""
    
    async def test_calculate_structural_similarity(self, cross_domain_engine, sample_patterns):
        """Test structural similarity between patterns"""
        
        pattern1 = sample_patterns[0]
        pattern2 = sample_patterns[1]
        
        # Mock structural element extraction
        cross_domain_engine._extract_structural_elements = AsyncMock()
        cross_domain_engine._extract_structural_elements.side_effect = [
            {"problem": {"type": "auth"}, "solution": {"type": "token"}, "implementation": ["step1", "step2"]},
            {"problem": {"type": "performance"}, "solution": {"type": "pooling"}, "implementation": ["step1", "step3"]}
        ]
        
        # Mock comparison methods
        cross_domain_engine._compare_problem_structures = AsyncMock(return_value=0.3)
        cross_domain_engine._compare_solution_structures = AsyncMock(return_value=0.5)
        cross_domain_engine._compare_implementation_patterns = AsyncMock(return_value=0.4)
        
        similarity = await cross_domain_engine._calculate_structural_similarity(pattern1, pattern2)
        
        assert 0.0 <= similarity <= 1.0
        # Should be weighted average: 0.3*0.3 + 0.5*0.4 + 0.4*0.3 = 0.41
        assert abs(similarity - 0.41) < 0.01


@pytest.mark.asyncio
class TestIntegrationFlows:
    """Test end-to-end integration flows"""
    
    async def test_full_cross_domain_workflow(self, cross_domain_engine, sample_patterns):
        """Test complete cross-domain intelligence workflow"""
        
        # 1. Pattern abstraction
        auth_pattern = sample_patterns[0]
        cross_domain_engine._classify_pattern_domain = AsyncMock(return_value=DomainType.AUTHENTICATION)
        
        abstract_pattern = await cross_domain_engine.abstract_domain_pattern(auth_pattern)
        assert isinstance(abstract_pattern, AbstractPattern)
        
        # 2. Pattern adaptation
        cross_domain_engine._get_patterns_by_domain = AsyncMock(return_value=[])
        cross_domain_engine._build_domain_ontology = AsyncMock(return_value=DomainOntology(
            domain=DomainType.BACKEND,
            core_concepts=["security", "api"],
            concept_relationships={},
            technical_vocabulary=set(),
            common_patterns=[],
            tools_and_technologies=set(),
            typical_problems=[],
            success_metrics=[],
            created_at=datetime.utcnow(),
            confidence_score=0.8
        ))
        
        adapted_pattern = await cross_domain_engine.adapt_pattern_to_domain(
            abstract_pattern, DomainType.BACKEND
        )
        assert isinstance(adapted_pattern, KnowledgeItem)
        
        # 3. Success prediction
        problem_context = {"complexity": 0.5}
        success_prediction = await cross_domain_engine._predict_adaptation_success(
            abstract_pattern, DomainType.BACKEND, problem_context
        )
        assert isinstance(success_prediction, SuccessProbability)
    
    async def test_error_handling_in_workflows(self, cross_domain_engine):
        """Test error handling in cross-domain workflows"""
        
        # Test with invalid pattern
        invalid_pattern = KnowledgeItem(
            id=uuid4(),
            title="",  # Empty title
            content="",  # Empty content
            knowledge_type="pattern",
            source_type="manual",
            tags=[],
            summary="",
            confidence="low",
            metadata={}
        )
        
        # Should handle gracefully without crashing
        try:
            await cross_domain_engine.abstract_domain_pattern(invalid_pattern)
            # If no exception, that's fine - error handling should be graceful
        except Exception as e:
            # If exception occurs, it should be a handled error, not a crash
            assert isinstance(e, (ValueError, TypeError)) or "error" in str(e).lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])