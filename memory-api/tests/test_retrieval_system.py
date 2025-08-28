# ABOUTME: Comprehensive tests for knowledge retrieval system
# ABOUTME: Tests context loading, similarity search, pattern matching, and cross-project intelligence

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from models.retrieval import (
    ContextLoadRequest, CurrentContext, ContextDepth,
    SimilaritySearchRequest, SimilarityQuery, SimilaritySearchContext,
    PatternSearchRequest, PatternType,
    RecommendationRequest
)
from services.retrieval_service import RetrievalService
from services.cache_intelligence import CacheIntelligence

class TestRetrievalService:
    """Test suite for knowledge retrieval service"""
    
    @pytest.fixture
    async def mock_databases(self):
        """Mock database connections"""
        databases = MagicMock()
        databases.postgres = AsyncMock()
        databases.redis = AsyncMock()
        databases.neo4j = AsyncMock()
        databases.qdrant = AsyncMock()
        return databases
    
    @pytest.fixture
    async def retrieval_service(self, mock_databases):
        """Create retrieval service with mocked dependencies"""
        return RetrievalService(mock_databases)
    
    @pytest.fixture
    def sample_context_request(self):
        """Sample context loading request"""
        return ContextLoadRequest(
            user_id="test-user-123",
            project_id="project-abc",
            current_context=CurrentContext(
                working_on="Implementing JWT authentication",
                technologies_involved=["FastAPI", "JWT", "PostgreSQL"],
                files_open=["/backend/auth.py", "/backend/models/user.py"],
                user_message="How should I implement JWT authentication securely?",
                problem_type="authentication"
            ),
            context_depth=ContextDepth.DETAILED,
            include_cross_project=True,
            max_items=20
        )
    
    @pytest.fixture
    def sample_similarity_request(self):
        """Sample similarity search request"""
        return SimilaritySearchRequest(
            user_id="test-user-123",
            query=SimilarityQuery(
                text="PostgreSQL connection pool exhaustion error",
                context=SimilaritySearchContext(
                    problem_type="database_performance",
                    technologies=["PostgreSQL", "SQLAlchemy"],
                    error_symptoms=["timeouts", "connection errors"]
                )
            ),
            search_scope={
                "projects": ["137docs", "nautBrain"],
                "knowledge_types": ["problem_solution", "code_change"],
                "time_range": "last_6_months"
            },
            similarity_threshold=0.7
        )
    
    @pytest.fixture
    def sample_vector_results(self):
        """Sample vector search results"""
        return [
            {
                "payload": {
                    "item_id": str(uuid4()),
                    "title": "JWT Authentication Implementation",
                    "knowledge_type": "code"
                },
                "score": 0.92
            },
            {
                "payload": {
                    "item_id": str(uuid4()),
                    "title": "FastAPI Security Middleware",
                    "knowledge_type": "code"
                },
                "score": 0.88
            }
        ]
    
    @pytest.fixture
    def sample_knowledge_items(self):
        """Sample knowledge items from database"""
        base_time = datetime.utcnow()
        
        return [
            type('KnowledgeItem', (), {
                'id': uuid4(),
                'title': 'JWT Authentication Implementation in 137docs',
                'content': 'Successfully implemented JWT auth with FastAPI middleware...',
                'knowledge_type': 'code',
                'summary': 'JWT implementation with proper security',
                'project_id': '137docs',
                'metadata': {
                    'key_insights': ['Use python-jose library', 'Implement refresh tokens'],
                    'lessons_learned': ['JWT secrets must be environment variables'],
                    'applicable_code': {
                        'file': '/backend/auth/jwt.py',
                        'relevant_sections': ['token generation', 'validation middleware']
                    },
                    'success_outcome': 'Authentication system handles 1000+ concurrent users'
                },
                'created_at': base_time - timedelta(days=30)
            })(),
            type('KnowledgeItem', (), {
                'id': uuid4(),
                'title': 'PostgreSQL Connection Pool Optimization',
                'content': 'Fixed connection pool exhaustion by adding proper cleanup...',
                'knowledge_type': 'insight',
                'summary': 'Database connection pool fixes',
                'project_id': 'nautBrain',
                'metadata': {
                    'key_insights': ['Always close connections in finally blocks'],
                    'lessons_learned': ['Monitor connection pool metrics'],
                    'success_outcome': '6.7x performance improvement'
                },
                'created_at': base_time - timedelta(days=15)
            })()
        ]

class TestContextLoading:
    """Test context loading functionality"""
    
    async def test_load_context_for_session_success(self, retrieval_service, sample_context_request, sample_vector_results, sample_knowledge_items):
        """Test successful context loading"""
        # Mock vector service
        with patch.object(retrieval_service.vector_service, 'search_similar', return_value=sample_vector_results):
            # Mock database fetching
            with patch.object(retrieval_service, '_fetch_knowledge_items_by_ids', return_value=sample_knowledge_items):
                # Mock knowledge count
                with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=1500):
                    
                    response = await retrieval_service.load_context_for_session(sample_context_request)
                    
                    # Verify response structure
                    assert response.message.startswith("Loaded")
                    assert "context" in response.context
                    assert "relevant_knowledge" in response.context
                    assert response.metadata.total_knowledge_items == 1500
                    assert response.metadata.items_returned > 0
                    assert response.metadata.search_time_ms > 0
    
    async def test_context_depth_basic(self, retrieval_service, sample_context_request):
        """Test basic context depth loading"""
        sample_context_request.context_depth = ContextDepth.BASIC
        
        with patch.object(retrieval_service, '_find_relevant_knowledge', return_value=[]):
            with patch.object(retrieval_service, '_find_similar_patterns', return_value=[]):
                with patch.object(retrieval_service, '_find_cross_project_insights', return_value=[]):
                    with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=100):
                        
                        response = await retrieval_service.load_context_for_session(sample_context_request)
                        
                        # Basic context should not include historical solutions or tech evolution
                        assert "historical_solutions" not in response.context
                        assert "technology_evolution" not in response.context
    
    async def test_context_depth_comprehensive(self, retrieval_service, sample_context_request):
        """Test comprehensive context depth loading"""
        sample_context_request.context_depth = ContextDepth.COMPREHENSIVE
        
        with patch.object(retrieval_service, '_find_relevant_knowledge', return_value=[]):
            with patch.object(retrieval_service, '_find_similar_patterns', return_value=[]):
                with patch.object(retrieval_service, '_find_cross_project_insights', return_value=[]):
                    with patch.object(retrieval_service, '_find_historical_solutions', return_value=[]):
                        with patch.object(retrieval_service, '_find_technology_evolution', return_value=[]):
                            with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=100):
                                
                                response = await retrieval_service.load_context_for_session(sample_context_request)
                                
                                # Comprehensive context should include all sections
                                assert "historical_solutions" in response.context
                                assert "technology_evolution" in response.context
    
    async def test_cross_project_filtering(self, retrieval_service, sample_context_request):
        """Test cross-project inclusion/exclusion"""
        # Test with cross-project enabled
        sample_context_request.include_cross_project = True
        
        with patch.object(retrieval_service, '_find_cross_project_insights') as mock_cross_project:
            mock_cross_project.return_value = [{"project": "other-project", "insight": "test"}]
            
            with patch.object(retrieval_service, '_find_relevant_knowledge', return_value=[]):
                with patch.object(retrieval_service, '_find_similar_patterns', return_value=[]):
                    with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=100):
                        
                        await retrieval_service.load_context_for_session(sample_context_request)
                        mock_cross_project.assert_called_once()
        
        # Test with cross-project disabled
        sample_context_request.include_cross_project = False
        
        with patch.object(retrieval_service, '_find_cross_project_insights') as mock_cross_project:
            mock_cross_project.return_value = []
            
            with patch.object(retrieval_service, '_find_relevant_knowledge', return_value=[]):
                with patch.object(retrieval_service, '_find_similar_patterns', return_value=[]):
                    with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=100):
                        
                        await retrieval_service.load_context_for_session(sample_context_request)
                        mock_cross_project.assert_called_once()

class TestSimilaritySearch:
    """Test similarity search functionality"""
    
    async def test_similarity_search_success(self, retrieval_service, sample_similarity_request):
        """Test successful similarity search"""
        mock_similar_items = [
            type('SimilarItem', (), {
                'knowledge_id': uuid4(),
                'similarity_score': 0.94,
                'title': 'Fixed PostgreSQL Pool Exhaustion in 137docs',
                'reusability_score': 0.88
            })()
        ]
        
        with patch.object(retrieval_service, '_apply_search_scope_filters', return_value=[]):
            with patch.object(retrieval_service, '_build_similar_items', return_value=mock_similar_items):
                with patch.object(retrieval_service.vector_service, 'search_similar', return_value=[]):
                    
                    response = await retrieval_service.search_similar_problems(sample_similarity_request)
                    
                    assert response.message.startswith("Found")
                    assert len(response.similar_items) == len(mock_similar_items)
                    assert "query_analysis" in response.__dict__
                    assert "search_metadata" in response.__dict__
    
    async def test_similarity_search_with_context(self, retrieval_service, sample_similarity_request):
        """Test similarity search with additional context"""
        # Verify context is properly incorporated into search
        original_query = sample_similarity_request.query.text
        
        with patch.object(retrieval_service.vector_service, 'search_similar') as mock_search:
            mock_search.return_value = []
            
            with patch.object(retrieval_service, '_apply_search_scope_filters', return_value=[]):
                with patch.object(retrieval_service, '_build_similar_items', return_value=[]):
                    
                    await retrieval_service.search_similar_problems(sample_similarity_request)
                    
                    # Verify search was called with enhanced query
                    mock_search.assert_called_once()
                    call_args = mock_search.call_args[1]
                    assert original_query in call_args['query']
                    assert "PostgreSQL" in call_args['query']
    
    async def test_similarity_search_empty_results(self, retrieval_service, sample_similarity_request):
        """Test similarity search with no results"""
        with patch.object(retrieval_service.vector_service, 'search_similar', return_value=[]):
            
            response = await retrieval_service.search_similar_problems(sample_similarity_request)
            
            assert response.message == "No similar problems found"
            assert len(response.similar_items) == 0
            assert response.search_metadata["total_results"] == 0

class TestPatternMatching:
    """Test pattern matching functionality"""
    
    async def test_find_reusable_patterns_success(self, retrieval_service):
        """Test successful pattern finding"""
        request = PatternSearchRequest(
            user_id="test-user-123",
            pattern_type=PatternType.ARCHITECTURAL,
            min_success_rate=0.8,
            min_usage_count=2,
            technologies=["FastAPI", "PostgreSQL"],
            projects=["137docs"]
        )
        
        mock_patterns = [
            type('ReusablePattern', (), {
                'pattern_name': 'FastAPI + PostgreSQL + JWT Authentication',
                'usage_count': 5,
                'success_rate': 0.92,
                'projects': ['137docs', 'nautBrain']
            })()
        ]
        
        with patch.object(retrieval_service, '_search_pattern_knowledge', return_value=[]):
            with patch.object(retrieval_service, '_aggregate_patterns', return_value=mock_patterns):
                
                response = await retrieval_service.find_reusable_patterns(request)
                
                assert response.message.startswith("Found")
                assert len(response.patterns) == 1
                assert response.patterns[0].success_rate >= request.min_success_rate
                assert response.patterns[0].usage_count >= request.min_usage_count
    
    async def test_pattern_filtering_by_success_rate(self, retrieval_service):
        """Test pattern filtering by success rate"""
        request = PatternSearchRequest(
            user_id="test-user-123",
            min_success_rate=0.9,  # High success rate requirement
            min_usage_count=1
        )
        
        mock_patterns = [
            type('ReusablePattern', (), {
                'pattern_name': 'High Success Pattern',
                'usage_count': 3,
                'success_rate': 0.95  # Meets requirement
            })(),
            type('ReusablePattern', (), {
                'pattern_name': 'Low Success Pattern',
                'usage_count': 5,
                'success_rate': 0.7  # Doesn't meet requirement
            })()
        ]
        
        with patch.object(retrieval_service, '_search_pattern_knowledge', return_value=[]):
            with patch.object(retrieval_service, '_aggregate_patterns', return_value=mock_patterns):
                
                response = await retrieval_service.find_reusable_patterns(request)
                
                # Only high success rate pattern should be returned
                assert len(response.patterns) == 1
                assert response.patterns[0].pattern_name == "High Success Pattern"

class TestTechnologyEvolution:
    """Test technology evolution tracking"""
    
    async def test_get_technology_evolution_success(self, retrieval_service):
        """Test successful technology evolution retrieval"""
        technology = "FastAPI"
        user_id = "test-user-123"
        
        mock_evolution = [
            type('TechnologyUsage', (), {
                'project': '137docs',
                'first_used': datetime.utcnow() - timedelta(days=90),
                'current_usage': 'Primary backend framework',
                'success_metrics': {'success_score': 0.9}
            })()
        ]
        
        with patch.object(retrieval_service.vector_service, 'search_similar', return_value=[]):
            with patch.object(retrieval_service, '_build_technology_evolution', return_value=mock_evolution):
                with patch.object(retrieval_service, '_generate_technology_recommendations', return_value=['Use async/await']):
                    
                    response = await retrieval_service.get_technology_evolution(user_id, technology)
                    
                    assert response.technology == technology
                    assert len(response.evolution) == 1
                    assert response.overall_success_rate > 0
                    assert len(response.recommendations) > 0
    
    async def test_technology_evolution_no_data(self, retrieval_service):
        """Test technology evolution with no data"""
        technology = "UnknownTech"
        user_id = "test-user-123"
        
        with patch.object(retrieval_service.vector_service, 'search_similar', return_value=[]):
            
            response = await retrieval_service.get_technology_evolution(user_id, technology)
            
            assert response.technology == technology
            assert len(response.evolution) == 0
            assert response.overall_success_rate == 0.0

class TestRecommendationGeneration:
    """Test recommendation generation"""
    
    async def test_generate_recommendations_success(self, retrieval_service):
        """Test successful recommendation generation"""
        request = RecommendationRequest(
            user_id="test-user-123",
            current_project="new-project",
            working_on="Setting up authentication system",
            technologies_considering=["FastAPI", "JWT", "PostgreSQL"]
        )
        
        mock_recommendations = [
            type('Recommendation', (), {
                'type': 'proven_pattern',
                'confidence': 0.91,
                'title': 'Use FastAPI + JWT Pattern from 137docs',
                'reasoning': 'This pattern succeeded in 137docs',
                'success_probability': 0.95
            })()
        ]
        
        with patch.object(retrieval_service, '_analyze_current_context', return_value={}):
            with patch.object(retrieval_service, '_find_applicable_knowledge', return_value=[]):
                with patch.object(retrieval_service, '_generate_pattern_recommendations', return_value=mock_recommendations):
                    with patch.object(retrieval_service, '_generate_technology_recommendations_for_context', return_value=[]):
                        with patch.object(retrieval_service, '_generate_risk_warnings', return_value=[]):
                            with patch.object(retrieval_service, '_generate_analysis_summary', return_value="Analysis complete"):
                                
                                response = await retrieval_service.generate_recommendations(request)
                                
                                assert response.message.startswith("Generated")
                                assert len(response.recommendations) == 1
                                assert response.confidence_score > 0
                                assert response.analysis_summary == "Analysis complete"
    
    async def test_recommendation_confidence_sorting(self, retrieval_service):
        """Test recommendations are sorted by confidence"""
        request = RecommendationRequest(
            user_id="test-user-123",
            current_project="test-project",
            working_on="Testing",
            technologies_considering=[]
        )
        
        mock_recommendations = [
            type('Recommendation', (), {
                'type': 'proven_pattern',
                'confidence': 0.7,
                'title': 'Low Confidence Rec'
            })(),
            type('Recommendation', (), {
                'type': 'proven_pattern',
                'confidence': 0.9,
                'title': 'High Confidence Rec'
            })()
        ]
        
        with patch.object(retrieval_service, '_analyze_current_context', return_value={}):
            with patch.object(retrieval_service, '_find_applicable_knowledge', return_value=[]):
                with patch.object(retrieval_service, '_generate_pattern_recommendations', return_value=mock_recommendations):
                    with patch.object(retrieval_service, '_generate_technology_recommendations_for_context', return_value=[]):
                        with patch.object(retrieval_service, '_generate_risk_warnings', return_value=[]):
                            with patch.object(retrieval_service, '_generate_analysis_summary', return_value="Analysis complete"):
                                
                                response = await retrieval_service.generate_recommendations(request)
                                
                                # Verify recommendations are sorted by confidence (highest first)
                                assert response.recommendations[0].title == "High Confidence Rec"
                                assert response.recommendations[1].title == "Low Confidence Rec"

class TestCacheIntelligence:
    """Test intelligent caching functionality"""
    
    @pytest.fixture
    async def cache_intelligence(self, mock_databases):
        """Create cache intelligence service with mocked dependencies"""
        return CacheIntelligence(mock_databases)
    
    async def test_get_cached_context_hit(self, cache_intelligence):
        """Test cache hit scenario"""
        cache_key = "test:context:123"
        user_id = "test-user"
        cached_data = {"context": "test data"}
        
        with patch.object(cache_intelligence, 'cache_get', return_value='{"context": "test data"}'):
            with patch.object(cache_intelligence, '_track_cache_access'):
                with patch.object(cache_intelligence, '_update_access_frequency'):
                    
                    result = await cache_intelligence.get_cached_context(cache_key, user_id)
                    
                    assert result == cached_data
    
    async def test_get_cached_context_miss(self, cache_intelligence):
        """Test cache miss scenario"""
        cache_key = "test:context:456"
        user_id = "test-user"
        
        with patch.object(cache_intelligence, 'cache_get', return_value=None):
            with patch.object(cache_intelligence, '_track_cache_access'):
                
                result = await cache_intelligence.get_cached_context(cache_key, user_id)
                
                assert result is None
    
    async def test_intelligent_ttl_calculation(self, cache_intelligence):
        """Test intelligent TTL calculation"""
        cache_key = "test:key"
        user_id = "test-user"
        context_type = "context"
        
        # Mock high access frequency
        with patch.object(cache_intelligence, '_get_access_frequency', return_value=15):
            
            ttl = await cache_intelligence._calculate_intelligent_ttl(cache_key, user_id, context_type)
            
            # High frequency should extend TTL
            assert ttl > cache_intelligence.default_ttl
    
    async def test_cache_warming(self, cache_intelligence):
        """Test cache warming for user"""
        user_id = "test-user"
        
        mock_patterns = type('AccessPattern', (), {
            'frequent_queries': ['query1', 'query2'],
            'frequent_projects': ['project1', 'project2']
        })()
        
        with patch.object(cache_intelligence, '_get_user_access_patterns', return_value=mock_patterns):
            with patch.object(cache_intelligence, 'cache_get', return_value=None):  # No existing cache
                with patch.object(cache_intelligence, '_generate_predictive_context', return_value={"test": "data"}):
                    with patch.object(cache_intelligence, '_generate_project_context', return_value={"project": "data"}):
                        with patch.object(cache_intelligence, 'set_cached_context', return_value=True):
                            
                            result = await cache_intelligence.warm_cache_for_user(user_id)
                            
                            assert result["preloaded"] > 0
                            assert "message" in result

class TestPerformanceAndScaling:
    """Test performance and scaling aspects"""
    
    async def test_concurrent_context_loading(self, retrieval_service, sample_context_request):
        """Test concurrent context loading requests"""
        # Create multiple requests
        requests = [sample_context_request for _ in range(10)]
        
        with patch.object(retrieval_service, '_find_relevant_knowledge', return_value=[]):
            with patch.object(retrieval_service, '_find_similar_patterns', return_value=[]):
                with patch.object(retrieval_service, '_find_cross_project_insights', return_value=[]):
                    with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=100):
                        
                        # Execute concurrently
                        tasks = [retrieval_service.load_context_for_session(req) for req in requests]
                        responses = await asyncio.gather(*tasks)
                        
                        # Verify all requests completed successfully
                        assert len(responses) == 10
                        for response in responses:
                            assert response.message.startswith("Loaded")
    
    async def test_large_result_set_handling(self, retrieval_service):
        """Test handling of large result sets"""
        # Create request with high max_items
        request = ContextLoadRequest(
            user_id="test-user",
            current_context=CurrentContext(working_on="test"),
            max_items=100
        )
        
        # Mock large result set
        large_results = [{"payload": {"item_id": str(uuid4())}, "score": 0.8} for _ in range(200)]
        
        with patch.object(retrieval_service.vector_service, 'search_similar', return_value=large_results):
            with patch.object(retrieval_service, '_fetch_knowledge_items_by_ids', return_value=[]):
                with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=1000):
                    
                    response = await retrieval_service.load_context_for_session(request)
                    
                    # Verify response doesn't exceed max_items
                    assert response.metadata.items_returned <= request.max_items

class TestErrorHandling:
    """Test error handling and resilience"""
    
    async def test_vector_service_failure_graceful_degradation(self, retrieval_service, sample_context_request):
        """Test graceful degradation when vector service fails"""
        # Mock vector service failure
        with patch.object(retrieval_service.vector_service, 'search_similar', side_effect=Exception("Vector service down")):
            with patch.object(retrieval_service, '_find_similar_patterns', return_value=[]):
                with patch.object(retrieval_service, '_find_cross_project_insights', return_value=[]):
                    with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=100):
                        
                        # Should still complete but with empty relevant_knowledge
                        response = await retrieval_service.load_context_for_session(sample_context_request)
                        
                        assert response.message.startswith("Loaded")
                        assert len(response.context.get("relevant_knowledge", [])) == 0
    
    async def test_database_connection_failure(self, retrieval_service, sample_context_request):
        """Test handling of database connection failures"""
        # Mock database failure
        with patch.object(retrieval_service, '_get_total_knowledge_count', side_effect=Exception("DB connection failed")):
            
            # Should raise exception for critical database operations
            with pytest.raises(Exception):
                await retrieval_service.load_context_for_session(sample_context_request)
    
    async def test_invalid_input_sanitization(self, retrieval_service):
        """Test input sanitization for security"""
        # Create request with potentially malicious input
        malicious_request = ContextLoadRequest(
            user_id="<script>alert('xss')</script>",
            current_context=CurrentContext(
                working_on="<script>malicious()</script>",
                user_message="'; DROP TABLE knowledge_items; --"
            )
        )
        
        # The service should handle this gracefully (sanitization happens at API level)
        with patch.object(retrieval_service, '_find_relevant_knowledge', return_value=[]):
            with patch.object(retrieval_service, '_find_similar_patterns', return_value=[]):
                with patch.object(retrieval_service, '_find_cross_project_insights', return_value=[]):
                    with patch.object(retrieval_service, '_get_total_knowledge_count', return_value=100):
                        
                        # Should not raise exception
                        response = await retrieval_service.load_context_for_session(malicious_request)
                        assert response is not None

# Integration tests would go here for testing with real databases
# Performance benchmarks would test actual response times under load
# End-to-end tests would test the complete API flow

if __name__ == "__main__":
    pytest.main([__file__, "-v"])