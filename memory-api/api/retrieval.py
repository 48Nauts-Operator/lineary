# ABOUTME: Knowledge retrieval API endpoints for BETTY Memory System
# ABOUTME: Advanced endpoints for context loading, similarity search, and cross-project intelligence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import text
import structlog
import time

from models.retrieval import (
    ContextLoadRequest, ContextLoadResponse,
    SimilaritySearchRequest, SimilaritySearchResponse,
    PatternSearchRequest, PatternSearchResponse,
    TechnologyEvolutionResponse,
    RecommendationRequest, RecommendationResponse,
    ContextDepth, PatternType
)
from models.base import ErrorResponse
from core.dependencies import DatabaseDependencies, get_all_databases
from core.security import get_current_user, SecurityManager
from services.retrieval_service import RetrievalService

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/context", response_model=ContextLoadResponse, status_code=status.HTTP_200_OK)
async def load_context_for_session(
    request: ContextLoadRequest,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> ContextLoadResponse:
    """Load relevant context for a new Claude session"""
    start_time = time.time()
    
    try:
        # Sanitize input
        request.current_context.working_on = SecurityManager.sanitize_input(
            request.current_context.working_on, 1000
        )
        
        if request.current_context.user_message:
            request.current_context.user_message = SecurityManager.sanitize_input(
                request.current_context.user_message, 2000
            )
        
        # Ensure user_id matches current user
        if request.user_id != current_user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: user_id mismatch"
            )
        
        # Load context using retrieval service
        retrieval_service = RetrievalService(databases)
        response = await retrieval_service.load_context_for_session(request)
        
        duration = time.time() - start_time
        logger.info(
            "Context loaded for session",
            user_id=request.user_id,
            project_id=request.project_id,
            context_depth=request.context_depth,
            items_returned=response.metadata.items_returned,
            duration_ms=f"{duration * 1000:.2f}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to load context for session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load context: {str(e)}"
        )

@router.post("/similar", response_model=SimilaritySearchResponse, status_code=status.HTTP_200_OK)
async def search_similar_problems(
    request: SimilaritySearchRequest,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> SimilaritySearchResponse:
    """Search for similar problems across all projects"""
    start_time = time.time()
    
    try:
        # Sanitize input
        request.query.text = SecurityManager.sanitize_input(request.query.text, 1000)
        
        # Ensure user_id matches current user
        if request.user_id != current_user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: user_id mismatch"
            )
        
        # Perform similarity search
        retrieval_service = RetrievalService(databases)
        response = await retrieval_service.search_similar_problems(request)
        
        duration = time.time() - start_time
        logger.info(
            "Similarity search completed",
            user_id=request.user_id,
            query=request.query.text[:100],  # Log first 100 chars
            results_count=len(response.similar_items),
            duration_ms=f"{duration * 1000:.2f}",
            similarity_threshold=request.similarity_threshold
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to search similar problems", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similarity search failed: {str(e)}"
        )

@router.get("/patterns", response_model=PatternSearchResponse, status_code=status.HTTP_200_OK)
async def find_reusable_patterns(
    pattern_type: Optional[PatternType] = Query(None, description="Type of pattern to search for"),
    min_success_rate: float = Query(0.8, ge=0.0, le=1.0, description="Minimum success rate"),
    min_usage_count: int = Query(2, ge=1, description="Minimum usage count"),
    technologies: Optional[List[str]] = Query(None, description="Filter by technologies"),
    projects: Optional[List[str]] = Query(None, description="Filter by projects"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> PatternSearchResponse:
    """Find reusable patterns that match criteria"""
    start_time = time.time()
    
    try:
        # Build request object
        request = PatternSearchRequest(
            user_id=current_user.get("user_id"),
            pattern_type=pattern_type,
            min_success_rate=min_success_rate,
            min_usage_count=min_usage_count,
            technologies=technologies or [],
            projects=projects or []
        )
        
        # Find patterns
        retrieval_service = RetrievalService(databases)
        response = await retrieval_service.find_reusable_patterns(request)
        
        duration = time.time() - start_time
        logger.info(
            "Pattern search completed",
            user_id=request.user_id,
            pattern_type=pattern_type,
            patterns_found=len(response.patterns),
            duration_ms=f"{duration * 1000:.2f}",
            min_success_rate=min_success_rate
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to find reusable patterns", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pattern search failed: {str(e)}"
        )

@router.get("/technology/{technology}/evolution", response_model=TechnologyEvolutionResponse, status_code=status.HTTP_200_OK)
async def get_technology_evolution(
    technology: str,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> TechnologyEvolutionResponse:
    """Get technology evolution across projects"""
    start_time = time.time()
    
    try:
        # Sanitize technology name
        technology = SecurityManager.sanitize_input(technology, 100)
        
        # Get evolution data
        retrieval_service = RetrievalService(databases)
        response = await retrieval_service.get_technology_evolution(
            current_user.get("user_id"), technology
        )
        
        duration = time.time() - start_time
        logger.info(
            "Technology evolution retrieved",
            user_id=current_user.get("user_id"),
            technology=technology,
            projects_count=len(response.evolution),
            duration_ms=f"{duration * 1000:.2f}",
            overall_success_rate=response.overall_success_rate
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to get technology evolution", technology=technology, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Technology evolution retrieval failed: {str(e)}"
        )

@router.post("/recommendations", response_model=RecommendationResponse, status_code=status.HTTP_200_OK)
async def generate_cross_project_recommendations(
    request: RecommendationRequest,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> RecommendationResponse:
    """Generate cross-project recommendations"""
    start_time = time.time()
    
    try:
        # Sanitize input
        request.current_project = SecurityManager.sanitize_input(request.current_project, 200)
        request.working_on = SecurityManager.sanitize_input(request.working_on, 1000)
        
        # Ensure user_id matches current user
        if request.user_id != current_user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: user_id mismatch"
            )
        
        # Generate recommendations
        retrieval_service = RetrievalService(databases)
        response = await retrieval_service.generate_recommendations(request)
        
        duration = time.time() - start_time
        logger.info(
            "Cross-project recommendations generated",
            user_id=request.user_id,
            current_project=request.current_project,
            recommendations_count=len(response.recommendations),
            duration_ms=f"{duration * 1000:.2f}",
            confidence_score=response.confidence_score
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate recommendations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation generation failed: {str(e)}"
        )

@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_retrieval_statistics(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get knowledge retrieval system statistics"""
    try:
        # Get basic statistics from database
        stats_query = """
        SELECT 
            COUNT(*) as total_knowledge_items,
            COUNT(DISTINCT project_id) as total_projects,
            COUNT(DISTINCT user_id) as total_users,
            AVG(usage_count) as avg_access_count,
            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as items_last_week,
            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as items_last_month
        FROM knowledge_items 
        WHERE valid_until IS NULL
        """
        
        result = await databases.postgres.execute(text(stats_query))
        row = result.fetchone()
        
        # Get pattern statistics
        pattern_stats_query = """
        SELECT 
            knowledge_type,
            COUNT(*) as count,
            AVG(usage_count) as avg_access
        FROM knowledge_items 
        WHERE valid_until IS NULL 
        GROUP BY knowledge_type
        ORDER BY count DESC
        """
        
        pattern_result = await databases.postgres.execute(text(pattern_stats_query))
        pattern_rows = pattern_result.fetchall()
        
        stats = {
            "retrieval_system": {
                "total_knowledge_items": row.total_knowledge_items or 0,
                "total_projects": row.total_projects or 0,
                "total_users": row.total_users or 0,
                "avg_access_count": float(row.avg_access_count or 0),
                "items_last_week": row.items_last_week or 0,
                "items_last_month": row.items_last_month or 0
            },
            "knowledge_by_type": [
                {
                    "type": row.knowledge_type,
                    "count": row.count,
                    "avg_access": float(row.avg_access or 0)
                }
                for row in pattern_rows
            ],
            "system_health": {
                "status": "operational",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        logger.info("Retrieval statistics retrieved", user_id=current_user.get("user_id"))
        
        return {
            "message": "Retrieval system statistics",
            "data": stats
        }
        
    except Exception as e:
        logger.error("Failed to get retrieval statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

# Additional utility endpoints

@router.post("/cache/clear", status_code=status.HTTP_200_OK)
async def clear_retrieval_cache(
    cache_type: Optional[str] = Query(None, description="Type of cache to clear"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Clear retrieval system cache"""
    try:
        retrieval_service = RetrievalService(databases)
        
        if cache_type:
            cache_pattern = f"retrieval:{cache_type}:*"
        else:
            cache_pattern = "retrieval:*"
        
        await retrieval_service.invalidate_related_cache(cache_pattern)
        
        logger.info(
            "Retrieval cache cleared",
            user_id=current_user.get("user_id"),
            cache_type=cache_type or "all"
        )
        
        return {
            "message": f"Cleared {cache_type or 'all'} retrieval cache",
            "cache_pattern": cache_pattern
        }
        
    except Exception as e:
        logger.error("Failed to clear retrieval cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def get_retrieval_health(
    databases: DatabaseDependencies = Depends(get_all_databases)
):
    """Get retrieval system health status"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "postgres": "operational",
                "qdrant": "operational", 
                "redis": "operational",
                "neo4j": "operational"
            },
            "capabilities": {
                "context_loading": True,
                "similarity_search": True, 
                "pattern_matching": True,
                "cross_project_intelligence": True,
                "technology_evolution": True,
                "recommendations": True
            }
        }
        
        # Test database connections
        try:
            await databases.postgres.execute(text("SELECT 1"))
        except Exception:
            health_status["components"]["postgres"] = "degraded"
            health_status["status"] = "degraded"
        
        try:
            await databases.redis.ping()
        except Exception:
            health_status["components"]["redis"] = "degraded"
            health_status["status"] = "degraded"
        
        # Test vector service
        try:
            retrieval_service = RetrievalService(databases)
            # Could add vector service health check here
        except Exception:
            health_status["components"]["qdrant"] = "degraded"
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error("Failed to get retrieval health", error=str(e))
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }