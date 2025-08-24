# ABOUTME: FastAPI routes for Agent Learning Feedback Loop system
# ABOUTME: REST API endpoints for machine learning-driven agent routing optimization

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from core.dependencies import get_databases, DatabaseDependencies
from services.agent_learning_engine import (
    AgentLearningEngine, 
    TaskOutcome, 
    TaskComplexity,
    AgentSpecialization,
    RoutingOptimization,
    SuccessPrediction
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/learning", tags=["agent-learning"])

# Pydantic models for API
class TaskOutcomeRequest(BaseModel):
    """Request model for recording task outcomes"""
    routing_id: str = Field(..., description="Routing decision identifier")
    agent_id: UUID = Field(..., description="Agent that executed the task")
    task_type: str = Field(..., description="Type of task executed")
    complexity: str = Field(..., description="Task complexity: simple, moderate, complex, critical")
    success_score: float = Field(..., ge=0.0, le=1.0, description="Task success score (0.0-1.0)")
    completion_time: float = Field(..., gt=0.0, description="Task completion time in seconds")
    quality_metrics: Dict[str, float] = Field(default={}, description="Quality metrics dictionary")
    user_satisfaction: Optional[float] = Field(None, ge=0.0, le=5.0, description="User satisfaction rating (0-5)")
    error_count: int = Field(default=0, ge=0, description="Number of errors encountered")
    retry_attempts: int = Field(default=0, ge=0, description="Number of retry attempts")
    cost_actual: Optional[float] = Field(None, ge=0.0, description="Actual cost in cents")
    context_metadata: Dict[str, Any] = Field(default={}, description="Additional context metadata")

class SuccessPredictionRequest(BaseModel):
    """Request model for success probability prediction"""
    agent_id: UUID = Field(..., description="Agent to evaluate")
    task_type: str = Field(..., description="Type of task")
    complexity: str = Field(..., description="Task complexity: simple, moderate, complex, critical")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10)")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    context_factors: Dict[str, Any] = Field(default={}, description="Additional context factors")

class SpecializationResponse(BaseModel):
    """Response model for agent specializations"""
    agent_id: str
    specialization_type: str
    task_types: List[str]
    complexity_preferences: List[str]
    confidence_score: float
    performance_advantage: float
    sample_size: int
    discovered_at: datetime
    last_validated: datetime

class OptimizationResponse(BaseModel):
    """Response model for routing optimizations"""
    optimization_id: str
    performance_improvement: float
    confidence_interval: List[float]  # [lower, upper]
    optimization_method: str
    applied_at: datetime
    validation_period_days: int
    agent_count: int
    task_types_affected: List[str]

class PredictionResponse(BaseModel):
    """Response model for success predictions"""
    agent_id: str
    task_type: str
    complexity: str
    predicted_success_rate: float
    confidence_interval: List[float]  # [lower, upper]
    risk_factors: List[str]
    prediction_model: str
    prediction_timestamp: datetime

class LearningAnalyticsResponse(BaseModel):
    """Response model for learning analytics"""
    learning_metrics: Dict[str, Any]
    recent_performance_trends: List[Dict[str, Any]]
    active_specializations: List[Dict[str, Any]]
    optimization_history: List[Dict[str, Any]]
    prediction_accuracy_trends: List[Dict[str, Any]]
    system_stats: Dict[str, Any]

# Route handlers
@router.post("/record-outcome")
async def record_task_outcome(
    outcome: TaskOutcomeRequest,
    background_tasks: BackgroundTasks,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Record task outcome for machine learning optimization"""
    try:
        learning_engine = AgentLearningEngine(databases)
        await learning_engine.initialize()
        
        # Convert request to TaskOutcome
        task_outcome = TaskOutcome(
            routing_id=outcome.routing_id,
            agent_id=outcome.agent_id,
            task_type=outcome.task_type,
            complexity=TaskComplexity(outcome.complexity),
            success_score=outcome.success_score,
            completion_time=outcome.completion_time,
            quality_metrics=outcome.quality_metrics,
            user_satisfaction=outcome.user_satisfaction,
            error_count=outcome.error_count,
            retry_attempts=outcome.retry_attempts,
            cost_actual=outcome.cost_actual,
            context_metadata=outcome.context_metadata
        )
        
        # Track outcome for learning
        await learning_engine.track_task_outcome(outcome.routing_id, task_outcome)
        
        return {
            'success': True,
            'message': 'Task outcome recorded successfully',
            'routing_id': outcome.routing_id,
            'learning_triggered': True,
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Recording task outcome failed", error=str(e), routing_id=outcome.routing_id)
        raise HTTPException(status_code=500, detail=f"Recording task outcome failed: {str(e)}")
    finally:
        if 'learning_engine' in locals():
            await learning_engine.cleanup()

@router.get("/specializations", response_model=List[SpecializationResponse])
async def get_agent_specializations(
    agent_id: Optional[UUID] = Query(None, description="Filter by specific agent"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get discovered agent specializations"""
    try:
        learning_engine = AgentLearningEngine(databases)
        await learning_engine.initialize()
        
        specializations_dict = await learning_engine.analyze_agent_specializations()
        
        # Convert to response format
        specializations = []
        async with databases.postgres.acquire() as conn:
            query = """
                SELECT * FROM agent_specializations 
                WHERE is_active = true AND confidence_score >= $1
            """
            params = [min_confidence]
            
            if agent_id:
                query += " AND agent_id = $2"
                params.append(agent_id)
            
            query += " ORDER BY confidence_score DESC"
            
            spec_records = await conn.fetch(query, *params)
            
            for record in spec_records:
                specializations.append(SpecializationResponse(
                    agent_id=str(record['agent_id']),
                    specialization_type=record['specialization_type'],
                    task_types=record['task_types'],
                    complexity_preferences=record['complexity_preferences'],
                    confidence_score=record['confidence_score'],
                    performance_advantage=record['performance_advantage'],
                    sample_size=record['sample_size'],
                    discovered_at=record['discovered_at'],
                    last_validated=record['last_validated']
                ))
        
        return specializations
        
    except Exception as e:
        logger.error("Getting specializations failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Getting specializations failed: {str(e)}")
    finally:
        if 'learning_engine' in locals():
            await learning_engine.cleanup()

@router.post("/optimize-routing", response_model=OptimizationResponse)
async def optimize_routing_weights(
    background_tasks: BackgroundTasks,
    force_optimization: bool = Query(False, description="Force optimization even with limited data"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Trigger routing weight optimization"""
    try:
        learning_engine = AgentLearningEngine(databases)
        await learning_engine.initialize()
        
        # Perform optimization
        optimization = await learning_engine.optimize_routing_weights()
        
        # Get additional metadata
        async with databases.postgres.acquire() as conn:
            agent_count = await conn.fetchval("""
                SELECT COUNT(DISTINCT jsonb_object_keys(agent_weights))
                FROM routing_optimizations 
                WHERE optimization_version = $1
            """, optimization.optimization_id)
            
            task_types = await conn.fetchval("""
                SELECT ARRAY_AGG(DISTINCT task_type)
                FROM agent_task_outcomes
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
        
        return OptimizationResponse(
            optimization_id=optimization.optimization_id,
            performance_improvement=optimization.performance_improvement,
            confidence_interval=[optimization.confidence_interval[0], optimization.confidence_interval[1]],
            optimization_method=optimization.optimization_method,
            applied_at=optimization.applied_at,
            validation_period_days=optimization.validation_period_days,
            agent_count=agent_count or 0,
            task_types_affected=task_types or []
        )
        
    except Exception as e:
        logger.error("Routing optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Routing optimization failed: {str(e)}")
    finally:
        if 'learning_engine' in locals():
            await learning_engine.cleanup()

@router.post("/predict-success", response_model=PredictionResponse)
async def predict_task_success(
    request: SuccessPredictionRequest,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Predict success probability for agent-task combination"""
    try:
        learning_engine = AgentLearningEngine(databases)
        await learning_engine.initialize()
        
        # Create task context for prediction
        from services.context_aware_router import TaskContext
        
        task_context = TaskContext(
            task_type=request.task_type,
            complexity=TaskComplexity(request.complexity),
            priority=request.priority,
            deadline=request.deadline,
            metadata=request.context_factors
        )
        
        # Generate prediction
        prediction = await learning_engine.predict_task_success_probability(task_context, request.agent_id)
        
        return PredictionResponse(
            agent_id=str(prediction.agent_id),
            task_type=prediction.task_type,
            complexity=prediction.complexity.value,
            predicted_success_rate=prediction.predicted_success_rate,
            confidence_interval=[prediction.confidence_interval[0], prediction.confidence_interval[1]],
            risk_factors=prediction.risk_factors,
            prediction_model=prediction.prediction_model,
            prediction_timestamp=prediction.prediction_timestamp
        )
        
    except Exception as e:
        logger.error("Success prediction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Success prediction failed: {str(e)}")
    finally:
        if 'learning_engine' in locals():
            await learning_engine.cleanup()

@router.get("/analytics", response_model=LearningAnalyticsResponse)
async def get_learning_analytics(
    hours: int = Query(24, ge=1, le=168, description="Hours of analytics data (1-168)"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get comprehensive learning system analytics"""
    try:
        learning_engine = AgentLearningEngine(databases)
        await learning_engine.initialize()
        
        analytics = await learning_engine.get_learning_analytics()
        
        return LearningAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error("Learning analytics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Learning analytics retrieval failed: {str(e)}")
    finally:
        if 'learning_engine' in locals():
            await learning_engine.cleanup()

@router.get("/performance-trends/{agent_id}")
async def get_agent_learning_trends(
    agent_id: UUID,
    hours: int = Query(168, ge=1, le=720, description="Hours of trend data (1-720)"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get learning performance trends for a specific agent"""
    try:
        async with databases.postgres.acquire() as conn:
            # Get success rate trends over time
            success_trends = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    task_type,
                    complexity,
                    AVG(success_score) as avg_success,
                    COUNT(*) as sample_size,
                    STDDEV(success_score) as std_success
                FROM agent_task_outcomes
                WHERE agent_id = $1 
                    AND created_at >= NOW() - INTERVAL '%s hours'
                GROUP BY DATE_TRUNC('hour', created_at), task_type, complexity
                ORDER BY hour ASC
            """ % hours, agent_id)
            
            # Get specialization discovery history
            specialization_history = await conn.fetch("""
                SELECT 
                    specialization_type,
                    confidence_score,
                    performance_advantage,
                    discovered_at,
                    last_validated
                FROM agent_specializations
                WHERE agent_id = $1
                    AND discovered_at >= NOW() - INTERVAL '%s hours'
                ORDER BY discovered_at ASC
            """ % hours, agent_id)
            
            # Get prediction accuracy for this agent
            prediction_accuracy = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('day', created_at) as day,
                    task_type,
                    complexity,
                    AVG(prediction_accuracy) as avg_accuracy,
                    COUNT(*) as prediction_count
                FROM success_predictions
                WHERE agent_id = $1 
                    AND prediction_accuracy IS NOT NULL
                    AND created_at >= NOW() - INTERVAL '%s hours'
                GROUP BY DATE_TRUNC('day', created_at), task_type, complexity
                ORDER BY day ASC
            """ % hours, agent_id)
        
        return {
            'success': True,
            'agent_id': str(agent_id),
            'learning_trends': {
                'success_rate_trends': [dict(trend) for trend in success_trends],
                'specialization_history': [dict(spec) for spec in specialization_history],
                'prediction_accuracy': [dict(pred) for pred in prediction_accuracy]
            },
            'period_hours': hours,
            'generated_at': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Learning trends retrieval failed", error=str(e), agent_id=str(agent_id))
        raise HTTPException(status_code=500, detail=f"Learning trends retrieval failed: {str(e)}")

@router.post("/validate-predictions")
async def validate_prediction_models(
    background_tasks: BackgroundTasks,
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Manually trigger prediction model validation"""
    try:
        learning_engine = AgentLearningEngine(databases)
        await learning_engine.initialize()
        
        # Trigger validation in background
        background_tasks.add_task(learning_engine._validate_predictions)
        
        return {
            'success': True,
            'message': 'Prediction validation triggered',
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Prediction validation trigger failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Prediction validation failed: {str(e)}")

@router.get("/optimization-history")
async def get_optimization_history(
    limit: int = Query(10, ge=1, le=50, description="Number of optimizations to return"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get routing optimization history"""
    try:
        async with databases.postgres.acquire() as conn:
            optimizations = await conn.fetch("""
                SELECT 
                    optimization_version as optimization_id,
                    performance_improvement,
                    confidence_lower,
                    confidence_upper,
                    optimization_method,
                    applied_at,
                    validation_period_days,
                    is_active,
                    validation_results
                FROM routing_optimizations
                ORDER BY applied_at DESC
                LIMIT $1
            """, limit)
        
        return {
            'success': True,
            'optimizations': [dict(opt) for opt in optimizations],
            'total_count': len(optimizations)
        }
        
    except Exception as e:
        logger.error("Optimization history retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Optimization history retrieval failed: {str(e)}")

@router.get("/learning-metrics")
async def get_learning_metrics(
    metric_name: Optional[str] = Query(None, description="Filter by specific metric name"),
    hours: int = Query(24, ge=1, le=168, description="Hours of metrics data"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Get detailed learning system metrics"""
    try:
        async with databases.postgres.acquire() as conn:
            query = """
                SELECT 
                    metric_name,
                    metric_value,
                    metric_metadata,
                    measurement_timestamp
                FROM learning_metrics
                WHERE measurement_timestamp >= NOW() - INTERVAL '%s hours'
            """ % hours
            
            params = []
            if metric_name:
                query += " AND metric_name = $1"
                params.append(metric_name)
            
            query += " ORDER BY measurement_timestamp DESC"
            
            metrics = await conn.fetch(query, *params)
        
        return {
            'success': True,
            'metrics': [dict(metric) for metric in metrics],
            'period_hours': hours,
            'filtered_by': metric_name
        }
        
    except Exception as e:
        logger.error("Learning metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Learning metrics retrieval failed: {str(e)}")

@router.post("/reset-learning-state")
async def reset_learning_state(
    confirm: bool = Query(False, description="Confirm reset action"),
    backup_data: bool = Query(True, description="Backup existing data before reset"),
    databases: DatabaseDependencies = Depends(get_databases)
):
    """Reset learning system state (use with caution)"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Reset must be confirmed with confirm=true parameter")
    
    try:
        async with databases.postgres.acquire() as conn:
            if backup_data:
                # Create backup tables
                backup_timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                
                await conn.execute(f"""
                    CREATE TABLE agent_task_outcomes_backup_{backup_timestamp} 
                    AS SELECT * FROM agent_task_outcomes
                """)
                
                await conn.execute(f"""
                    CREATE TABLE agent_specializations_backup_{backup_timestamp}
                    AS SELECT * FROM agent_specializations
                """)
                
                await conn.execute(f"""
                    CREATE TABLE routing_optimizations_backup_{backup_timestamp}
                    AS SELECT * FROM routing_optimizations
                """)
            
            # Reset learning tables
            await conn.execute("DELETE FROM success_predictions")
            await conn.execute("DELETE FROM learning_metrics")
            await conn.execute("UPDATE agent_specializations SET is_active = false")
            await conn.execute("UPDATE routing_optimizations SET is_active = false")
        
        return {
            'success': True,
            'message': 'Learning state reset successfully',
            'backup_created': backup_data,
            'reset_timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Learning state reset failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Learning state reset failed: {str(e)}")

@router.get("/health")
async def learning_health_check():
    """Health check endpoint for learning system"""
    return {
        'status': 'healthy',
        'service': 'Agent Learning Feedback Loop',
        'version': '1.0.0',
        'capabilities': [
            'outcome_tracking',
            'specialization_detection', 
            'routing_optimization',
            'success_prediction',
            'performance_analytics'
        ],
        'timestamp': datetime.utcnow()
    }