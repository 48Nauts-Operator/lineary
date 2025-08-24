# ABOUTME: API endpoints for Source Validation & Verification System operations and monitoring
# ABOUTME: Provides REST API for validation control, monitoring, compliance reporting, and real-time alerts

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Path
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
from services.source_validation_service import (
    SourceValidationService, ValidationResult, ValidationStatus, 
    CredibilityLevel, ValidationSeverity, get_validation_service
)
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/source-validation", tags=["source-validation"])

# Pydantic models for API requests/responses
class ValidationRequest(BaseModel):
    item_ids: List[UUID] = Field(..., description="Knowledge item IDs to validate")
    validation_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Validation configuration options")
    priority: int = Field(default=5, ge=1, le=10, description="Validation priority (1=lowest, 10=highest)")

class BulkValidationRequest(BaseModel):
    source_filters: Optional[List[str]] = Field(default=None, description="Filter by specific sources")
    quality_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum quality threshold for validation")
    max_items: int = Field(default=1000, ge=1, le=10000, description="Maximum items to validate")
    validation_options: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ValidationResultResponse(BaseModel):
    validation_id: str
    item_id: str
    source_name: str
    status: str
    credibility_score: float
    accuracy_score: float
    security_score: float
    freshness_score: float
    overall_score: float
    validation_time: float
    timestamp: datetime
    issues: List[Dict[str, Any]]
    recommendations: List[str]

class ValidationStatsResponse(BaseModel):
    total_validations: int
    success_rate: float
    average_score: float
    average_validation_time: float
    quarantined_items: int
    failed_validations: int
    error_rate: float
    performance_metrics: Dict[str, Any]
    source_breakdown: List[Dict[str, Any]]

class SourceCredibilityResponse(BaseModel):
    source_name: str
    base_credibility: float
    historical_accuracy: float
    community_validation: float
    reputation_score: float
    total_validations: int
    successful_validations: int
    last_validation: Optional[datetime]

class SecurityAlertResponse(BaseModel):
    alert_id: str
    alert_type: str
    alert_level: str
    alert_title: str
    alert_message: str
    source_name: Optional[str]
    item_id: Optional[str]
    status: str
    created_at: datetime
    metrics: Dict[str, Any]

async def get_validation_service_dep(
    db_manager: DatabaseManager = Depends(get_db_manager),
    vector_service: VectorService = Depends(get_vector_service)
) -> SourceValidationService:
    """Dependency to get validation service"""
    return await get_validation_service(db_manager, vector_service)

@router.post("/validate", response_model=List[ValidationResultResponse])
async def validate_items(
    request: ValidationRequest,
    background_tasks: BackgroundTasks,
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """
    Validate specific knowledge items
    
    Performs comprehensive validation including credibility assessment,
    accuracy verification, security scanning, and freshness evaluation.
    """
    try:
        logger.info("Starting item validation",
                   item_count=len(request.item_ids),
                   priority=request.priority)
        
        # Get knowledge items from database
        db_manager = validation_service.db_manager
        items = []
        
        async with db_manager.get_postgres_pool().acquire() as conn:
            for item_id in request.item_ids:
                item_data = await conn.fetchrow(
                    "SELECT * FROM knowledge_items WHERE id = $1", item_id
                )
                if item_data:
                    item = KnowledgeItem(
                        id=item_data['id'],
                        title=item_data['title'],
                        content=item_data['content'],
                        knowledge_type=item_data['knowledge_type'],
                        source_type=item_data['source_type'],
                        source_url=item_data['source_url'] or '',
                        tags=item_data['tags'] or [],
                        summary=item_data['summary'] or '',
                        confidence=item_data['confidence'] or 'medium',
                        metadata=item_data['metadata'] or {},
                        created_at=item_data['created_at'],
                        updated_at=item_data['updated_at']
                    )
                    items.append(item)
        
        if not items:
            raise HTTPException(status_code=404, detail="No valid items found for validation")
        
        # Perform validation for each item
        validation_results = []
        for item in items:
            result = await validation_service.validate_knowledge_item(item)
            validation_results.append(ValidationResultResponse(
                validation_id=result.validation_id,
                item_id=result.item_id,
                source_name=result.source_name,
                status=result.status.value,
                credibility_score=result.credibility_score,
                accuracy_score=result.accuracy_score,
                security_score=result.security_score,
                freshness_score=result.freshness_score,
                overall_score=result.overall_score,
                validation_time=result.validation_time,
                timestamp=result.timestamp,
                issues=result.issues,
                recommendations=result.recommendations
            ))
        
        logger.info("Item validation completed",
                   validated_items=len(validation_results),
                   successful_validations=len([r for r in validation_results if r.status == 'validated']))
        
        return validation_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Validation request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/validate/bulk")
async def bulk_validate(
    request: BulkValidationRequest,
    background_tasks: BackgroundTasks,
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """
    Perform bulk validation of knowledge items
    
    Validates multiple items based on filters and criteria.
    Returns validation job ID for tracking progress.
    """
    try:
        logger.info("Starting bulk validation",
                   source_filters=request.source_filters,
                   max_items=request.max_items)
        
        # Generate job ID for tracking
        job_id = str(uuid4())
        
        # Query items for validation
        db_manager = validation_service.db_manager
        async with db_manager.get_postgres_pool().acquire() as conn:
            # Build query based on filters
            query = """
                SELECT id, title, content, knowledge_type, source_type, source_url,
                       tags, summary, confidence, metadata, created_at, updated_at
                FROM knowledge_items 
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if request.source_filters:
                param_count += 1
                query += f" AND source_type = ANY(${param_count})"
                params.append(request.source_filters)
            
            if request.quality_threshold > 0:
                param_count += 1
                query += f" AND quality_score >= ${param_count}"
                params.append(request.quality_threshold)
            
            param_count += 1
            query += f" ORDER BY created_at DESC LIMIT ${param_count}"
            params.append(request.max_items)
            
            items_data = await conn.fetch(query, *params)
        
        if not items_data:
            return {
                "job_id": job_id,
                "status": "completed",
                "message": "No items found matching criteria",
                "items_to_validate": 0,
                "started_at": datetime.utcnow().isoformat()
            }
        
        # Convert to KnowledgeItem objects
        items = []
        for item_data in items_data:
            item = KnowledgeItem(
                id=item_data['id'],
                title=item_data['title'],
                content=item_data['content'],
                knowledge_type=item_data['knowledge_type'],
                source_type=item_data['source_type'],
                source_url=item_data['source_url'] or '',
                tags=item_data['tags'] or [],
                summary=item_data['summary'] or '',
                confidence=item_data['confidence'] or 'medium',
                metadata=item_data['metadata'] or {},
                created_at=item_data['created_at'],
                updated_at=item_data['updated_at']
            )
            items.append(item)
        
        # Start bulk validation in background
        background_tasks.add_task(
            _perform_bulk_validation,
            validation_service,
            items,
            job_id,
            request.validation_options
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": "Bulk validation started",
            "items_to_validate": len(items),
            "started_at": datetime.utcnow().isoformat(),
            "estimated_completion": (datetime.utcnow() + timedelta(seconds=len(items) * 0.5)).isoformat()
        }
        
    except Exception as e:
        logger.error("Bulk validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def _perform_bulk_validation(
    validation_service: SourceValidationService,
    items: List[KnowledgeItem],
    job_id: str,
    validation_options: Dict[str, Any]
):
    """Background task to perform bulk validation"""
    try:
        logger.info("Starting bulk validation task",
                   job_id=job_id,
                   item_count=len(items))
        
        successful_validations = 0
        failed_validations = 0
        
        for item in items:
            try:
                result = await validation_service.validate_knowledge_item(item)
                if result.status == ValidationStatus.VALIDATED:
                    successful_validations += 1
                else:
                    failed_validations += 1
                    
            except Exception as e:
                logger.error("Item validation failed in bulk job",
                           job_id=job_id,
                           item_id=str(item.id),
                           error=str(e))
                failed_validations += 1
        
        logger.info("Bulk validation completed",
                   job_id=job_id,
                   successful=successful_validations,
                   failed=failed_validations)
        
    except Exception as e:
        logger.error("Bulk validation task failed", job_id=job_id, error=str(e))

@router.get("/statistics", response_model=ValidationStatsResponse)
async def get_validation_statistics(
    time_range: str = Query(default="24h", regex="^(1h|6h|24h|7d|30d)$", description="Time range for statistics"),
    source_filter: Optional[str] = Query(default=None, description="Filter statistics by source"),
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """Get comprehensive validation statistics"""
    try:
        logger.info("Getting validation statistics", time_range=time_range, source_filter=source_filter)
        
        stats = await validation_service.get_validation_statistics()
        
        # Format response
        return ValidationStatsResponse(
            total_validations=stats['overall']['total_validations'],
            success_rate=stats['overall']['success_rate'],
            average_score=stats['overall']['average_score'],
            average_validation_time=stats['overall']['average_validation_time'],
            quarantined_items=stats['overall']['quarantined_items'],
            failed_validations=stats['overall']['failed_validations'],
            error_rate=stats['overall']['error_rate'],
            performance_metrics=stats['performance'],
            source_breakdown=stats['by_source']
        )
        
    except Exception as e:
        logger.error("Failed to get validation statistics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credibility/{source_name}", response_model=SourceCredibilityResponse)
async def get_source_credibility(
    source_name: str = Path(..., description="Source name to get credibility for"),
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """Get credibility assessment for a specific source"""
    try:
        # Get source credibility from service
        source_cred = await validation_service._get_source_credibility(source_name)
        
        return SourceCredibilityResponse(
            source_name=source_cred.source_name,
            base_credibility=source_cred.base_credibility,
            historical_accuracy=source_cred.historical_accuracy,
            community_validation=source_cred.community_validation,
            reputation_score=source_cred.reputation_score,
            total_validations=source_cred.validation_count,
            successful_validations=source_cred.successful_validations,
            last_validation=source_cred.last_updated
        )
        
    except Exception as e:
        logger.error("Failed to get source credibility", source=source_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credibility", response_model=List[SourceCredibilityResponse])
async def get_all_source_credibility(
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """Get credibility assessment for all sources"""
    try:
        db_manager = validation_service.db_manager
        
        async with db_manager.get_postgres_pool().acquire() as conn:
            sources_data = await conn.fetch("""
                SELECT source_name, base_credibility, historical_accuracy,
                       community_validation, reputation_score, total_validations,
                       successful_validations, last_validation
                FROM source_credibility
                ORDER BY reputation_score DESC
            """)
        
        return [
            SourceCredibilityResponse(
                source_name=row['source_name'],
                base_credibility=float(row['base_credibility']),
                historical_accuracy=float(row['historical_accuracy']),
                community_validation=float(row['community_validation']),
                reputation_score=float(row['reputation_score']),
                total_validations=row['total_validations'],
                successful_validations=row['successful_validations'],
                last_validation=row['last_validation']
            )
            for row in sources_data
        ]
        
    except Exception as e:
        logger.error("Failed to get all source credibility", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=List[SecurityAlertResponse])
async def get_security_alerts(
    status: Optional[str] = Query(default=None, description="Filter by alert status"),
    alert_level: Optional[str] = Query(default=None, description="Filter by alert level"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum alerts to return"),
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """Get security and validation alerts"""
    try:
        db_manager = validation_service.db_manager
        
        async with db_manager.get_postgres_pool().acquire() as conn:
            # Build query
            query = """
                SELECT id, alert_type, alert_level, alert_title, alert_message,
                       source_name, item_id, status, created_at, metrics
                FROM validation_alerts
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if status:
                param_count += 1
                query += f" AND status = ${param_count}"
                params.append(status)
            
            if alert_level:
                param_count += 1
                query += f" AND alert_level = ${param_count}"
                params.append(alert_level)
            
            param_count += 1
            query += f" ORDER BY created_at DESC LIMIT ${param_count}"
            params.append(limit)
            
            alerts_data = await conn.fetch(query, *params)
        
        return [
            SecurityAlertResponse(
                alert_id=str(row['id']),
                alert_type=row['alert_type'],
                alert_level=row['alert_level'],
                alert_title=row['alert_title'],
                alert_message=row['alert_message'],
                source_name=row['source_name'],
                item_id=str(row['item_id']) if row['item_id'] else None,
                status=row['status'],
                created_at=row['created_at'],
                metrics=row['metrics'] or {}
            )
            for row in alerts_data
        ]
        
    except Exception as e:
        logger.error("Failed to get security alerts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID = Path(..., description="Alert ID to acknowledge"),
    acknowledgment: Dict[str, str] = None,
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """Acknowledge a security alert"""
    try:
        db_manager = validation_service.db_manager
        
        async with db_manager.get_postgres_pool().acquire() as conn:
            result = await conn.execute("""
                UPDATE validation_alerts 
                SET status = 'acknowledged',
                    acknowledged_by = $2,
                    acknowledged_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
            """, alert_id, acknowledgment.get('acknowledged_by', 'system') if acknowledgment else 'system')
        
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "alert_id": str(alert_id),
            "status": "acknowledged",
            "acknowledged_at": datetime.utcnow().isoformat(),
            "acknowledged_by": acknowledgment.get('acknowledged_by', 'system') if acknowledgment else 'system'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to acknowledge alert", alert_id=str(alert_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """Health check for the validation system"""
    try:
        # Get basic statistics to test system health
        stats = await validation_service.get_validation_statistics()
        
        # Check if system meets performance requirements
        avg_validation_time = stats['overall']['average_validation_time']
        success_rate = stats['overall']['success_rate']
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "performance": {
                "average_validation_time": avg_validation_time,
                "meets_latency_requirement": avg_validation_time < 0.5,  # <500ms
                "success_rate": success_rate,
                "meets_accuracy_requirement": success_rate >= 0.995,  # 99.5%
                "total_validations": stats['overall']['total_validations']
            },
            "components": {
                "ml_validator": "operational",
                "security_scanner": "operational",
                "credibility_assessor": "operational",
                "database": "operational"
            }
        }
        
        # Determine overall health
        if (avg_validation_time >= 0.5 or success_rate < 0.995 or 
            stats['overall']['error_rate'] > 0.01):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/compliance/audit-log")
async def get_audit_log(
    start_date: Optional[datetime] = Query(default=None, description="Start date for audit log"),
    end_date: Optional[datetime] = Query(default=None, description="End date for audit log"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    limit: int = Query(default=1000, ge=1, le=10000, description="Maximum log entries"),
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """Get audit log for compliance reporting (GDPR/SOC2)"""
    try:
        db_manager = validation_service.db_manager
        
        # Set default time range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        async with db_manager.get_postgres_pool().acquire() as conn:
            # Build audit query
            query = """
                SELECT event_type, validation_id, item_id, source_name,
                       event_data, user_id, ip_address, event_timestamp,
                       correlation_id, gdpr_applicable
                FROM validation_audit_log
                WHERE event_timestamp BETWEEN $1 AND $2
            """
            params = [start_date, end_date]
            param_count = 2
            
            if event_type:
                param_count += 1
                query += f" AND event_type = ${param_count}"
                params.append(event_type)
            
            param_count += 1
            query += f" ORDER BY event_timestamp DESC LIMIT ${param_count}"
            params.append(limit)
            
            audit_entries = await conn.fetch(query, *params)
        
        return {
            "audit_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_entries": len(audit_entries),
            "entries": [
                {
                    "event_type": row['event_type'],
                    "validation_id": row['validation_id'],
                    "item_id": str(row['item_id']) if row['item_id'] else None,
                    "source_name": row['source_name'],
                    "event_data": row['event_data'] or {},
                    "user_id": row['user_id'],
                    "ip_address": str(row['ip_address']) if row['ip_address'] else None,
                    "event_timestamp": row['event_timestamp'].isoformat(),
                    "correlation_id": row['correlation_id'],
                    "gdpr_applicable": row['gdpr_applicable']
                }
                for row in audit_entries
            ],
            "compliance_summary": {
                "gdpr_events": len([r for r in audit_entries if r['gdpr_applicable']]),
                "unique_users": len(set(r['user_id'] for r in audit_entries if r['user_id'])),
                "event_types": list(set(r['event_type'] for r in audit_entries))
            }
        }
        
    except Exception as e:
        logger.error("Failed to get audit log", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Stream endpoint for real-time validation monitoring
@router.get("/stream/validation-events")
async def stream_validation_events(
    sources: Optional[List[str]] = Query(default=None),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
    validation_service: SourceValidationService = Depends(get_validation_service_dep)
):
    """Stream real-time validation events"""
    async def event_generator():
        """Generator for streaming validation events"""
        try:
            db_manager = validation_service.db_manager
            last_check_time = datetime.utcnow()
            
            while True:
                # Query for recent validation results
                async with db_manager.get_postgres_pool().acquire() as conn:
                    query = """
                        SELECT validation_id, item_id, source_name, status,
                               overall_score, validation_time, timestamp
                        FROM source_validations
                        WHERE timestamp > $1
                    """
                    params = [last_check_time]
                    
                    if sources:
                        query += " AND source_name = ANY($2)"
                        params.append(sources)
                    
                    if min_score > 0:
                        param_idx = len(params) + 1
                        query += f" AND overall_score >= ${param_idx}"
                        params.append(min_score)
                    
                    query += " ORDER BY timestamp ASC"
                    
                    recent_validations = await conn.fetch(query, *params)
                
                # Stream new validation events
                for validation in recent_validations:
                    event_data = {
                        "event_type": "validation_completed",
                        "validation_id": validation['validation_id'],
                        "item_id": str(validation['item_id']),
                        "source_name": validation['source_name'],
                        "status": validation['status'],
                        "overall_score": float(validation['overall_score']),
                        "validation_time": float(validation['validation_time']),
                        "timestamp": validation['timestamp'].isoformat()
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                
                last_check_time = datetime.utcnow()
                await asyncio.sleep(2)  # Check every 2 seconds
                
        except Exception as e:
            error_event = {
                "event_type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )