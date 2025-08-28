# ABOUTME: Graphiti temporal knowledge graph API endpoints for BETTY Memory System
# ABOUTME: Provides REST API for knowledge ingestion, entity extraction, and context retrieval

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from core.dependencies import get_databases
from services.graphiti_service import GraphitiService, ConversationEpisode

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/graphiti", tags=["graphiti"])

class EpisodeCreateRequest(BaseModel):
    """Request model for creating a conversation episode"""
    session_id: str = Field(..., description="Chat session ID")
    user_id: str = Field(..., description="User identifier")
    project_name: str = Field(..., description="Project context")
    conversation_content: str = Field(..., description="Conversation text to analyze")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class EpisodeIngestRequest(BaseModel):
    """Request model for ingesting an episode"""
    episode_id: str = Field(..., description="Episode ID to ingest")
    extract_entities: bool = Field(default=True, description="Whether to extract entities")

class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge graph search"""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")
    search_type: str = Field(default="hybrid", description="Search type: semantic, keyword, graph, hybrid")

class CrossProjectInsightsRequest(BaseModel):
    """Request model for cross-project insights"""
    current_project: str = Field(..., description="Current project name")
    query_context: str = Field(..., description="Context for finding similar patterns")

class TemporalContextRequest(BaseModel):
    """Request model for temporal context"""
    entity_name: str = Field(..., description="Entity name to get temporal context for")
    start_time: Optional[datetime] = Field(default=None, description="Start time for temporal range")
    end_time: Optional[datetime] = Field(default=None, description="End time for temporal range")

@router.post("/episodes", response_model=Dict[str, Any])
async def create_episode(
    request: EpisodeCreateRequest,
    databases = Depends(get_databases)
):
    """Create a new conversation episode for knowledge extraction"""
    try:
        graphiti_service = GraphitiService(databases)
        
        episode = await graphiti_service.create_episode(
            session_id=request.session_id,
            user_id=request.user_id,
            project_name=request.project_name,
            conversation_content=request.conversation_content,
            metadata=request.metadata
        )
        
        return {
            "episode_id": episode.episode_id,
            "session_id": episode.session_id,
            "project_name": episode.project_name,
            "timestamp": episode.timestamp.isoformat(),
            "content_length": len(episode.conversation_content),
            "status": "created"
        }
        
    except Exception as e:
        logger.error("Failed to create episode", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/episodes/ingest", response_model=Dict[str, Any])
async def ingest_episode(
    request: EpisodeIngestRequest,
    background_tasks: BackgroundTasks,
    databases = Depends(get_databases)
):
    """Ingest episode into temporal knowledge graph (async processing)"""
    try:
        graphiti_service = GraphitiService(databases)
        
        # Create episode object (in real implementation, this would be retrieved from storage)
        # For now, we'll handle this as a background task
        
        # Add ingestion as background task for better performance
        background_tasks.add_task(
            _ingest_episode_background,
            graphiti_service,
            request.episode_id,
            request.extract_entities
        )
        
        return {
            "episode_id": request.episode_id,
            "status": "ingestion_started",
            "extract_entities": request.extract_entities,
            "message": "Episode ingestion started in background"
        }
        
    except Exception as e:
        logger.error("Failed to start episode ingestion", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def _ingest_episode_background(
    graphiti_service: GraphitiService,
    episode_id: str,
    extract_entities: bool
):
    """Background task for episode ingestion"""
    try:
        # TODO: Retrieve episode from storage
        # For now, this is a placeholder
        logger.info(
            "Background episode ingestion started",
            episode_id=episode_id,
            extract_entities=extract_entities
        )
        
        # Actual ingestion logic would go here
        
    except Exception as e:
        logger.error(
            "Background episode ingestion failed",
            episode_id=episode_id,
            error=str(e)
        )

@router.post("/episodes/ingest-direct", response_model=Dict[str, Any])
async def ingest_episode_direct(
    request: EpisodeCreateRequest,
    databases = Depends(get_databases)
):
    """Create and immediately ingest episode (synchronous)"""
    try:
        graphiti_service = GraphitiService(databases)
        
        # Create episode
        episode = await graphiti_service.create_episode(
            session_id=request.session_id,
            user_id=request.user_id,
            project_name=request.project_name,
            conversation_content=request.conversation_content,
            metadata=request.metadata
        )
        
        # Ingest immediately
        ingestion_result = await graphiti_service.ingest_episode(
            episode=episode,
            extract_entities=True
        )
        
        return {
            "episode": {
                "episode_id": episode.episode_id,
                "session_id": episode.session_id,
                "project_name": episode.project_name,
                "timestamp": episode.timestamp.isoformat()
            },
            "ingestion": ingestion_result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error("Failed to ingest episode directly", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=List[Dict[str, Any]])
async def search_knowledge_graph(
    request: KnowledgeSearchRequest,
    databases = Depends(get_databases)
):
    """Search the temporal knowledge graph for relevant context"""
    try:
        graphiti_service = GraphitiService(databases)
        
        results = await graphiti_service.search_knowledge_graph(
            query=request.query,
            limit=request.limit,
            search_type=request.search_type
        )
        
        return results
        
    except Exception as e:
        logger.error("Knowledge graph search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/insights/cross-project", response_model=List[Dict[str, Any]])
async def get_cross_project_insights(
    request: CrossProjectInsightsRequest,
    databases = Depends(get_databases)
):
    """Get insights from other projects based on current context"""
    try:
        graphiti_service = GraphitiService(databases)
        
        insights = await graphiti_service.get_cross_project_insights(
            current_project=request.current_project,
            query_context=request.query_context
        )
        
        return insights
        
    except Exception as e:
        logger.error("Cross-project insights failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/temporal/context", response_model=Dict[str, Any])
async def get_temporal_context(
    request: TemporalContextRequest,
    databases = Depends(get_databases)
):
    """Get temporal evolution of an entity or relationship"""
    try:
        graphiti_service = GraphitiService(databases)
        
        time_range = None
        if request.start_time or request.end_time:
            time_range = {
                "start": request.start_time,
                "end": request.end_time
            }
        
        temporal_data = await graphiti_service.get_temporal_context(
            entity_name=request.entity_name,
            time_range=time_range
        )
        
        return temporal_data
        
    except Exception as e:
        logger.error("Temporal context retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities/extract")
async def extract_entities_from_text(
    text: str,
    project_context: Optional[str] = None,
    databases = Depends(get_databases)
):
    """Extract domain-specific entities from text"""
    try:
        graphiti_service = GraphitiService(databases)
        
        entities = await graphiti_service.extract_entities_from_text(
            text=text,
            project_context=project_context
        )
        
        # Convert Pydantic models to dict for JSON response
        entities_data = []
        for entity in entities:
            entities_data.append({
                "uuid": entity.uuid,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "project_context": entity.project_context,
                "confidence_score": entity.confidence_score,
                "source_episode": entity.source_episode
            })
        
        return {
            "text_length": len(text),
            "project_context": project_context,
            "entities_count": len(entities_data),
            "entities": entities_data
        }
        
    except Exception as e:
        logger.error("Entity extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=Dict[str, Any])
async def get_graph_statistics(
    databases = Depends(get_databases)
):
    """Get knowledge graph statistics and health metrics"""
    try:
        graphiti_service = GraphitiService(databases)
        
        stats = await graphiti_service.get_graph_statistics()
        
        return stats
        
    except Exception as e:
        logger.error("Graph statistics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maintenance/cleanup", response_model=Dict[str, Any])
async def cleanup_old_episodes(
    retention_days: int = 90,
    background_tasks: BackgroundTasks = None,
    databases = Depends(get_databases)
):
    """Clean up old episodes and optimize graph storage"""
    try:
        graphiti_service = GraphitiService(databases)
        
        if background_tasks:
            # Run cleanup as background task
            background_tasks.add_task(
                _cleanup_episodes_background,
                graphiti_service,
                retention_days
            )
            
            return {
                "status": "cleanup_started_background",
                "retention_days": retention_days,
                "message": "Episode cleanup started in background"
            }
        else:
            # Run cleanup synchronously  
            cleanup_result = await graphiti_service.cleanup_old_episodes(
                retention_days=retention_days
            )
            
            return cleanup_result
        
    except Exception as e:
        logger.error("Episode cleanup failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def _cleanup_episodes_background(
    graphiti_service: GraphitiService,
    retention_days: int
):
    """Background task for episode cleanup"""
    try:
        result = await graphiti_service.cleanup_old_episodes(retention_days)
        logger.info(
            "Background episode cleanup completed",
            **result
        )
        
    except Exception as e:
        logger.error(
            "Background episode cleanup failed",
            retention_days=retention_days,
            error=str(e)
        )