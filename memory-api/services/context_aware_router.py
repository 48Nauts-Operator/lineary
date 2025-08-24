# ABOUTME: Context-Aware Agent Routing System for BETTY Multi-Agent Platform
# ABOUTME: Intelligent agent selection, performance tracking, and routing optimization

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from uuid import UUID, uuid4
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import structlog

from .base_service import BaseService
from .agent_manager import AgentManager
from ..core.config import get_settings
from ..core.dependencies import DatabaseDependencies

logger = structlog.get_logger(__name__)

class TaskComplexity(Enum):
    """Task complexity classification"""
    SIMPLE = "simple"      # Basic queries, single operations
    MODERATE = "moderate"  # Multi-step operations, some reasoning
    COMPLEX = "complex"    # Multi-agent coordination, advanced reasoning
    CRITICAL = "critical"  # High-stakes, requires best agents

class AgentLoadLevel(Enum):
    """Agent current load classification"""
    LOW = "low"        # < 30% capacity
    MEDIUM = "medium"  # 30-70% capacity
    HIGH = "high"      # 70-90% capacity
    OVERLOADED = "overloaded"  # > 90% capacity

@dataclass
class TaskContext:
    """Context information for task routing decisions"""
    task_type: str
    complexity: TaskComplexity
    priority: int = 5  # 1-10, higher = more important
    deadline: Optional[datetime] = None
    project_id: str = "default"
    user_id: str = "system"
    required_capabilities: List[str] = None
    preferred_agents: List[str] = None
    fallback_agents: List[str] = None
    sensitive_data: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.required_capabilities is None:
            self.required_capabilities = []
        if self.preferred_agents is None:
            self.preferred_agents = []
        if self.fallback_agents is None:
            self.fallback_agents = []
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class AgentSelection:
    """Result of agent selection process"""
    agent_id: UUID
    agent_name: str
    confidence_score: float  # 0.0-1.0
    selection_reason: str
    fallback_agents: List[UUID]
    estimated_completion_time: float  # seconds
    cost_estimate: int  # cents
    selection_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.selection_metadata is None:
            self.selection_metadata = {}

@dataclass
class RoutingResult:
    """Result of routing operation"""
    success: bool
    agent_selection: Optional[AgentSelection]
    routing_time_ms: float
    error_message: Optional[str] = None
    fallback_used: bool = False
    retry_count: int = 0

@dataclass
class AgentHealthStatus:
    """Agent health and performance status"""
    agent_id: UUID
    agent_name: str
    status: str  # active, inactive, failed, rate_limited
    load_level: AgentLoadLevel
    response_time_p95: float  # 95th percentile response time
    success_rate: float  # 0.0-1.0
    error_rate: float  # 0.0-1.0
    cost_per_request: float  # average cost in cents
    last_health_check: datetime
    predictive_failure_score: float  # 0.0-1.0, higher = more likely to fail
    capacity_utilization: float  # 0.0-1.0

@dataclass
class PerformanceScore:
    """Agent performance scoring"""
    overall_score: float  # 0.0-1.0
    reliability_score: float  # Based on success rate and uptime
    performance_score: float  # Based on response time
    cost_efficiency_score: float  # Based on cost vs. quality
    capability_match_score: float  # How well agent matches task requirements
    load_score: float  # Current load consideration
    historical_score: float  # Based on past performance with similar tasks

class ContextAwareAgentRouter(BaseService):
    """Context-Aware Agent Routing System for intelligent agent selection and coordination"""
    
    def __init__(self, databases: DatabaseDependencies):
        super().__init__(databases)
        self.agent_manager = AgentManager(databases)
        self.settings = get_settings()
        
        # Performance tracking caches
        self.agent_performance_cache: Dict[str, PerformanceScore] = {}
        self.agent_health_cache: Dict[str, AgentHealthStatus] = {}
        self.routing_history: List[Dict[str, Any]] = []
        
        # Circuit breaker state
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Load balancing
        self.agent_load_tracker: Dict[str, int] = {}  # agent_id -> current active requests
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize the routing system"""
        await super().initialize()
        await self.agent_manager.initialize()
        
        # Initialize performance tracking tables if needed
        await self._initialize_routing_tables()
        
        # Start background monitoring tasks
        await self._start_background_tasks()
        
        logger.info("Context-Aware Agent Router initialized")

    async def _initialize_routing_tables(self):
        """Initialize database tables for routing system"""
        try:
            # Agent routing metrics table
            await self.postgres.execute("""
                CREATE TABLE IF NOT EXISTS agent_routing_metrics (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    task_type VARCHAR(100) NOT NULL,
                    complexity VARCHAR(20) NOT NULL,
                    selection_score FLOAT NOT NULL,
                    routing_time_ms FLOAT NOT NULL,
                    execution_success BOOLEAN,
                    execution_time_ms FLOAT,
                    task_completion_time FLOAT,
                    cost_actual_cents INTEGER,
                    user_satisfaction_score FLOAT, -- 1-5 rating if available
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                )
            """)
            
            # Create indexes separately
            await self.postgres.execute("CREATE INDEX IF NOT EXISTS idx_routing_metrics_agent_id ON agent_routing_metrics(agent_id)")
            await self.postgres.execute("CREATE INDEX IF NOT EXISTS idx_routing_metrics_task_type ON agent_routing_metrics(task_type)")
            await self.postgres.execute("CREATE INDEX IF NOT EXISTS idx_routing_metrics_complexity ON agent_routing_metrics(complexity)")
            await self.postgres.execute("CREATE INDEX IF NOT EXISTS idx_routing_metrics_created_at ON agent_routing_metrics(created_at)")
            
            # Circuit breaker state table
            await self.postgres.execute("""
                CREATE TABLE IF NOT EXISTS agent_circuit_breakers (
                    agent_id UUID PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
                    state VARCHAR(20) NOT NULL DEFAULT 'CLOSED', -- CLOSED, OPEN, HALF_OPEN
                    failure_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    last_failure_time TIMESTAMP WITH TIME ZONE,
                    next_retry_time TIMESTAMP WITH TIME ZONE,
                    failure_threshold INTEGER DEFAULT 5,
                    recovery_timeout_ms INTEGER DEFAULT 60000,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Agent performance snapshots
            await self.postgres.execute("""
                CREATE TABLE IF NOT EXISTS agent_performance_snapshots (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    snapshot_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    overall_score FLOAT NOT NULL,
                    reliability_score FLOAT NOT NULL,
                    performance_score FLOAT NOT NULL,
                    cost_efficiency_score FLOAT NOT NULL,
                    capability_match_score FLOAT NOT NULL,
                    load_score FLOAT NOT NULL,
                    historical_score FLOAT NOT NULL,
                    active_requests INTEGER DEFAULT 0,
                    load_level VARCHAR(20),
                    predictive_failure_score FLOAT DEFAULT 0.0,
                    metadata JSONB DEFAULT '{}'
                )
            """)
            
            # Create indexes
            await self.postgres.execute("CREATE INDEX IF NOT EXISTS idx_performance_snapshots_agent_id ON agent_performance_snapshots(agent_id)")
            await self.postgres.execute("CREATE INDEX IF NOT EXISTS idx_performance_snapshots_time ON agent_performance_snapshots(snapshot_time)")
            
        except Exception as e:
            logger.error("Failed to initialize routing tables", error=str(e))
            raise

    async def _start_background_tasks(self):
        """Start background monitoring and optimization tasks"""
        # Performance monitoring task
        perf_task = asyncio.create_task(self._performance_monitor_loop())
        self._background_tasks.append(perf_task)
        
        # Circuit breaker management
        circuit_task = asyncio.create_task(self._circuit_breaker_monitor_loop())
        self._background_tasks.append(circuit_task)
        
        # Performance snapshot collection
        snapshot_task = asyncio.create_task(self._performance_snapshot_loop())
        self._background_tasks.append(snapshot_task)

    async def select_optimal_agent(self, task: TaskContext, context: Dict[str, Any] = None) -> RoutingResult:
        """Select the optimal agent for a given task with full context awareness"""
        start_time = time.time()
        
        try:
            logger.info("Starting agent selection", 
                       task_type=task.task_type, 
                       complexity=task.complexity.value,
                       priority=task.priority)
            
            # 1. Find candidate agents based on capabilities
            candidates = await self._find_candidate_agents(task)
            if not candidates:
                return RoutingResult(
                    success=False,
                    agent_selection=None,
                    routing_time_ms=(time.time() - start_time) * 1000,
                    error_message="No agents found with required capabilities"
                )
            
            # 2. Apply circuit breaker filtering
            available_candidates = await self._filter_circuit_breakers(candidates)
            if not available_candidates:
                return RoutingResult(
                    success=False,
                    agent_selection=None,
                    routing_time_ms=(time.time() - start_time) * 1000,
                    error_message="All capable agents are in circuit breaker state"
                )
            
            # 3. Calculate performance scores for each candidate
            scored_candidates = await self._score_candidates(available_candidates, task, context or {})
            
            # 4. Apply load balancing and select best agent
            selected_agent = await self._select_best_agent(scored_candidates, task)
            
            # 5. Record routing decision
            await self._record_routing_decision(task, selected_agent, scored_candidates)
            
            routing_time = (time.time() - start_time) * 1000
            
            logger.info("Agent selection completed",
                       selected_agent=selected_agent.agent_name,
                       confidence=selected_agent.confidence_score,
                       routing_time_ms=routing_time)
            
            return RoutingResult(
                success=True,
                agent_selection=selected_agent,
                routing_time_ms=routing_time
            )
            
        except Exception as e:
            routing_time = (time.time() - start_time) * 1000
            logger.error("Agent selection failed", error=str(e), routing_time_ms=routing_time)
            
            return RoutingResult(
                success=False,
                agent_selection=None,
                routing_time_ms=routing_time,
                error_message=str(e)
            )

    async def _find_candidate_agents(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Find candidate agents based on task requirements"""
        async with self.postgres.acquire() as conn:
            # If preferred agents specified, start with those
            if task.preferred_agents:
                preferred_candidates = await conn.fetch("""
                    SELECT a.*, ac.priority, c.name as capability_name
                    FROM agents a
                    JOIN agent_capabilities ac ON a.id = ac.agent_id
                    JOIN capabilities c ON ac.capability_id = c.id
                    WHERE a.name = ANY($1) AND a.status = 'active'
                """, task.preferred_agents)
                
                if preferred_candidates:
                    return [dict(agent) for agent in preferred_candidates]
            
            # Find agents by required capabilities
            if task.required_capabilities:
                capability_query = """
                    SELECT a.*, ac.priority, c.name as capability_name,
                           COUNT(DISTINCT c.id) as matching_capabilities
                    FROM agents a
                    JOIN agent_capabilities ac ON a.id = ac.agent_id
                    JOIN capabilities c ON ac.capability_id = c.id
                    WHERE a.status = 'active' AND c.name = ANY($1)
                    GROUP BY a.id, ac.priority, c.name
                    HAVING COUNT(DISTINCT c.id) = $2
                    ORDER BY ac.priority DESC, a.created_at ASC
                """
                
                candidates = await conn.fetch(capability_query, 
                                            task.required_capabilities,
                                            len(task.required_capabilities))
            else:
                # Get all active agents if no specific requirements
                candidates = await conn.fetch("""
                    SELECT a.*, ac.priority, c.name as capability_name
                    FROM agents a
                    LEFT JOIN agent_capabilities ac ON a.id = ac.agent_id
                    LEFT JOIN capabilities c ON ac.capability_id = c.id
                    WHERE a.status = 'active'
                    ORDER BY ac.priority DESC NULLS LAST, a.created_at ASC
                """)
        
        return [dict(agent) for agent in candidates]

    async def _filter_circuit_breakers(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out agents that are in circuit breaker OPEN state"""
        filtered_candidates = []
        
        async with self.postgres.acquire() as conn:
            for candidate in candidates:
                agent_id = candidate['id']
                
                # Check circuit breaker state
                breaker_state = await conn.fetchrow("""
                    SELECT state, next_retry_time FROM agent_circuit_breakers
                    WHERE agent_id = $1
                """, agent_id)
                
                if not breaker_state or breaker_state['state'] == 'CLOSED':
                    # Circuit breaker is closed or doesn't exist (new agent)
                    filtered_candidates.append(candidate)
                elif breaker_state['state'] == 'HALF_OPEN':
                    # Allow some traffic through for testing
                    filtered_candidates.append(candidate)
                elif breaker_state['state'] == 'OPEN':
                    # Check if retry time has passed
                    if breaker_state['next_retry_time'] and breaker_state['next_retry_time'] <= datetime.utcnow():
                        # Move to HALF_OPEN state
                        await conn.execute("""
                            UPDATE agent_circuit_breakers 
                            SET state = 'HALF_OPEN', updated_at = NOW()
                            WHERE agent_id = $1
                        """, agent_id)
                        filtered_candidates.append(candidate)
                    # else: skip agent, circuit breaker is open
        
        return filtered_candidates

    async def _score_candidates(self, candidates: List[Dict[str, Any]], task: TaskContext, context: Dict[str, Any]) -> List[Tuple[Dict[str, Any], PerformanceScore]]:
        """Score candidate agents based on multiple criteria"""
        scored_candidates = []
        
        for candidate in candidates:
            agent_id = UUID(candidate['id'])
            
            # Get cached performance score or calculate new one
            cache_key = str(agent_id)
            if cache_key in self.agent_performance_cache:
                base_score = self.agent_performance_cache[cache_key]
            else:
                base_score = await self._calculate_performance_score(agent_id, task, context)
                self.agent_performance_cache[cache_key] = base_score
            
            # Adjust score based on current load
            load_adjusted_score = await self._adjust_score_for_load(agent_id, base_score)
            
            # Adjust score based on task-specific factors
            final_score = await self._adjust_score_for_task(load_adjusted_score, candidate, task)
            
            scored_candidates.append((candidate, final_score))
        
        # Sort by overall score (descending)
        scored_candidates.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        return scored_candidates

    async def _calculate_performance_score(self, agent_id: UUID, task: TaskContext, context: Dict[str, Any]) -> PerformanceScore:
        """Calculate comprehensive performance score for an agent"""
        async with self.postgres.acquire() as conn:
            # Get agent statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(CASE WHEN execution_success THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(execution_time_ms) as avg_execution_time,
                    AVG(cost_actual_cents) as avg_cost,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_response_time
                FROM agent_routing_metrics
                WHERE agent_id = $1 
                AND created_at >= NOW() - INTERVAL '7 days'
            """, agent_id)
            
            # Get recent health status
            health = await conn.fetchrow("""
                SELECT status, response_time_ms, health_data
                FROM agent_health_logs
                WHERE agent_id = $1
                ORDER BY checked_at DESC
                LIMIT 1
            """, agent_id)
            
            # Calculate reliability score (0.0-1.0)
            reliability_score = stats['success_rate'] if stats and stats['success_rate'] else 0.8  # Default for new agents
            
            # Calculate performance score based on response time
            avg_response_time = stats['avg_execution_time'] if stats and stats['avg_execution_time'] else 1000  # Default 1s
            performance_score = max(0.0, min(1.0, 1.0 - (avg_response_time - 100) / 5000))  # Scale 100ms-5000ms to 1.0-0.0
            
            # Calculate cost efficiency score
            avg_cost = stats['avg_cost'] if stats and stats['avg_cost'] else 10  # Default cost
            cost_efficiency_score = max(0.1, min(1.0, 20 / avg_cost))  # Inverse relationship with cost
            
            # Calculate capability match score (this could be enhanced with semantic matching)
            capability_match_score = 0.8  # Default - could be improved with actual capability matching
            
            # Current load score (will be adjusted in _adjust_score_for_load)
            load_score = 1.0
            
            # Historical performance with similar tasks
            historical_score = await self._get_historical_performance(agent_id, task.task_type, task.complexity)
            
            # Calculate overall score (weighted average)
            overall_score = (
                reliability_score * 0.25 +
                performance_score * 0.20 +
                cost_efficiency_score * 0.15 +
                capability_match_score * 0.20 +
                load_score * 0.10 +
                historical_score * 0.10
            )
            
        return PerformanceScore(
            overall_score=overall_score,
            reliability_score=reliability_score,
            performance_score=performance_score,
            cost_efficiency_score=cost_efficiency_score,
            capability_match_score=capability_match_score,
            load_score=load_score,
            historical_score=historical_score
        )

    async def _get_historical_performance(self, agent_id: UUID, task_type: str, complexity: TaskComplexity) -> float:
        """Get historical performance score for similar tasks"""
        async with self.postgres.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT AVG(CASE WHEN execution_success THEN 1.0 ELSE 0.0 END) as historical_success_rate
                FROM agent_routing_metrics
                WHERE agent_id = $1 
                AND task_type = $2 
                AND complexity = $3
                AND created_at >= NOW() - INTERVAL '30 days'
            """, agent_id, task_type, complexity.value)
            
        return result['historical_success_rate'] if result and result['historical_success_rate'] else 0.8

    async def _adjust_score_for_load(self, agent_id: UUID, score: PerformanceScore) -> PerformanceScore:
        """Adjust performance score based on current agent load"""
        current_load = self.agent_load_tracker.get(str(agent_id), 0)
        
        # Define load capacity (this could be agent-specific)
        max_capacity = 10  # Max concurrent requests per agent
        load_ratio = current_load / max_capacity
        
        # Calculate load penalty
        if load_ratio < 0.3:
            load_penalty = 0.0  # No penalty for low load
        elif load_ratio < 0.7:
            load_penalty = 0.1  # Small penalty for medium load
        elif load_ratio < 0.9:
            load_penalty = 0.3  # Larger penalty for high load
        else:
            load_penalty = 0.7  # Heavy penalty for overload
        
        # Apply load penalty to overall score
        adjusted_score = score.overall_score * (1.0 - load_penalty)
        load_score = 1.0 - load_penalty
        
        return PerformanceScore(
            overall_score=adjusted_score,
            reliability_score=score.reliability_score,
            performance_score=score.performance_score,
            cost_efficiency_score=score.cost_efficiency_score,
            capability_match_score=score.capability_match_score,
            load_score=load_score,
            historical_score=score.historical_score
        )

    async def _adjust_score_for_task(self, score: PerformanceScore, candidate: Dict[str, Any], task: TaskContext) -> PerformanceScore:
        """Adjust score based on task-specific requirements"""
        adjusted_overall = score.overall_score
        
        # Priority-based adjustments
        if task.priority >= 8:  # High priority tasks
            if score.reliability_score >= 0.9:
                adjusted_overall *= 1.1  # Prefer highly reliable agents
        elif task.priority <= 3:  # Low priority tasks
            # Prefer cost-efficient agents for low priority
            adjusted_overall = (adjusted_overall * 0.7) + (score.cost_efficiency_score * 0.3)
        
        # Complexity-based adjustments
        if task.complexity == TaskComplexity.CRITICAL:
            # For critical tasks, heavily weight reliability
            adjusted_overall = (score.reliability_score * 0.6) + (adjusted_overall * 0.4)
        elif task.complexity == TaskComplexity.SIMPLE:
            # For simple tasks, weight cost efficiency more
            adjusted_overall = (adjusted_overall * 0.7) + (score.cost_efficiency_score * 0.3)
        
        # Deadline-based adjustments
        if task.deadline:
            time_until_deadline = (task.deadline - datetime.utcnow()).total_seconds()
            if time_until_deadline < 300:  # Less than 5 minutes
                # Prefer fast agents for urgent tasks
                adjusted_overall = (adjusted_overall * 0.6) + (score.performance_score * 0.4)
        
        return PerformanceScore(
            overall_score=min(1.0, adjusted_overall),  # Cap at 1.0
            reliability_score=score.reliability_score,
            performance_score=score.performance_score,
            cost_efficiency_score=score.cost_efficiency_score,
            capability_match_score=score.capability_match_score,
            load_score=score.load_score,
            historical_score=score.historical_score
        )

    async def _select_best_agent(self, scored_candidates: List[Tuple[Dict[str, Any], PerformanceScore]], task: TaskContext) -> AgentSelection:
        """Select the best agent from scored candidates"""
        if not scored_candidates:
            raise ValueError("No scored candidates available")
        
        # Get the top candidate
        best_candidate, best_score = scored_candidates[0]
        
        # Prepare fallback agents (next 3 best)
        fallback_agents = []
        for candidate, _ in scored_candidates[1:4]:  # Take up to 3 fallbacks
            fallback_agents.append(UUID(candidate['id']))
        
        # Estimate completion time and cost
        estimated_time = await self._estimate_completion_time(UUID(best_candidate['id']), task)
        estimated_cost = await self._estimate_cost(UUID(best_candidate['id']), task)
        
        # Generate selection reason
        selection_reason = self._generate_selection_reason(best_candidate, best_score, task)
        
        return AgentSelection(
            agent_id=UUID(best_candidate['id']),
            agent_name=best_candidate['name'],
            confidence_score=best_score.overall_score,
            selection_reason=selection_reason,
            fallback_agents=fallback_agents,
            estimated_completion_time=estimated_time,
            cost_estimate=estimated_cost,
            selection_metadata={
                'performance_breakdown': asdict(best_score),
                'load_level': self._get_load_level(UUID(best_candidate['id'])),
                'selection_timestamp': datetime.utcnow().isoformat()
            }
        )

    async def _estimate_completion_time(self, agent_id: UUID, task: TaskContext) -> float:
        """Estimate task completion time for an agent"""
        async with self.postgres.acquire() as conn:
            # Get historical completion times for similar tasks
            result = await conn.fetchrow("""
                SELECT AVG(execution_time_ms) as avg_time
                FROM agent_routing_metrics
                WHERE agent_id = $1 
                AND task_type = $2 
                AND complexity = $3
                AND created_at >= NOW() - INTERVAL '14 days'
            """, agent_id, task.task_type, task.complexity.value)
        
        if result and result['avg_time']:
            base_time = result['avg_time'] / 1000  # Convert to seconds
        else:
            # Default estimates based on complexity
            complexity_defaults = {
                TaskComplexity.SIMPLE: 2.0,
                TaskComplexity.MODERATE: 10.0,
                TaskComplexity.COMPLEX: 30.0,
                TaskComplexity.CRITICAL: 60.0
            }
            base_time = complexity_defaults.get(task.complexity, 10.0)
        
        # Adjust for current load
        current_load = self.agent_load_tracker.get(str(agent_id), 0)
        load_multiplier = 1.0 + (current_load * 0.1)  # 10% increase per concurrent request
        
        return base_time * load_multiplier

    async def _estimate_cost(self, agent_id: UUID, task: TaskContext) -> int:
        """Estimate task cost for an agent in cents"""
        async with self.postgres.acquire() as conn:
            # Get historical costs for similar tasks
            result = await conn.fetchrow("""
                SELECT AVG(cost_actual_cents) as avg_cost
                FROM agent_routing_metrics
                WHERE agent_id = $1 
                AND task_type = $2 
                AND complexity = $3
                AND created_at >= NOW() - INTERVAL '14 days'
            """, agent_id, task.task_type, task.complexity.value)
        
        if result and result['avg_cost']:
            return int(result['avg_cost'])
        else:
            # Default cost estimates based on complexity
            complexity_defaults = {
                TaskComplexity.SIMPLE: 1,
                TaskComplexity.MODERATE: 5,
                TaskComplexity.COMPLEX: 20,
                TaskComplexity.CRITICAL: 50
            }
            return complexity_defaults.get(task.complexity, 10)

    def _generate_selection_reason(self, candidate: Dict[str, Any], score: PerformanceScore, task: TaskContext) -> str:
        """Generate human-readable reason for agent selection"""
        reasons = []
        
        if score.reliability_score >= 0.9:
            reasons.append(f"high reliability ({score.reliability_score:.1%})")
        
        if score.performance_score >= 0.8:
            reasons.append("excellent response time")
        
        if score.cost_efficiency_score >= 0.8:
            reasons.append("cost efficient")
        
        if score.load_score >= 0.9:
            reasons.append("low current load")
        
        if score.historical_score >= 0.8:
            reasons.append(f"strong performance on similar {task.complexity.value} tasks")
        
        if not reasons:
            reasons.append("best available option")
        
        return f"Selected for {', '.join(reasons[:3])}."  # Limit to top 3 reasons

    def _get_load_level(self, agent_id: UUID) -> str:
        """Get current load level for an agent"""
        current_load = self.agent_load_tracker.get(str(agent_id), 0)
        max_capacity = 10  # This could be agent-specific
        load_ratio = current_load / max_capacity
        
        if load_ratio < 0.3:
            return "low"
        elif load_ratio < 0.7:
            return "medium"
        elif load_ratio < 0.9:
            return "high"
        else:
            return "overloaded"

    async def _record_routing_decision(self, task: TaskContext, selection: AgentSelection, all_candidates: List[Tuple[Dict[str, Any], PerformanceScore]]):
        """Record routing decision for future optimization"""
        async with self.postgres.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_routing_metrics (
                    agent_id, task_type, complexity, selection_score,
                    routing_time_ms, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, selection.agent_id, task.task_type, task.complexity.value,
                selection.confidence_score, time.time() * 1000,
                json.dumps({
                    'task_metadata': asdict(task),
                    'selection_metadata': selection.selection_metadata,
                    'candidates_considered': len(all_candidates),
                    'fallback_count': len(selection.fallback_agents)
                }))

    async def route_with_fallback(self, task: TaskContext, preferred_agents: List[str] = None) -> RoutingResult:
        """Route task with automatic fallback handling"""
        retry_count = 0
        max_retries = 3
        
        # Override task preferred agents if specified
        if preferred_agents:
            task.preferred_agents = preferred_agents
        
        while retry_count <= max_retries:
            result = await self.select_optimal_agent(task)
            
            if result.success:
                # Track load for selected agent
                agent_id_str = str(result.agent_selection.agent_id)
                self.agent_load_tracker[agent_id_str] = self.agent_load_tracker.get(agent_id_str, 0) + 1
                
                return RoutingResult(
                    success=True,
                    agent_selection=result.agent_selection,
                    routing_time_ms=result.routing_time_ms,
                    fallback_used=(retry_count > 0),
                    retry_count=retry_count
                )
            
            # If primary selection failed, try fallback agents
            if retry_count < max_retries:
                # Move to next preferred agent or let system choose
                if task.fallback_agents and retry_count < len(task.fallback_agents):
                    task.preferred_agents = [task.fallback_agents[retry_count]]
                else:
                    task.preferred_agents = []  # Let system choose best available
                
                retry_count += 1
                await asyncio.sleep(0.1 * retry_count)  # Exponential backoff
            else:
                break
        
        return RoutingResult(
            success=False,
            agent_selection=None,
            routing_time_ms=result.routing_time_ms,
            error_message="All routing attempts failed after retries",
            fallback_used=True,
            retry_count=retry_count
        )

    async def coordinate_multi_agent_task(self, complex_task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multiple agents for complex tasks"""
        # This is a placeholder for multi-agent coordination
        # Implementation would depend on specific multi-agent task requirements
        
        subtasks = complex_task.get('subtasks', [])
        results = {}
        
        # Parallel execution of subtasks
        async def execute_subtask(subtask_data):
            subtask_context = TaskContext(
                task_type=subtask_data.get('type', 'general'),
                complexity=TaskComplexity(subtask_data.get('complexity', 'moderate')),
                required_capabilities=subtask_data.get('capabilities', [])
            )
            
            routing_result = await self.route_with_fallback(subtask_context)
            
            if routing_result.success:
                # Here you would actually execute the task with the selected agent
                # For now, return the routing information
                return {
                    'subtask_id': subtask_data.get('id'),
                    'agent_selected': str(routing_result.agent_selection.agent_id),
                    'agent_name': routing_result.agent_selection.agent_name,
                    'status': 'routed'
                }
            else:
                return {
                    'subtask_id': subtask_data.get('id'),
                    'status': 'failed',
                    'error': routing_result.error_message
                }
        
        # Execute all subtasks in parallel
        subtask_results = await asyncio.gather(
            *[execute_subtask(subtask) for subtask in subtasks],
            return_exceptions=True
        )
        
        return {
            'coordination_id': str(uuid4()),
            'total_subtasks': len(subtasks),
            'completed_subtasks': len([r for r in subtask_results if isinstance(r, dict) and r.get('status') == 'routed']),
            'failed_subtasks': len([r for r in subtask_results if isinstance(r, dict) and r.get('status') == 'failed']),
            'subtask_results': subtask_results
        }

    async def monitor_agent_health(self) -> List[AgentHealthStatus]:
        """Get comprehensive health status for all agents"""
        health_statuses = []
        
        async with self.postgres.acquire() as conn:
            agents = await conn.fetch("""
                SELECT id, name, status FROM agents WHERE status IN ('active', 'inactive')
            """)
            
            for agent in agents:
                agent_id = agent['id']
                
                # Get latest health metrics
                health_data = await conn.fetchrow("""
                    SELECT status, response_time_ms, health_data, checked_at
                    FROM agent_health_logs
                    WHERE agent_id = $1
                    ORDER BY checked_at DESC
                    LIMIT 1
                """, agent_id)
                
                # Get performance metrics
                perf_data = await conn.fetchrow("""
                    SELECT 
                        AVG(CASE WHEN execution_success THEN 1.0 ELSE 0.0 END) as success_rate,
                        AVG(CASE WHEN NOT execution_success THEN 1.0 ELSE 0.0 END) as error_rate,
                        AVG(execution_time_ms) as avg_response_time,
                        AVG(cost_actual_cents) as avg_cost,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_response_time
                    FROM agent_routing_metrics
                    WHERE agent_id = $1 
                    AND created_at >= NOW() - INTERVAL '1 hour'
                """, agent_id)
                
                # Calculate load level
                current_load = self.agent_load_tracker.get(str(agent_id), 0)
                max_capacity = 10  # Could be agent-specific
                load_ratio = current_load / max_capacity
                
                if load_ratio < 0.3:
                    load_level = AgentLoadLevel.LOW
                elif load_ratio < 0.7:
                    load_level = AgentLoadLevel.MEDIUM
                elif load_ratio < 0.9:
                    load_level = AgentLoadLevel.HIGH
                else:
                    load_level = AgentLoadLevel.OVERLOADED
                
                # Calculate predictive failure score
                failure_score = await self._calculate_failure_prediction(agent_id)
                
                health_status = AgentHealthStatus(
                    agent_id=agent_id,
                    agent_name=agent['name'],
                    status=health_data['status'] if health_data else 'unknown',
                    load_level=load_level,
                    response_time_p95=perf_data['p95_response_time'] if perf_data and perf_data['p95_response_time'] else 0.0,
                    success_rate=perf_data['success_rate'] if perf_data and perf_data['success_rate'] else 0.0,
                    error_rate=perf_data['error_rate'] if perf_data and perf_data['error_rate'] else 0.0,
                    cost_per_request=perf_data['avg_cost'] if perf_data and perf_data['avg_cost'] else 0.0,
                    last_health_check=health_data['checked_at'] if health_data else datetime.utcnow(),
                    predictive_failure_score=failure_score,
                    capacity_utilization=load_ratio
                )
                
                health_statuses.append(health_status)
        
        return health_statuses

    async def _calculate_failure_prediction(self, agent_id: UUID) -> float:
        """Calculate predictive failure score based on recent patterns"""
        async with self.postgres.acquire() as conn:
            # Get recent failure patterns
            recent_metrics = await conn.fetch("""
                SELECT execution_success, created_at
                FROM agent_routing_metrics
                WHERE agent_id = $1 
                AND created_at >= NOW() - INTERVAL '2 hours'
                ORDER BY created_at DESC
                LIMIT 20
            """, agent_id)
            
            if not recent_metrics:
                return 0.0
            
            # Calculate failure rate trend
            failures = [not m['execution_success'] for m in recent_metrics]
            if not failures:
                return 0.0
            
            failure_rate = sum(failures) / len(failures)
            
            # Weight recent failures more heavily
            weighted_failures = 0.0
            total_weight = 0.0
            
            for i, failed in enumerate(failures):
                weight = 1.0 / (i + 1)  # Recent failures get higher weight
                weighted_failures += failed * weight
                total_weight += weight
            
            weighted_failure_rate = weighted_failures / total_weight if total_weight > 0 else 0.0
            
            # Return prediction score (0.0 = low failure risk, 1.0 = high failure risk)
            return min(1.0, weighted_failure_rate * 1.5)  # Amplify the signal slightly

    async def _performance_monitor_loop(self):
        """Background task to monitor agent performance"""
        while True:
            try:
                # Update performance caches
                agents = await self.agent_manager.get_agents(status='active')
                
                for agent_data in agents:
                    agent_id = UUID(agent_data['id'])
                    
                    # Update performance score
                    task_context = TaskContext(
                        task_type="general",
                        complexity=TaskComplexity.MODERATE
                    )
                    
                    perf_score = await self._calculate_performance_score(agent_id, task_context, {})
                    self.agent_performance_cache[str(agent_id)] = perf_score
                
                logger.debug("Performance cache updated", agents_updated=len(agents))
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error("Performance monitor error", error=str(e))
                await asyncio.sleep(60)  # Shorter retry on error

    async def _circuit_breaker_monitor_loop(self):
        """Background task to manage circuit breaker states"""
        while True:
            try:
                async with self.postgres.acquire() as conn:
                    # Check for agents that need circuit breaker state updates
                    breakers_to_update = await conn.fetch("""
                        SELECT agent_id, state, failure_count, success_count, next_retry_time
                        FROM agent_circuit_breakers
                        WHERE state != 'CLOSED' OR failure_count > 0
                    """)
                    
                    for breaker in breakers_to_update:
                        agent_id = breaker['agent_id']
                        state = breaker['state']
                        failure_count = breaker['failure_count']
                        success_count = breaker['success_count']
                        
                        if state == 'HALF_OPEN':
                            # Check if agent has recovered
                            if success_count >= 3:  # 3 successes to close circuit
                                await conn.execute("""
                                    UPDATE agent_circuit_breakers
                                    SET state = 'CLOSED', failure_count = 0, success_count = 0
                                    WHERE agent_id = $1
                                """, agent_id)
                                
                                logger.info("Circuit breaker closed", agent_id=str(agent_id))
                        
                        elif state == 'CLOSED' and failure_count >= 5:
                            # Open circuit breaker
                            next_retry = datetime.utcnow() + timedelta(minutes=1)  # 1 minute timeout
                            
                            await conn.execute("""
                                UPDATE agent_circuit_breakers
                                SET state = 'OPEN', next_retry_time = $2
                                WHERE agent_id = $1
                            """, agent_id, next_retry)
                            
                            logger.warning("Circuit breaker opened", agent_id=str(agent_id))
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error("Circuit breaker monitor error", error=str(e))
                await asyncio.sleep(30)

    async def _performance_snapshot_loop(self):
        """Background task to collect performance snapshots"""
        while True:
            try:
                health_statuses = await self.monitor_agent_health()
                
                async with self.postgres.acquire() as conn:
                    for health in health_statuses:
                        # Get current performance score
                        perf_score = self.agent_performance_cache.get(str(health.agent_id))
                        
                        if perf_score:
                            await conn.execute("""
                                INSERT INTO agent_performance_snapshots (
                                    agent_id, overall_score, reliability_score, performance_score,
                                    cost_efficiency_score, capability_match_score, load_score,
                                    historical_score, active_requests, load_level,
                                    predictive_failure_score, metadata
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                            """, health.agent_id, perf_score.overall_score,
                                perf_score.reliability_score, perf_score.performance_score,
                                perf_score.cost_efficiency_score, perf_score.capability_match_score,
                                perf_score.load_score, perf_score.historical_score,
                                self.agent_load_tracker.get(str(health.agent_id), 0),
                                health.load_level.value, health.predictive_failure_score,
                                json.dumps({
                                    'response_time_p95': health.response_time_p95,
                                    'success_rate': health.success_rate,
                                    'cost_per_request': health.cost_per_request
                                }))
                
                logger.debug("Performance snapshots collected", count=len(health_statuses))
                
                # Sleep for 10 minutes
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error("Performance snapshot error", error=str(e))
                await asyncio.sleep(300)  # 5 minute retry on error

    async def record_execution_result(self, agent_id: UUID, task_context: TaskContext, success: bool, 
                                    execution_time_ms: float, actual_cost_cents: int = None):
        """Record the result of task execution for learning and optimization"""
        async with self.postgres.acquire() as conn:
            await conn.execute("""
                UPDATE agent_routing_metrics
                SET execution_success = $2, execution_time_ms = $3, 
                    cost_actual_cents = $4, task_completion_time = $5
                WHERE agent_id = $1
                AND created_at >= NOW() - INTERVAL '1 minute'
                ORDER BY created_at DESC
                LIMIT 1
            """, agent_id, success, execution_time_ms, actual_cost_cents or 0, execution_time_ms / 1000)
            
            # Update circuit breaker
            if success:
                await conn.execute("""
                    INSERT INTO agent_circuit_breakers (agent_id, success_count)
                    VALUES ($1, 1)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        success_count = agent_circuit_breakers.success_count + 1,
                        updated_at = NOW()
                """, agent_id)
            else:
                await conn.execute("""
                    INSERT INTO agent_circuit_breakers (agent_id, failure_count, last_failure_time)
                    VALUES ($1, 1, NOW())
                    ON CONFLICT (agent_id) DO UPDATE SET
                        failure_count = agent_circuit_breakers.failure_count + 1,
                        last_failure_time = NOW(),
                        updated_at = NOW()
                """, agent_id)
        
        # Update load tracking
        agent_id_str = str(agent_id)
        if agent_id_str in self.agent_load_tracker:
            self.agent_load_tracker[agent_id_str] = max(0, self.agent_load_tracker[agent_id_str] - 1)
        
        # Invalidate performance cache to force recalculation
        if agent_id_str in self.agent_performance_cache:
            del self.agent_performance_cache[agent_id_str]

    async def get_routing_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get routing analytics and performance insights"""
        async with self.postgres.acquire() as conn:
            # Overall routing metrics
            overall_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_routings,
                    AVG(routing_time_ms) as avg_routing_time,
                    AVG(CASE WHEN execution_success THEN 1.0 ELSE 0.0 END) as success_rate,
                    COUNT(DISTINCT agent_id) as unique_agents_used
                FROM agent_routing_metrics
                WHERE created_at >= NOW() - INTERVAL '%s hours'
            """ % hours)
            
            # Agent performance breakdown
            agent_performance = await conn.fetch("""
                SELECT 
                    a.name as agent_name,
                    COUNT(rm.*) as routing_count,
                    AVG(rm.routing_time_ms) as avg_routing_time,
                    AVG(rm.execution_time_ms) as avg_execution_time,
                    AVG(CASE WHEN rm.execution_success THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(rm.cost_actual_cents) as avg_cost
                FROM agents a
                JOIN agent_routing_metrics rm ON a.id = rm.agent_id
                WHERE rm.created_at >= NOW() - INTERVAL '%s hours'
                GROUP BY a.id, a.name
                ORDER BY routing_count DESC
            """ % hours)
            
            # Task type breakdown
            task_breakdown = await conn.fetch("""
                SELECT 
                    task_type,
                    complexity,
                    COUNT(*) as count,
                    AVG(routing_time_ms) as avg_routing_time,
                    AVG(CASE WHEN execution_success THEN 1.0 ELSE 0.0 END) as success_rate
                FROM agent_routing_metrics
                WHERE created_at >= NOW() - INTERVAL '%s hours'
                GROUP BY task_type, complexity
                ORDER BY count DESC
            """ % hours)
            
            # Circuit breaker status
            circuit_status = await conn.fetch("""
                SELECT 
                    a.name as agent_name,
                    cb.state,
                    cb.failure_count,
                    cb.success_count,
                    cb.next_retry_time
                FROM agent_circuit_breakers cb
                JOIN agents a ON cb.agent_id = a.id
                WHERE cb.state != 'CLOSED' OR cb.failure_count > 0
            """)
        
        return {
            'analytics_period_hours': hours,
            'overall_metrics': dict(overall_stats) if overall_stats else {},
            'agent_performance': [dict(perf) for perf in agent_performance],
            'task_breakdown': [dict(task) for task in task_breakdown],
            'circuit_breaker_status': [dict(cb) for cb in circuit_status],
            'current_load_distribution': dict(self.agent_load_tracker),
            'performance_cache_size': len(self.agent_performance_cache)
        }

    async def cleanup(self):
        """Cleanup resources and stop background tasks"""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._background_tasks.clear()
        
        # Clear caches
        self.agent_performance_cache.clear()
        self.agent_health_cache.clear()
        self.agent_load_tracker.clear()
        self.routing_history.clear()
        
        await self.agent_manager.cleanup()
        await super().cleanup()
        
        logger.info("Context-Aware Agent Router cleaned up")