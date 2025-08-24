# ABOUTME: Enhanced error handling API endpoints for Betty Memory System
# ABOUTME: Provides REST interface for error monitoring, analysis, and management

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

from core.dependencies import get_databases, DatabaseDependencies
from core.security import get_current_user
from core.error_classification import (
    get_error_classification_engine, ErrorClassificationEngine,
    ErrorSeverity, ErrorCategory, ErrorSubcategory
)
from services.error_monitoring_service import (
    get_monitoring_service, ErrorMonitoringService,
    AlertSeverity, SystemHealthMetrics
)

logger = structlog.get_logger(__name__)

# Create router for enhanced error handling endpoints
router = APIRouter(prefix="/api/v2/error-handling", tags=["Enhanced Error Handling"])

# Request/Response models

class ErrorReportRequest(BaseModel):
    """Request model for reporting errors"""
    error_type: str = Field(..., description="Type of error that occurred")
    error_message: str = Field(..., description="Error message")
    component: str = Field(..., description="Component where error occurred")
    endpoint: Optional[str] = Field(None, description="API endpoint if applicable")
    user_id: Optional[str] = Field(None, description="User ID if known")
    session_id: Optional[str] = Field(None, description="Session ID if applicable")
    project_id: Optional[str] = Field(None, description="Project ID if applicable")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class ErrorClassificationResponse(BaseModel):
    """Response model for error classification"""
    error_id: str
    category: str
    subcategory: Optional[str]
    severity: str
    confidence_score: float
    auto_recoverable: bool
    estimated_impact: str
    classification_time_ms: float
    classification_reasons: List[str]
    similar_errors: List[str]

class RemediationPlanResponse(BaseModel):
    """Response model for remediation plans"""
    plan_id: str
    error_classification: ErrorClassificationResponse
    total_estimated_time_minutes: int
    success_probability: float
    manual_intervention_required: bool
    auto_executable: bool
    steps: List[Dict[str, Any]]

class RecoveryResultResponse(BaseModel):
    """Response model for recovery attempts"""
    recovery_id: str
    error_id: str
    success: bool
    steps_executed: List[str]
    steps_failed: List[str]
    final_status: str
    error_resolution_time_minutes: float
    manual_intervention_needed: bool
    recovery_notes: List[str]

class SystemHealthResponse(BaseModel):
    """Response model for system health"""
    timestamp: str
    overall_health_score: float
    error_rate_per_minute: float
    avg_response_time_ms: float
    memory_usage_percent: float
    cpu_usage_percent: float
    database_health: Dict[str, str]
    active_incidents: int
    services_degraded: List[str]
    services_down: List[str]

class AlertResponse(BaseModel):
    """Response model for alerts"""
    alert_id: str
    severity: str
    title: str
    description: str
    component: str
    created_at: str
    affected_users: int
    estimated_downtime_minutes: Optional[int]
    recovery_eta: Optional[str]
    recommended_actions: List[str]
    tags: List[str]

class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis"""
    trends: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    recommendations: List[str]
    analysis_window_hours: int
    total_errors_analyzed: int

# API Endpoints

@router.post("/errors/report", response_model=ErrorClassificationResponse)
async def report_error(
    request: ErrorReportRequest,
    current_user: dict = Depends(get_current_user),
    error_engine: ErrorClassificationEngine = Depends(get_error_classification_engine),
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Report an error for classification and monitoring.
    
    This endpoint allows manual reporting of errors that may not be caught
    by the automatic error handling middleware.
    """
    try:
        logger.info("Manual error report received",
                   error_type=request.error_type,
                   component=request.component,
                   user_id=current_user.get('user_id'))
        
        # Create a mock Exception for classification
        class ReportedException(Exception):
            def __init__(self, message: str, error_type: str):
                self.message = message
                self.error_type = error_type
                super().__init__(message)
        
        error = ReportedException(request.error_message, request.error_type)
        
        # Create error context from request
        from core.error_classification import ErrorContext
        error_context = ErrorContext(
            timestamp=datetime.now(timezone.utc),
            user_id=request.user_id or current_user.get('user_id'),
            session_id=request.session_id,
            project_id=request.project_id,
            endpoint=request.endpoint,
            method="POST",  # Since this is a manual report
            request_id=f"manual-report-{datetime.now().isoformat()}",
            extra_fields=request.context_data
        )
        
        # Classify the error
        classification = await error_engine.classify_error(error, error_context)
        
        # Report to monitoring service
        await monitoring_service.report_error(classification, {
            "component": request.component,
            "manual_report": True,
            "reported_by": current_user.get('user_id')
        })
        
        # Convert to response model
        response = ErrorClassificationResponse(
            error_id=classification.error_id,
            category=classification.category.value,
            subcategory=classification.subcategory.value if classification.subcategory else None,
            severity=classification.severity.value,
            confidence_score=classification.confidence_score,
            auto_recoverable=classification.auto_recoverable,
            estimated_impact=classification.estimated_impact,
            classification_time_ms=classification.classification_time_ms,
            classification_reasons=classification.classification_reasons,
            similar_errors=classification.similar_errors
        )
        
        logger.info("Error classification completed",
                   error_id=classification.error_id,
                   category=classification.category.value,
                   severity=classification.severity.value)
        
        return response
        
    except Exception as e:
        logger.error("Error reporting failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error reporting failed: {str(e)}")

@router.get("/errors/{error_id}/remediation", response_model=RemediationPlanResponse)
async def get_remediation_plan(
    error_id: str,
    current_user: dict = Depends(get_current_user),
    error_engine: ErrorClassificationEngine = Depends(get_error_classification_engine)
):
    """
    Get remediation plan for a specific error.
    
    Returns a detailed plan with steps to resolve the error.
    """
    try:
        logger.info("Remediation plan requested", error_id=error_id)
        
        # Get error classification from engine
        if error_id not in error_engine.error_patterns:
            raise HTTPException(status_code=404, detail="Error not found")
        
        classification = error_engine.error_patterns[error_id]
        
        # Generate remediation strategy
        remediation_plan = await error_engine.get_remediation_strategy(classification)
        
        # Convert to response model
        response = RemediationPlanResponse(
            plan_id=remediation_plan.plan_id,
            error_classification=ErrorClassificationResponse(
                error_id=classification.error_id,
                category=classification.category.value,
                subcategory=classification.subcategory.value if classification.subcategory else None,
                severity=classification.severity.value,
                confidence_score=classification.confidence_score,
                auto_recoverable=classification.auto_recoverable,
                estimated_impact=classification.estimated_impact,
                classification_time_ms=classification.classification_time_ms,
                classification_reasons=classification.classification_reasons,
                similar_errors=classification.similar_errors
            ),
            total_estimated_time_minutes=remediation_plan.total_estimated_time_minutes,
            success_probability=remediation_plan.success_probability,
            manual_intervention_required=remediation_plan.manual_intervention_required,
            auto_executable=remediation_plan.auto_executable,
            steps=[
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "action_type": step.action_type,
                    "priority": step.priority,
                    "estimated_time_minutes": step.estimated_time_minutes,
                    "command": step.command,
                    "verification_query": step.verification_query,
                    "dependencies": step.dependencies
                }
                for step in remediation_plan.steps
            ]
        )
        
        logger.info("Remediation plan generated",
                   error_id=error_id,
                   plan_id=remediation_plan.plan_id,
                   steps_count=len(remediation_plan.steps))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Remediation plan generation failed", error_id=error_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Remediation plan generation failed: {str(e)}")

@router.post("/errors/{error_id}/recover", response_model=RecoveryResultResponse)
async def attempt_error_recovery(
    error_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    error_engine: ErrorClassificationEngine = Depends(get_error_classification_engine)
):
    """
    Attempt automated recovery for a specific error.
    
    Executes the automated recovery process for recoverable errors.
    """
    try:
        logger.info("Manual recovery attempt initiated", 
                   error_id=error_id, 
                   user_id=current_user.get('user_id'))
        
        # Attempt recovery
        recovery_result = await error_engine.execute_auto_recovery(error_id)
        
        # Convert to response model
        response = RecoveryResultResponse(
            recovery_id=recovery_result.recovery_id,
            error_id=recovery_result.error_id,
            success=recovery_result.success,
            steps_executed=recovery_result.steps_executed,
            steps_failed=recovery_result.steps_failed,
            final_status=recovery_result.final_status,
            error_resolution_time_minutes=recovery_result.error_resolution_time_minutes,
            manual_intervention_needed=recovery_result.manual_intervention_needed,
            recovery_notes=recovery_result.recovery_notes
        )
        
        logger.info("Recovery attempt completed",
                   error_id=error_id,
                   recovery_id=recovery_result.recovery_id,
                   success=recovery_result.success)
        
        return response
        
    except Exception as e:
        logger.error("Recovery attempt failed", error_id=error_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Recovery attempt failed: {str(e)}")

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Get current system health metrics.
    
    Provides real-time system health information including error rates,
    performance metrics, and service status.
    """
    try:
        health_metrics = monitoring_service.get_health_metrics()
        
        if not health_metrics:
            # Return default health metrics if none available
            health_metrics = SystemHealthMetrics(
                timestamp=datetime.now(timezone.utc),
                overall_health_score=100.0,
                error_rate_per_minute=0.0,
                avg_response_time_ms=0.0,
                memory_usage_percent=0.0,
                cpu_usage_percent=0.0,
                database_health={},
                active_incidents=0
            )
        
        response = SystemHealthResponse(
            timestamp=health_metrics.timestamp.isoformat(),
            overall_health_score=health_metrics.overall_health_score,
            error_rate_per_minute=health_metrics.error_rate_per_minute,
            avg_response_time_ms=health_metrics.avg_response_time_ms,
            memory_usage_percent=health_metrics.memory_usage_percent,
            cpu_usage_percent=health_metrics.cpu_usage_percent,
            database_health=health_metrics.database_health,
            active_incidents=health_metrics.active_incidents,
            services_degraded=health_metrics.services_degraded,
            services_down=health_metrics.services_down
        )
        
        return response
        
    except Exception as e:
        logger.error("Health metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health metrics retrieval failed: {str(e)}")

@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(
    severity: Optional[str] = Query(None, description="Filter by alert severity"),
    component: Optional[str] = Query(None, description="Filter by component"),
    limit: int = Query(50, le=200, description="Maximum number of alerts to return"),
    current_user: dict = Depends(get_current_user),
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Get active alerts with optional filtering.
    
    Returns a list of currently active alerts in the system.
    """
    try:
        active_alerts = monitoring_service.get_active_alerts()
        
        # Apply filters
        if severity:
            active_alerts = [alert for alert in active_alerts if alert.severity.value == severity.lower()]
        
        if component:
            active_alerts = [alert for alert in active_alerts if alert.component == component]
        
        # Limit results
        active_alerts = active_alerts[:limit]
        
        # Convert to response models
        response = [
            AlertResponse(
                alert_id=alert.alert_id,
                severity=alert.severity.value,
                title=alert.title,
                description=alert.description,
                component=alert.component,
                created_at=alert.created_at.isoformat(),
                affected_users=alert.affected_users,
                estimated_downtime_minutes=alert.estimated_downtime_minutes,
                recovery_eta=alert.recovery_eta.isoformat() if alert.recovery_eta else None,
                recommended_actions=alert.recommended_actions,
                tags=list(alert.tags)
            )
            for alert in active_alerts
        ]
        
        logger.info("Active alerts retrieved",
                   total_alerts=len(response),
                   severity_filter=severity,
                   component_filter=component)
        
        return response
        
    except Exception as e:
        logger.error("Alert retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Alert retrieval failed: {str(e)}")

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_notes: str = Query("", description="Notes about the resolution"),
    current_user: dict = Depends(get_current_user),
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Resolve an active alert.
    
    Marks an alert as resolved and removes it from active alerts.
    """
    try:
        success = await monitoring_service.alert_manager.resolve_alert(
            alert_id=alert_id,
            resolution_notes=f"Resolved by {current_user.get('user_id')}: {resolution_notes}"
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found or already resolved")
        
        logger.info("Alert resolved",
                   alert_id=alert_id,
                   resolved_by=current_user.get('user_id'))
        
        return {"message": "Alert resolved successfully", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Alert resolution failed", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Alert resolution failed: {str(e)}")

@router.get("/trends/analysis", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    hours: int = Query(24, ge=1, le=168, description="Analysis window in hours (max 1 week)"),
    current_user: dict = Depends(get_current_user),
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Get error trend analysis.
    
    Provides analysis of error patterns, trends, and recommendations
    for the specified time window.
    """
    try:
        # Update analysis window
        original_window = monitoring_service.trend_analyzer.analysis_window_hours
        monitoring_service.trend_analyzer.analysis_window_hours = hours
        
        # Get trend analysis
        trend_analysis = monitoring_service.get_trend_analysis()
        
        # Restore original window
        monitoring_service.trend_analyzer.analysis_window_hours = original_window
        
        response = TrendAnalysisResponse(
            trends=trend_analysis["trends"],
            patterns=[
                {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "first_occurrence": pattern.first_occurrence.isoformat(),
                    "last_occurrence": pattern.last_occurrence.isoformat(),
                    "occurrence_count": pattern.occurrence_count,
                    "affected_components": list(pattern.affected_components),
                    "error_rate_per_minute": pattern.error_rate_per_minute,
                    "severity_distribution": pattern.severity_distribution,
                    "user_impact_estimate": pattern.user_impact_estimate
                }
                for pattern in trend_analysis["patterns"]
            ],
            recommendations=trend_analysis["recommendations"],
            analysis_window_hours=hours,
            total_errors_analyzed=trend_analysis["total_errors_analyzed"]
        )
        
        logger.info("Trend analysis completed",
                   analysis_window_hours=hours,
                   trends_detected=len(response.trends),
                   patterns_found=len(response.patterns))
        
        return response
        
    except Exception as e:
        logger.error("Trend analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@router.get("/monitoring/status")
async def get_monitoring_status(
    current_user: dict = Depends(get_current_user),
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Get current monitoring service status.
    
    Provides information about the monitoring service configuration and status.
    """
    try:
        status = monitoring_service.get_service_status()
        
        logger.info("Monitoring status requested", user_id=current_user.get('user_id'))
        
        return {
            "message": "Monitoring service status retrieved successfully",
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Monitoring status retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Monitoring status retrieval failed: {str(e)}")

@router.post("/monitoring/start")
async def start_monitoring(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Start the error monitoring service.
    
    Initiates background monitoring tasks for error analysis and alerting.
    """
    try:
        # Start monitoring in background
        background_tasks.add_task(monitoring_service.start_monitoring)
        
        logger.info("Monitoring service start initiated", user_id=current_user.get('user_id'))
        
        return {
            "message": "Error monitoring service starting",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Monitoring service start failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring service: {str(e)}")

@router.post("/monitoring/stop")
async def stop_monitoring(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Stop the error monitoring service.
    
    Gracefully stops background monitoring tasks.
    """
    try:
        # Stop monitoring in background
        background_tasks.add_task(monitoring_service.stop_monitoring)
        
        logger.info("Monitoring service stop initiated", user_id=current_user.get('user_id'))
        
        return {
            "message": "Error monitoring service stopping",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Monitoring service stop failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring service: {str(e)}")

# Error statistics endpoints

@router.get("/statistics/overview")
async def get_error_statistics_overview(
    hours: int = Query(24, ge=1, le=168, description="Statistics window in hours"),
    current_user: dict = Depends(get_current_user),
    monitoring_service: ErrorMonitoringService = Depends(get_monitoring_service)
):
    """
    Get error statistics overview.
    
    Provides comprehensive error statistics for the specified time window.
    """
    try:
        # Get recent errors from trend analyzer
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours)
        
        recent_errors = [
            error for error in monitoring_service.trend_analyzer.error_history
            if error["timestamp"] > cutoff_time
        ]
        
        # Calculate statistics
        total_errors = len(recent_errors)
        
        # Group by category
        category_stats = {}
        severity_stats = {}
        component_stats = {}
        
        for error in recent_errors:
            classification = error["classification"]
            context = error["context"]
            
            # Category statistics
            category = classification.category.value
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
            
            # Severity statistics
            severity = classification.severity.value
            if severity not in severity_stats:
                severity_stats[severity] = 0
            severity_stats[severity] += 1
            
            # Component statistics
            component = context.get("component", "unknown")
            if component not in component_stats:
                component_stats[component] = 0
            component_stats[component] += 1
        
        # Calculate error rate
        error_rate = total_errors / hours if hours > 0 else 0
        
        # Get active alerts summary
        alerts_summary = monitoring_service.alert_manager.get_alert_summary()
        
        response = {
            "time_window_hours": hours,
            "total_errors": total_errors,
            "error_rate_per_hour": round(error_rate, 2),
            "category_breakdown": category_stats,
            "severity_breakdown": severity_stats,
            "component_breakdown": component_stats,
            "active_alerts": alerts_summary,
            "analysis_timestamp": now.isoformat()
        }
        
        logger.info("Error statistics overview generated",
                   hours=hours,
                   total_errors=total_errors,
                   user_id=current_user.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error("Error statistics generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error statistics generation failed: {str(e)}")

# Health check endpoint for the error handling system itself
@router.get("/ping")
async def error_handling_health_check():
    """Health check endpoint for the error handling system"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "betty-enhanced-error-handling",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
    )

# Export router
__all__ = ["router"]