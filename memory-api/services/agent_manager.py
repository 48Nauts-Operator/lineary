# ABOUTME: Agent manager service for BETTY Multi-Agent Platform
# ABOUTME: Orchestrates agent instances, handles routing, and manages provider lifecycles

import asyncio
from typing import Dict, List, Any, Optional
from uuid import UUID
import structlog
import time

from .base_service import BaseService
from .agent_service import AgentService, AgentUsage
from ..providers.base_provider import BaseProvider, ChatRequest, ChatResponse
from ..providers.claude_provider import ClaudeProvider
from ..providers.openai_provider import OpenAIProvider
from ..core.config import get_settings

logger = structlog.get_logger(__name__)

class AgentManager(BaseService):
    """Central manager for all agent instances and operations"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.agent_service = AgentService(db_manager)
        self.active_providers: Dict[str, BaseProvider] = {}
        self.provider_classes = {
            'claude': ClaudeProvider,
            'openai': OpenAIProvider,
            # Add more providers as implemented
        }
        self.rate_limiters: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize the agent manager"""
        await super().initialize()
        await self.agent_service.initialize()
        await self._load_active_agents()
        
    async def _load_active_agents(self):
        """Load and initialize all active agents"""
        try:
            agents = await self.agent_service.get_agents(status='active')
            
            for agent_data in agents:
                agent_id = UUID(agent_data['id'])
                
                if agent_data['agent_type'] == 'api_based':
                    provider = await self._create_provider_instance(agent_data)
                    if provider:
                        self.active_providers[str(agent_id)] = provider
                        logger.info("Agent loaded", agent_id=str(agent_id), 
                                  provider=agent_data['provider'])
                        
        except Exception as e:
            logger.error("Failed to load active agents", error=str(e))
    
    async def _create_provider_instance(self, agent_data: Dict[str, Any]) -> Optional[BaseProvider]:
        """Create a provider instance for an agent"""
        try:
            provider_type = agent_data['provider']
            agent_id = UUID(agent_data['id'])
            
            if provider_type not in self.provider_classes:
                logger.warning("Unknown provider type", provider=provider_type)
                return None
            
            # Get credentials from agent service
            credentials = await self.agent_service.get_agent_credentials(agent_id)
            
            # Create provider instance
            provider_class = self.provider_classes[provider_type]
            provider = provider_class(agent_id, agent_data['config'], credentials)
            
            # Initialize provider
            if await provider.initialize():
                return provider
            else:
                logger.error("Failed to initialize provider", agent_id=str(agent_id))
                return None
                
        except Exception as e:
            logger.error("Failed to create provider instance", error=str(e))
            return None
    
    async def chat_with_agent(self, agent_id: UUID, request: ChatRequest) -> ChatResponse:
        """Send a chat request to a specific agent"""
        agent_id_str = str(agent_id)
        
        # Check if agent is loaded
        if agent_id_str not in self.active_providers:
            await self._load_single_agent(agent_id)
            
        if agent_id_str not in self.active_providers:
            raise ValueError(f"Agent {agent_id} is not available")
        
        provider = self.active_providers[agent_id_str]
        
        # Check rate limits
        if not await self._check_rate_limit(agent_id):
            raise Exception("Rate limit exceeded for agent")
        
        try:
            # Record request start
            start_time = time.time()
            
            # Make chat request
            response = await provider.chat(request)
            
            # Calculate metrics
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Update usage statistics
            usage = AgentUsage(
                request_count=1,
                token_usage=response.usage,
                cost_cents=response.cost_cents,
                success_count=1
            )
            
            await self.agent_service.update_usage(agent_id, usage)
            
            # Update rate limiter
            await self._update_rate_limit(agent_id, response.usage)
            
            logger.info("Chat completed successfully", 
                       agent_id=agent_id_str,
                       duration_ms=duration_ms,
                       tokens=response.usage.get('total_tokens', 0))
            
            return response
            
        except Exception as e:
            # Record error
            usage = AgentUsage(
                request_count=1,
                error_count=1
            )
            await self.agent_service.update_usage(agent_id, usage)
            
            logger.error("Chat failed", agent_id=agent_id_str, error=str(e))
            raise
    
    async def chat_with_best_agent(self, capability: str, request: ChatRequest) -> ChatResponse:
        """Route request to the best available agent for a specific capability"""
        
        # Find agents with the requested capability
        suitable_agents = await self._find_agents_by_capability(capability)
        
        if not suitable_agents:
            raise ValueError(f"No agents available with capability: {capability}")
        
        # Select best agent based on cost, availability, and performance
        best_agent = await self._select_best_agent(suitable_agents, request)
        
        return await self.chat_with_agent(best_agent['id'], request)
    
    async def _find_agents_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Find active agents that have a specific capability"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            agents = await conn.fetch("""
                SELECT a.*, ac.priority
                FROM agents a
                JOIN agent_capabilities ac ON a.id = ac.agent_id
                JOIN capabilities c ON ac.capability_id = c.id
                WHERE a.status = 'active' AND c.name = $1
                ORDER BY ac.priority DESC, a.created_at ASC
            """, capability)
            
        return [dict(agent) for agent in agents]
    
    async def _select_best_agent(self, agents: List[Dict[str, Any]], request: ChatRequest) -> Dict[str, Any]:
        """Select the best agent from a list based on various criteria"""
        if not agents:
            raise ValueError("No agents provided for selection")
        
        # Simple selection strategy: prefer higher priority, then lower cost
        # In a production system, this could be much more sophisticated
        
        best_agent = agents[0]  # Start with first (highest priority)
        
        for agent in agents[1:]:
            agent_id = UUID(agent['id'])
            
            # Check if agent is available (not rate limited)
            if not await self._check_rate_limit(agent_id):
                continue
                
            # Could add more sophisticated selection logic here:
            # - Current load
            # - Response time history
            # - Cost optimization
            # - Model capabilities
            
            if agent['priority'] > best_agent['priority']:
                best_agent = agent
        
        return best_agent
    
    async def _load_single_agent(self, agent_id: UUID):
        """Load a single agent by ID"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            agent_data = await conn.fetchrow("""
                SELECT * FROM agents WHERE id = $1 AND status = 'active'
            """, agent_id)
            
        if agent_data:
            agent_dict = dict(agent_data)
            # Parse JSON fields
            import json
            agent_dict['capabilities'] = json.loads(agent_dict['capabilities'])
            agent_dict['config'] = json.loads(agent_dict['config'])
            agent_dict['metadata'] = json.loads(agent_dict['metadata'])
            
            provider = await self._create_provider_instance(agent_dict)
            if provider:
                self.active_providers[str(agent_id)] = provider
    
    async def _check_rate_limit(self, agent_id: UUID) -> bool:
        """Check if agent is within rate limits"""
        agent_id_str = str(agent_id)
        
        # Get current usage for today
        async with self.db_manager.postgres_pool.acquire() as conn:
            usage = await conn.fetchrow("""
                SELECT * FROM agent_usage 
                WHERE agent_id = $1 AND created_date = CURRENT_DATE
            """, agent_id)
        
        if not usage:
            return True  # No usage recorded yet
        
        # Simple rate limiting logic - can be made more sophisticated
        max_requests_per_day = 10000  # Default limit
        max_tokens_per_hour = 1000000  # Default limit
        
        if usage['request_count'] >= max_requests_per_day:
            return False
            
        # Could add hourly token limits, etc.
        return True
    
    async def _update_rate_limit(self, agent_id: UUID, usage: Dict[str, int]):
        """Update rate limiting counters"""
        # This could track more granular rate limiting
        # For now, usage is already tracked in chat_with_agent
        pass
    
    async def get_agent_stats(self, agent_id: UUID) -> Dict[str, Any]:
        """Get comprehensive statistics for an agent"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            # Get basic agent info
            agent = await conn.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Get usage stats for last 30 days
            usage_stats = await conn.fetch("""
                SELECT 
                    created_date,
                    request_count,
                    token_usage,
                    cost_cents,
                    error_count,
                    success_count
                FROM agent_usage 
                WHERE agent_id = $1 AND created_date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY created_date DESC
            """, agent_id)
            
            # Get recent health checks
            health_logs = await conn.fetch("""
                SELECT * FROM agent_health_logs 
                WHERE agent_id = $1 
                ORDER BY checked_at DESC 
                LIMIT 10
            """, agent_id)
            
        # Calculate totals
        total_requests = sum(stat['request_count'] for stat in usage_stats)
        total_cost = sum(stat['cost_cents'] for stat in usage_stats)
        total_errors = sum(stat['error_count'] for stat in usage_stats)
        total_success = sum(stat['success_count'] for stat in usage_stats)
        
        return {
            "agent": dict(agent),
            "stats": {
                "total_requests": total_requests,
                "total_cost_cents": total_cost,
                "total_errors": total_errors,
                "total_success": total_success,
                "success_rate": total_success / max(total_requests, 1),
                "avg_cost_per_request": total_cost / max(total_requests, 1)
            },
            "usage_history": [dict(stat) for stat in usage_stats],
            "health_history": [dict(log) for log in health_logs],
            "is_active": str(agent_id) in self.active_providers
        }
    
    async def reload_agent(self, agent_id: UUID) -> Dict[str, Any]:
        """Reload an agent's configuration and restart if needed"""
        agent_id_str = str(agent_id)
        
        try:
            # Stop current provider if running
            if agent_id_str in self.active_providers:
                await self.active_providers[agent_id_str].cleanup()
                del self.active_providers[agent_id_str]
            
            # Reload agent
            await self._load_single_agent(agent_id)
            
            is_loaded = agent_id_str in self.active_providers
            
            return {
                "agent_id": agent_id_str,
                "reloaded": is_loaded,
                "status": "active" if is_loaded else "failed"
            }
            
        except Exception as e:
            logger.error("Failed to reload agent", agent_id=agent_id_str, error=str(e))
            return {
                "agent_id": agent_id_str,
                "reloaded": False,
                "status": "error",
                "error": str(e)
            }
    
    async def get_all_capabilities(self) -> List[Dict[str, Any]]:
        """Get all available capabilities across all agents"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            capabilities = await conn.fetch("""
                SELECT 
                    c.*,
                    COUNT(ac.agent_id) as agent_count,
                    AVG(ac.priority) as avg_priority
                FROM capabilities c
                LEFT JOIN agent_capabilities ac ON c.id = ac.capability_id
                LEFT JOIN agents a ON ac.agent_id = a.id AND a.status = 'active'
                GROUP BY c.id, c.name, c.category, c.description, c.parameters, c.created_at
                ORDER BY c.category, c.name
            """)
            
        return [dict(cap) for cap in capabilities]
    
    async def cleanup(self):
        """Cleanup all providers and resources"""
        for provider in self.active_providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error("Error cleaning up provider", error=str(e))
        
        self.active_providers.clear()
        await super().cleanup()