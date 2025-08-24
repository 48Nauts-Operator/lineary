# ABOUTME: Intelligent Routing Service - Integration layer between Context-Aware Router and Learning Engine
# ABOUTME: Enhanced routing with machine learning-driven optimizations and continuous improvement

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass
import structlog

from .base_service import BaseService
from .context_aware_router import (
    ContextAwareAgentRouter, TaskContext, TaskComplexity, 
    AgentSelection, RoutingResult, PerformanceScore
)
from .agent_learning_engine import AgentLearningEngine, TaskOutcome, SuccessPrediction
from ..core.dependencies import DatabaseDependencies

logger = structlog.get_logger(__name__)

@dataclass
class EnhancedRoutingResult:
    """Enhanced routing result with learning insights"""
    routing_result: RoutingResult
    success_prediction: Optional[SuccessPrediction]
    learning_insights: Dict[str, Any]
    optimization_confidence: float
    alternative_agents: List[Dict[str, Any]]
    routing_explanation: str

class IntelligentRoutingService(BaseService):
    """Intelligent Routing Service - ML-enhanced agent routing with continuous learning"""
    
    def __init__(self, databases: DatabaseDependencies):
        super().__init__(databases)
        self.context_router = ContextAwareAgentRouter(databases)
        self.learning_engine = AgentLearningEngine(databases)
        
        # Integration settings
        self.learning_enabled = True
        self.prediction_threshold = 0.6  # Minimum predicted success rate
        self.optimization_weight = 0.3   # Weight of learning optimizations vs base routing
        
        # Routing cache for performance
        self.routing_cache: Dict[str, EnhancedRoutingResult] = {}
        self.cache_ttl = 300  # 5 minutes

    async def initialize(self):
        """Initialize the intelligent routing service"""
        await super().initialize()
        await self.context_router.initialize()
        await self.learning_engine.initialize()
        
        logger.info("Intelligent Routing Service initialized", 
                   learning_enabled=self.learning_enabled,
                   prediction_threshold=self.prediction_threshold)

    async def route_task_with_learning(self, task: TaskContext, 
                                     enable_prediction: bool = True,
                                     enable_optimization: bool = True) -> EnhancedRoutingResult:
        """Route task with machine learning enhancements"""
        routing_id = str(uuid4())
        start_time = time.time()
        
        try:
            logger.info("Starting intelligent routing",
                       task_type=task.task_type,
                       complexity=task.complexity.value,
                       routing_id=routing_id)
            
            # Step 1: Get base routing recommendation
            base_result = await self.context_router.select_optimal_agent(task)
            
            if not base_result.success:
                return EnhancedRoutingResult(
                    routing_result=base_result,
                    success_prediction=None,
                    learning_insights={},
                    optimization_confidence=0.0,
                    alternative_agents=[],
                    routing_explanation="Base routing failed"
                )
            
            # Step 2: Apply learning optimizations if enabled
            optimized_selection = base_result.agent_selection
            learning_insights = {}
            optimization_confidence = 0.0
            
            if enable_optimization and self.learning_enabled:
                optimization_result = await self._apply_learning_optimizations(
                    task, base_result, routing_id)
                if optimization_result:
                    optimized_selection = optimization_result['selection']
                    learning_insights = optimization_result['insights']
                    optimization_confidence = optimization_result['confidence']
            
            # Step 3: Generate success prediction if enabled
            success_prediction = None
            if enable_prediction and self.learning_enabled:
                try:
                    success_prediction = await self.learning_engine.predict_task_success_probability(
                        task, optimized_selection.agent_id)
                    
                    # Check if prediction meets threshold
                    if success_prediction.predicted_success_rate < self.prediction_threshold:
                        logger.warning("Low success prediction, considering alternatives",
                                     predicted_rate=success_prediction.predicted_success_rate,
                                     agent_id=str(optimized_selection.agent_id))
                        
                        # Try to find better alternative
                        alternative_result = await self._find_alternative_agent(task, optimized_selection.agent_id)
                        if alternative_result:
                            optimized_selection = alternative_result['selection']
                            success_prediction = alternative_result['prediction']
                            learning_insights['alternative_selected'] = True
                
                except Exception as e:
                    logger.warning("Success prediction failed", error=str(e))
            
            # Step 4: Generate alternative agents for fallback
            alternative_agents = await self._generate_alternative_agents(task, optimized_selection.agent_id)
            
            # Step 5: Create routing explanation
            routing_explanation = self._generate_routing_explanation(
                base_result, optimized_selection, success_prediction, learning_insights)
            
            # Update routing result with optimized selection
            enhanced_result = RoutingResult(
                success=True,
                agent_selection=optimized_selection,
                routing_time_ms=(time.time() - start_time) * 1000,
                fallback_used=base_result.fallback_used,
                retry_count=base_result.retry_count
            )
            
            # Create enhanced routing result
            enhanced_routing = EnhancedRoutingResult(
                routing_result=enhanced_result,
                success_prediction=success_prediction,
                learning_insights=learning_insights,
                optimization_confidence=optimization_confidence,
                alternative_agents=alternative_agents,
                routing_explanation=routing_explanation
            )
            
            # Cache result
            cache_key = f"{task.task_type}_{task.complexity.value}_{hash(str(task.metadata))}"
            self.routing_cache[cache_key] = enhanced_routing
            
            logger.info("Intelligent routing completed",
                       routing_id=routing_id,
                       selected_agent=optimized_selection.agent_name,
                       predicted_success=success_prediction.predicted_success_rate if success_prediction else None,
                       optimization_applied=optimization_confidence > 0.0)
            
            return enhanced_routing
            
        except Exception as e:
            routing_time = (time.time() - start_time) * 1000
            logger.error("Intelligent routing failed", error=str(e), routing_id=routing_id)
            
            # Return base result as fallback
            return EnhancedRoutingResult(
                routing_result=RoutingResult(
                    success=False,
                    agent_selection=None,
                    routing_time_ms=routing_time,
                    error_message=str(e)
                ),
                success_prediction=None,
                learning_insights={'error': str(e)},
                optimization_confidence=0.0,
                alternative_agents=[],
                routing_explanation=f"Routing failed: {str(e)}"
            )

    async def _apply_learning_optimizations(self, task: TaskContext, base_result: RoutingResult, 
                                          routing_id: str) -> Optional[Dict[str, Any]]:
        """Apply learning engine optimizations to base routing result"""
        try:
            # Get agent specializations
            specializations = await self.learning_engine.analyze_agent_specializations()
            
            # Check if current selection has strong specialization for this task
            selected_agent_id = str(base_result.agent_selection.agent_id)
            agent_specializations = specializations.get(selected_agent_id, [])
            
            # Look for better specialized agents
            better_agent = None
            best_advantage = 0.0
            
            for agent_id, agent_specs in specializations.items():
                for spec_desc in agent_specs:
                    if task.task_type in spec_desc.lower():
                        # This agent has specialization in the task type
                        # Get specialization details from database
                        specialization_data = await self._get_specialization_details(
                            UUID(agent_id), task.task_type, task.complexity)
                        
                        if specialization_data and specialization_data['performance_advantage'] > best_advantage:
                            # Check if this agent is available and healthy
                            if await self._check_agent_availability(UUID(agent_id)):
                                better_agent = UUID(agent_id)
                                best_advantage = specialization_data['performance_advantage']
            
            if better_agent and better_agent != base_result.agent_selection.agent_id:
                # Create new selection with better agent
                optimized_selection = AgentSelection(
                    agent_id=better_agent,
                    agent_name=f"Specialized Agent {str(better_agent)[-8:]}",
                    confidence_score=min(1.0, base_result.agent_selection.confidence_score + best_advantage),
                    selection_reason=f"ML optimization: {best_advantage:.2%} performance advantage for {task.task_type}",
                    fallback_agents=base_result.agent_selection.fallback_agents,
                    estimated_completion_time=base_result.agent_selection.estimated_completion_time * (1.0 - best_advantage * 0.3),
                    cost_estimate=base_result.agent_selection.cost_estimate,
                    selection_metadata={
                        'optimization_applied': True,
                        'performance_advantage': best_advantage,
                        'optimization_type': 'specialization_match'
                    }
                )
                
                return {
                    'selection': optimized_selection,
                    'insights': {
                        'optimization_type': 'specialization_match',
                        'performance_advantage': best_advantage,
                        'original_agent': str(base_result.agent_selection.agent_id),
                        'optimized_agent': str(better_agent)
                    },
                    'confidence': min(1.0, best_advantage * 2.0)  # Confidence based on advantage
                }
            
            # If no better specialized agent found, apply routing weight optimizations
            return await self._apply_routing_weight_optimization(task, base_result)
            
        except Exception as e:
            logger.warning("Learning optimization failed", error=str(e))
            return None

    async def _get_specialization_details(self, agent_id: UUID, task_type: str, complexity: TaskComplexity) -> Optional[Dict[str, Any]]:
        """Get specialization details for an agent and task type"""
        async with self.postgres.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT performance_advantage, confidence_score, sample_size
                FROM agent_specializations
                WHERE agent_id = $1 
                  AND $2 = ANY(task_types)
                  AND $3 = ANY(complexity_preferences)
                  AND is_active = true
                ORDER BY confidence_score DESC
                LIMIT 1
            """, agent_id, task_type, complexity.value)
            
            return dict(result) if result else None

    async def _check_agent_availability(self, agent_id: UUID) -> bool:
        """Check if agent is available and healthy"""
        try:
            health_statuses = await self.context_router.monitor_agent_health()
            
            for health in health_statuses:
                if health.agent_id == agent_id:
                    return (health.status == 'active' and 
                           health.load_level.value != 'overloaded' and
                           health.predictive_failure_score < 0.7)
            
            return False  # Agent not found in health status
        except:
            return True  # Assume available if health check fails

    async def _apply_routing_weight_optimization(self, task: TaskContext, base_result: RoutingResult) -> Optional[Dict[str, Any]]:
        """Apply routing weight-based optimizations"""
        try:
            # Get current routing weights from learning engine
            agent_id_str = str(base_result.agent_selection.agent_id)
            task_key = f"{task.task_type}_{task.complexity.value}"
            
            current_weight = self.learning_engine.routing_weights.get(agent_id_str, {}).get(task_key, 0.5)
            
            # If weight is significantly low, try to find better alternative
            if current_weight < 0.4:  # Below average performance
                alternatives = await self._find_high_weight_alternatives(task)
                
                if alternatives:
                    best_alternative = alternatives[0]
                    optimized_selection = AgentSelection(
                        agent_id=best_alternative['agent_id'],
                        agent_name=best_alternative['agent_name'],
                        confidence_score=best_alternative['weight'],
                        selection_reason=f"ML optimization: Higher success probability ({best_alternative['weight']:.2%})",
                        fallback_agents=base_result.agent_selection.fallback_agents,
                        estimated_completion_time=base_result.agent_selection.estimated_completion_time,
                        cost_estimate=base_result.agent_selection.cost_estimate,
                        selection_metadata={
                            'optimization_applied': True,
                            'weight_improvement': best_alternative['weight'] - current_weight,
                            'optimization_type': 'routing_weight'
                        }
                    )
                    
                    return {
                        'selection': optimized_selection,
                        'insights': {
                            'optimization_type': 'routing_weight',
                            'weight_improvement': best_alternative['weight'] - current_weight,
                            'original_weight': current_weight,
                            'optimized_weight': best_alternative['weight']
                        },
                        'confidence': min(1.0, (best_alternative['weight'] - current_weight) * 2.0)
                    }
            
            return None  # No optimization applied
            
        except Exception as e:
            logger.warning("Routing weight optimization failed", error=str(e))
            return None

    async def _find_high_weight_alternatives(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Find agents with high routing weights for the given task"""
        task_key = f"{task.task_type}_{task.complexity.value}"
        alternatives = []
        
        for agent_id_str, task_weights in self.learning_engine.routing_weights.items():
            weight = task_weights.get(task_key, 0.0)
            if weight > 0.6:  # High performance threshold
                try:
                    agent_id = UUID(agent_id_str)
                    if await self._check_agent_availability(agent_id):
                        alternatives.append({
                            'agent_id': agent_id,
                            'agent_name': f"Agent {agent_id_str[-8:]}",
                            'weight': weight
                        })
                except:
                    continue
        
        # Sort by weight descending
        alternatives.sort(key=lambda x: x['weight'], reverse=True)
        return alternatives[:3]  # Top 3 alternatives

    async def _find_alternative_agent(self, task: TaskContext, current_agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Find alternative agent when current selection has low success prediction"""
        try:
            # Get all available agents and their predictions
            alternatives = []
            
            async with self.postgres.acquire() as conn:
                agents = await conn.fetch("""
                    SELECT id, name FROM agents 
                    WHERE status = 'active' AND id != $1
                    LIMIT 10
                """, current_agent_id)
            
            for agent in agents:
                try:
                    prediction = await self.learning_engine.predict_task_success_probability(
                        task, agent['id'])
                    
                    if prediction.predicted_success_rate > self.prediction_threshold:
                        alternatives.append({
                            'agent_id': agent['id'],
                            'agent_name': agent['name'],
                            'prediction': prediction
                        })
                except:
                    continue
            
            if alternatives:
                # Sort by predicted success rate
                alternatives.sort(key=lambda x: x['prediction'].predicted_success_rate, reverse=True)
                best_alternative = alternatives[0]
                
                # Create new selection
                selection = AgentSelection(
                    agent_id=best_alternative['agent_id'],
                    agent_name=best_alternative['agent_name'],
                    confidence_score=best_alternative['prediction'].predicted_success_rate,
                    selection_reason=f"Alternative selected: {best_alternative['prediction'].predicted_success_rate:.2%} success rate",
                    fallback_agents=[],
                    estimated_completion_time=30.0,  # Default estimate
                    cost_estimate=10,  # Default estimate
                    selection_metadata={'alternative_selection': True}
                )
                
                return {
                    'selection': selection,
                    'prediction': best_alternative['prediction']
                }
            
            return None
            
        except Exception as e:
            logger.warning("Alternative agent search failed", error=str(e))
            return None

    async def _generate_alternative_agents(self, task: TaskContext, current_agent_id: UUID) -> List[Dict[str, Any]]:
        """Generate list of alternative agents for fallback"""
        alternatives = []
        
        try:
            # Get specialized agents for this task type
            specializations = await self.learning_engine.analyze_agent_specializations()
            
            for agent_id_str, specs in specializations.items():
                agent_id = UUID(agent_id_str)
                if agent_id != current_agent_id:
                    for spec in specs:
                        if task.task_type.lower() in spec.lower():
                            alternatives.append({
                                'agent_id': agent_id_str,
                                'specialization': spec,
                                'type': 'specialized'
                            })
                            break
            
            # Get high-performance agents from routing weights
            task_key = f"{task.task_type}_{task.complexity.value}"
            for agent_id_str, task_weights in self.learning_engine.routing_weights.items():
                if UUID(agent_id_str) != current_agent_id:
                    weight = task_weights.get(task_key, 0.0)
                    if weight > 0.7:
                        alternatives.append({
                            'agent_id': agent_id_str,
                            'performance_weight': weight,
                            'type': 'high_performance'
                        })
            
            # Limit and deduplicate
            unique_agents = {}
            for alt in alternatives:
                if alt['agent_id'] not in unique_agents:
                    unique_agents[alt['agent_id']] = alt
            
            return list(unique_agents.values())[:5]  # Top 5 alternatives
            
        except Exception as e:
            logger.warning("Alternative agents generation failed", error=str(e))
            return []

    def _generate_routing_explanation(self, base_result: RoutingResult, 
                                    optimized_selection: AgentSelection,
                                    success_prediction: Optional[SuccessPrediction],
                                    learning_insights: Dict[str, Any]) -> str:
        """Generate human-readable routing explanation"""
        explanation_parts = []
        
        # Base selection reason
        explanation_parts.append(f"Selected {optimized_selection.agent_name}")
        explanation_parts.append(f"(confidence: {optimized_selection.confidence_score:.1%})")
        
        # Optimization information
        if learning_insights.get('optimization_applied'):
            opt_type = learning_insights.get('optimization_type', 'unknown')
            if opt_type == 'specialization_match':
                advantage = learning_insights.get('performance_advantage', 0)
                explanation_parts.append(f"via ML specialization detection (+{advantage:.1%} advantage)")
            elif opt_type == 'routing_weight':
                improvement = learning_insights.get('weight_improvement', 0)
                explanation_parts.append(f"via routing weight optimization (+{improvement:.1%} success rate)")
        
        # Prediction information
        if success_prediction:
            explanation_parts.append(f"with {success_prediction.predicted_success_rate:.1%} predicted success")
            
            if success_prediction.risk_factors:
                explanation_parts.append(f"(risks: {', '.join(success_prediction.risk_factors[:2])})")
        
        # Alternative selection
        if learning_insights.get('alternative_selected'):
            explanation_parts.append("(alternative due to low success prediction)")
        
        return ". ".join(explanation_parts) + "."

    async def record_task_outcome_with_learning(self, routing_id: str, agent_id: UUID,
                                              task: TaskContext, success: bool,
                                              completion_time: float, quality_metrics: Dict[str, float] = None,
                                              user_satisfaction: float = None,
                                              error_count: int = 0, cost_actual: float = None) -> None:
        """Record task outcome and trigger learning updates"""
        try:
            # Create task outcome
            success_score = 1.0 if success else 0.0
            
            # Adjust success score based on quality metrics
            if quality_metrics:
                avg_quality = sum(quality_metrics.values()) / len(quality_metrics)
                success_score = (success_score + avg_quality) / 2.0
            
            task_outcome = TaskOutcome(
                routing_id=routing_id,
                agent_id=agent_id,
                task_type=task.task_type,
                complexity=task.complexity,
                success_score=success_score,
                completion_time=completion_time,
                quality_metrics=quality_metrics or {},
                user_satisfaction=user_satisfaction,
                error_count=error_count,
                retry_attempts=0,  # Could be tracked separately
                cost_actual=cost_actual
            )
            
            # Track outcome in learning engine
            await self.learning_engine.track_task_outcome(routing_id, task_outcome)
            
            # Also record in context router for backwards compatibility
            await self.context_router.record_execution_result(
                agent_id, task, success, completion_time * 1000, int(cost_actual) if cost_actual else None)
            
            logger.info("Task outcome recorded with learning",
                       routing_id=routing_id,
                       success_score=success_score,
                       agent_id=str(agent_id))
            
        except Exception as e:
            logger.error("Failed to record task outcome with learning", error=str(e), routing_id=routing_id)

    async def get_intelligent_routing_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive routing analytics with learning insights"""
        try:
            # Get base routing analytics
            base_analytics = await self.context_router.get_routing_analytics(hours)
            
            # Get learning analytics
            learning_analytics = await self.learning_engine.get_learning_analytics()
            
            # Combine and enhance
            combined_analytics = {
                'base_routing': base_analytics,
                'learning_system': learning_analytics,
                'integration_metrics': {
                    'learning_enabled': self.learning_enabled,
                    'optimization_weight': self.optimization_weight,
                    'prediction_threshold': self.prediction_threshold,
                    'cache_size': len(self.routing_cache)
                },
                'performance_improvements': await self._calculate_performance_improvements(hours)
            }
            
            return combined_analytics
            
        except Exception as e:
            logger.error("Failed to get intelligent routing analytics", error=str(e))
            return {}

    async def _calculate_performance_improvements(self, hours: int) -> Dict[str, Any]:
        """Calculate performance improvements from learning integration"""
        try:
            async with self.postgres.acquire() as conn:
                # Compare performance before/after learning optimizations
                with_learning = await conn.fetchrow("""
                    SELECT AVG(success_score) as avg_success
                    FROM agent_task_outcomes
                    WHERE created_at >= NOW() - INTERVAL '%s hours'
                      AND context_metadata->>'optimization_applied' = 'true'
                """ % hours)
                
                without_learning = await conn.fetchrow("""
                    SELECT AVG(success_score) as avg_success
                    FROM agent_task_outcomes
                    WHERE created_at >= NOW() - INTERVAL '%s hours'
                      AND (context_metadata->>'optimization_applied' IS NULL 
                           OR context_metadata->>'optimization_applied' = 'false')
                """ % hours)
                
                if with_learning['avg_success'] and without_learning['avg_success']:
                    improvement = (with_learning['avg_success'] - without_learning['avg_success']) / without_learning['avg_success'] * 100
                else:
                    improvement = 0.0
                
                return {
                    'success_rate_improvement_percent': improvement,
                    'with_learning_success_rate': with_learning['avg_success'] or 0.0,
                    'without_learning_success_rate': without_learning['avg_success'] or 0.0
                }
            
        except Exception as e:
            logger.warning("Performance improvement calculation failed", error=str(e))
            return {}

    async def cleanup(self):
        """Cleanup intelligent routing service"""
        self.routing_cache.clear()
        
        await self.context_router.cleanup()
        await self.learning_engine.cleanup()
        await super().cleanup()
        
        logger.info("Intelligent Routing Service cleaned up")