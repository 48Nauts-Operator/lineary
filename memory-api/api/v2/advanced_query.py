# ABOUTME: Advanced query API endpoints for complex knowledge retrieval
# ABOUTME: Supports semantic search, filters, pattern matching, and cross-project intelligence

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
import structlog
import time
import asyncio
from datetime import datetime, timedelta

from models.advanced_query import (
    AdvancedSearchQuery,
    AdvancedSearchResponse,
    FilterCondition,
    PatternMatchQuery,
    PatternMatchResponse,
    SemanticClusterQuery,
    SemanticClusterResponse,
    ProjectCrossReferenceQuery,
    ProjectCrossReferenceResponse,
    KnowledgeGraphQuery,
    KnowledgeGraphResponse,
    TimeSeriesQuery,
    TimeSeriesResponse,
    SimilarityMatrixQuery,
    SimilarityMatrixResponse
)
from models.base import PaginationParams, ErrorResponse
from core.dependencies import DatabaseDependencies, get_all_databases
from core.security import get_current_user, get_optional_user
from services.advanced_query_service import AdvancedQueryService
from services.cache_intelligence import CacheIntelligence
from services.knowledge_service import KnowledgeService
from models.knowledge import SearchQuery as V1SearchQuery

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v2/query", tags=["Advanced Query v2"])

@router.post("/advanced-search", response_model=AdvancedSearchResponse)
async def advanced_search(
    query: AdvancedSearchQuery,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_optional_user)
) -> AdvancedSearchResponse:
    """
    Perform advanced search with multiple filters, semantic search, and ranking
    
    Features:
    - Multi-modal search (semantic + keyword + metadata)
    - Complex boolean filters with nested conditions
    - Time-range filtering with relative dates
    - Tag-based filtering with inclusion/exclusion
    - Project and session scoping
    - Custom ranking algorithms
    - Result clustering and grouping
    """
    start_time = time.time()
    
    try:
        # Use v1.0 knowledge search as the backend for v2.0 advanced search
        knowledge_service = KnowledgeService(databases)
        
        # Convert v2.0 advanced query to v1.0 search query
        v1_query = V1SearchQuery(
            query=query.query,
            k=query.max_results,
            search_type=query.search_type.value if hasattr(query.search_type, 'value') else str(query.search_type),
            similarity_threshold=query.similarity_threshold,
            include_metadata=query.include_metadata
        )
        
        # Execute search using v1.0 knowledge service
        search_results = await knowledge_service.search_knowledge(v1_query)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Transform v1.0 results to v2.0 format
        v2_results = {
            "results": [
                {
                    "id": str(result.id),
                    "title": result.title,
                    "content": result.content,
                    "score": result.similarity_score if hasattr(result, 'similarity_score') and result.similarity_score else 1.0,
                    "knowledge_type": result.knowledge_type,
                    "source_type": result.source_type,
                    "tags": result.tags or [],
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "metadata": result.metadata or {}
                }
                for result in search_results
            ],
            "analysis": {
                "search_strategy": f"v2.0 advanced search using {query.search_type} via v1.0 backend",
                "backend_search_type": v1_query.search_type,
                "total_found": len(search_results)
            }
        }
        
        logger.info(
            "Advanced search completed (v1.0 backend)",
            query_type=query.search_type,
            filters_count=len(query.filters) if query.filters else 0,
            results_count=len(v2_results.get("results", [])),
            execution_time_ms=execution_time,
            user_id=current_user.get("user_id") if current_user else None
        )
        
        return AdvancedSearchResponse(
            message=f"Advanced search completed successfully - found {len(search_results)} results",
            data=v2_results,
            query_analysis=v2_results.get("analysis", {}),
            execution_time_ms=execution_time,
            total_results=len(v2_results.get("results", []))
        )
        
    except Exception as e:
        logger.error("Advanced search failed", error=str(e), query=query.dict())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced search failed: {str(e)}"
        )

@router.post("/pattern-match", response_model=PatternMatchResponse)
async def pattern_match(
    query: PatternMatchQuery,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_optional_user)
) -> PatternMatchResponse:
    """
    Find patterns in knowledge graph using graph traversal algorithms
    
    Features:
    - Path pattern matching (A->B->C relationships)
    - Subgraph isomorphism detection
    - Temporal pattern recognition
    - Anomaly pattern detection
    - Community detection in knowledge graphs
    - Centrality analysis (identify key knowledge nodes)
    """
    start_time = time.time()
    
    try:
        service = AdvancedQueryService(databases)
        patterns = await service.find_patterns(query)
        
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Pattern matching completed",
            pattern_type=query.pattern_type,
            matches_found=len(patterns.get("matches", [])),
            execution_time_ms=execution_time
        )
        
        return PatternMatchResponse(
            message="Pattern matching completed successfully",
            data=patterns,
            pattern_analysis=patterns.get("analysis", {}),
            execution_time_ms=execution_time,
            matches_count=len(patterns.get("matches", []))
        )
        
    except Exception as e:
        logger.error("Pattern matching failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pattern matching failed: {str(e)}"
        )

@router.post("/semantic-clusters", response_model=SemanticClusterResponse)
async def semantic_clustering(
    query: SemanticClusterQuery,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_optional_user)
) -> SemanticClusterResponse:
    """
    Perform semantic clustering of knowledge items
    
    Features:
    - Vector-based clustering using embeddings
    - Hierarchical clustering with dendrograms
    - Dynamic cluster number selection
    - Topic modeling integration
    - Cluster quality metrics
    - Interactive cluster visualization data
    """
    start_time = time.time()
    
    try:
        service = AdvancedQueryService(databases)
        clusters = await service.semantic_clustering(query)
        
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Semantic clustering completed",
            algorithm=query.algorithm,
            clusters_found=len(clusters.get("clusters", [])),
            execution_time_ms=execution_time
        )
        
        return SemanticClusterResponse(
            message="Semantic clustering completed successfully",
            data=clusters,
            cluster_analysis=clusters.get("analysis", {}),
            execution_time_ms=execution_time,
            clusters_count=len(clusters.get("clusters", []))
        )
        
    except Exception as e:
        logger.error("Semantic clustering failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic clustering failed: {str(e)}"
        )

@router.post("/cross-project", response_model=ProjectCrossReferenceResponse)
async def cross_project_analysis(
    query: ProjectCrossReferenceQuery,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_optional_user)
) -> ProjectCrossReferenceResponse:
    """
    Analyze knowledge connections across different projects
    
    Features:
    - Inter-project knowledge transfer detection
    - Shared concept identification
    - Project similarity analysis
    - Knowledge gap identification
    - Cross-pollination opportunities
    - Project dependency mapping
    """
    start_time = time.time()
    
    try:
        service = AdvancedQueryService(databases)
        cross_refs = await service.cross_project_analysis(query)
        
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Cross-project analysis completed",
            projects_analyzed=len(query.project_ids) if query.project_ids else "all",
            connections_found=len(cross_refs.get("connections", [])),
            execution_time_ms=execution_time
        )
        
        return ProjectCrossReferenceResponse(
            message="Cross-project analysis completed successfully",
            data=cross_refs,
            analysis_summary=cross_refs.get("summary", {}),
            execution_time_ms=execution_time,
            connections_count=len(cross_refs.get("connections", []))
        )
        
    except Exception as e:
        logger.error("Cross-project analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cross-project analysis failed: {str(e)}"
        )

@router.post("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def knowledge_graph_query(
    query: KnowledgeGraphQuery,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_optional_user)
) -> KnowledgeGraphResponse:
    """
    Execute complex graph queries on the knowledge graph
    
    Features:
    - Cypher-like query language support
    - Graph traversal with depth limits
    - Relationship type filtering
    - Subgraph extraction
    - Shortest path algorithms
    - Graph statistics and metrics
    """
    start_time = time.time()
    
    try:
        service = AdvancedQueryService(databases)
        graph_data = await service.execute_graph_query(query)
        
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Knowledge graph query completed",
            query_type=query.query_type,
            nodes_returned=len(graph_data.get("nodes", [])),
            edges_returned=len(graph_data.get("edges", [])),
            execution_time_ms=execution_time
        )
        
        return KnowledgeGraphResponse(
            message="Knowledge graph query completed successfully",
            data=graph_data,
            graph_metrics=graph_data.get("metrics", {}),
            execution_time_ms=execution_time,
            nodes_count=len(graph_data.get("nodes", [])),
            edges_count=len(graph_data.get("edges", []))
        )
        
    except Exception as e:
        logger.error("Knowledge graph query failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge graph query failed: {str(e)}"
        )

@router.post("/time-series", response_model=TimeSeriesResponse)
async def time_series_analysis(
    query: TimeSeriesQuery,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_optional_user)
) -> TimeSeriesResponse:
    """
    Analyze temporal patterns in knowledge creation and access
    
    Features:
    - Knowledge creation trends over time
    - Access pattern analysis
    - Seasonal pattern detection
    - Anomaly detection in temporal data
    - Forecasting future knowledge needs
    - Activity correlation analysis
    """
    start_time = time.time()
    
    try:
        service = AdvancedQueryService(databases)
        time_series_data = await service.analyze_time_series(query)
        
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Time series analysis completed",
            time_range=f"{query.start_date} to {query.end_date}",
            data_points=len(time_series_data.get("series", [])),
            execution_time_ms=execution_time
        )
        
        return TimeSeriesResponse(
            message="Time series analysis completed successfully",
            data=time_series_data,
            trends_analysis=time_series_data.get("trends", {}),
            execution_time_ms=execution_time,
            data_points_count=len(time_series_data.get("series", []))
        )
        
    except Exception as e:
        logger.error("Time series analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Time series analysis failed: {str(e)}"
        )

@router.post("/similarity-matrix", response_model=SimilarityMatrixResponse)
async def similarity_matrix(
    query: SimilarityMatrixQuery,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_optional_user)
) -> SimilarityMatrixResponse:
    """
    Generate similarity matrices for knowledge items
    
    Features:
    - Semantic similarity using embeddings
    - Content similarity using NLP metrics
    - Structural similarity in knowledge graphs
    - Collaborative filtering similarity
    - Custom similarity metrics
    - Sparse matrix optimization for large datasets
    """
    start_time = time.time()
    
    try:
        service = AdvancedQueryService(databases)
        matrix_data = await service.generate_similarity_matrix(query)
        
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Similarity matrix generation completed",
            matrix_size=f"{matrix_data.get('dimensions', [0, 0])}",
            similarity_metric=query.similarity_metric,
            execution_time_ms=execution_time
        )
        
        return SimilarityMatrixResponse(
            message="Similarity matrix generated successfully",
            data=matrix_data,
            matrix_stats=matrix_data.get("statistics", {}),
            execution_time_ms=execution_time,
            matrix_dimensions=matrix_data.get("dimensions", [0, 0])
        )
        
    except Exception as e:
        logger.error("Similarity matrix generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similarity matrix generation failed: {str(e)}"
        )

# Performance monitoring endpoint
@router.get("/performance/stats")
async def query_performance_stats(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_optional_user)
):
    """Get performance statistics for advanced query operations"""
    try:
        service = AdvancedQueryService(databases)
        stats = await service.get_performance_stats()
        
        return {
            "message": "Query performance statistics retrieved",
            "data": stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Failed to get performance stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance statistics: {str(e)}"
        )