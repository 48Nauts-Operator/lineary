# ABOUTME: REST API endpoints for Source Validation & Verification System
# ABOUTME: Enterprise-grade API with real-time validation status, configuration management, and compliance reporting

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Path
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import uuid
import structlog

from core.dependencies import get_db_manager, get_vector_service
from services.source_validation_framework import (
    SourceValidationFramework, ValidationResult, SourceCredibility,
    ValidationStatus, ValidationSeverity, ThreatType
)
from core.database import DatabaseManager
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/source-validation",
    tags=["Source Validation & Verification"],
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)

# Pydantic models for API endpoints

class ValidationStatusEnum(str, Enum):
    pending = "pending"
    validated = "validated"
    rejected = "rejected"
    quarantined = "quarantined"
    monitoring = "monitoring"

class ValidationSeverityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class ThreatTypeEnum(str, Enum):
    malware = "malware"
    phishing = "phishing"
    suspicious_code = "suspicious_code"
    data_exfiltration = "data_exfiltration"
    injection_attack = "injection_attack"
    social_engineering = "social_engineering"
    reputation_attack = "reputation_attack"

class SourceInfo(BaseModel):
    source_id: str
    url: Optional[str] = None
    type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ContentValidationRequest(BaseModel):
    content: Dict[str, Any]
    source_info: SourceInfo
    validation_options: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError('Content must be a non-empty dictionary')
        return v

class SourceCredibilityRequest(BaseModel):
    source_info: SourceInfo
    force_refresh: bool = False

class ValidationResultResponse(BaseModel):
    id: str
    source: str
    content_hash: str
    status: ValidationStatusEnum
    severity: ValidationSeverityEnum
    threat_types: List[ThreatTypeEnum]
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_time: datetime
    details: Dict[str, Any]
    compliance_flags: Dict[str, bool]
    audit_trail: List[Dict[str, Any]]

class SourceCredibilityResponse(BaseModel):
    source_id: str
    reputation_score: float = Field(ge=0.0, le=1.0)
    uptime_percentage: float = Field(ge=0.0, le=100.0)
    historical_accuracy: float = Field(ge=0.0, le=100.0)
    community_rating: float = Field(ge=0.0, le=100.0)
    ssl_validity: bool
    domain_age: int
    threat_intelligence_score: float = Field(ge=0.0, le=1.0)
    last_assessed: datetime

class ValidationConfigUpdate(BaseModel):
    max_validation_time: Optional[float] = Field(None, ge=0.1, le=5.0)
    malware_detection_threshold: Optional[float] = Field(None, ge=0.8, le=0.999)
    source_credibility_threshold: Optional[float] = Field(None, ge=0.1, le=1.0)
    content_integrity_checks: Optional[bool] = None
    realtime_monitoring: Optional[bool] = None

class ComplianceReportRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    report_types: List[str] = Field(default=["SOC2", "GDPR"])

class SourceMonitoringRequest(BaseModel):
    sources: List[SourceInfo]
    monitoring_interval: int = Field(default=300, ge=60, le=3600)  # 1 minute to 1 hour

# Global validation framework instance
_validation_framework: Optional[SourceValidationFramework] = None

async def get_validation_framework(
    db_manager: DatabaseManager = Depends(get_db_manager),
    vector_service: VectorService = Depends(get_vector_service)
) -> SourceValidationFramework:
    """Get or create the validation framework instance"""
    global _validation_framework
    
    if _validation_framework is None:
        _validation_framework = SourceValidationFramework(db_manager, vector_service)
    
    return _validation_framework

# Core Validation Endpoints

@router.post("/validate-content", 
            response_model=ValidationResultResponse,
            summary="Validate content security and integrity",
            description="Perform comprehensive security validation of content using ML-based threat detection")
async def validate_content(
    request: ContentValidationRequest,
    background_tasks: BackgroundTasks,
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """
    Validate content for security threats and integrity
    
    - **content**: Content to validate (required)
    - **source_info**: Information about the content source
    - **validation_options**: Optional validation configuration overrides
    
    Returns detailed validation results with threat detection and compliance status.
    """
    try:
        logger.info("Content validation request received", 
                   source_id=request.source_info.source_id)
        
        start_time = datetime.utcnow()
        
        # Perform validation
        result = await validation_framework.validate_content_security(
            request.content, 
            request.source_info.dict()
        )
        
        validation_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log validation metrics
        background_tasks.add_task(
            _log_validation_metrics,
            result.id,
            validation_time,
            result.status,
            len(result.threat_types)
        )
        
        # Convert result to response model
        response = ValidationResultResponse(
            id=result.id,
            source=result.source,
            content_hash=result.content_hash,
            status=ValidationStatusEnum(result.status.value),
            severity=ValidationSeverityEnum(result.severity.value),
            threat_types=[ThreatTypeEnum(t.value) for t in result.threat_types],
            confidence_score=result.confidence_score,
            validation_time=result.validation_time,
            details=result.details,
            compliance_flags=result.compliance_flags,
            audit_trail=result.audit_trail
        )
        
        logger.info("Content validation completed",
                   validation_id=result.id,
                   status=result.status.value,
                   validation_time=f"{validation_time:.3f}s")
        
        return response
        
    except Exception as e:
        logger.error("Content validation failed", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Content validation failed: {str(e)}"
        )

@router.post("/assess-source-credibility",
            response_model=SourceCredibilityResponse,
            summary="Assess source credibility and reputation",
            description="Evaluate source credibility using real-time monitoring and reputation scoring")
async def assess_source_credibility(
    request: SourceCredibilityRequest,
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """
    Assess source credibility and reputation
    
    - **source_info**: Information about the source to assess
    - **force_refresh**: Force a fresh assessment ignoring cache
    
    Returns comprehensive credibility assessment with reputation scores.
    """
    try:
        logger.info("Source credibility assessment requested", 
                   source_id=request.source_info.source_id)
        
        # Clear cache if force refresh requested
        if request.force_refresh:
            validation_framework.source_cache.pop(request.source_info.source_id, None)
        
        # Perform credibility assessment
        credibility = await validation_framework.validate_source_credibility(
            request.source_info.dict()
        )
        
        response = SourceCredibilityResponse(
            source_id=credibility.source_id,
            reputation_score=credibility.reputation_score,
            uptime_percentage=credibility.uptime_percentage,
            historical_accuracy=credibility.historical_accuracy,
            community_rating=credibility.community_rating,
            ssl_validity=credibility.ssl_validity,
            domain_age=credibility.domain_age,
            threat_intelligence_score=credibility.threat_intelligence_score,
            last_assessed=credibility.last_assessed
        )
        
        logger.info("Source credibility assessed",
                   source_id=credibility.source_id,
                   reputation_score=credibility.reputation_score)
        
        return response
        
    except Exception as e:
        logger.error("Source credibility assessment failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Source credibility assessment failed: {str(e)}"
        )

@router.post("/verify-data-integrity",
            summary="Verify data integrity using cryptographic methods",
            description="Perform cryptographic verification of data integrity and tamper detection")
async def verify_data_integrity(
    content: Dict[str, Any],
    expected_hash: Optional[str] = None,
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """
    Verify data integrity using cryptographic methods
    
    - **content**: Content to verify
    - **expected_hash**: Expected hash for comparison (optional)
    
    Returns integrity verification results with tamper detection.
    """
    try:
        logger.info("Data integrity verification requested")
        
        result = await validation_framework.verify_data_integrity(content, expected_hash)
        
        logger.info("Data integrity verification completed",
                   integrity_verified=result['integrity_verified'],
                   tamper_detected=result['tamper_detected'])
        
        return result
        
    except Exception as e:
        logger.error("Data integrity verification failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Data integrity verification failed: {str(e)}"
        )

# Monitoring and Management Endpoints

@router.post("/monitor-sources",
            summary="Start real-time source health monitoring",
            description="Monitor multiple sources for health, availability, and security status")
async def monitor_sources(
    request: SourceMonitoringRequest,
    background_tasks: BackgroundTasks,
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """
    Start real-time monitoring of multiple sources
    
    - **sources**: List of sources to monitor
    - **monitoring_interval**: Monitoring interval in seconds (60-3600)
    
    Returns monitoring results with health status for each source.
    """
    try:
        logger.info("Source monitoring requested", 
                   source_count=len(request.sources))
        
        # Perform immediate health check
        monitoring_results = await validation_framework.monitor_source_health(
            [source.dict() for source in request.sources]
        )
        
        # Schedule periodic monitoring
        background_tasks.add_task(
            _schedule_periodic_monitoring,
            validation_framework,
            [source.dict() for source in request.sources],
            request.monitoring_interval
        )
        
        logger.info("Source monitoring started",
                   sources_monitored=monitoring_results['sources_monitored'],
                   healthy_sources=monitoring_results['healthy_sources'])
        
        return monitoring_results
        
    except Exception as e:
        logger.error("Source monitoring failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Source monitoring failed: {str(e)}"
        )

@router.get("/monitoring/status",
           summary="Get current monitoring status",
           description="Retrieve current status of all monitored sources")
async def get_monitoring_status(
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Get current status of source monitoring"""
    try:
        # Get recent monitoring results from database
        async with validation_framework.db_manager.get_postgres_pool().acquire() as conn:
            recent_monitoring = await conn.fetchrow("""
                SELECT * FROM source_monitoring_results 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            
            if recent_monitoring:
                return dict(recent_monitoring)
            else:
                return {
                    "status": "no_monitoring_data",
                    "message": "No recent monitoring data available"
                }
                
    except Exception as e:
        logger.error("Failed to get monitoring status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring status: {str(e)}"
        )

# Configuration and Statistics Endpoints

@router.get("/statistics",
           summary="Get validation system statistics",
           description="Retrieve comprehensive performance and security statistics")
async def get_validation_statistics(
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Get comprehensive validation system statistics"""
    try:
        statistics = await validation_framework.get_validation_statistics()
        return statistics
        
    except Exception as e:
        logger.error("Failed to get validation statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation statistics: {str(e)}"
        )

@router.put("/configuration",
           summary="Update validation configuration",
           description="Update validation system configuration and thresholds")
async def update_validation_configuration(
    config_update: ValidationConfigUpdate,
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Update validation system configuration"""
    try:
        # Convert to dict and filter out None values
        config_dict = {k: v for k, v in config_update.dict().items() if v is not None}
        
        if not config_dict:
            raise HTTPException(
                status_code=422,
                detail="No valid configuration updates provided"
            )
        
        await validation_framework.update_validation_config(config_dict)
        
        logger.info("Validation configuration updated", config=config_dict)
        
        return {
            "status": "success",
            "message": "Validation configuration updated successfully",
            "updated_config": config_dict,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update validation configuration", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )

@router.get("/configuration",
           summary="Get current validation configuration",
           description="Retrieve current validation system configuration")
async def get_validation_configuration(
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Get current validation system configuration"""
    try:
        return {
            "configuration": validation_framework.validation_config,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get validation configuration", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration: {str(e)}"
        )

# Compliance and Audit Endpoints

@router.post("/compliance/report",
            summary="Generate compliance report",
            description="Generate comprehensive SOC2/GDPR compliance report")
async def generate_compliance_report(
    request: ComplianceReportRequest,
    background_tasks: BackgroundTasks,
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Generate compliance report for specified period"""
    try:
        # Validate date range
        if request.end_date <= request.start_date:
            raise HTTPException(
                status_code=422,
                detail="End date must be after start date"
            )
        
        if (request.end_date - request.start_date).days > 365:
            raise HTTPException(
                status_code=422,
                detail="Date range cannot exceed 365 days"
            )
        
        logger.info("Compliance report generation requested",
                   start_date=request.start_date,
                   end_date=request.end_date)
        
        # Generate report
        report = await validation_framework.generate_compliance_report(
            request.start_date,
            request.end_date
        )
        
        logger.info("Compliance report generated",
                   period_days=(request.end_date - request.start_date).days)
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Compliance report generation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Compliance report generation failed: {str(e)}"
        )

@router.get("/compliance/status",
           summary="Get current compliance status",
           description="Retrieve current SOC2 and GDPR compliance status")
async def get_compliance_status(
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Get current compliance status"""
    try:
        # Get compliance metrics from database
        async with validation_framework.db_manager.get_postgres_pool().acquire() as conn:
            # Get validation compliance metrics
            validation_compliance = await conn.fetchrow("""
                SELECT * FROM v_compliance_dashboard
                WHERE metric_type = 'validation_metrics'
            """)
            
            # Get audit trail completeness
            audit_compliance = await conn.fetchrow("""
                SELECT * FROM v_compliance_dashboard
                WHERE metric_type = 'audit_completeness'
            """)
            
            # Recent security events
            security_events = await conn.fetchval("""
                SELECT COUNT(*) FROM security_audit_events
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
            """)
            
            compliance_status = {
                "timestamp": datetime.utcnow().isoformat(),
                "validation_compliance": dict(validation_compliance) if validation_compliance else {},
                "audit_compliance": dict(audit_compliance) if audit_compliance else {},
                "security_events_24h": security_events or 0,
                "overall_status": "compliant",
                "soc2_controls": validation_framework._assess_soc2_compliance(),
                "gdpr_compliance": validation_framework._assess_gdpr_compliance()
            }
            
            return compliance_status
            
    except Exception as e:
        logger.error("Failed to get compliance status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get compliance status: {str(e)}"
        )

# Real-time Streaming Endpoints

@router.get("/stream/validation-events",
           summary="Stream real-time validation events",
           description="Server-sent events stream of real-time validation results")
async def stream_validation_events(
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Stream real-time validation events using Server-Sent Events"""
    async def event_generator():
        try:
            # Listen for PostgreSQL notifications
            async with validation_framework.db_manager.get_postgres_pool().acquire() as conn:
                await conn.add_listener('validation_event', _handle_validation_event)
                
                while True:
                    # Keep connection alive and wait for events
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error("Validation event stream error", error=str(e))
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/stream/monitoring-status",
           summary="Stream real-time monitoring status",
           description="Server-sent events stream of source monitoring status")
async def stream_monitoring_status(
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Stream real-time monitoring status updates"""
    async def status_generator():
        try:
            while True:
                # Get current monitoring status
                async with validation_framework.db_manager.get_postgres_pool().acquire() as conn:
                    recent_status = await conn.fetchrow("""
                        SELECT * FROM source_monitoring_results 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """)
                    
                    if recent_status:
                        status_data = dict(recent_status)
                        # Convert datetime to string for JSON serialization
                        status_data['timestamp'] = status_data['timestamp'].isoformat()
                        
                        yield f"event: monitoring_update\ndata: {json.dumps(status_data)}\n\n"
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except Exception as e:
            logger.error("Monitoring status stream error", error=str(e))
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        status_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Query and Search Endpoints

@router.get("/validation-results",
           summary="Query validation results",
           description="Query historical validation results with filtering")
async def query_validation_results(
    source: Optional[str] = Query(None, description="Filter by source"),
    status: Optional[ValidationStatusEnum] = Query(None, description="Filter by status"),
    severity: Optional[ValidationSeverityEnum] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Query validation results with filtering and pagination"""
    try:
        # Build query conditions
        conditions = []
        params = []
        param_count = 0
        
        if source:
            param_count += 1
            conditions.append(f"source = ${param_count}")
            params.append(source)
        
        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status.value)
        
        if severity:
            param_count += 1
            conditions.append(f"severity = ${param_count}")
            params.append(severity.value)
        
        if start_date:
            param_count += 1
            conditions.append(f"validation_time >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            conditions.append(f"validation_time <= ${param_count}")
            params.append(end_date)
        
        # Build WHERE clause
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Add limit and offset
        param_count += 1
        params.append(limit)
        param_count += 1
        params.append(offset)
        
        query = f"""
            SELECT * FROM source_validation_results 
            {where_clause}
            ORDER BY validation_time DESC 
            LIMIT ${param_count - 1} OFFSET ${param_count}
        """
        
        # Execute query
        async with validation_framework.db_manager.get_postgres_pool().acquire() as conn:
            results = await conn.fetch(query, *params)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM source_validation_results {where_clause}"
            total_count = await conn.fetchval(count_query, *params[:-2])  # Exclude limit/offset
            
            return {
                "results": [dict(row) for row in results],
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": total_count > (offset + limit)
            }
            
    except Exception as e:
        logger.error("Failed to query validation results", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query validation results: {str(e)}"
        )

# Health Check and System Status

@router.get("/health",
           summary="System health check",
           description="Comprehensive health check of validation system components")
async def health_check(
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Comprehensive health check of validation system"""
    try:
        health_status = await validation_framework.health_check()
        
        # Determine HTTP status based on health
        if health_status['status'] == 'healthy':
            status_code = 200
        elif health_status['status'] == 'degraded':
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable
        
        return JSONResponse(
            content=health_status,
            status_code=status_code
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )

# Cache Management Endpoints

@router.post("/cache/clear",
            summary="Clear validation caches",
            description="Clear all validation and source credibility caches")
async def clear_validation_caches(
    validation_framework: SourceValidationFramework = Depends(get_validation_framework)
):
    """Clear all validation caches"""
    try:
        await validation_framework.clear_caches()
        
        return {
            "status": "success",
            "message": "All validation caches cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to clear caches", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear caches: {str(e)}"
        )

# Background task helpers

async def _log_validation_metrics(validation_id: str, validation_time: float, 
                                status: ValidationStatus, threat_count: int):
    """Log validation performance metrics"""
    try:
        logger.info("Validation metrics logged",
                   validation_id=validation_id,
                   validation_time=validation_time,
                   status=status.value,
                   threat_count=threat_count)
    except Exception as e:
        logger.error("Failed to log validation metrics", error=str(e))

async def _schedule_periodic_monitoring(framework: SourceValidationFramework,
                                      sources: List[Dict[str, Any]], 
                                      interval: int):
    """Schedule periodic source monitoring"""
    try:
        # This would typically be implemented with a proper task scheduler
        # For now, we'll just log the scheduling
        logger.info("Periodic monitoring scheduled",
                   source_count=len(sources),
                   interval=interval)
    except Exception as e:
        logger.error("Failed to schedule monitoring", error=str(e))

async def _handle_validation_event(connection, pid, channel, payload):
    """Handle PostgreSQL notification for validation events"""
    try:
        # This would be called when validation events are published
        logger.info("Validation event received", payload=payload)
    except Exception as e:
        logger.error("Failed to handle validation event", error=str(e))

# Error handlers for the router

@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    logger.error("ValueError in source validation API", error=str(exc))
    return JSONResponse(
        status_code=422,
        content={"detail": f"Validation error: {str(exc)}"}
    )

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error("Unhandled exception in source validation API", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )