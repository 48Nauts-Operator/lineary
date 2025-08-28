# ABOUTME: FastAPI routes for BETTY Multi-Agent Platform with Context-Aware Routing
# ABOUTME: Provides REST API endpoints for agent registration, intelligent routing, and operations

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
import structlog
import json
import asyncio
from pydantic import BaseModel, Field

from ..services.agent_service import AgentService, AgentRegistration, AgentConfig
from ..services.agent_manager import AgentManager
# from ..services.context_aware_router import (
#     ContextAwareAgentRouter, 
#     TaskContext, 
#     TaskComplexity, 
#     AgentSelection,
#     RoutingResult,
#     AgentHealthStatus
# )  # Temporarily disabled to test basic API
from ..providers.base_provider import ChatRequest, Message
from ..core.dependencies import get_databases, DatabaseDependencies

logger = structlog.get_logger(__name__)

router = APIRouter()

# Pydantic models for Context-Aware Routing
class TaskRequest(BaseModel):
    """Request model for intelligent task routing"""
    task_type: str = Field(..., description="Type of task to route")
    complexity: str = Field(default="moderate", description="Task complexity: simple, moderate, complex, critical") 
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10)")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    project_id: str = Field(default="default", description="Project identifier")
    user_id: str = Field(default="system", description="User identifier")
    required_capabilities: List[str] = Field(default=[], description="Required agent capabilities")
    preferred_agents: List[str] = Field(default=[], description="Preferred agent names")
    fallback_agents: List[str] = Field(default=[], description="Fallback agent names")
    sensitive_data: bool = Field(default=False, description="Contains sensitive data")
    metadata: Dict[str, Any] = Field(default={}, description="Additional task metadata")

class ExecutionResult(BaseModel):
    """Model for recording task execution results"""
    agent_id: UUID = Field(..., description="Agent that executed the task")
    task_type: str = Field(..., description="Type of task executed")
    complexity: str = Field(..., description="Task complexity")
    success: bool = Field(..., description="Whether execution was successful")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    actual_cost_cents: Optional[int] = Field(None, description="Actual cost in cents")
    user_satisfaction: Optional[float] = Field(None, ge=1.0, le=5.0, description="User satisfaction rating 1-5")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")

@router.post("/register", response_model=Dict[str, Any])
async def register_agent(
    registration: AgentRegistration,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Register a new agent in the system"""
    try:
        agent_service = AgentService(databases)
        await agent_service.initialize()
        
        result = await agent_service.register_agent(registration)
        
        logger.info("Agent registration requested", 
                   agent_name=registration.name,
                   provider=registration.provider)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Agent registration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """List all registered agents with optional filtering"""
    try:
        agent_service = AgentService(databases)
        await agent_service.initialize()
        
        agents = await agent_service.get_agents(status=status)
        
        # Filter by provider if specified
        if provider:
            agents = [agent for agent in agents if agent['provider'] == provider]
        
        return agents
        
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{agent_id}", response_model=Dict[str, Any])
async def get_agent(
    agent_id: UUID,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get detailed information about a specific agent"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        stats = await agent_manager.get_agent_stats(agent_id)
        return stats
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get agent", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{agent_id}/start", response_model=Dict[str, Any])
async def start_agent(
    agent_id: UUID,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Start an agent (particularly for local processes)"""
    try:
        agent_service = AgentService(databases)
        await agent_service.initialize()
        
        result = await agent_service.start_agent(agent_id)
        
        logger.info("Agent start requested", agent_id=str(agent_id))
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to start agent", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{agent_id}/stop", response_model=Dict[str, Any])
async def stop_agent(
    agent_id: UUID,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Stop an agent"""
    try:
        agent_service = AgentService(databases)
        await agent_service.initialize()
        
        result = await agent_service.stop_agent(agent_id)
        
        logger.info("Agent stop requested", agent_id=str(agent_id))
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to stop agent", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{agent_id}/reload", response_model=Dict[str, Any])
async def reload_agent(
    agent_id: UUID,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Reload an agent's configuration"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        result = await agent_manager.reload_agent(agent_id)
        
        logger.info("Agent reload requested", agent_id=str(agent_id))
        return result
        
    except Exception as e:
        logger.error("Failed to reload agent", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{agent_id}/chat", response_model=Dict[str, Any])
async def chat_with_agent(
    agent_id: UUID,
    request: ChatRequest,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Send a chat request to a specific agent"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        response = await agent_manager.chat_with_agent(agent_id, request)
        
        return {
            "agent_id": str(agent_id),
            "response": response.dict(),
            "success": True
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Chat failed", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent_id}/chat/stream")
async def chat_with_agent_stream(
    agent_id: UUID,
    request: ChatRequest,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Stream a chat response from a specific agent"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        agent_id_str = str(agent_id)
        
        # Check if agent is available
        if agent_id_str not in agent_manager.active_providers:
            await agent_manager._load_single_agent(agent_id)
            
        if agent_id_str not in agent_manager.active_providers:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not available")
        
        provider = agent_manager.active_providers[agent_id_str]
        
        async def generate_stream():
            try:
                async for chunk in provider.chat_stream(request):
                    # Format as SSE
                    yield f"data: {json.dumps({'chunk': chunk, 'type': 'content'})}\n\n"
                    
                # Send completion signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error("Stream chat failed", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/capability/{capability}", response_model=Dict[str, Any])
async def chat_with_capability(
    capability: str,
    request: ChatRequest,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Route chat request to the best agent for a specific capability"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        response = await agent_manager.chat_with_best_agent(capability, request)
        
        return {
            "capability": capability,
            "response": response.dict(),
            "success": True
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Capability chat failed", capability=capability, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities", response_model=List[Dict[str, Any]])
async def list_capabilities(
    databases: DatabaseDependencies = Depends(get_databases)
):
    """List all available capabilities across agents"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        capabilities = await agent_manager.get_all_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error("Failed to list capabilities", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{agent_id}/config", response_model=Dict[str, Any])
async def update_agent_config(
    agent_id: UUID,
    config: AgentConfig,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Update agent configuration"""
    try:
        # Use the database dependencies pattern
        # Check if agent exists
        result = await databases.postgres.execute(
            "SELECT id FROM agents WHERE id = $1",
            {"id": agent_id}
        )
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update or insert configuration
        await databases.postgres.execute("""
            INSERT INTO agent_configurations (agent_id, environment, config_key, config_value, is_sensitive)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (agent_id, environment, config_key) 
            DO UPDATE SET config_value = $4, is_sensitive = $5, updated_at = NOW()
        """, {
            "agent_id": agent_id, 
            "environment": config.environment, 
            "config_key": config.config_key,
            "config_value": json.dumps(config.config_value),
            "is_sensitive": config.is_sensitive
        })
        
        return {
            "agent_id": str(agent_id),
            "config_updated": True,
            "environment": config.environment,
            "config_key": config.config_key
        }
        
    except Exception as e:
        logger.error("Failed to update config", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{agent_id}/health", response_model=Dict[str, Any])
async def check_agent_health(
    agent_id: UUID,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Check the health status of an agent"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        agent_id_str = str(agent_id)
        
        if agent_id_str in agent_manager.active_providers:
            provider = agent_manager.active_providers[agent_id_str]
            health_status = await provider.health_check()
        else:
            health_status = {
                "status": "inactive",
                "message": "Agent not loaded"
            }
        
        return {
            "agent_id": agent_id_str,
            "health": health_status,
            "timestamp": "now"  # Could use actual timestamp
        }
        
    except Exception as e:
        logger.error("Health check failed", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{agent_id}", response_model=Dict[str, Any])
async def delete_agent(
    agent_id: UUID,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Delete an agent from the system"""
    try:
        # First stop the agent if running
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        agent_id_str = str(agent_id)
        if agent_id_str in agent_manager.active_providers:
            await agent_manager.active_providers[agent_id_str].cleanup()
            del agent_manager.active_providers[agent_id_str]
        
        # Delete from database (cascading deletes will handle related records)
        result = await databases.postgres.execute("""
            DELETE FROM agents WHERE id = $1 RETURNING id
        """, {"id": agent_id})
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Agent not found")
        
        logger.info("Agent deleted", agent_id=str(agent_id))
        
        return {
            "agent_id": str(agent_id),
            "deleted": True,
            "message": "Agent deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete agent", agent_id=str(agent_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# CONTEXT-AWARE AGENT ROUTING ENDPOINTS - TEMPORARILY DISABLED
# ============================================================================

# Context-Aware Routing endpoints temporarily disabled for testing
# Will be re-enabled once basic agent API is working

"""
CONTEXT-AWARE ROUTING ENDPOINTS (TEMPORARILY DISABLED)

@router.post("/routing/select-optimal", response_model=Dict[str, Any])
async def select_optimal_agent(
    task: TaskRequest,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Select the optimal agent for a given task using intelligent routing"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Convert request to TaskContext
        task_context = TaskContext(
            task_type=task.task_type,
            complexity=TaskComplexity(task.complexity),
            priority=task.priority,
            deadline=task.deadline,
            project_id=task.project_id,
            user_id=task.user_id,
            required_capabilities=task.required_capabilities,
            preferred_agents=task.preferred_agents,
            fallback_agents=task.fallback_agents,
            sensitive_data=task.sensitive_data,
            metadata=task.metadata
        )
        
        # Perform intelligent agent selection
        result = await router_service.select_optimal_agent(task_context)
        
        # Convert to response format
        if result.success and result.agent_selection:
            response_data = {
                "success": True,
                "agent_selection": {
                    "agent_id": str(result.agent_selection.agent_id),
                    "agent_name": result.agent_selection.agent_name,
                    "confidence_score": result.agent_selection.confidence_score,
                    "selection_reason": result.agent_selection.selection_reason,
                    "fallback_agents": [str(a) for a in result.agent_selection.fallback_agents],
                    "estimated_completion_time": result.agent_selection.estimated_completion_time,
                    "cost_estimate": result.agent_selection.cost_estimate,
                    "selection_metadata": result.agent_selection.selection_metadata or {}
                },
                "routing_time_ms": result.routing_time_ms,
                "fallback_used": result.fallback_used,
                "retry_count": result.retry_count
            }
        else:
            response_data = {
                "success": False,
                "error_message": result.error_message,
                "routing_time_ms": result.routing_time_ms
            }
        
        logger.info("Optimal agent selection completed", 
                   success=result.success,
                   routing_time_ms=result.routing_time_ms,
                   task_type=task.task_type)
        
        return response_data
        
    except Exception as e:
        logger.error("Optimal agent selection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent selection failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@# @router.post("/routing/route-with-fallback", response_model=Dict[str, Any])
async def route_with_fallback(
    task: TaskRequest,
    preferred_agents: Optional[List[str]] = Query(None, description="Override preferred agents"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Route task with automatic fallback handling and retry logic"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Convert request to TaskContext
        task_context = TaskContext(
            task_type=task.task_type,
            complexity=TaskComplexity(task.complexity),
            priority=task.priority,
            deadline=task.deadline,
            project_id=task.project_id,
            user_id=task.user_id,
            required_capabilities=task.required_capabilities,
            preferred_agents=task.preferred_agents,
            fallback_agents=task.fallback_agents,
            sensitive_data=task.sensitive_data,
            metadata=task.metadata
        )
        
        # Route with intelligent fallback
        result = await router_service.route_with_fallback(task_context, preferred_agents)
        
        # Convert to response format
        if result.success and result.agent_selection:
            response_data = {
                "success": True,
                "agent_selection": {
                    "agent_id": str(result.agent_selection.agent_id),
                    "agent_name": result.agent_selection.agent_name,
                    "confidence_score": result.agent_selection.confidence_score,
                    "selection_reason": result.agent_selection.selection_reason,
                    "fallback_agents": [str(a) for a in result.agent_selection.fallback_agents],
                    "estimated_completion_time": result.agent_selection.estimated_completion_time,
                    "cost_estimate": result.agent_selection.cost_estimate,
                    "selection_metadata": result.agent_selection.selection_metadata or {}
                },
                "routing_time_ms": result.routing_time_ms,
                "fallback_used": result.fallback_used,
                "retry_count": result.retry_count
            }
        else:
            response_data = {
                "success": False,
                "error_message": result.error_message,
                "routing_time_ms": result.routing_time_ms,
                "fallback_used": result.fallback_used,
                "retry_count": result.retry_count
            }
        
        logger.info("Fallback routing completed", 
                   success=result.success,
                   fallback_used=result.fallback_used,
                   retry_count=result.retry_count)
        
        return response_data
        
    except Exception as e:
        logger.error("Fallback routing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Fallback routing failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@router.get("/routing/health-status", response_model=List[Dict[str, Any]])
async def get_agent_health_status(
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get comprehensive health status for all agents with performance metrics"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Get health status for all agents
        health_statuses = await router_service.monitor_agent_health()
        
        # Convert to response format
        health_responses = []
        for health in health_statuses:
            health_responses.append({
                "agent_id": str(health.agent_id),
                "agent_name": health.agent_name,
                "status": health.status,
                "load_level": health.load_level.value,
                "response_time_p95": health.response_time_p95,
                "success_rate": health.success_rate,
                "error_rate": health.error_rate,
                "cost_per_request": health.cost_per_request,
                "last_health_check": health.last_health_check,
                "predictive_failure_score": health.predictive_failure_score,
                "capacity_utilization": health.capacity_utilization
            })
        
        logger.info("Agent health status retrieved", agent_count=len(health_responses))
        return health_responses
        
    except Exception as e:
        logger.error("Health status retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health status retrieval failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@# @router.post("/routing/record-execution")
async def record_execution_result(
    execution_result: ExecutionResult,
    background_tasks: BackgroundTasks,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Record the result of task execution for learning and optimization"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Convert to TaskContext for recording
        task_context = TaskContext(
            task_type=execution_result.task_type,
            complexity=TaskComplexity(execution_result.complexity)
        )
        
        # Record execution result for machine learning
        await router_service.record_execution_result(
            agent_id=execution_result.agent_id,
            task_context=task_context,
            success=execution_result.success,
            execution_time_ms=execution_result.execution_time_ms,
            actual_cost_cents=execution_result.actual_cost_cents
        )
        
        logger.info("Execution result recorded", 
                   agent_id=str(execution_result.agent_id),
                   success=execution_result.success)
        
        return {
            "success": True,
            "message": "Execution result recorded successfully",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Recording execution result failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Recording execution result failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@router.get("/routing/analytics")
async def get_routing_analytics(
    hours: int = Query(24, ge=1, le=168, description="Hours of analytics data (1-168)"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get routing analytics and performance insights"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Get comprehensive analytics data
        analytics = await router_service.get_routing_analytics(hours=hours)
        
        return {
            "success": True,
            "analytics": analytics,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Analytics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@# @router.post("/routing/circuit-breaker/{agent_id}/reset")
async def reset_circuit_breaker(
    agent_id: UUID,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Manually reset circuit breaker for an agent"""
    try:
        # Reset circuit breaker to CLOSED state
        await databases.postgres.execute("""
            INSERT INTO agent_circuit_breakers (agent_id, state, failure_count, success_count)
            VALUES ($1, 'CLOSED', 0, 0)
            ON CONFLICT (agent_id) DO UPDATE SET
                state = 'CLOSED',
                failure_count = 0,
                success_count = 0,
                updated_at = NOW()
        """, {"agent_id": agent_id})
        
        logger.info("Circuit breaker reset", agent_id=str(agent_id))
        
        return {
            "success": True,
            "message": f"Circuit breaker reset for agent {agent_id}",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Circuit breaker reset failed", error=str(e), agent_id=str(agent_id))
        raise HTTPException(status_code=500, detail=f"Circuit breaker reset failed: {str(e)}")

@router.get("/routing/performance-trends/{agent_id}")
async def get_agent_performance_trends(
    agent_id: UUID,
    hours: int = Query(168, ge=1, le=720, description="Hours of trend data (1-720)"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get performance trends for a specific agent over time"""
    try:
        # Get performance snapshots over time
        snapshots_result = await databases.postgres.execute("""
            SELECT 
                snapshot_time,
                overall_score,
                reliability_score,
                performance_score,
                cost_efficiency_score,
                load_score,
                active_requests,
                load_level,
                predictive_failure_score
            FROM agent_performance_snapshots
            WHERE agent_id = $1 
            AND snapshot_time >= NOW() - INTERVAL '%s hours'
            ORDER BY snapshot_time ASC
        """ % hours, {"agent_id": agent_id})
        snapshots = snapshots_result.fetchall()
        
        # Get recent routing metrics
        metrics_result = await databases.postgres.execute("""
            SELECT 
                DATE_TRUNC('hour', created_at) as hour,
                COUNT(*) as routing_count,
                AVG(routing_time_ms) as avg_routing_time,
                AVG(CASE WHEN execution_success THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(execution_time_ms) as avg_execution_time
            FROM agent_routing_metrics
            WHERE agent_id = $1 
            AND created_at >= NOW() - INTERVAL '%s hours'
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour ASC
        """ % hours, {"agent_id": agent_id})
        routing_metrics = metrics_result.fetchall()
        
        return {
            "success": True,
            "agent_id": str(agent_id),
            "trends": {
                "performance_snapshots": [dict(snap) for snap in snapshots],
                "hourly_metrics": [dict(metric) for metric in routing_metrics]
            },
            "period_hours": hours,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Performance trends retrieval failed", error=str(e), agent_id=str(agent_id))
        raise HTTPException(status_code=500, detail=f"Performance trends retrieval failed: {str(e)}")

@router.get("/routing/health")
async def routing_system_health():
    """Health check endpoint for the Context-Aware Routing System"""
    return {
        "status": "healthy",
        "service": "Context-Aware Agent Routing System",
        "version": "1.0.0",
        "features": [
            "Intelligent Agent Selection",
            "Performance-Based Routing",
            "Circuit Breaker Protection",
            "Load Balancing",
            "Predictive Failure Detection",
            "Multi-Agent Coordination"
        ],
        "timestamp": datetime.utcnow()
    }

# Enhanced capability-based routing (upgrade to existing endpoint)
@router.post("/chat/smart-capability/{capability}", response_model=Dict[str, Any])
async def smart_chat_with_capability(
    capability: str,
    request: ChatRequest,
    priority: int = Query(5, ge=1, le=10, description="Task priority (1-10)"),
    complexity: str = Query("moderate", description="Task complexity"),
    deadline_minutes: Optional[int] = Query(None, description="Deadline in minutes from now"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Route chat request using Context-Aware Routing for optimal agent selection"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Create task context for intelligent routing
        deadline = None
        if deadline_minutes:
            from datetime import timedelta
            deadline = datetime.utcnow() + timedelta(minutes=deadline_minutes)
        
        task_context = TaskContext(
            task_type="chat_request",
            complexity=TaskComplexity(complexity),
            priority=priority,
            deadline=deadline,
            required_capabilities=[capability],
            metadata={"chat_request": True, "capability": capability}
        )
        
        # Get optimal agent selection
        routing_result = await router_service.select_optimal_agent(task_context)
        
        if not routing_result.success:
            raise HTTPException(status_code=404, detail=f"No suitable agent found for capability: {capability}")
        
        # Execute chat with selected agent
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        selected_agent_id = routing_result.agent_selection.agent_id
        response = await agent_manager.chat_with_agent(selected_agent_id, request)
        
        # Record execution result
        task_context_record = TaskContext(
            task_type="chat_request",
            complexity=TaskComplexity(complexity)
        )
        
        await router_service.record_execution_result(
            agent_id=selected_agent_id,
            task_context=task_context_record,
            success=True,  # Assume success if no exception thrown
            execution_time_ms=routing_result.routing_time_ms + 1000,  # Estimate total time
            actual_cost_cents=routing_result.agent_selection.cost_estimate
        )
        
        return {
            "capability": capability,
            "agent_selection": {
                "agent_id": str(routing_result.agent_selection.agent_id),
                "agent_name": routing_result.agent_selection.agent_name,
                "confidence_score": routing_result.agent_selection.confidence_score,
                "selection_reason": routing_result.agent_selection.selection_reason
            },
            "routing_time_ms": routing_result.routing_time_ms,
            "response": response.dict(),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Smart capability chat failed", capability=capability, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()
        if 'agent_manager' in locals():
            await agent_manager.cleanup()