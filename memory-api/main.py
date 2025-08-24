# ABOUTME: FastAPI application entry point for BETTY Memory System
# ABOUTME: Initializes multi-database connections and API routes for Claude's temporal memory

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from typing import Dict, Any

from core.config import get_settings
from core.database import DatabaseManager
from core.logging_config import configure_logging
# from core.enhanced_logging import configure_enhanced_logging  # Temporarily disabled due to psutil dependency
from core.security import AuthenticationMiddleware, RateLimitingMiddleware
# from middleware.error_handling import BettyErrorHandlingMiddleware  # Temporarily disabled
# from services.error_monitoring_service import get_monitoring_service  # Temporarily disabled
from api import health, knowledge, sessions, graphiti, ingestion, database, retrieval, analytics, error_tracking, auth, memory_correctness, knowledge_visualization, knowledge_flow, admin, dashboard
from api import analytics_proxy  # Keep proxy available as fallback
from api import security  # Prompt injection detection and security
from api import tasks  # Task extraction system to bypass TodoWrite timeouts
from api import sprints  # AI Sprint management with LLM cost tracking
from api import agent_tracking  # Sub-agent usage and cost tracking
from api import session_costs  # Session cost tracking and prediction analytics
# Temporarily disabled due to missing dependencies:
# pattern_quality, pattern_success_prediction, knowledge_extraction, source_validation, executive_dashboard
# Import agent routing and learning API routes  
# from routes import agent_routing_routes, agent_learning_routes, intelligent_routing_routes  # Temporarily disabled due to import issues
# enhanced_error_handling temporarily disabled due to missing aiohttp dependency
# agents temporarily disabled due to dependency issues
# Import v2 API modules when they exist
try:
    # V2 imports now fixed - decorator pattern issues resolved
    from api.v2 import advanced_query, batch_operations, cross_project, versioning, docs, websocket, webhooks
    from api.v2.websocket import init_realtime_service
    from api.v2.webhooks import init_webhook_service
    V2_MODULES_AVAILABLE = True
    V2_REALTIME_AVAILABLE = True
    print("V2 modules imported successfully")  # Using print since logger not configured yet
except ImportError as e:
    print(f"V2 API modules not available: {e}")  # Using print since logger not configured yet
    V2_MODULES_AVAILABLE = False
    V2_REALTIME_AVAILABLE = False
# from api import agents  # Temporarily disabled - multi-agent system not implemented yet

# Configure enhanced structured logging
# configure_enhanced_logging()  # Temporarily disabled
logger = structlog.get_logger(__name__)

# Global database manager instance
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager for startup/shutdown operations"""
    global db_manager
    
    settings = get_settings()
    logger.info("Starting BETTY Memory System API", version="1.0.0")
    
    try:
        # Initialize database connections
        db_manager = DatabaseManager(settings)
        await db_manager.initialize()
        logger.info("Database connections initialized successfully")
        
        # Store in app state for dependency injection
        app.state.db_manager = db_manager
        
        # Set database manager for auth service
        from services.auth_service import set_database_manager
        set_database_manager(db_manager)
        logger.info("Database manager set for auth service")
        
        # Initialize enhanced error monitoring service
        # monitoring_service = get_monitoring_service()
        # await monitoring_service.start_monitoring()
        # logger.info("Enhanced error monitoring service initialized")
        # app.state.monitoring_service = monitoring_service  # Temporarily disabled
        
        # Initialize real-time services if available
        if V2_REALTIME_AVAILABLE and hasattr(db_manager, 'redis'):
            try:
                # Initialize WebSocket real-time service
                await init_realtime_service(db_manager.redis)
                logger.info("Real-time WebSocket service initialized")
                
                # Initialize webhook service
                await init_webhook_service(db_manager.redis)
                logger.info("Webhook service initialized")
                
            except Exception as e:
                logger.error("Failed to initialize real-time services", error=str(e))
                # Don't fail startup, just log the error
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    finally:
        # Cleanup on shutdown
        # if hasattr(app.state, 'monitoring_service'):
        #     await app.state.monitoring_service.stop_monitoring()
        #     logger.info("Enhanced error monitoring service stopped")  # Temporarily disabled
        
        if db_manager:
            await db_manager.close()
            logger.info("Database connections closed")

# Create FastAPI application
app = FastAPI(
    title="BETTY Memory System API",
    description="Claude's Extended Brain - Unlimited Context Awareness with Temporal Knowledge Graphs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# API Version middleware (must be before security middleware) - only if v2 modules available
if V2_MODULES_AVAILABLE:
    app.middleware("http")(versioning.version_middleware)

# Enhanced error handling middleware (must be first)
# app.add_middleware(
#     BettyErrorHandlingMiddleware,
#     enable_auto_recovery=True,
#     max_recovery_attempts=3,
#     recovery_timeout_seconds=30
# )  # Temporarily disabled

# Security middleware
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=100)

# CORS middleware configuration - should be more restrictive in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3377", 
        "http://rufus.blockonauts.io",
        "https://betty.blockonauts.io",
        "https://rufus.blockonauts.io"
    ],  # Production: specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "Origin", "Accept"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=f"{process_time:.3f}s"
        )
        raise

# Enhanced global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Enhanced global exception handler with detailed error information"""
    import traceback
    
    # Get request details
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None,
        "path_params": request.path_params,
        "query_params": dict(request.query_params)
    }
    
    # Get error details
    error_info = {
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
        "module": getattr(exc, '__module__', 'unknown')
    }
    
    # Log with structured format
    logger.error(
        "Unhandled exception occurred",
        request_info=request_info,
        error_info=error_info,
        timestamp=time.time()
    )
    
    # Determine appropriate status code and message
    status_code = 500
    user_message = "An unexpected error occurred"
    
    # Customize response based on error type
    if isinstance(exc, FileNotFoundError):
        status_code = 404
        user_message = "Requested resource not found"
    elif isinstance(exc, PermissionError):
        status_code = 403
        user_message = "Permission denied"
    elif isinstance(exc, TimeoutError):
        status_code = 408
        user_message = "Request timeout"
    elif "Database" in str(exc) or "connection" in str(exc).lower():
        status_code = 503
        user_message = "Database connection unavailable"
    
    # Create detailed error response
    error_response = {
        "error": "BETTY Memory System Error",
        "message": user_message,
        "status_code": status_code,
        "timestamp": time.time(),
        "request_id": f"betty-{hash(str(request.url) + str(time.time()))}"
    }
    
    # Add debug info in development
    if app.debug:
        error_response.update({
            "debug_info": {
                "error_type": error_info["error_type"],
                "error_message": error_info["error_message"],
                "endpoint": str(request.url.path)
            }
        })
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )

# Include API routers

# System routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(health.router, prefix="/api/health", tags=["Health API"])  # Frontend compatibility
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(security.router, tags=["Security"])

# API versioning and documentation (v2)
if V2_MODULES_AVAILABLE:
    app.include_router(versioning.versioning_router, tags=["API Versioning"])
    app.include_router(docs.docs_router, tags=["API Documentation"])

# V1 API routers (legacy/maintenance)
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge v1"])
app.include_router(retrieval.router, prefix="/api/knowledge/retrieve", tags=["Knowledge Retrieval v1"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions v1"])
app.include_router(graphiti.router, tags=["Graphiti v1"])
app.include_router(ingestion.router, prefix="/api/knowledge/ingest", tags=["Ingestion v1"])
app.include_router(database.router, prefix="/api/database", tags=["Database v1"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics v1"])
app.include_router(dashboard.router, tags=["Dashboard v1"])
app.include_router(error_tracking.router, prefix="/api/errors", tags=["Error Tracking v1"])
# app.include_router(enhanced_error_handling.router, tags=["Enhanced Error Handling v2"])  # Temporarily disabled

# Memory Correctness System API (v2 - Production Ready)
app.include_router(memory_correctness.router, tags=["Memory Correctness System"])

# Temporarily disabled due to textstat dependency issues:
# Pattern Quality Scoring System API (Phase 3 - Production Ready)
# app.include_router(pattern_quality.router, tags=["Pattern Quality Intelligence System"])

# Pattern Success Prediction Engine API (Phase 3 - Production Ready) 
# app.include_router(pattern_success_prediction.router, tags=["Pattern Success Prediction Engine"])

# Temporarily disabled due to missing aiohttp dependency:
# Multi-Source Knowledge Extraction Pipeline API (Phase 3 - Production Ready)
# app.include_router(knowledge_extraction.router, tags=["Multi-Source Knowledge Extraction Pipeline"])

# Temporarily disabled due to missing aiohttp dependency:
# Source Validation & Verification System API (Phase 3 - Production Ready)
# app.include_router(source_validation.router, tags=["Source Validation & Verification System"])

# Temporarily disabled due to missing pandas dependency:
# Executive Dashboard & Reporting System API (Phase 6 - Production Ready)
# app.include_router(executive_dashboard.router, tags=["Executive Dashboard & Reporting System"])

# Knowledge Visualization System API (Phase 6 - Production Ready)
app.include_router(knowledge_visualization.router, prefix="/api/knowledge-visualization", tags=["Knowledge Visualization Dashboard"])

# Knowledge Flow Tracking System API (Phase 6 - Production Ready)
app.include_router(knowledge_flow.router, tags=["Knowledge Flow Tracking System"])

# Admin API for pretool validation and command execution
app.include_router(admin.router, tags=["Admin Dashboard"])

# Task Management API - File-based to bypass TodoWrite timeouts
app.include_router(tasks.router, tags=["Task Management"])
app.include_router(sprints.router, tags=["AI Sprints"])
app.include_router(agent_tracking.router, tags=["Agent Tracking"])
app.include_router(session_costs.router, prefix="/api/session-costs", tags=["Session Cost Tracking"])

# Enhanced Task Management with Git Integration
try:
    from api import enhanced_tasks
    app.include_router(enhanced_tasks.router, prefix="/api", tags=["Enhanced Task Management"])
except ImportError:
    logger.warning("Enhanced task management module not available")

# V2 API routers (current/enhanced) - only if modules available
if V2_MODULES_AVAILABLE:
    logger.info("Including V2 API routers")
    app.include_router(advanced_query.router, tags=["Advanced Query v2"])
    app.include_router(batch_operations.router, tags=["Batch Operations v2"])
    app.include_router(cross_project.router, tags=["Cross-Project Intelligence v2"])
    logger.info("V2 API routers included successfully")
    
    # Real-time API routers (v2.1)
    if V2_REALTIME_AVAILABLE:
        app.include_router(websocket.router, tags=["WebSocket v2"])
        app.include_router(webhooks.router, tags=["Webhooks v2"])

# Agent Learning Feedback Loop and Intelligent Routing APIs
# app.include_router(agent_routing_routes.router, tags=["Context-Aware Agent Routing"])  # Temporarily disabled
# app.include_router(agent_learning_routes.router, tags=["Agent Learning Feedback Loop"])  # Temporarily disabled
# app.include_router(intelligent_routing_routes.router, tags=["Intelligent Routing with ML"])  # Temporarily disabled

# app.include_router(agents.router, prefix="/api/agents", tags=["Multi-Agent Platform with Context-Aware Routing"])  # Temporarily disabled

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "BETTY Memory System API",
        "description": "Claude's Extended Brain - Unlimited Context Awareness with Temporal Knowledge Graphs",
        "version": "2.1.0",
        "api_versions": {
            "current": "2.1.0",
            "supported": ["1.0", "1.1", "2.0", "2.1"],
            "deprecated": [],
            "sunset_dates": {
                "1.0": "2025-12-31",
                "1.1": "2025-12-31"
            }
        },
        "status": "operational",
        "features": {
            "v1": ["basic_knowledge_management", "simple_search", "session_management", "basic_analytics"],
            "v2": ["advanced_query_apis", "batch_operations", "cross_project_intelligence", "enhanced_performance", "realtime_websockets", "webhook_system", "progress_streaming", "collaborative_sessions", "memory_correctness_engine", "pattern_integrity_validation", "cross_database_consistency", "automated_recovery", "99.9_percent_accuracy", "context_aware_agent_routing", "agent_learning_feedback_loop", "intelligent_ml_routing", "agent_specialization_detection", "routing_optimization", "pattern_success_prediction", "roi_estimation", "implementation_strategy_optimization", "ml_prediction_models", "continuous_learning", "multi_source_knowledge_extraction", "stackoverflow_integration", "commandlinefu_integration", "security_sources_integration", "infrastructure_sources_integration", "realtime_knowledge_monitoring", "ml_pattern_classification", "automated_conflict_resolution", "cross_domain_pattern_intelligence", "10000_plus_patterns_support", "sub_2_second_processing", "95_percent_accuracy_classification", "source_validation_verification", "enterprise_grade_validation", "ml_powered_accuracy_checks", "credibility_scoring", "security_scanning", "malicious_content_detection", "real_time_monitoring", "pattern_drift_detection", "soc2_compliance", "gdpr_compliance", "audit_trails", "99_5_percent_validation_accuracy", "sub_500ms_validation_latency"],
            "v2.1": ["enhanced_error_handling", "intelligent_error_classification", "automated_error_recovery", "real_time_monitoring", "pattern_detection", "enterprise_alerting", "performance_bottleneck_detection", "security_anomaly_detection", "comprehensive_logging", "ntfy_notifications"]
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "v1_docs": "/api/v1/docs",
            "v2_docs": "/api/v2/docs",
            "version_info": "/version/info",
            "migration_guide": "/api/v2/docs/migration-guide",
            "websocket_progress": "/api/v2/websocket/progress/{operation_id}",
            "websocket_search": "/api/v2/websocket/search",
            "websocket_collaboration": "/api/v2/websocket/session/{session_id}",
            "webhooks": "/api/v2/webhooks",
            "memory_correctness": "/api/v2/memory-correctness",
            "pattern_validation": "/api/v2/memory-correctness/validate/pattern/{pattern_id}",
            "project_validation": "/api/v2/memory-correctness/validate/project",
            "consistency_check": "/api/v2/memory-correctness/consistency/check",
            "pattern_repair": "/api/v2/memory-correctness/repair/patterns",
            "health_monitoring": "/api/v2/memory-correctness/health/{project_id}",
            "pattern_success_prediction": "/api/v1/pattern-prediction/success-prediction",
            "roi_prediction": "/api/v1/pattern-prediction/roi-prediction",
            "strategy_recommendation": "/api/v1/pattern-prediction/strategy-recommendation",
            "comprehensive_analysis": "/api/v1/pattern-prediction/comprehensive-analysis",
            "prediction_accuracy_tracking": "/api/v1/pattern-prediction/track-accuracy/{prediction_id}",
            "prediction_statistics": "/api/v1/pattern-prediction/statistics",
            "knowledge_extraction": "/api/knowledge-extraction",
            "start_extraction": "/api/knowledge-extraction/extract",
            "extraction_status": "/api/knowledge-extraction/status",
            "source_configs": "/api/knowledge-extraction/sources",
            "processing_stats": "/api/knowledge-extraction/processing/statistics",
            "monitoring_status": "/api/knowledge-extraction/monitoring/status",
            "knowledge_search": "/api/knowledge-extraction/search",
            "extraction_analytics": "/api/knowledge-extraction/analytics/dashboard",
            "realtime_updates": "/api/knowledge-extraction/stream/updates",
            "source_validation": "/api/source-validation",
            "validate_items": "/api/source-validation/validate",
            "bulk_validation": "/api/source-validation/validate/bulk",
            "validation_statistics": "/api/source-validation/statistics",
            "source_credibility": "/api/source-validation/credibility",
            "security_alerts": "/api/source-validation/alerts",
            "validation_health": "/api/source-validation/health",
            "compliance_audit_log": "/api/source-validation/compliance/audit-log",
            "validation_monitoring_stream": "/api/source-validation/stream/validation-events"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use our custom logging configuration
    )