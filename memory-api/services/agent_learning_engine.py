# ABOUTME: Agent Learning Feedback Loop - Intelligent system for progressive agent routing optimization
# ABOUTME: Machine learning engine that learns from task outcomes and improves agent selection

import asyncio
import time
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import structlog
from collections import defaultdict, deque

from .base_service import BaseService
from .context_aware_router import TaskContext, TaskComplexity, AgentSelection, PerformanceScore
from ..core.dependencies import DatabaseDependencies
from ..core.config import get_settings

logger = structlog.get_logger(__name__)

@dataclass
class TaskOutcome:
    """Task execution outcome for learning"""
    routing_id: str
    agent_id: UUID
    task_type: str
    complexity: TaskComplexity
    success_score: float  # 0.0-1.0
    completion_time: float  # seconds
    quality_metrics: Dict[str, float]
    user_satisfaction: Optional[float] = None
    error_count: int = 0
    retry_attempts: int = 0
    cost_actual: Optional[float] = None
    timestamp: datetime = None
    context_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.context_metadata is None:
            self.context_metadata = {}

@dataclass
class AgentSpecialization:
    """Detected agent specialization pattern"""
    agent_id: UUID
    specialization_type: str
    task_types: List[str]
    complexity_preferences: List[TaskComplexity]
    confidence_score: float  # 0.0-1.0
    performance_advantage: float  # Performance gain over average
    sample_size: int
    discovered_at: datetime
    last_validated: datetime

@dataclass
class RoutingOptimization:
    """Routing weight optimization result"""
    optimization_id: str
    agent_weights: Dict[str, Dict[str, float]]  # agent_id -> task_type -> weight
    performance_improvement: float  # Expected improvement percentage
    confidence_interval: Tuple[float, float]
    optimization_method: str
    applied_at: datetime
    validation_period_days: int = 7

@dataclass
class SuccessPrediction:
    """Success probability prediction for agent-task combination"""
    agent_id: UUID
    task_type: str
    complexity: TaskComplexity
    predicted_success_rate: float  # 0.0-1.0
    confidence_interval: Tuple[float, float]
    risk_factors: List[str]
    prediction_model: str
    prediction_timestamp: datetime

class OptimizationMethod(Enum):
    """Optimization algorithm methods"""
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GRADIENT_DESCENT = "gradient_descent"
    GENETIC_ALGORITHM = "genetic_algorithm"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    ENSEMBLE_METHOD = "ensemble_method"

class AgentLearningEngine(BaseService):
    """Agent Learning Feedback Loop - Core ML engine for routing optimization"""
    
    def __init__(self, databases: DatabaseDependencies):
        super().__init__(databases)
        self.settings = get_settings()
        
        # Learning state
        self.outcome_history: deque = deque(maxlen=10000)  # Recent outcomes for real-time learning
        self.agent_specializations: Dict[str, AgentSpecialization] = {}
        self.routing_weights: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.success_predictors: Dict[str, Any] = {}  # Lightweight ML models
        
        # Performance tracking
        self.performance_baselines: Dict[str, float] = {}
        self.optimization_history: List[RoutingOptimization] = []
        self.learning_metrics: Dict[str, Any] = {
            'total_outcomes_processed': 0,
            'specializations_discovered': 0,
            'optimizations_applied': 0,
            'accuracy_improvements': []
        }
        
        # Real-time adaptation parameters
        self.learning_rate = 0.01
        self.exploration_rate = 0.1
        self.confidence_threshold = 0.8
        self.minimum_sample_size = 20
        
        # Background learning tasks
        self._learning_tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize the learning engine"""
        await super().initialize()
        
        # Initialize learning database tables
        await self._initialize_learning_tables()
        
        # Load existing learning state
        await self._load_learning_state()
        
        # Start background learning processes
        await self._start_learning_tasks()
        
        logger.info("Agent Learning Engine initialized", 
                   learning_rate=self.learning_rate,
                   confidence_threshold=self.confidence_threshold)

    async def _initialize_learning_tables(self):
        """Initialize database tables for learning system"""
        async with self.postgres.acquire() as conn:
            # Task outcomes table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_task_outcomes (
                    outcome_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    routing_id VARCHAR(255) NOT NULL,
                    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    task_type VARCHAR(100) NOT NULL,
                    complexity VARCHAR(20) NOT NULL,
                    success_score FLOAT NOT NULL CHECK (success_score >= 0.0 AND success_score <= 1.0),
                    completion_time_seconds FLOAT NOT NULL,
                    quality_metrics JSONB DEFAULT '{}',
                    user_satisfaction FLOAT CHECK (user_satisfaction >= 0.0 AND user_satisfaction <= 5.0),
                    error_count INTEGER DEFAULT 0,
                    retry_attempts INTEGER DEFAULT 0,
                    cost_actual_cents INTEGER,
                    context_metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    
                    INDEX idx_task_outcomes_agent_id (agent_id),
                    INDEX idx_task_outcomes_task_type (task_type),
                    INDEX idx_task_outcomes_complexity (complexity),
                    INDEX idx_task_outcomes_success_score (success_score),
                    INDEX idx_task_outcomes_created_at (created_at),
                    INDEX idx_task_outcomes_routing_id (routing_id)
                )
            """)
            
            # Agent specializations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_specializations (
                    specialization_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    specialization_type VARCHAR(100) NOT NULL,
                    task_types TEXT[] NOT NULL,
                    complexity_preferences TEXT[] NOT NULL,
                    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
                    performance_advantage FLOAT NOT NULL,
                    sample_size INTEGER NOT NULL,
                    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_validated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT true,
                    validation_history JSONB DEFAULT '{}',
                    
                    UNIQUE (agent_id, specialization_type),
                    INDEX idx_specializations_agent_id (agent_id),
                    INDEX idx_specializations_type (specialization_type),
                    INDEX idx_specializations_confidence (confidence_score),
                    INDEX idx_specializations_discovered_at (discovered_at)
                )
            """)
            
            # Routing optimizations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_optimizations (
                    optimization_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    optimization_version VARCHAR(50) NOT NULL,
                    agent_weights JSONB NOT NULL,
                    performance_improvement FLOAT NOT NULL,
                    confidence_lower FLOAT NOT NULL,
                    confidence_upper FLOAT NOT NULL,
                    optimization_method VARCHAR(50) NOT NULL,
                    sample_size INTEGER NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    validation_period_days INTEGER DEFAULT 7,
                    is_active BOOLEAN DEFAULT true,
                    validation_results JSONB DEFAULT '{}',
                    
                    INDEX idx_routing_optimizations_version (optimization_version),
                    INDEX idx_routing_optimizations_improvement (performance_improvement),
                    INDEX idx_routing_optimizations_applied_at (applied_at),
                    INDEX idx_routing_optimizations_active (is_active)
                )
            """)
            
            # Success predictions table (for validation tracking)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS success_predictions (
                    prediction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    task_type VARCHAR(100) NOT NULL,
                    complexity VARCHAR(20) NOT NULL,
                    predicted_success_rate FLOAT NOT NULL CHECK (predicted_success_rate >= 0.0 AND predicted_success_rate <= 1.0),
                    confidence_lower FLOAT NOT NULL,
                    confidence_upper FLOAT NOT NULL,
                    risk_factors TEXT[],
                    prediction_model VARCHAR(50) NOT NULL,
                    prediction_accuracy FLOAT,
                    actual_outcome_id UUID REFERENCES agent_task_outcomes(outcome_id),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    validated_at TIMESTAMP WITH TIME ZONE,
                    
                    INDEX idx_success_predictions_agent_task (agent_id, task_type, complexity),
                    INDEX idx_success_predictions_accuracy (prediction_accuracy),
                    INDEX idx_success_predictions_created_at (created_at)
                )
            """)
            
            # Learning metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_metrics (
                    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value FLOAT NOT NULL,
                    metric_metadata JSONB DEFAULT '{}',
                    measurement_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    
                    INDEX idx_learning_metrics_name_time (metric_name, measurement_timestamp),
                    INDEX idx_learning_metrics_value (metric_value)
                )
            """)

    async def _load_learning_state(self):
        """Load existing learning state from database"""
        async with self.postgres.acquire() as conn:
            # Load agent specializations
            specializations = await conn.fetch("""
                SELECT * FROM agent_specializations 
                WHERE is_active = true
                ORDER BY confidence_score DESC
            """)
            
            for spec in specializations:
                agent_specialization = AgentSpecialization(
                    agent_id=spec['agent_id'],
                    specialization_type=spec['specialization_type'],
                    task_types=spec['task_types'],
                    complexity_preferences=[TaskComplexity(c) for c in spec['complexity_preferences']],
                    confidence_score=spec['confidence_score'],
                    performance_advantage=spec['performance_advantage'],
                    sample_size=spec['sample_size'],
                    discovered_at=spec['discovered_at'],
                    last_validated=spec['last_validated']
                )
                
                self.agent_specializations[f"{spec['agent_id']}_{spec['specialization_type']}"] = agent_specialization
            
            # Load routing weights from latest optimization
            latest_optimization = await conn.fetchrow("""
                SELECT agent_weights FROM routing_optimizations 
                WHERE is_active = true 
                ORDER BY applied_at DESC 
                LIMIT 1
            """)
            
            if latest_optimization:
                self.routing_weights = defaultdict(lambda: defaultdict(float), latest_optimization['agent_weights'])
            
            # Load recent outcomes for learning
            recent_outcomes = await conn.fetch("""
                SELECT * FROM agent_task_outcomes 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 1000
            """)
            
            for outcome_data in recent_outcomes:
                outcome = TaskOutcome(
                    routing_id=outcome_data['routing_id'],
                    agent_id=outcome_data['agent_id'],
                    task_type=outcome_data['task_type'],
                    complexity=TaskComplexity(outcome_data['complexity']),
                    success_score=outcome_data['success_score'],
                    completion_time=outcome_data['completion_time_seconds'],
                    quality_metrics=outcome_data['quality_metrics'] or {},
                    user_satisfaction=outcome_data['user_satisfaction'],
                    error_count=outcome_data['error_count'],
                    retry_attempts=outcome_data['retry_attempts'],
                    cost_actual=outcome_data['cost_actual_cents'],
                    timestamp=outcome_data['created_at'],
                    context_metadata=outcome_data['context_metadata'] or {}
                )
                self.outcome_history.append(outcome)
        
        logger.info("Learning state loaded", 
                   specializations_count=len(self.agent_specializations),
                   recent_outcomes_count=len(self.outcome_history))

    async def _start_learning_tasks(self):
        """Start background learning processes"""
        # Specialization detection task
        spec_task = asyncio.create_task(self._specialization_detection_loop())
        self._learning_tasks.append(spec_task)
        
        # Routing optimization task
        opt_task = asyncio.create_task(self._routing_optimization_loop())
        self._learning_tasks.append(opt_task)
        
        # Model validation task
        val_task = asyncio.create_task(self._model_validation_loop())
        self._learning_tasks.append(val_task)
        
        # Performance monitoring task
        perf_task = asyncio.create_task(self._performance_monitoring_loop())
        self._learning_tasks.append(perf_task)

    async def track_task_outcome(self, routing_id: str, outcome: TaskOutcome) -> None:
        """Track task outcome for learning and optimization"""
        try:
            # Add to real-time learning history
            outcome.routing_id = routing_id
            self.outcome_history.append(outcome)
            
            # Store in database
            async with self.postgres.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_task_outcomes (
                        routing_id, agent_id, task_type, complexity, success_score,
                        completion_time_seconds, quality_metrics, user_satisfaction,
                        error_count, retry_attempts, cost_actual_cents, context_metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """, routing_id, outcome.agent_id, outcome.task_type, outcome.complexity.value,
                    outcome.success_score, outcome.completion_time, json.dumps(outcome.quality_metrics),
                    outcome.user_satisfaction, outcome.error_count, outcome.retry_attempts,
                    outcome.cost_actual, json.dumps(outcome.context_metadata))
            
            # Update learning metrics
            self.learning_metrics['total_outcomes_processed'] += 1
            
            # Trigger incremental learning
            await self._incremental_learning_update(outcome)
            
            logger.debug("Task outcome tracked", 
                        routing_id=routing_id,
                        agent_id=str(outcome.agent_id),
                        success_score=outcome.success_score)
            
        except Exception as e:
            logger.error("Failed to track task outcome", error=str(e), routing_id=routing_id)

    async def _incremental_learning_update(self, outcome: TaskOutcome):
        """Perform incremental learning updates based on new outcome"""
        agent_id_str = str(outcome.agent_id)
        task_key = f"{outcome.task_type}_{outcome.complexity.value}"
        
        # Update routing weights using exponential moving average
        current_weight = self.routing_weights[agent_id_str][task_key]
        success_signal = outcome.success_score * (2.0 - outcome.completion_time / 30.0)  # Time penalty
        
        # Apply learning rate
        new_weight = current_weight + self.learning_rate * (success_signal - current_weight)
        self.routing_weights[agent_id_str][task_key] = max(0.0, min(1.0, new_weight))
        
        # Check for immediate specialization patterns
        agent_outcomes = [o for o in self.outcome_history if o.agent_id == outcome.agent_id]
        if len(agent_outcomes) >= self.minimum_sample_size:
            await self._detect_specialization_patterns(outcome.agent_id, agent_outcomes)

    async def analyze_agent_specializations(self) -> Dict[str, List[str]]:
        """Analyze and return current agent specializations"""
        specializations_by_agent = defaultdict(list)
        
        for spec_key, specialization in self.agent_specializations.items():
            agent_id_str = str(specialization.agent_id)
            
            # Include only high-confidence specializations
            if specialization.confidence_score >= self.confidence_threshold:
                spec_description = f"{specialization.specialization_type}: {', '.join(specialization.task_types)}"
                specializations_by_agent[agent_id_str].append(spec_description)
        
        # Also analyze recent patterns from outcome history
        recent_patterns = await self._analyze_recent_patterns()
        for agent_id_str, patterns in recent_patterns.items():
            specializations_by_agent[agent_id_str].extend(patterns)
        
        return dict(specializations_by_agent)

    async def _analyze_recent_patterns(self) -> Dict[str, List[str]]:
        """Analyze recent outcome patterns for emerging specializations"""
        patterns = defaultdict(list)
        
        # Group outcomes by agent
        agent_outcomes = defaultdict(list)
        for outcome in self.outcome_history:
            agent_outcomes[str(outcome.agent_id)].append(outcome)
        
        for agent_id_str, outcomes in agent_outcomes.items():
            if len(outcomes) < 10:  # Need minimum sample
                continue
            
            # Analyze task type performance
            task_performance = defaultdict(list)
            for outcome in outcomes:
                task_performance[outcome.task_type].append(outcome.success_score)
            
            # Find high-performance task types
            for task_type, scores in task_performance.items():
                if len(scores) >= 5:  # Minimum sample per task type
                    avg_score = np.mean(scores)
                    if avg_score > 0.8:  # High performance threshold
                        patterns[agent_id_str].append(f"Recent high performance in {task_type} (avg: {avg_score:.2f})")
        
        return patterns

    async def optimize_routing_weights(self) -> RoutingOptimization:
        """Optimize routing weights based on accumulated learning"""
        try:
            start_time = time.time()
            
            # Collect performance data for optimization
            performance_data = await self._collect_performance_data()
            
            if not performance_data:
                raise ValueError("Insufficient data for optimization")
            
            # Apply optimization algorithm (using ensemble approach)
            optimized_weights, improvement, confidence = await self._apply_optimization_algorithm(performance_data)
            
            # Create optimization record
            optimization = RoutingOptimization(
                optimization_id=str(uuid4()),
                agent_weights=optimized_weights,
                performance_improvement=improvement,
                confidence_interval=confidence,
                optimization_method=OptimizationMethod.ENSEMBLE_METHOD.value,
                applied_at=datetime.utcnow()
            )
            
            # Store optimization
            await self._store_optimization(optimization)
            
            # Apply optimization
            self.routing_weights = defaultdict(lambda: defaultdict(float), optimized_weights)
            self.optimization_history.append(optimization)
            self.learning_metrics['optimizations_applied'] += 1
            
            optimization_time = time.time() - start_time
            
            logger.info("Routing weights optimized",
                       optimization_id=optimization.optimization_id,
                       improvement=improvement,
                       confidence_interval=confidence,
                       optimization_time_ms=optimization_time * 1000)
            
            return optimization
            
        except Exception as e:
            logger.error("Routing optimization failed", error=str(e))
            raise

    async def _collect_performance_data(self) -> Dict[str, Any]:
        """Collect performance data for optimization"""
        async with self.postgres.acquire() as conn:
            # Get agent performance by task type and complexity
            performance_data = await conn.fetch("""
                SELECT 
                    agent_id,
                    task_type,
                    complexity,
                    COUNT(*) as sample_size,
                    AVG(success_score) as avg_success,
                    STDDEV(success_score) as std_success,
                    AVG(completion_time_seconds) as avg_time,
                    AVG(CASE WHEN user_satisfaction IS NOT NULL THEN user_satisfaction ELSE 3.0 END) as avg_satisfaction
                FROM agent_task_outcomes
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY agent_id, task_type, complexity
                HAVING COUNT(*) >= $1
                ORDER BY avg_success DESC
            """, self.minimum_sample_size)
        
        # Structure data for optimization
        structured_data = {
            'agent_performance': {},
            'task_requirements': {},
            'baseline_metrics': {}
        }
        
        for row in performance_data:
            agent_id = str(row['agent_id'])
            task_key = f"{row['task_type']}_{row['complexity']}"
            
            if agent_id not in structured_data['agent_performance']:
                structured_data['agent_performance'][agent_id] = {}
            
            structured_data['agent_performance'][agent_id][task_key] = {
                'success_rate': row['avg_success'],
                'std_dev': row['std_success'] or 0.1,
                'avg_time': row['avg_time'],
                'satisfaction': row['avg_satisfaction'],
                'sample_size': row['sample_size']
            }
            
            # Calculate baseline metrics
            if task_key not in structured_data['baseline_metrics']:
                structured_data['baseline_metrics'][task_key] = []
            structured_data['baseline_metrics'][task_key].append(row['avg_success'])
        
        # Calculate task baseline averages
        for task_key, success_rates in structured_data['baseline_metrics'].items():
            structured_data['baseline_metrics'][task_key] = {
                'avg_success': np.mean(success_rates),
                'std_success': np.std(success_rates)
            }
        
        return structured_data

    async def _apply_optimization_algorithm(self, performance_data: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, float]], float, Tuple[float, float]]:
        """Apply optimization algorithm to improve routing weights"""
        # Ensemble of optimization methods for robustness
        
        # Method 1: Bayesian optimization
        bayesian_weights = self._bayesian_optimization(performance_data)
        
        # Method 2: Performance-based weighting
        performance_weights = self._performance_based_optimization(performance_data)
        
        # Method 3: Risk-adjusted optimization
        risk_weights = self._risk_adjusted_optimization(performance_data)
        
        # Ensemble combination
        optimized_weights = defaultdict(lambda: defaultdict(float))
        
        all_weights = [bayesian_weights, performance_weights, risk_weights]
        weights_count = len(all_weights)
        
        for weight_set in all_weights:
            for agent_id, tasks in weight_set.items():
                for task_key, weight in tasks.items():
                    optimized_weights[agent_id][task_key] += weight / weights_count
        
        # Calculate expected improvement
        current_performance = self._calculate_current_performance(performance_data)
        expected_performance = self._calculate_expected_performance(optimized_weights, performance_data)
        
        improvement = (expected_performance - current_performance) / current_performance * 100
        
        # Estimate confidence interval (simplified approach)
        confidence_lower = improvement * 0.7  # Conservative lower bound
        confidence_upper = improvement * 1.3  # Optimistic upper bound
        
        return dict(optimized_weights), improvement, (confidence_lower, confidence_upper)

    def _bayesian_optimization(self, performance_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Bayesian optimization for routing weights"""
        weights = defaultdict(lambda: defaultdict(float))
        
        for agent_id, tasks in performance_data['agent_performance'].items():
            for task_key, metrics in tasks.items():
                # Bayesian update with beta distribution
                prior_alpha, prior_beta = 1.0, 1.0  # Uniform prior
                
                # Update with observed data
                successes = metrics['success_rate'] * metrics['sample_size']
                failures = (1 - metrics['success_rate']) * metrics['sample_size']
                
                posterior_alpha = prior_alpha + successes
                posterior_beta = prior_beta + failures
                
                # Expected value of beta distribution
                bayesian_weight = posterior_alpha / (posterior_alpha + posterior_beta)
                
                # Adjust for uncertainty (lower confidence = lower weight)
                uncertainty = 1.0 / (posterior_alpha + posterior_beta)
                adjusted_weight = bayesian_weight * (1.0 - uncertainty)
                
                weights[agent_id][task_key] = max(0.0, min(1.0, adjusted_weight))
        
        return weights

    def _performance_based_optimization(self, performance_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Performance-based optimization"""
        weights = defaultdict(lambda: defaultdict(float))
        
        for agent_id, tasks in performance_data['agent_performance'].items():
            for task_key, metrics in tasks.items():
                baseline = performance_data['baseline_metrics'].get(task_key, {})
                baseline_success = baseline.get('avg_success', 0.5)
                
                # Performance advantage over baseline
                advantage = metrics['success_rate'] - baseline_success
                
                # Adjust for time efficiency
                time_factor = max(0.1, 1.0 - (metrics['avg_time'] - 5.0) / 30.0)  # Prefer faster responses
                
                # Adjust for satisfaction
                satisfaction_factor = metrics['satisfaction'] / 5.0  # Normalize to 0-1
                
                # Combined weight
                weight = max(0.0, 0.5 + advantage * 2.0) * time_factor * satisfaction_factor
                
                weights[agent_id][task_key] = min(1.0, weight)
        
        return weights

    def _risk_adjusted_optimization(self, performance_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Risk-adjusted optimization considering variability"""
        weights = defaultdict(lambda: defaultdict(float))
        
        for agent_id, tasks in performance_data['agent_performance'].items():
            for task_key, metrics in tasks.items():
                # Base performance
                base_weight = metrics['success_rate']
                
                # Risk adjustment (penalize high variability)
                risk_penalty = metrics['std_dev'] / 2.0  # Higher std dev = higher risk
                risk_adjusted = base_weight - risk_penalty
                
                # Sample size confidence (higher samples = more confidence)
                confidence_multiplier = min(1.0, metrics['sample_size'] / 50.0)
                
                final_weight = max(0.0, risk_adjusted * confidence_multiplier)
                
                weights[agent_id][task_key] = min(1.0, final_weight)
        
        return weights

    def _calculate_current_performance(self, performance_data: Dict[str, Any]) -> float:
        """Calculate current overall performance score"""
        total_performance = 0.0
        total_weight = 0.0
        
        for agent_id, tasks in performance_data['agent_performance'].items():
            for task_key, metrics in tasks.items():
                weight = metrics['sample_size']  # Weight by sample size
                total_performance += metrics['success_rate'] * weight
                total_weight += weight
        
        return total_performance / total_weight if total_weight > 0 else 0.5

    def _calculate_expected_performance(self, optimized_weights: Dict[str, Dict[str, float]], 
                                      performance_data: Dict[str, Any]) -> float:
        """Calculate expected performance with optimized weights"""
        # Simplified expected performance calculation
        # In a full implementation, this would involve more sophisticated modeling
        
        total_expected = 0.0
        total_weight = 0.0
        
        for agent_id, tasks in optimized_weights.items():
            agent_data = performance_data['agent_performance'].get(agent_id, {})
            for task_key, weight in tasks.items():
                task_metrics = agent_data.get(task_key, {})
                if task_metrics:
                    # Expected improvement based on weight optimization
                    base_success = task_metrics['success_rate']
                    weight_boost = weight * 0.1  # Assume 10% max improvement from better weighting
                    expected_success = min(1.0, base_success + weight_boost)
                    
                    sample_weight = task_metrics['sample_size']
                    total_expected += expected_success * sample_weight
                    total_weight += sample_weight
        
        return total_expected / total_weight if total_weight > 0 else 0.5

    async def _store_optimization(self, optimization: RoutingOptimization):
        """Store optimization result in database"""
        async with self.postgres.acquire() as conn:
            await conn.execute("""
                INSERT INTO routing_optimizations (
                    optimization_version, agent_weights, performance_improvement,
                    confidence_lower, confidence_upper, optimization_method, 
                    sample_size, validation_period_days
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, optimization.optimization_id, json.dumps(optimization.agent_weights),
                optimization.performance_improvement, optimization.confidence_interval[0],
                optimization.confidence_interval[1], optimization.optimization_method,
                len(self.outcome_history), optimization.validation_period_days)

    async def predict_task_success_probability(self, task: TaskContext, agent_id: UUID) -> SuccessPrediction:
        """Predict success probability for agent-task combination"""
        try:
            agent_id_str = str(agent_id)
            task_key = f"{task.task_type}_{task.complexity.value}"
            
            # Get historical performance data
            agent_outcomes = [o for o in self.outcome_history 
                            if o.agent_id == agent_id and o.task_type == task.task_type 
                            and o.complexity == task.complexity]
            
            if len(agent_outcomes) < 5:  # Insufficient data, use general patterns
                predicted_rate, confidence_interval, risk_factors = await self._predict_with_limited_data(task, agent_id)
                model_name = "limited_data_baseline"
            else:
                # Use full prediction model
                predicted_rate, confidence_interval, risk_factors = await self._predict_with_sufficient_data(
                    agent_outcomes, task, agent_id)
                model_name = "historical_performance_model"
            
            prediction = SuccessPrediction(
                agent_id=agent_id,
                task_type=task.task_type,
                complexity=task.complexity,
                predicted_success_rate=predicted_rate,
                confidence_interval=confidence_interval,
                risk_factors=risk_factors,
                prediction_model=model_name,
                prediction_timestamp=datetime.utcnow()
            )
            
            # Store prediction for validation tracking
            await self._store_prediction(prediction)
            
            logger.debug("Success probability predicted",
                        agent_id=agent_id_str,
                        task_type=task.task_type,
                        predicted_rate=predicted_rate)
            
            return prediction
            
        except Exception as e:
            logger.error("Success prediction failed", error=str(e), agent_id=str(agent_id))
            
            # Return conservative default prediction
            return SuccessPrediction(
                agent_id=agent_id,
                task_type=task.task_type,
                complexity=task.complexity,
                predicted_success_rate=0.6,  # Conservative default
                confidence_interval=(0.4, 0.8),
                risk_factors=["insufficient_data", "prediction_error"],
                prediction_model="fallback_default",
                prediction_timestamp=datetime.utcnow()
            )

    async def _predict_with_limited_data(self, task: TaskContext, agent_id: UUID) -> Tuple[float, Tuple[float, float], List[str]]:
        """Make prediction with limited historical data"""
        # Use general patterns and agent specializations
        agent_id_str = str(agent_id)
        base_rate = 0.7  # Default success rate
        
        # Check for specialization match
        for spec_key, specialization in self.agent_specializations.items():
            if str(specialization.agent_id) == agent_id_str:
                if (task.task_type in specialization.task_types and 
                    task.complexity in specialization.complexity_preferences):
                    base_rate += specialization.performance_advantage * 0.3
        
        # Check routing weights
        task_key = f"{task.task_type}_{task.complexity.value}"
        weight = self.routing_weights[agent_id_str].get(task_key, 0.0)
        base_rate = (base_rate + weight) / 2.0  # Average with routing weight
        
        # Wide confidence interval due to limited data
        confidence_interval = (max(0.0, base_rate - 0.3), min(1.0, base_rate + 0.3))
        
        risk_factors = ["limited_historical_data"]
        if task.complexity == TaskComplexity.CRITICAL:
            risk_factors.append("high_complexity_task")
        
        return base_rate, confidence_interval, risk_factors

    async def _predict_with_sufficient_data(self, outcomes: List[TaskOutcome], task: TaskContext, agent_id: UUID) -> Tuple[float, Tuple[float, float], List[str]]:
        """Make prediction with sufficient historical data"""
        # Calculate historical success rate
        success_scores = [o.success_score for o in outcomes]
        mean_success = np.mean(success_scores)
        std_success = np.std(success_scores)
        
        # Trend analysis (recent vs older outcomes)
        recent_outcomes = [o for o in outcomes if (datetime.utcnow() - o.timestamp).days <= 7]
        older_outcomes = [o for o in outcomes if (datetime.utcnow() - o.timestamp).days > 7]
        
        if recent_outcomes and older_outcomes:
            recent_avg = np.mean([o.success_score for o in recent_outcomes])
            older_avg = np.mean([o.success_score for o in older_outcomes])
            trend_factor = (recent_avg - older_avg) * 0.2  # Weight trend at 20%
        else:
            trend_factor = 0.0
        
        # Context adjustments
        context_adjustment = 0.0
        
        # Priority adjustment
        if hasattr(task, 'priority'):
            if task.priority >= 8:  # High priority
                context_adjustment -= 0.05  # Slightly more conservative for high priority
            elif task.priority <= 3:  # Low priority
                context_adjustment += 0.05  # Slightly more optimistic for low priority
        
        # Deadline pressure adjustment
        if hasattr(task, 'deadline') and task.deadline:
            time_until_deadline = (task.deadline - datetime.utcnow()).total_seconds() / 3600  # hours
            if time_until_deadline < 2:  # Less than 2 hours
                context_adjustment -= 0.1  # More conservative under time pressure
        
        # Final prediction
        predicted_rate = mean_success + trend_factor + context_adjustment
        predicted_rate = max(0.0, min(1.0, predicted_rate))
        
        # Confidence interval based on standard deviation and sample size
        confidence_width = std_success / math.sqrt(len(outcomes))
        confidence_interval = (
            max(0.0, predicted_rate - 1.96 * confidence_width),
            min(1.0, predicted_rate + 1.96 * confidence_width)
        )
        
        # Risk factors identification
        risk_factors = []
        
        if std_success > 0.3:
            risk_factors.append("high_performance_variability")
        
        if any(o.error_count > 0 for o in recent_outcomes):
            risk_factors.append("recent_errors_detected")
        
        if any(o.retry_attempts > 1 for o in outcomes):
            risk_factors.append("retry_pattern_observed")
        
        if trend_factor < -0.1:
            risk_factors.append("declining_performance_trend")
        
        return predicted_rate, confidence_interval, risk_factors

    async def _store_prediction(self, prediction: SuccessPrediction):
        """Store success prediction in database for validation tracking"""
        async with self.postgres.acquire() as conn:
            await conn.execute("""
                INSERT INTO success_predictions (
                    agent_id, task_type, complexity, predicted_success_rate,
                    confidence_lower, confidence_upper, risk_factors, prediction_model
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, prediction.agent_id, prediction.task_type, prediction.complexity.value,
                prediction.predicted_success_rate, prediction.confidence_interval[0],
                prediction.confidence_interval[1], prediction.risk_factors, prediction.prediction_model)

    async def _specialization_detection_loop(self):
        """Background task for detecting agent specializations"""
        while True:
            try:
                # Analyze all agents for specialization patterns
                async with self.postgres.acquire() as conn:
                    agents = await conn.fetch("""
                        SELECT DISTINCT agent_id FROM agent_task_outcomes 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                
                for agent_record in agents:
                    agent_id = agent_record['agent_id']
                    agent_outcomes = [o for o in self.outcome_history if o.agent_id == agent_id]
                    
                    if len(agent_outcomes) >= self.minimum_sample_size:
                        await self._detect_specialization_patterns(agent_id, agent_outcomes)
                
                # Sleep for 30 minutes
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error("Specialization detection loop error", error=str(e))
                await asyncio.sleep(300)  # 5 minute retry on error

    async def _detect_specialization_patterns(self, agent_id: UUID, outcomes: List[TaskOutcome]):
        """Detect specialization patterns for a specific agent"""
        try:
            # Group outcomes by task type and complexity
            performance_groups = defaultdict(list)
            
            for outcome in outcomes:
                key = (outcome.task_type, outcome.complexity.value)
                performance_groups[key].append(outcome.success_score)
            
            # Calculate performance statistics
            overall_performance = np.mean([o.success_score for o in outcomes])
            
            detected_specializations = []
            
            for (task_type, complexity), scores in performance_groups.items():
                if len(scores) >= 5:  # Minimum sample for specialization
                    avg_performance = np.mean(scores)
                    performance_advantage = avg_performance - overall_performance
                    
                    # Detect specialization if significantly better than average
                    if performance_advantage > 0.15 and avg_performance > 0.8:
                        confidence = min(1.0, performance_advantage * 2.0)
                        
                        specialization = AgentSpecialization(
                            agent_id=agent_id,
                            specialization_type=f"{task_type}_{complexity}",
                            task_types=[task_type],
                            complexity_preferences=[TaskComplexity(complexity)],
                            confidence_score=confidence,
                            performance_advantage=performance_advantage,
                            sample_size=len(scores),
                            discovered_at=datetime.utcnow(),
                            last_validated=datetime.utcnow()
                        )
                        
                        detected_specializations.append(specialization)
            
            # Store new specializations
            for spec in detected_specializations:
                spec_key = f"{agent_id}_{spec.specialization_type}"
                self.agent_specializations[spec_key] = spec
                
                # Store in database
                await self._store_specialization(spec)
                
                self.learning_metrics['specializations_discovered'] += 1
                
                logger.info("New specialization detected",
                           agent_id=str(agent_id),
                           specialization=spec.specialization_type,
                           confidence=spec.confidence_score,
                           advantage=spec.performance_advantage)
                
        except Exception as e:
            logger.error("Specialization detection failed", error=str(e), agent_id=str(agent_id))

    async def _store_specialization(self, specialization: AgentSpecialization):
        """Store agent specialization in database"""
        async with self.postgres.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_specializations (
                    agent_id, specialization_type, task_types, complexity_preferences,
                    confidence_score, performance_advantage, sample_size
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (agent_id, specialization_type) DO UPDATE SET
                    confidence_score = $5,
                    performance_advantage = $6,
                    sample_size = $7,
                    last_validated = NOW()
            """, specialization.agent_id, specialization.specialization_type,
                specialization.task_types, [c.value for c in specialization.complexity_preferences],
                specialization.confidence_score, specialization.performance_advantage, specialization.sample_size)

    async def _routing_optimization_loop(self):
        """Background task for routing optimization"""
        while True:
            try:
                # Run optimization every 6 hours
                await asyncio.sleep(21600)
                
                # Check if we have enough new data for optimization
                if len(self.outcome_history) >= 100:  # Minimum outcomes for optimization
                    await self.optimize_routing_weights()
                
            except Exception as e:
                logger.error("Routing optimization loop error", error=str(e))
                await asyncio.sleep(3600)  # 1 hour retry on error

    async def _model_validation_loop(self):
        """Background task for validating prediction models"""
        while True:
            try:
                # Validate predictions every 4 hours
                await asyncio.sleep(14400)
                
                await self._validate_predictions()
                
            except Exception as e:
                logger.error("Model validation loop error", error=str(e))
                await asyncio.sleep(1800)  # 30 minute retry on error

    async def _validate_predictions(self):
        """Validate prediction accuracy against actual outcomes"""
        async with self.postgres.acquire() as conn:
            # Get predictions that can be validated
            predictions = await conn.fetch("""
                SELECT p.*, o.success_score as actual_success
                FROM success_predictions p
                JOIN agent_task_outcomes o ON p.agent_id = o.agent_id 
                    AND p.task_type = o.task_type 
                    AND p.complexity = o.complexity
                WHERE p.prediction_accuracy IS NULL
                    AND o.created_at > p.created_at
                    AND o.created_at <= p.created_at + INTERVAL '24 hours'
            """)
            
            total_predictions = len(predictions)
            accurate_predictions = 0
            
            for pred in predictions:
                predicted_rate = pred['predicted_success_rate']
                actual_success = pred['actual_success']
                
                # Calculate prediction accuracy (inverse of absolute error)
                error = abs(predicted_rate - actual_success)
                accuracy = max(0.0, 1.0 - error)
                
                if error <= 0.2:  # Within 20% is considered accurate
                    accurate_predictions += 1
                
                # Update prediction record
                await conn.execute("""
                    UPDATE success_predictions 
                    SET prediction_accuracy = $1, validated_at = NOW()
                    WHERE prediction_id = $2
                """, accuracy, pred['prediction_id'])
            
            if total_predictions > 0:
                overall_accuracy = accurate_predictions / total_predictions
                self.learning_metrics['accuracy_improvements'].append(overall_accuracy)
                
                # Store accuracy metric
                await conn.execute("""
                    INSERT INTO learning_metrics (metric_name, metric_value, metric_metadata)
                    VALUES ('prediction_accuracy', $1, $2)
                """, overall_accuracy, json.dumps({
                    'total_predictions': total_predictions,
                    'accurate_predictions': accurate_predictions,
                    'validation_date': datetime.utcnow().isoformat()
                }))
                
                logger.info("Prediction validation completed",
                           total_predictions=total_predictions,
                           overall_accuracy=overall_accuracy)

    async def _performance_monitoring_loop(self):
        """Background task for monitoring learning system performance"""
        while True:
            try:
                # Monitor every 15 minutes
                await asyncio.sleep(900)
                
                # Check system health
                await self._monitor_learning_health()
                
            except Exception as e:
                logger.error("Performance monitoring loop error", error=str(e))
                await asyncio.sleep(300)  # 5 minute retry on error

    async def _monitor_learning_health(self):
        """Monitor the health of the learning system"""
        # Check memory usage
        outcomes_count = len(self.outcome_history)
        specializations_count = len(self.agent_specializations)
        
        # Log metrics
        async with self.postgres.acquire() as conn:
            await conn.execute("""
                INSERT INTO learning_metrics (metric_name, metric_value, metric_metadata)
                VALUES ('system_health', 1.0, $1)
            """, json.dumps({
                'outcomes_in_memory': outcomes_count,
                'active_specializations': specializations_count,
                'routing_weights_count': sum(len(tasks) for tasks in self.routing_weights.values()),
                'learning_rate': self.learning_rate,
                'total_outcomes_processed': self.learning_metrics['total_outcomes_processed']
            }))

    async def get_learning_analytics(self) -> Dict[str, Any]:
        """Get comprehensive learning analytics"""
        async with self.postgres.acquire() as conn:
            # Recent performance trends
            recent_outcomes = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    AVG(success_score) as avg_success,
                    COUNT(*) as outcome_count
                FROM agent_task_outcomes
                WHERE created_at >= NOW() - INTERVAL '48 hours'
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour
            """)
            
            # Specialization summary
            specializations = await conn.fetch("""
                SELECT 
                    specialization_type,
                    COUNT(*) as agent_count,
                    AVG(confidence_score) as avg_confidence,
                    AVG(performance_advantage) as avg_advantage
                FROM agent_specializations
                WHERE is_active = true
                GROUP BY specialization_type
                ORDER BY avg_advantage DESC
            """)
            
            # Optimization history
            optimizations = await conn.fetch("""
                SELECT 
                    optimization_method,
                    performance_improvement,
                    applied_at
                FROM routing_optimizations
                WHERE is_active = true
                ORDER BY applied_at DESC
                LIMIT 10
            """)
            
            # Prediction accuracy trends
            accuracy_trends = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('day', measurement_timestamp) as day,
                    AVG(metric_value) as avg_accuracy
                FROM learning_metrics
                WHERE metric_name = 'prediction_accuracy'
                    AND measurement_timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('day', measurement_timestamp)
                ORDER BY day
            """)
        
        return {
            'learning_metrics': self.learning_metrics,
            'recent_performance_trends': [dict(row) for row in recent_outcomes],
            'active_specializations': [dict(row) for row in specializations],
            'optimization_history': [dict(row) for row in optimizations],
            'prediction_accuracy_trends': [dict(row) for row in accuracy_trends],
            'system_stats': {
                'outcomes_in_memory': len(self.outcome_history),
                'active_specializations': len(self.agent_specializations),
                'routing_weights_active': sum(len(tasks) for tasks in self.routing_weights.values()),
                'learning_rate': self.learning_rate,
                'confidence_threshold': self.confidence_threshold
            }
        }

    async def cleanup(self):
        """Cleanup learning engine resources"""
        # Cancel background learning tasks
        for task in self._learning_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._learning_tasks.clear()
        
        # Clear learning state
        self.outcome_history.clear()
        self.agent_specializations.clear()
        self.routing_weights.clear()
        self.success_predictors.clear()
        
        await super().cleanup()
        
        logger.info("Agent Learning Engine cleaned up")