# ABOUTME: FastAPI routes for Intelligent Routing Service - ML-enhanced agent routing
# ABOUTME: REST API endpoints for intelligent routing with continuous learning and optimization

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from core.dependencies import get_databases, DatabaseDependencies
from services.intelligent_routing_service import IntelligentRoutingService, EnhancedRoutingResult
from services.context_aware_router import TaskContext, TaskComplexity

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/intelligent-routing", tags=["intelligent-routing"])

# Pydantic models for API
class IntelligentTaskRequest(BaseModel):
    """Request model for intelligent task routing"""
    task_type: str = Field(..., description="Type of task to route")
    complexity: str = Field(default="moderate", description="Task complexity: simple, moderate, complex, critical")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10)")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    project_id: str = Field(default="default", description="Project identifier")
    user_id: str = Field(default="system", description="User identifier")
    required_capabilities: List[str] = Field(default=[], description="Required agent capabilities")
    preferred_agents: List[str] = Field(default=[], description="Preferred agent names")
    sensitive_data: bool = Field(default=False, description="Contains sensitive data")
    enable_ml_prediction: bool = Field(default=True, description="Enable ML success prediction")
    enable_ml_optimization: bool = Field(default=True, description="Enable ML routing optimization")
    context_metadata: Dict[str, Any] = Field(default={}, description="Additional context metadata")

class TaskOutcomeRequest(BaseModel):
    """Request model for recording intelligent routing outcomes"""
    routing_id: str = Field(..., description="Routing decision identifier")
    agent_id: UUID = Field(..., description="Agent that executed the task")
    task_type: str = Field(..., description="Type of task executed")
    complexity: str = Field(..., description="Task complexity")
    success: bool = Field(..., description="Whether task was successful")
    completion_time: float = Field(..., gt=0.0, description="Task completion time in seconds")
    quality_metrics: Dict[str, float] = Field(default={}, description="Quality metrics (0.0-1.0)")
    user_satisfaction: Optional[float] = Field(None, ge=0.0, le=5.0, description="User satisfaction (0-5)")
    error_count: int = Field(default=0, ge=0, description="Number of errors encountered")
    cost_actual: Optional[float] = Field(None, ge=0.0, description="Actual cost in cents")

class SuccessPredictionResponse(BaseModel):
    """Response model for success predictions"""
    agent_id: str
    task_type: str
    complexity: str
    predicted_success_rate: float
    confidence_interval: List[float]  # [lower, upper]
    risk_factors: List[str]
    prediction_model: str
    prediction_timestamp: datetime

class AlternativeAgent(BaseModel):
    """Alternative agent information"""
    agent_id: str
    agent_name: Optional[str] = None
    specialization: Optional[str] = None
    performance_weight: Optional[float] = None
    agent_type: str  # specialized, high_performance, fallback

class EnhancedRoutingResponse(BaseModel):
    """Response model for intelligent routing"""
    success: bool
    routing_id: str
    selected_agent: Dict[str, Any]
    routing_time_ms: float
    success_prediction: Optional[SuccessPredictionResponse]
    learning_insights: Dict[str, Any]
    optimization_confidence: float
    alternative_agents: List[AlternativeAgent]
    routing_explanation: str
    fallback_used: bool = False
    error_message: Optional[str] = None

class IntelligentAnalyticsResponse(BaseModel):
    """Response model for intelligent routing analytics"""
    base_routing: Dict[str, Any]
    learning_system: Dict[str, Any]
    integration_metrics: Dict[str, Any]
    performance_improvements: Dict[str, Any]
    generated_at: datetime

# Route handlers
@router.post("/route", response_model=EnhancedRoutingResponse)
async def route_task_intelligently(
    task: IntelligentTaskRequest,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Route task with machine learning enhancements and continuous learning"""
    routing_id = f"ir_{int(datetime.utcnow().timestamp() * 1000)}"
    
    try:
        intelligent_router = IntelligentRoutingService(databases)
        await intelligent_router.initialize()
        
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
            fallback_agents=[],
            sensitive_data=task.sensitive_data,
            metadata=task.context_metadata
        )
        
        # Perform intelligent routing
        result = await intelligent_router.route_task_with_learning(
            task_context, 
            enable_prediction=task.enable_ml_prediction,
            enable_optimization=task.enable_ml_optimization
        )
        
        # Convert to response format
        success_prediction = None
        if result.success_prediction:
            success_prediction = SuccessPredictionResponse(
                agent_id=str(result.success_prediction.agent_id),
                task_type=result.success_prediction.task_type,
                complexity=result.success_prediction.complexity.value,
                predicted_success_rate=result.success_prediction.predicted_success_rate,
                confidence_interval=[
                    result.success_prediction.confidence_interval[0],
                    result.success_prediction.confidence_interval[1]
                ],
                risk_factors=result.success_prediction.risk_factors,
                prediction_model=result.success_prediction.prediction_model,
                prediction_timestamp=result.success_prediction.prediction_timestamp
            )
        
        alternative_agents = []
        for alt in result.alternative_agents:
            alternative_agents.append(AlternativeAgent(
                agent_id=alt.get('agent_id', ''),
                agent_name=alt.get('agent_name'),
                specialization=alt.get('specialization'),
                performance_weight=alt.get('performance_weight'),
                agent_type=alt.get('type', 'fallback')
            ))
        
        selected_agent_info = {}
        if result.routing_result.agent_selection:
            selected_agent_info = {
                'agent_id': str(result.routing_result.agent_selection.agent_id),
                'agent_name': result.routing_result.agent_selection.agent_name,
                'confidence_score': result.routing_result.agent_selection.confidence_score,
                'selection_reason': result.routing_result.agent_selection.selection_reason,
                'estimated_completion_time': result.routing_result.agent_selection.estimated_completion_time,
                'cost_estimate': result.routing_result.agent_selection.cost_estimate,
                'metadata': result.routing_result.agent_selection.selection_metadata
            }
        
        return EnhancedRoutingResponse(
            success=result.routing_result.success,
            routing_id=routing_id,
            selected_agent=selected_agent_info,
            routing_time_ms=result.routing_result.routing_time_ms,
            success_prediction=success_prediction,
            learning_insights=result.learning_insights,
            optimization_confidence=result.optimization_confidence,
            alternative_agents=alternative_agents,
            routing_explanation=result.routing_explanation,
            fallback_used=result.routing_result.fallback_used,
            error_message=result.routing_result.error_message
        )
        
    except Exception as e:
        logger.error("Intelligent routing failed", error=str(e), routing_id=routing_id)
        raise HTTPException(status_code=500, detail=f"Intelligent routing failed: {str(e)}")
    finally:
        if 'intelligent_router' in locals():
            await intelligent_router.cleanup()

@router.post("/record-outcome")
async def record_intelligent_routing_outcome(
    outcome: TaskOutcomeRequest,
    background_tasks: BackgroundTasks,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Record task outcome for intelligent routing with learning feedback"""
    try:
        intelligent_router = IntelligentRoutingService(databases)
        await intelligent_router.initialize()
        
        # Convert to task context
        task_context = TaskContext(
            task_type=outcome.task_type,
            complexity=TaskComplexity(outcome.complexity)
        )
        
        # Record outcome with learning
        await intelligent_router.record_task_outcome_with_learning(
            routing_id=outcome.routing_id,
            agent_id=outcome.agent_id,
            task=task_context,
            success=outcome.success,
            completion_time=outcome.completion_time,
            quality_metrics=outcome.quality_metrics,
            user_satisfaction=outcome.user_satisfaction,
            error_count=outcome.error_count,
            cost_actual=outcome.cost_actual
        )
        
        return {
            'success': True,
            'message': 'Intelligent routing outcome recorded successfully',
            'routing_id': outcome.routing_id,
            'learning_updated': True,
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Recording intelligent routing outcome failed", 
                    error=str(e), routing_id=outcome.routing_id)
        raise HTTPException(status_code=500, detail=f"Recording outcome failed: {str(e)}")
    finally:
        if 'intelligent_router' in locals():
            await intelligent_router.cleanup()

@router.get("/analytics", response_model=IntelligentAnalyticsResponse)
async def get_intelligent_routing_analytics(
    hours: int = Query(24, ge=1, le=168, description="Hours of analytics data (1-168)"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get comprehensive intelligent routing analytics with ML insights"""
    try:
        intelligent_router = IntelligentRoutingService(databases)
        await intelligent_router.initialize()
        
        analytics = await intelligent_router.get_intelligent_routing_analytics(hours)
        
        return IntelligentAnalyticsResponse(
            base_routing=analytics.get('base_routing', {}),
            learning_system=analytics.get('learning_system', {}),
            integration_metrics=analytics.get('integration_metrics', {}),
            performance_improvements=analytics.get('performance_improvements', {}),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Intelligent routing analytics failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")
    finally:
        if 'intelligent_router' in locals():
            await intelligent_router.cleanup()

@router.get("/performance-comparison")
async def get_performance_comparison(
    hours: int = Query(24, ge=1, le=168, description="Hours for comparison"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Compare performance between standard routing and intelligent routing"""
    try:
        async with databases.postgres.acquire() as conn:
            # Performance with ML optimization
            ml_performance = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(success_score) as avg_success_rate,
                    AVG(completion_time_seconds) as avg_completion_time,
                    STDDEV(success_score) as success_rate_std
                FROM agent_task_outcomes
                WHERE created_at >= NOW() - INTERVAL '%s hours'
                  AND context_metadata->>'optimization_applied' = 'true'
            """ % hours)
            
            # Performance without ML optimization
            standard_performance = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(success_score) as avg_success_rate,
                    AVG(completion_time_seconds) as avg_completion_time,
                    STDDEV(success_score) as success_rate_std
                FROM agent_task_outcomes
                WHERE created_at >= NOW() - INTERVAL '%s hours'
                  AND (context_metadata->>'optimization_applied' IS NULL 
                       OR context_metadata->>'optimization_applied' = 'false')
            """ % hours)
            
            # Task type breakdown
            task_type_performance = await conn.fetch("""
                SELECT 
                    task_type,
                    AVG(CASE WHEN context_metadata->>'optimization_applied' = 'true' 
                        THEN success_score END) as ml_success_rate,
                    AVG(CASE WHEN (context_metadata->>'optimization_applied' IS NULL 
                                  OR context_metadata->>'optimization_applied' = 'false')
                        THEN success_score END) as standard_success_rate,
                    COUNT(*) as total_tasks
                FROM agent_task_outcomes
                WHERE created_at >= NOW() - INTERVAL '%s hours'
                GROUP BY task_type
                HAVING COUNT(*) >= 5
                ORDER BY total_tasks DESC
            """ % hours)
        
        # Calculate improvements
        improvement_metrics = {}
        if (ml_performance['avg_success_rate'] and standard_performance['avg_success_rate'] and
            ml_performance['total_requests'] > 0 and standard_performance['total_requests'] > 0):
            
            success_improvement = (
                (ml_performance['avg_success_rate'] - standard_performance['avg_success_rate']) / 
                standard_performance['avg_success_rate'] * 100
            )
            
            time_improvement = (
                (standard_performance['avg_completion_time'] - ml_performance['avg_completion_time']) /
                standard_performance['avg_completion_time'] * 100
            ) if (ml_performance['avg_completion_time'] and standard_performance['avg_completion_time']) else 0
            
            improvement_metrics = {
                'success_rate_improvement_percent': success_improvement,
                'completion_time_improvement_percent': time_improvement,
                'consistency_improvement': (
                    standard_performance['success_rate_std'] - ml_performance['success_rate_std']
                ) if (ml_performance['success_rate_std'] and standard_performance['success_rate_std']) else 0
            }
        
        return {
            'success': True,
            'comparison_period_hours': hours,
            'ml_optimized_performance': dict(ml_performance) if ml_performance else {},
            'standard_routing_performance': dict(standard_performance) if standard_performance else {},
            'improvement_metrics': improvement_metrics,
            'task_type_breakdown': [dict(row) for row in task_type_performance],
            'generated_at': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Performance comparison failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Performance comparison failed: {str(e)}")

@router.get("/optimization-impact")
async def get_optimization_impact(
    agent_id: Optional[UUID] = Query(None, description="Filter by specific agent"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    hours: int = Query(48, ge=1, le=168, description="Hours of data to analyze"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Analyze the impact of ML optimizations on routing decisions"""
    try:
        async with databases.postgres.acquire() as conn:
            base_query = """
                SELECT 
                    ato.agent_id,
                    a.name as agent_name,
                    ato.task_type,
                    ato.complexity,
                    COUNT(*) as total_tasks,
                    AVG(ato.success_score) as avg_success,
                    AVG(ato.completion_time_seconds) as avg_completion_time,
                    COUNT(CASE WHEN ato.context_metadata->>'optimization_applied' = 'true' THEN 1 END) as optimized_tasks,
                    AVG(CASE WHEN ato.context_metadata->>'optimization_applied' = 'true' 
                        THEN ato.success_score END) as optimized_success_rate,
                    AVG(CASE WHEN (ato.context_metadata->>'optimization_applied' IS NULL 
                                  OR ato.context_metadata->>'optimization_applied' = 'false')
                        THEN ato.success_score END) as standard_success_rate
                FROM agent_task_outcomes ato
                JOIN agents a ON ato.agent_id = a.id
                WHERE ato.created_at >= NOW() - INTERVAL '%s hours'
            """ % hours
            
            params = []
            if agent_id:
                base_query += " AND ato.agent_id = $%d" % (len(params) + 1)
                params.append(agent_id)
            
            if task_type:
                base_query += " AND ato.task_type = $%d" % (len(params) + 1)
                params.append(task_type)
            
            base_query += """
                GROUP BY ato.agent_id, a.name, ato.task_type, ato.complexity
                HAVING COUNT(*) >= 3
                ORDER BY total_tasks DESC
            """
            
            impact_analysis = await conn.fetch(base_query, *params)
            
            # Get optimization type breakdown
            optimization_types = await conn.fetch("""
                SELECT 
                    context_metadata->>'optimization_type' as optimization_type,
                    COUNT(*) as usage_count,
                    AVG(success_score) as avg_success_rate
                FROM agent_task_outcomes
                WHERE created_at >= NOW() - INTERVAL '%s hours'
                  AND context_metadata->>'optimization_applied' = 'true'
                  AND context_metadata->>'optimization_type' IS NOT NULL
                GROUP BY context_metadata->>'optimization_type'
                ORDER BY usage_count DESC
            """ % hours)
        
        # Calculate impact scores
        impact_results = []
        for row in impact_analysis:
            impact_score = 0.0
            if row['optimized_success_rate'] and row['standard_success_rate']:
                impact_score = (
                    (row['optimized_success_rate'] - row['standard_success_rate']) / 
                    row['standard_success_rate'] * 100
                )
            
            impact_results.append({
                **dict(row),
                'optimization_impact_percent': impact_score,
                'optimization_adoption_rate': (row['optimized_tasks'] / row['total_tasks'] * 100) if row['total_tasks'] > 0 else 0
            })
        
        return {
            'success': True,
            'analysis_period_hours': hours,
            'agent_task_impact': impact_results,
            'optimization_type_performance': [dict(row) for row in optimization_types],
            'filter_applied': {
                'agent_id': str(agent_id) if agent_id else None,
                'task_type': task_type
            },
            'generated_at': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Optimization impact analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Impact analysis failed: {str(e)}")

@router.post("/trigger-learning-update")
async def trigger_learning_update(
    background_tasks: BackgroundTasks,
    force_optimization: bool = Query(False, description="Force routing optimization"),
    force_specialization_detection: bool = Query(False, description="Force specialization detection"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Manually trigger learning system updates"""
    try:
        intelligent_router = IntelligentRoutingService(databases)
        await intelligent_router.initialize()
        
        triggered_updates = []
        
        if force_optimization:
            background_tasks.add_task(intelligent_router.learning_engine.optimize_routing_weights)
            triggered_updates.append('routing_optimization')
        
        if force_specialization_detection:
            # This would trigger specialization detection for all agents
            background_tasks.add_task(intelligent_router.learning_engine._specialization_detection_loop)
            triggered_updates.append('specialization_detection')
        
        # Always trigger prediction validation
        background_tasks.add_task(intelligent_router.learning_engine._validate_predictions)
        triggered_updates.append('prediction_validation')
        
        return {
            'success': True,
            'message': 'Learning updates triggered successfully',
            'triggered_updates': triggered_updates,
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Learning update trigger failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Learning update failed: {str(e)}")
    finally:
        if 'intelligent_router' in locals():
            await intelligent_router.cleanup()

@router.get("/health")
async def intelligent_routing_health_check():
    """Health check endpoint for intelligent routing system"""
    return {
        'status': 'healthy',
        'service': 'Intelligent Routing Service',
        'version': '1.0.0',
        'components': {
            'context_aware_router': 'active',
            'learning_engine': 'active',
            'integration_layer': 'active'
        },
        'capabilities': [
            'ml_enhanced_routing',
            'success_prediction',
            'routing_optimization',
            'specialization_detection',
            'continuous_learning',
            'performance_analytics'
        ],
        'timestamp': datetime.utcnow()
    }