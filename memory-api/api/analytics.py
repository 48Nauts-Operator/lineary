# ABOUTME: Analytics API endpoints for BETTY Memory System dashboard visualizations
# ABOUTME: Provides comprehensive metrics for knowledge growth, cross-project intelligence, and system performance

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import structlog
import time

from models.analytics import (
    KnowledgeGrowthResponse,
    CrossProjectConnectionsResponse,
    PatternUsageResponse,
    RealTimeActivityResponse,
    IntelligenceMetricsResponse,
    SystemPerformanceResponse,
    TechnologyTrendsResponse,
    ActivityFeedItem,
    ProjectNetworkNode,
    PatternUsageItem,
    TechnologyAdoption
)
from models.base import ErrorResponse
from core.dependencies import DatabaseDependencies, get_all_databases
from core.security import get_current_user
from services.analytics_service import AnalyticsService

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/knowledge-growth", response_model=KnowledgeGrowthResponse)
async def get_knowledge_growth(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> KnowledgeGrowthResponse:
    """Get knowledge base growth metrics and trends"""
    start_time = time.time()
    
    try:
        analytics_service = AnalyticsService(databases)
        growth_data = await analytics_service.get_knowledge_growth_metrics(days)
        
        duration = time.time() - start_time
        logger.info(
            "Knowledge growth metrics retrieved",
            days=days,
            total_items=growth_data.total_knowledge_items,
            duration_ms=f"{duration * 1000:.2f}"
        )
        
        return KnowledgeGrowthResponse(
            message=f"Knowledge growth data for last {days} days",
            data=growth_data
        )
        
    except Exception as e:
        logger.error("Failed to get knowledge growth metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve growth metrics: {str(e)}"
        )

@router.get("/cross-project-connections", response_model=CrossProjectConnectionsResponse)
async def get_cross_project_connections(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> CrossProjectConnectionsResponse:
    """Get cross-project intelligence network and connection patterns"""
    try:
        analytics_service = AnalyticsService(databases)
        connections_data = await analytics_service.get_cross_project_connections()
        
        logger.info(
            "Cross-project connections retrieved",
            total_projects=len(connections_data.project_nodes),
            total_connections=len(connections_data.connections)
        )
        
        return CrossProjectConnectionsResponse(
            message="Cross-project intelligence network data",
            data=connections_data
        )
        
    except Exception as e:
        logger.error("Failed to get cross-project connections", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve connections: {str(e)}"
        )

@router.get("/pattern-usage", response_model=PatternUsageResponse)
async def get_pattern_usage(
    limit: int = Query(20, ge=1, le=100, description="Maximum patterns to return"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> PatternUsageResponse:
    """Get most used patterns and their success rates across projects"""
    try:
        analytics_service = AnalyticsService(databases)
        pattern_data = await analytics_service.get_pattern_usage_metrics(limit)
        
        logger.info(
            "Pattern usage metrics retrieved",
            total_patterns=len(pattern_data.hot_patterns)
        )
        
        return PatternUsageResponse(
            message=f"Top {limit} pattern usage metrics",
            data=pattern_data
        )
        
    except Exception as e:
        logger.error("Failed to get pattern usage metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pattern metrics: {str(e)}"
        )

@router.get("/real-time-activity", response_model=RealTimeActivityResponse)
async def get_real_time_activity(
    limit: int = Query(50, ge=1, le=200, description="Maximum activity items to return"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> RealTimeActivityResponse:
    """Get real-time knowledge activity feed"""
    try:
        analytics_service = AnalyticsService(databases)
        activity_data = await analytics_service.get_real_time_activity(limit)
        
        logger.info(
            "Real-time activity retrieved",
            activity_count=len(activity_data.activities)
        )
        
        return RealTimeActivityResponse(
            message=f"Latest {limit} knowledge activities",
            data=activity_data
        )
        
    except Exception as e:
        logger.error("Failed to get real-time activity", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity feed: {str(e)}"
        )

@router.get("/intelligence-metrics", response_model=IntelligenceMetricsResponse)
async def get_intelligence_metrics(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> IntelligenceMetricsResponse:
    """Get BETTY intelligence quality and capability metrics"""
    try:
        analytics_service = AnalyticsService(databases)
        intelligence_data = await analytics_service.get_intelligence_metrics()
        
        logger.info(
            "Intelligence metrics retrieved",
            overall_score=intelligence_data.overall_intelligence_score
        )
        
        return IntelligenceMetricsResponse(
            message="BETTY intelligence quality metrics",
            data=intelligence_data
        )
        
    except Exception as e:
        logger.error("Failed to get intelligence metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve intelligence metrics: {str(e)}"
        )

@router.get("/system-performance", response_model=SystemPerformanceResponse)
async def get_system_performance(
    hours: int = Query(24, ge=1, le=168, description="Hours of performance data"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> SystemPerformanceResponse:
    """Get system performance metrics and health indicators"""
    try:
        analytics_service = AnalyticsService(databases)
        performance_data = await analytics_service.get_system_performance_metrics(hours)
        
        logger.info(
            "System performance metrics retrieved",
            hours=hours,
            avg_response_time=performance_data.average_response_time_ms
        )
        
        return SystemPerformanceResponse(
            message=f"System performance data for last {hours} hours",
            data=performance_data
        )
        
    except Exception as e:
        logger.error("Failed to get system performance metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )

@router.get("/technology-trends", response_model=TechnologyTrendsResponse)
async def get_technology_trends(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> TechnologyTrendsResponse:
    """Get technology adoption trends and evolution across projects"""
    try:
        analytics_service = AnalyticsService(databases)
        trends_data = await analytics_service.get_technology_trends()
        
        logger.info(
            "Technology trends retrieved",
            technologies_tracked=len(trends_data.technology_adoptions)
        )
        
        return TechnologyTrendsResponse(
            message="Technology evolution and adoption trends",
            data=trends_data
        )
        
    except Exception as e:
        logger.error("Failed to get technology trends", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve technology trends: {str(e)}"
        )

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive dashboard summary with all key metrics"""
    try:
        analytics_service = AnalyticsService(databases)
        
        # Get all dashboard data in parallel
        summary_data = await analytics_service.get_dashboard_summary()
        
        logger.info("Dashboard summary retrieved successfully")
        
        return {
            "message": "BETTY Analytics Dashboard Summary",
            "timestamp": datetime.utcnow().isoformat(),
            "data": summary_data
        }
        
    except Exception as e:
        logger.error("Failed to get dashboard summary", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard summary: {str(e)}"
        )

@router.post("/refresh-cache")
async def refresh_analytics_cache(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Refresh analytics cache for updated metrics"""
    try:
        analytics_service = AnalyticsService(databases)
        await analytics_service.refresh_analytics_cache()
        
        logger.info("Analytics cache refreshed successfully")
        
        return {
            "message": "Analytics cache refreshed successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error("Failed to refresh analytics cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh cache: {str(e)}"
        )