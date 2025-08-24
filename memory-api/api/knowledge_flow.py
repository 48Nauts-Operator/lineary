# ABOUTME: Knowledge Flow API - Real-time tracking of Betty's knowledge ingestion and storage process
# ABOUTME: Provides transparent audit trail and visualization of how knowledge flows through Betty's system

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Optional, Any
import structlog
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum
from pydantic import BaseModel
import asyncio

from core.database import DatabaseManager

router = APIRouter(prefix="/api/knowledge-flow", tags=["Knowledge Flow"])
logger = structlog.get_logger(__name__)

# Knowledge Flow Models
class KnowledgeSourceType(str, Enum):
    DOCUMENT = "document"
    CODE = "code" 
    CONVERSATION = "conversation"
    WEB_SCRAPE = "web_scrape"
    API_RESPONSE = "api_response"

class ProcessingStage(str, Enum):
    INGESTED = "ingested"
    PARSING = "parsing"
    PATTERN_EXTRACTION = "pattern_extraction"
    QUALITY_SCORING = "quality_scoring"
    RELATIONSHIP_MAPPING = "relationship_mapping"
    STORAGE_POSTGRES = "storage_postgres"
    STORAGE_NEO4J = "storage_neo4j"
    STORAGE_QDRANT = "storage_qdrant"
    STORAGE_REDIS = "storage_redis"
    COMPLETED = "completed"
    FAILED = "failed"

class KnowledgeFlowEvent(BaseModel):
    event_id: str
    source_id: str
    source_type: KnowledgeSourceType
    source_name: str
    stage: ProcessingStage
    timestamp: datetime
    processing_time_ms: Optional[int] = None
    data_size_bytes: Optional[int] = None
    patterns_extracted: Optional[int] = None
    quality_score: Optional[float] = None
    storage_locations: List[str] = []
    metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None

class KnowledgeFlowSession(BaseModel):
    session_id: str
    source_type: KnowledgeSourceType
    source_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_items_processed: int = 0
    patterns_generated: int = 0
    avg_quality_score: Optional[float] = None
    storage_distribution: Dict[str, int] = {}
    status: str = "active"

# In-memory storage for real-time tracking (in production, use Redis)
active_sessions: Dict[str, KnowledgeFlowSession] = {}
recent_events: List[KnowledgeFlowEvent] = []
MAX_RECENT_EVENTS = 1000

async def get_db_manager() -> DatabaseManager:
    """Dependency to get database manager"""
    # This would be injected in real implementation
    from main import db_manager
    return db_manager

@router.post("/sessions/start")
async def start_knowledge_flow_session(
    source_type: KnowledgeSourceType,
    source_name: str,
    metadata: Dict[str, Any] = {}
) -> Dict[str, str]:
    """Start a new knowledge flow tracking session"""
    session_id = str(uuid.uuid4())
    
    session = KnowledgeFlowSession(
        session_id=session_id,
        source_type=source_type,
        source_name=source_name,
        started_at=datetime.utcnow()
    )
    
    active_sessions[session_id] = session
    
    # Log session start event
    event = KnowledgeFlowEvent(
        event_id=str(uuid.uuid4()),
        source_id=session_id,
        source_type=source_type,
        source_name=source_name,
        stage=ProcessingStage.INGESTED,
        timestamp=datetime.utcnow(),
        metadata=metadata
    )
    
    recent_events.append(event)
    if len(recent_events) > MAX_RECENT_EVENTS:
        recent_events.pop(0)
    
    logger.info(
        "Knowledge flow session started",
        session_id=session_id,
        source_type=source_type,
        source_name=source_name
    )
    
    return {"session_id": session_id, "status": "started"}

@router.post("/events/track")
async def track_knowledge_flow_event(
    event: KnowledgeFlowEvent,
    db_manager: DatabaseManager = Depends(get_db_manager)
) -> Dict[str, str]:
    """Track a knowledge flow event"""
    
    # Add to recent events
    recent_events.append(event)
    if len(recent_events) > MAX_RECENT_EVENTS:
        recent_events.pop(0)
    
    # Update session if it exists
    if event.source_id in active_sessions:
        session = active_sessions[event.source_id]
        
        if event.stage == ProcessingStage.COMPLETED:
            session.completed_at = event.timestamp
            session.status = "completed"
        elif event.stage == ProcessingStage.FAILED:
            session.status = "failed"
            
        if event.patterns_extracted:
            session.patterns_generated += event.patterns_extracted
            
        if event.quality_score:
            # Update running average
            if session.avg_quality_score is None:
                session.avg_quality_score = event.quality_score
            else:
                session.avg_quality_score = (session.avg_quality_score + event.quality_score) / 2
                
        # Update storage distribution
        for location in event.storage_locations:
            session.storage_distribution[location] = session.storage_distribution.get(location, 0) + 1
            
        session.total_items_processed += 1
    
    # Store in audit log (PostgreSQL)
    try:
        async with db_manager.get_postgres_session() as session_db:
            # In real implementation, store in audit_log table
            pass
    except Exception as e:
        logger.error("Failed to store audit log", error=str(e))
    
    logger.info(
        "Knowledge flow event tracked",
        event_id=event.event_id,
        source_id=event.source_id,
        stage=event.stage,
        processing_time_ms=event.processing_time_ms
    )
    
    return {"status": "tracked", "event_id": event.event_id}

@router.get("/sessions/active")
async def get_active_sessions() -> Dict[str, Any]:
    """Get all active knowledge flow sessions"""
    return {
        "active_sessions": list(active_sessions.values()),
        "total_active": len(active_sessions)
    }

@router.get("/events/recent")
async def get_recent_events(limit: int = 50) -> Dict[str, Any]:
    """Get recent knowledge flow events"""
    return {
        "events": recent_events[-limit:] if recent_events else [],
        "total_events": len(recent_events)
    }

@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str) -> KnowledgeFlowSession:
    """Get details for a specific session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]

@router.get("/stats/realtime")
async def get_realtime_stats() -> Dict[str, Any]:
    """Get real-time knowledge flow statistics"""
    now = datetime.utcnow()
    last_hour = now - timedelta(hours=1)
    last_24h = now - timedelta(hours=24)
    
    # Filter events by time
    events_last_hour = [e for e in recent_events if e.timestamp >= last_hour]
    events_last_24h = [e for e in recent_events if e.timestamp >= last_24h]
    
    # Calculate stats
    patterns_last_hour = sum(e.patterns_extracted or 0 for e in events_last_hour)
    patterns_last_24h = sum(e.patterns_extracted or 0 for e in events_last_24h)
    
    # Storage distribution
    storage_dist = {}
    for event in events_last_24h:
        for location in event.storage_locations:
            storage_dist[location] = storage_dist.get(location, 0) + 1
    
    # Average processing times
    processing_times = [e.processing_time_ms for e in events_last_24h if e.processing_time_ms]
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Quality scores
    quality_scores = [e.quality_score for e in events_last_24h if e.quality_score]
    avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    return {
        "realtime_stats": {
            "active_sessions": len(active_sessions),
            "events_last_hour": len(events_last_hour),
            "events_last_24h": len(events_last_24h),
            "patterns_generated_last_hour": patterns_last_hour,
            "patterns_generated_last_24h": patterns_last_24h,
            "avg_processing_time_ms": round(avg_processing_time, 2),
            "avg_quality_score": round(avg_quality_score, 2),
            "storage_distribution": storage_dist,
            "source_type_breakdown": {
                source_type.value: len([e for e in events_last_24h if e.source_type == source_type])
                for source_type in KnowledgeSourceType
            }
        },
        "timestamp": now.isoformat()
    }

@router.get("/audit/search")
async def search_audit_log(
    source_type: Optional[KnowledgeSourceType] = None,
    stage: Optional[ProcessingStage] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """Search the knowledge flow audit log"""
    
    # Filter recent events (in production, query PostgreSQL)
    filtered_events = recent_events
    
    if source_type:
        filtered_events = [e for e in filtered_events if e.source_type == source_type]
    
    if stage:
        filtered_events = [e for e in filtered_events if e.stage == stage]
        
    if start_date:
        filtered_events = [e for e in filtered_events if e.timestamp >= start_date]
        
    if end_date:
        filtered_events = [e for e in filtered_events if e.timestamp <= end_date]
    
    # Limit results
    filtered_events = filtered_events[-limit:]
    
    return {
        "events": filtered_events,
        "total_found": len(filtered_events),
        "filters_applied": {
            "source_type": source_type,
            "stage": stage,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
    }

@router.post("/demo/ingest-documentation")
async def demo_ingest_documentation(
    url: str,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Demo endpoint: Simulate ingesting documentation with full flow tracking"""
    
    session_id = await start_knowledge_flow_session(
        source_type=KnowledgeSourceType.WEB_SCRAPE,
        source_name=url,
        metadata={"demo": True, "url": url}
    )
    
    # Start background processing
    background_tasks.add_task(simulate_documentation_processing, session_id["session_id"], url)
    
    return {
        "message": "Documentation ingestion started",
        "session_id": session_id["session_id"],
        "url": url
    }

async def simulate_documentation_processing(session_id: str, url: str):
    """Simulate the full documentation processing pipeline"""
    
    try:
        stages = [
            (ProcessingStage.PARSING, 1200, "Parsing documentation structure"),
            (ProcessingStage.PATTERN_EXTRACTION, 2500, "Extracting knowledge patterns"),
            (ProcessingStage.QUALITY_SCORING, 800, "Calculating quality scores"),
            (ProcessingStage.RELATIONSHIP_MAPPING, 1500, "Mapping relationships"),
            (ProcessingStage.STORAGE_POSTGRES, 300, "Storing metadata in PostgreSQL"),
            (ProcessingStage.STORAGE_NEO4J, 450, "Storing relationships in Neo4j"),
            (ProcessingStage.STORAGE_QDRANT, 600, "Storing vectors in Qdrant"),
            (ProcessingStage.STORAGE_REDIS, 100, "Caching in Redis"),
            (ProcessingStage.COMPLETED, 0, "Processing completed")
        ]
        
        patterns_extracted = 0
        
        for stage, processing_time, description in stages:
            await asyncio.sleep(processing_time / 1000)  # Simulate processing time
            
            # Generate realistic data based on stage
            if stage == ProcessingStage.PATTERN_EXTRACTION:
                patterns_extracted = 12
            
            storage_locations = []
            if "STORAGE_" in stage.value:
                storage_locations = [stage.value.replace("STORAGE_", "").lower()]
            
            event = KnowledgeFlowEvent(
                event_id=str(uuid.uuid4()),
                source_id=session_id,
                source_type=KnowledgeSourceType.WEB_SCRAPE,
                source_name=url,
                stage=stage,
                timestamp=datetime.utcnow(),
                processing_time_ms=processing_time,
                data_size_bytes=15000 if stage == ProcessingStage.PARSING else None,
                patterns_extracted=patterns_extracted if stage == ProcessingStage.PATTERN_EXTRACTION else None,
                quality_score=0.89 if stage == ProcessingStage.QUALITY_SCORING else None,
                storage_locations=storage_locations,
                metadata={"description": description, "demo": True}
            )
            
            await track_knowledge_flow_event(event)
            
        logger.info("Documentation processing simulation completed", session_id=session_id)
        
    except Exception as e:
        # Track error
        error_event = KnowledgeFlowEvent(
            event_id=str(uuid.uuid4()),
            source_id=session_id,
            source_type=KnowledgeSourceType.WEB_SCRAPE,
            source_name=url,
            stage=ProcessingStage.FAILED,
            timestamp=datetime.utcnow(),
            error_message=str(e),
            metadata={"demo": True}
        )
        
        await track_knowledge_flow_event(error_event)
        logger.error("Documentation processing failed", session_id=session_id, error=str(e))