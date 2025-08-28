# ABOUTME: API endpoints for Multi-Source Knowledge Extraction Pipeline operations and monitoring
# ABOUTME: Provides REST API for extraction control, monitoring, and real-time updates

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import structlog
import json
import asyncio
from collections import defaultdict

from core.dependencies import get_db_manager, get_vector_service
from core.database import DatabaseManager
from models.knowledge import KnowledgeItem
from models.pattern_quality import PatternContext
from services.multi_source_knowledge_extractor import (
    MultiSourceKnowledgeExtractor, ExtractionResult, SourceConfig
)
from services.knowledge_processing_pipeline import (
    KnowledgeProcessingPipeline, ProcessingResult, ProcessingStage
)
from services.realtime_knowledge_updater import (
    RealtimeKnowledgeUpdater, UpdateEvent, UpdateType
)
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer
from services.pattern_intelligence_service import PatternIntelligenceEngine

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/knowledge-extraction", tags=["knowledge-extraction"])

# Pydantic models for API requests/responses
class ExtractionRequest(BaseModel):
    sources: Optional[List[str]] = Field(default=None, description="Specific sources to extract from")
    max_items_per_source: int = Field(default=1000, ge=1, le=10000, description="Maximum items per source")
    quality_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum quality threshold")
    priority: int = Field(default=0, ge=0, le=10, description="Processing priority")

class SourceConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    rate_limit: Optional[float] = Field(None, ge=0.1, le=10.0)
    quality_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    timeout: Optional[float] = Field(None, ge=1.0, le=300.0)

class ProcessingStatusResponse(BaseModel):
    processing_id: UUID
    item_id: UUID
    current_stage: str
    started_at: datetime
    processing_time: float

class ExtractionStatsResponse(BaseModel):
    total_extracted: int
    total_processed: int
    total_stored: int
    sources_active: int
    sources_configured: int
    sources_enabled: int
    last_extraction: Optional[datetime]
    average_quality_threshold: float
    supported_sources: List[str]

class MonitoringStatusResponse(BaseModel):
    monitoring_active: bool
    active_monitors: int
    update_queue_size: int
    active_workers: int
    monitor_status: Dict[str, Any]
    statistics: Dict[str, Any]
    recent_updates: List[Dict[str, Any]]

from services.extraction_pipeline_manager import get_pipeline_manager

async def get_extraction_pipeline():
    """Get the extraction pipeline components"""
    try:
        # This will be injected from the main app
        from core.dependencies import get_db_manager
        db_manager = await get_db_manager()
        pipeline_manager = await get_pipeline_manager(db_manager)
        return pipeline_manager.get_pipeline_components()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Extraction pipeline not available: {str(e)}")

@router.post("/extract", response_model=Dict[str, ExtractionResult])
async def start_extraction(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    pipeline = Depends(get_extraction_pipeline)
):
    """
    Start knowledge extraction from specified sources
    
    This endpoint initiates extraction from all enabled sources or specific sources
    if provided. Returns extraction results for each source.
    """
    try:
        logger.info("Starting knowledge extraction",
                   sources=request.sources,
                   max_items=request.max_items_per_source,
                   quality_threshold=request.quality_threshold)
        
        extractor = pipeline['extractor']
        
        # If specific sources requested, temporarily enable only those
        original_states = {}
        if request.sources:
            for source_name, config in extractor.sources.items():
                original_states[source_name] = config.enabled
                config.enabled = source_name in request.sources
        
        try:
            # Start extraction
            results = await extractor.extract_all_sources(
                max_items_per_source=request.max_items_per_source,
                quality_threshold=request.quality_threshold
            )
            
            # Convert results to serializable format
            serializable_results = {}
            for source_name, result in results.items():
                serializable_results[source_name] = {
                    "source_name": result.source_name,
                    "items_extracted": result.items_extracted,
                    "items_processed": result.items_processed,
                    "items_stored": result.items_stored,
                    "errors": result.errors,
                    "processing_time": result.processing_time,
                    "quality_scores": result.quality_scores
                }
            
            return serializable_results
            
        finally:
            # Restore original states
            if request.sources:
                for source_name, original_state in original_states.items():
                    extractor.sources[source_name].enabled = original_state
        
    except Exception as e:
        logger.error("Knowledge extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.get("/status", response_model=ExtractionStatsResponse)
async def get_extraction_status(
    pipeline = Depends(get_extraction_pipeline)
):
    """Get current extraction pipeline statistics and status"""
    try:
        extractor = pipeline['extractor']
        stats = await extractor.get_extraction_statistics()
        
        return ExtractionStatsResponse(
            total_extracted=stats['total_extracted'],
            total_processed=stats['total_processed'],
            total_stored=stats['total_stored'],
            sources_active=stats['sources_active'],
            sources_configured=stats['sources_configured'],
            sources_enabled=stats['sources_enabled'],
            last_extraction=datetime.fromisoformat(stats['last_extraction']) if stats['last_extraction'] else None,
            average_quality_threshold=stats['average_quality_threshold'],
            supported_sources=stats['supported_sources']
        )
        
    except Exception as e:
        logger.error("Failed to get extraction status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.get("/sources")
async def get_source_configurations(
    pipeline = Depends(get_extraction_pipeline)
):
    """Get configuration for all knowledge sources"""
    try:
        extractor = pipeline['extractor']
        
        source_configs = {}
        for name, config in extractor.sources.items():
            source_configs[name] = {
                "name": config.name,
                "base_url": config.base_url,
                "rate_limit": config.rate_limit,
                "timeout": config.timeout,
                "enabled": config.enabled,
                "quality_weight": config.quality_weight
            }
        
        return source_configs
        
    except Exception as e:
        logger.error("Failed to get source configurations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sources/{source_name}")
async def update_source_configuration(
    source_name: str,
    config_update: SourceConfigUpdate,
    pipeline = Depends(get_extraction_pipeline)
):
    """Update configuration for a specific source"""
    try:
        extractor = pipeline['extractor']
        
        if source_name not in extractor.sources:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")
        
        source_config = extractor.sources[source_name]
        
        # Update configuration
        if config_update.enabled is not None:
            source_config.enabled = config_update.enabled
        if config_update.rate_limit is not None:
            source_config.rate_limit = config_update.rate_limit
        if config_update.quality_weight is not None:
            source_config.quality_weight = config_update.quality_weight
        if config_update.timeout is not None:
            source_config.timeout = config_update.timeout
        
        logger.info(f"Updated configuration for source {source_name}",
                   enabled=source_config.enabled,
                   rate_limit=source_config.rate_limit)
        
        return {
            "source_name": source_name,
            "updated": True,
            "current_config": {
                "enabled": source_config.enabled,
                "rate_limit": source_config.rate_limit,
                "quality_weight": source_config.quality_weight,
                "timeout": source_config.timeout
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update source configuration for {source_name}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing/statistics")
async def get_processing_statistics(
    pipeline = Depends(get_extraction_pipeline)
):
    """Get knowledge processing pipeline statistics"""
    try:
        processor = pipeline['processor']
        stats = await processor.get_processing_statistics()
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get processing statistics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing/status/{processing_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    processing_id: UUID,
    pipeline = Depends(get_extraction_pipeline)
):
    """Get status of a specific processing task"""
    try:
        processor = pipeline['processor']
        status = await processor.get_processing_status(processing_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Processing task not found")
        
        return ProcessingStatusResponse(
            processing_id=UUID(status['processing_id']),
            item_id=UUID(status['item_id']),
            current_stage=status['current_stage'],
            started_at=datetime.fromisoformat(status['started_at']),
            processing_time=status['processing_time']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get processing status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/processing/submit")
async def submit_item_for_processing(
    knowledge_item: dict,
    priority: int = Query(default=0, ge=0, le=10),
    pipeline = Depends(get_extraction_pipeline)
):
    """Submit a knowledge item for processing"""
    try:
        processor = pipeline['processor']
        
        # Convert dict to KnowledgeItem
        item = KnowledgeItem(
            id=UUID(knowledge_item['id']) if 'id' in knowledge_item else uuid4(),
            title=knowledge_item['title'],
            content=knowledge_item['content'],
            knowledge_type=knowledge_item.get('knowledge_type', 'pattern'),
            source_type=knowledge_item.get('source_type', 'manual'),
            source_url=knowledge_item.get('source_url', ''),
            tags=knowledge_item.get('tags', []),
            summary=knowledge_item.get('summary', ''),
            confidence=knowledge_item.get('confidence', 'medium'),
            metadata=knowledge_item.get('metadata', {})
        )
        
        processing_id = await processor.submit_for_processing(item, priority)
        
        return {
            "processing_id": str(processing_id),
            "item_id": str(item.id),
            "submitted_at": datetime.utcnow().isoformat(),
            "priority": priority
        }
        
    except Exception as e:
        logger.error("Failed to submit item for processing", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(
    pipeline = Depends(get_extraction_pipeline)
):
    """Get real-time monitoring status"""
    try:
        updater = pipeline['updater']
        status = await updater.get_monitoring_status()
        
        return MonitoringStatusResponse(
            monitoring_active=status['monitoring_active'],
            active_monitors=status['active_monitors'],
            update_queue_size=status['update_queue_size'],
            active_workers=status['active_workers'],
            monitor_status=status['monitor_status'],
            statistics=status['statistics'],
            recent_updates=status['recent_updates']
        )
        
    except Exception as e:
        logger.error("Failed to get monitoring status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/start")
async def start_monitoring(
    pipeline = Depends(get_extraction_pipeline)
):
    """Start real-time monitoring of knowledge sources"""
    try:
        updater = pipeline['updater']
        await updater.start_monitoring()
        
        return {
            "monitoring_started": True,
            "started_at": datetime.utcnow().isoformat(),
            "message": "Real-time monitoring started successfully"
        }
        
    except Exception as e:
        logger.error("Failed to start monitoring", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/stop")
async def stop_monitoring(
    pipeline = Depends(get_extraction_pipeline)
):
    """Stop real-time monitoring"""
    try:
        updater = pipeline['updater']
        await updater.stop_monitoring()
        
        return {
            "monitoring_stopped": True,
            "stopped_at": datetime.utcnow().isoformat(),
            "message": "Real-time monitoring stopped successfully"
        }
        
    except Exception as e:
        logger.error("Failed to stop monitoring", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_extracted_knowledge(
    query: str = Query(..., min_length=1, description="Search query"),
    sources: Optional[List[str]] = Query(default=None, description="Filter by sources"),
    domains: Optional[List[str]] = Query(default=None, description="Filter by domains"),
    quality_threshold: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum quality score"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    pipeline = Depends(get_extraction_pipeline)
):
    """Search through extracted knowledge with filters"""
    try:
        db_manager = pipeline['db_manager']
        vector_service = pipeline['vector_service']
        
        # Perform vector search
        query_embedding = await vector_service.generate_embedding(query)
        similar_items = await vector_service.search_similar(
            query_embedding, 
            limit=limit * 2,  # Get more candidates for filtering
            threshold=0.3  # Lower threshold for initial search
        )
        
        # Apply filters and format results
        results = []
        for item in similar_items:
            # Apply source filter
            if sources and item.source_type not in sources:
                continue
                
            # Apply domain filter (from metadata)
            if domains and item.metadata:
                item_domain = item.metadata.get('classification', {}).get('primary_domain')
                if item_domain not in domains:
                    continue
            
            # Apply quality threshold
            quality_score = item.metadata.get('quality_scores', {}).get('overall', 0.0) if item.metadata else 0.0
            if quality_score < quality_threshold:
                continue
            
            # Format result
            result = {
                "id": str(item.id),
                "title": item.title,
                "summary": item.summary,
                "source_type": item.source_type,
                "source_url": item.source_url,
                "tags": item.tags,
                "confidence": item.confidence,
                "quality_score": quality_score,
                "domain": item.metadata.get('classification', {}).get('primary_domain') if item.metadata else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
            }
            results.append(result)
            
            if len(results) >= limit:
                break
        
        # Apply offset
        paginated_results = results[offset:offset + limit]
        
        return {
            "query": query,
            "total_found": len(results),
            "returned": len(paginated_results),
            "offset": offset,
            "limit": limit,
            "results": paginated_results,
            "filters_applied": {
                "sources": sources,
                "domains": domains,
                "quality_threshold": quality_threshold
            }
        }
        
    except Exception as e:
        logger.error("Knowledge search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/dashboard")
async def get_extraction_analytics(
    time_range: str = Query(default="7d", regex="^(1d|7d|30d|90d)$", description="Time range for analytics"),
    pipeline = Depends(get_extraction_pipeline)
):
    """Get extraction analytics for dashboard"""
    try:
        db_manager = pipeline['db_manager']
        
        # Parse time range
        time_delta_map = {
            "1d": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90)
        }
        
        since_date = datetime.utcnow() - time_delta_map[time_range]
        
        # Get analytics data from database
        async with db_manager.get_postgres_pool().acquire() as conn:
            # Extraction trends
            extraction_trends = await conn.fetch("""
                SELECT DATE(timestamp) as date,
                       COUNT(*) as extractions,
                       SUM(total_extracted) as total_items,
                       SUM(total_stored) as stored_items,
                       AVG(CASE WHEN JSONB_TYPEOF(extraction_results) = 'object' 
                               THEN (SELECT AVG((value->>'avg_quality')::float) 
                                     FROM jsonb_each(extraction_results))
                               ELSE 0 END) as avg_quality
                FROM extraction_stats 
                WHERE timestamp >= $1
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, since_date)
            
            # Source performance
            source_performance = await conn.fetch("""
                SELECT source_type,
                       COUNT(*) as items_count,
                       AVG(quality_score) as avg_quality,
                       MAX(created_at) as last_extraction
                FROM knowledge_items 
                WHERE created_at >= $1
                GROUP BY source_type
                ORDER BY items_count DESC
            """, since_date)
            
            # Domain distribution
            domain_distribution = await conn.fetch("""
                SELECT metadata->>'classification'->>'primary_domain' as domain,
                       COUNT(*) as count
                FROM knowledge_items 
                WHERE created_at >= $1 
                AND metadata->>'classification'->>'primary_domain' IS NOT NULL
                GROUP BY domain
                ORDER BY count DESC
            """, since_date)
            
            # Quality score distribution
            quality_distribution = await conn.fetch("""
                SELECT CASE 
                       WHEN quality_score >= 0.8 THEN 'high'
                       WHEN quality_score >= 0.6 THEN 'medium' 
                       WHEN quality_score >= 0.4 THEN 'low'
                       ELSE 'very_low'
                       END as quality_tier,
                       COUNT(*) as count
                FROM knowledge_items 
                WHERE created_at >= $1 
                AND quality_score IS NOT NULL
                GROUP BY quality_tier
                ORDER BY CASE quality_tier 
                         WHEN 'very_low' THEN 1
                         WHEN 'low' THEN 2  
                         WHEN 'medium' THEN 3
                         WHEN 'high' THEN 4
                         END
            """, since_date)
        
        # Format response
        analytics = {
            "time_range": time_range,
            "period": {
                "start": since_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "extraction_trends": [
                {
                    "date": str(row["date"]),
                    "extractions": row["extractions"],
                    "total_items": row["total_items"],
                    "stored_items": row["stored_items"],
                    "avg_quality": float(row["avg_quality"]) if row["avg_quality"] else 0.0
                }
                for row in extraction_trends
            ],
            "source_performance": [
                {
                    "source": row["source_type"],
                    "items_count": row["items_count"],
                    "avg_quality": float(row["avg_quality"]) if row["avg_quality"] else 0.0,
                    "last_extraction": row["last_extraction"].isoformat() if row["last_extraction"] else None
                }
                for row in source_performance
            ],
            "domain_distribution": [
                {"domain": row["domain"], "count": row["count"]}
                for row in domain_distribution
            ],
            "quality_distribution": [
                {"quality_tier": row["quality_tier"], "count": row["count"]}
                for row in quality_distribution
            ]
        }
        
        return analytics
        
    except Exception as e:
        logger.error("Failed to get extraction analytics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(
    pipeline = Depends(get_extraction_pipeline)
):
    """Health check for the knowledge extraction system"""
    try:
        extractor = pipeline['extractor']
        processor = pipeline['processor']
        updater = pipeline['updater']
        
        # Check component health
        extractor_stats = await extractor.get_extraction_statistics()
        processor_stats = await processor.get_processing_statistics()
        monitoring_status = await updater.get_monitoring_status()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "extractor": {
                    "status": "healthy",
                    "sources_enabled": extractor_stats["sources_enabled"],
                    "last_extraction": extractor_stats["last_extraction"]
                },
                "processor": {
                    "status": "healthy",
                    "queue_size": processor_stats["queue_size"],
                    "active_workers": processor_stats["active_workers"]
                },
                "updater": {
                    "status": "healthy" if monitoring_status["monitoring_active"] else "inactive",
                    "active_monitors": monitoring_status["active_monitors"],
                    "update_queue_size": monitoring_status["update_queue_size"]
                }
            },
            "overall_metrics": {
                "total_items_stored": extractor_stats["total_stored"],
                "processing_throughput": processor_stats.get("average_throughput", 0.0),
                "monitoring_active": monitoring_status["monitoring_active"]
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Stream endpoints for real-time updates
@router.get("/stream/updates")
async def stream_updates(
    sources: Optional[List[str]] = Query(default=None),
    pipeline = Depends(get_extraction_pipeline)
):
    """Stream real-time knowledge updates"""
    async def update_generator():
        """Generator for streaming updates"""
        try:
            updater = pipeline['updater']
            last_update_time = datetime.utcnow()
            
            while True:
                # Get recent updates
                status = await updater.get_monitoring_status()
                recent_updates = status.get('recent_updates', [])
                
                # Filter updates since last check
                new_updates = [
                    update for update in recent_updates
                    if datetime.fromisoformat(update['processed_at']) > last_update_time
                ]
                
                # Apply source filter if specified
                if sources:
                    new_updates = [
                        update for update in new_updates
                        if update['source'] in sources
                    ]
                
                # Yield new updates
                for update in new_updates:
                    yield f"data: {json.dumps(update)}\n\n"
                
                last_update_time = datetime.utcnow()
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        update_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )