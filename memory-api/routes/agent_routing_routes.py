# ABOUTME: FastAPI routes for Context-Aware Agent Routing System
# ABOUTME: REST API endpoints for intelligent agent selection and routing analytics

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from core.dependencies import get_databases, DatabaseDependencies
from services.context_aware_router import (
    ContextAwareAgentRouter, 
    TaskContext, 
    TaskComplexity, 
    AgentSelection,
    RoutingResult,
    AgentHealthStatus
)
from services.agent_manager import AgentManager

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/routing", tags=["agent-routing"])

# Pydantic models for API
class TaskRequest(BaseModel):
    """Request model for task routing"""
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

class MultiAgentTaskRequest(BaseModel):
    """Request model for multi-agent coordination"""
    task_name: str = Field(..., description="Name of the complex task")
    subtasks: List[Dict[str, Any]] = Field(..., description="List of subtasks to coordinate")
    coordination_strategy: str = Field(default="parallel", description="parallel, sequential, or hybrid")
    deadline: Optional[datetime] = Field(None, description="Overall task deadline")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority")

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

class AgentSelectionResponse(BaseModel):
    """Response model for agent selection"""
    agent_id: str
    agent_name: str
    confidence_score: float
    selection_reason: str
    fallback_agents: List[str]
    estimated_completion_time: float
    cost_estimate: int
    selection_metadata: Dict[str, Any]

class RoutingResponse(BaseModel):
    """Response model for routing operations"""
    success: bool
    agent_selection: Optional[AgentSelectionResponse]
    routing_time_ms: float
    error_message: Optional[str] = None
    fallback_used: bool = False
    retry_count: int = 0

class AgentHealthResponse(BaseModel):
    """Response model for agent health status"""
    agent_id: str
    agent_name: str
    status: str
    load_level: str
    response_time_p95: float
    success_rate: float
    error_rate: float
    cost_per_request: float
    last_health_check: datetime
    predictive_failure_score: float
    capacity_utilization: float

# Route handlers
@router.post("/select-agent", response_model=RoutingResponse)
async def select_optimal_agent(
    task: TaskRequest,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Select the optimal agent for a given task"""
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
        
        # Perform agent selection
        result = await router_service.select_optimal_agent(task_context)
        
        # Convert to response model
        if result.success and result.agent_selection:
            agent_selection = AgentSelectionResponse(
                agent_id=str(result.agent_selection.agent_id),
                agent_name=result.agent_selection.agent_name,
                confidence_score=result.agent_selection.confidence_score,
                selection_reason=result.agent_selection.selection_reason,
                fallback_agents=[str(a) for a in result.agent_selection.fallback_agents],
                estimated_completion_time=result.agent_selection.estimated_completion_time,
                cost_estimate=result.agent_selection.cost_estimate,
                selection_metadata=result.agent_selection.selection_metadata or {}
            )
        else:
            agent_selection = None
        
        return RoutingResponse(
            success=result.success,
            agent_selection=agent_selection,
            routing_time_ms=result.routing_time_ms,
            error_message=result.error_message,
            fallback_used=result.fallback_used,
            retry_count=result.retry_count
        )
        
    except Exception as e:
        logger.error("Agent selection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent selection failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@router.post("/route-with-fallback", response_model=RoutingResponse)
async def route_with_fallback(
    task: TaskRequest,
    preferred_agents: Optional[List[str]] = Query(None, description="Override preferred agents"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Route task with automatic fallback handling"""
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
        
        # Route with fallback
        result = await router_service.route_with_fallback(task_context, preferred_agents)
        
        # Convert to response model
        if result.success and result.agent_selection:
            agent_selection = AgentSelectionResponse(
                agent_id=str(result.agent_selection.agent_id),
                agent_name=result.agent_selection.agent_name,
                confidence_score=result.agent_selection.confidence_score,
                selection_reason=result.agent_selection.selection_reason,
                fallback_agents=[str(a) for a in result.agent_selection.fallback_agents],
                estimated_completion_time=result.agent_selection.estimated_completion_time,
                cost_estimate=result.agent_selection.cost_estimate,
                selection_metadata=result.agent_selection.selection_metadata or {}
            )
        else:
            agent_selection = None
        
        return RoutingResponse(
            success=result.success,
            agent_selection=agent_selection,
            routing_time_ms=result.routing_time_ms,
            error_message=result.error_message,
            fallback_used=result.fallback_used,
            retry_count=result.retry_count
        )
        
    except Exception as e:
        logger.error("Fallback routing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Fallback routing failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@router.post("/multi-agent-coordination")
async def coordinate_multi_agent_task(
    task: MultiAgentTaskRequest,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Coordinate multiple agents for complex tasks"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Prepare complex task data
        complex_task = {
            'name': task.task_name,
            'subtasks': task.subtasks,
            'strategy': task.coordination_strategy,
            'deadline': task.deadline,
            'priority': task.priority
        }
        
        # Coordinate multi-agent task
        result = await router_service.coordinate_multi_agent_task(complex_task)
        
        return {
            'success': True,
            'coordination_result': result,
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Multi-agent coordination failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Multi-agent coordination failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@router.get("/agent-health", response_model=List[AgentHealthResponse])
async def get_agent_health_status(
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get comprehensive health status for all agents"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Get health status for all agents
        health_statuses = await router_service.monitor_agent_health()
        
        # Convert to response models
        health_responses = []
        for health in health_statuses:
            health_responses.append(AgentHealthResponse(
                agent_id=str(health.agent_id),
                agent_name=health.agent_name,
                status=health.status,
                load_level=health.load_level.value,
                response_time_p95=health.response_time_p95,
                success_rate=health.success_rate,
                error_rate=health.error_rate,
                cost_per_request=health.cost_per_request,
                last_health_check=health.last_health_check,
                predictive_failure_score=health.predictive_failure_score,
                capacity_utilization=health.capacity_utilization
            ))
        
        return health_responses
        
    except Exception as e:
        logger.error("Health status retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health status retrieval failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@router.post("/record-execution-result")
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
        
        # Record execution result
        await router_service.record_execution_result(
            agent_id=execution_result.agent_id,
            task_context=task_context,
            success=execution_result.success,
            execution_time_ms=execution_result.execution_time_ms,
            actual_cost_cents=execution_result.actual_cost_cents
        )
        
        return {
            'success': True,
            'message': 'Execution result recorded successfully',
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Recording execution result failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Recording execution result failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@router.get("/analytics")
async def get_routing_analytics(
    hours: int = Query(24, ge=1, le=168, description="Hours of analytics data (1-168)"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get routing analytics and performance insights"""
    try:
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Get analytics data
        analytics = await router_service.get_routing_analytics(hours=hours)
        
        return {
            'success': True,
            'analytics': analytics,
            'generated_at': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Analytics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()

@router.get("/capabilities")
async def get_available_capabilities(
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get all available capabilities across all agents"""
    try:
        agent_manager = AgentManager(databases)
        await agent_manager.initialize()
        
        capabilities = await agent_manager.get_all_capabilities()
        
        return {
            'success': True,
            'capabilities': capabilities,
            'total_count': len(capabilities)
        }
        
    except Exception as e:
        logger.error("Capabilities retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Capabilities retrieval failed: {str(e)}")
    finally:
        if 'agent_manager' in locals():
            await agent_manager.cleanup()

@router.post("/circuit-breaker/{agent_id}/reset")
async def reset_circuit_breaker(
    agent_id: UUID,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Manually reset circuit breaker for an agent"""
    try:
        async with databases.postgres.acquire() as conn:
            # Reset circuit breaker to CLOSED state
            await conn.execute("""
                INSERT INTO agent_circuit_breakers (agent_id, state, failure_count, success_count)
                VALUES ($1, 'CLOSED', 0, 0)
                ON CONFLICT (agent_id) DO UPDATE SET
                    state = 'CLOSED',
                    failure_count = 0,
                    success_count = 0,
                    updated_at = NOW()
            """, agent_id)
            
            logger.info("Circuit breaker reset", agent_id=str(agent_id))
        
        return {
            'success': True,
            'message': f'Circuit breaker reset for agent {agent_id}',
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Circuit breaker reset failed", error=str(e), agent_id=str(agent_id))
        raise HTTPException(status_code=500, detail=f"Circuit breaker reset failed: {str(e)}")

@router.get("/performance-trends/{agent_id}")
async def get_agent_performance_trends(
    agent_id: UUID,
    hours: int = Query(168, ge=1, le=720, description="Hours of trend data (1-720)"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get performance trends for a specific agent"""
    try:
        async with databases.postgres.acquire() as conn:
            # Get performance snapshots over time
            snapshots = await conn.fetch("""
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
            """ % hours, agent_id)
            
            # Get recent routing metrics
            routing_metrics = await conn.fetch("""
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
            """ % hours, agent_id)
        
        return {
            'success': True,
            'agent_id': str(agent_id),
            'trends': {
                'performance_snapshots': [dict(snap) for snap in snapshots],
                'hourly_metrics': [dict(metric) for metric in routing_metrics]
            },
            'period_hours': hours,
            'generated_at': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Performance trends retrieval failed", error=str(e), agent_id=str(agent_id))
        raise HTTPException(status_code=500, detail=f"Performance trends retrieval failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint for routing system"""
    return {
        'status': 'healthy',
        'service': 'Context-Aware Agent Routing System',
        'version': '1.0.0',
        'timestamp': datetime.utcnow()
    }

# Load testing endpoint (development only)
@router.post("/load-test")
async def load_test_routing(
    num_requests: int = Query(100, ge=1, le=1000, description="Number of test requests"),
    concurrent: int = Query(10, ge=1, le=50, description="Concurrent requests"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Load test the routing system (development only)"""
    try:
        import asyncio
        import random
        
        router_service = ContextAwareAgentRouter(databases)
        await router_service.initialize()
        
        # Generate test tasks
        task_types = ['code_analysis', 'code_generation', 'debugging', 'security_audit']
        complexities = ['simple', 'moderate', 'complex']
        
        async def make_test_request():
            task_context = TaskContext(
                task_type=random.choice(task_types),
                complexity=TaskComplexity(random.choice(complexities)),
                priority=random.randint(1, 10),
                required_capabilities=[random.choice(task_types)]
            )
            
            start_time = datetime.utcnow()
            result = await router_service.select_optimal_agent(task_context)
            end_time = datetime.utcnow()
            
            return {
                'success': result.success,
                'routing_time_ms': result.routing_time_ms,
                'total_time_ms': (end_time - start_time).total_seconds() * 1000,
                'selected_agent': result.agent_selection.agent_name if result.agent_selection else None
            }
        
        # Run concurrent requests in batches
        results = []
        for batch_start in range(0, num_requests, concurrent):
            batch_size = min(concurrent, num_requests - batch_start)
            batch_results = await asyncio.gather(
                *[make_test_request() for _ in range(batch_size)],
                return_exceptions=True
            )
            results.extend(batch_results)
        
        # Calculate statistics
        successful_results = [r for r in results if isinstance(r, dict) and r['success']]
        failed_results = [r for r in results if isinstance(r, Exception) or (isinstance(r, dict) and not r['success'])]
        
        if successful_results:
            avg_routing_time = sum(r['routing_time_ms'] for r in successful_results) / len(successful_results)
            avg_total_time = sum(r['total_time_ms'] for r in successful_results) / len(successful_results)
            p95_routing_time = sorted([r['routing_time_ms'] for r in successful_results])[int(len(successful_results) * 0.95)]
        else:
            avg_routing_time = avg_total_time = p95_routing_time = 0
        
        return {
            'success': True,
            'load_test_results': {
                'total_requests': num_requests,
                'successful_requests': len(successful_results),
                'failed_requests': len(failed_results),
                'success_rate': len(successful_results) / num_requests,
                'avg_routing_time_ms': avg_routing_time,
                'avg_total_time_ms': avg_total_time,
                'p95_routing_time_ms': p95_routing_time,
                'concurrent_requests': concurrent
            },
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Load test failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Load test failed: {str(e)}")
    finally:
        if 'router_service' in locals():
            await router_service.cleanup()