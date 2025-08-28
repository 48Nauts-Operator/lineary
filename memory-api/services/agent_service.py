# ABOUTME: Core agent registration and management service for BETTY Multi-Agent Platform
# ABOUTME: Handles agent lifecycle, credential management, and provider integrations

import asyncio
import json
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
import structlog
import asyncpg
import redis.asyncio as redis
import hvac
from pydantic import BaseModel, Field

from services.base_service import BaseService
from core.config import get_settings

logger = structlog.get_logger(__name__)

# Pydantic models for type safety
class AgentRegistration(BaseModel):
    """Agent registration request model"""
    name: str = Field(..., description="Unique agent identifier")
    display_name: str = Field(..., description="Human-readable agent name")
    agent_type: str = Field(..., description="Type: api_based, local_process, or custom")
    provider: str = Field(..., description="Provider: claude, openai, gemini, devon, custom")
    description: Optional[str] = None
    version: str = Field(default="1.0.0")
    capabilities: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    credentials: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    """Agent configuration model"""
    environment: str = Field(default="production")
    config_key: str
    config_value: Any
    is_sensitive: bool = Field(default=False)

class AgentUsage(BaseModel):
    """Agent usage tracking model"""
    request_count: int = Field(default=0)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    cost_cents: int = Field(default=0)
    rate_limit_hits: int = Field(default=0)
    error_count: int = Field(default=0)
    success_count: int = Field(default=0)

class LocalProcessConfig(BaseModel):
    """Local process configuration model"""
    port: Optional[int] = None
    working_directory: str
    command_line: str
    environment_vars: Dict[str, str] = Field(default_factory=dict)
    max_restarts: int = Field(default=3)

class AgentService(BaseService):
    """Core service for agent registration and management"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.vault_client = None
        self.settings = get_settings()
        self.local_processes: Dict[str, subprocess.Popen] = {}
        
    async def initialize(self):
        """Initialize the agent service and Vault connection"""
        await super().initialize()
        await self._initialize_vault()
        await self._start_health_monitor()
        
    async def _initialize_vault(self):
        """Initialize HashiCorp Vault connection"""
        try:
            vault_url = "https://vault.blockonauts.io:8200"
            self.vault_client = hvac.Client(url=vault_url)
            
            # Authenticate with Vault (you'll need to set up authentication)
            # For now, we'll assume token-based auth
            if hasattr(self.settings, 'vault_token'):
                self.vault_client.token = self.settings.vault_token
                
            if self.vault_client.is_authenticated():
                logger.info("Successfully connected to Vault", url=vault_url)
            else:
                logger.warning("Vault connection established but not authenticated")
                
        except Exception as e:
            logger.error("Failed to connect to Vault", error=str(e))
            self.vault_client = None

    async def register_agent(self, registration: AgentRegistration) -> Dict[str, Any]:
        """Register a new agent in the system"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            async with conn.transaction():
                try:
                    # Check if agent name already exists
                    existing = await conn.fetchrow(
                        "SELECT id FROM agents WHERE name = $1", registration.name
                    )
                    if existing:
                        raise ValueError(f"Agent '{registration.name}' already exists")
                    
                    # Insert agent record
                    agent_id = await conn.fetchval("""
                        INSERT INTO agents (name, display_name, agent_type, provider, 
                                          description, version, capabilities, config, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id
                    """, registration.name, registration.display_name, registration.agent_type,
                        registration.provider, registration.description, registration.version,
                        json.dumps(registration.capabilities), json.dumps(registration.config),
                        json.dumps(registration.metadata))
                    
                    # Store credentials in Vault
                    if registration.credentials:
                        await self._store_credentials(agent_id, registration.credentials)
                    
                    # Set up capabilities
                    await self._assign_capabilities(conn, agent_id, registration.capabilities)
                    
                    # Initialize usage tracking
                    await conn.execute("""
                        INSERT INTO agent_usage (agent_id) VALUES ($1)
                    """, agent_id)
                    
                    # Set up local process if needed
                    if registration.agent_type == 'local_process':
                        await self._setup_local_process(conn, agent_id, registration.config)
                    
                    logger.info("Agent registered successfully", 
                              agent_id=str(agent_id), name=registration.name)
                    
                    return {
                        "agent_id": str(agent_id),
                        "name": registration.name,
                        "status": "registered",
                        "message": "Agent registered successfully"
                    }
                    
                except Exception as e:
                    logger.error("Failed to register agent", error=str(e), name=registration.name)
                    raise

    async def _store_credentials(self, agent_id: UUID, credentials: Dict[str, str]):
        """Store agent credentials securely in Vault"""
        if not self.vault_client:
            logger.warning("Vault not available, skipping credential storage")
            return
            
        vault_path = f"betty/agents/{agent_id}"
        
        try:
            # Store credentials in Vault
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=vault_path,
                secret=credentials
            )
            
            # Store references in database
            async with self.db_manager.postgres_pool.acquire() as conn:
                for key, value in credentials.items():
                    await conn.execute("""
                        INSERT INTO agent_credentials (agent_id, credential_type, vault_path, vault_key)
                        VALUES ($1, $2, $3, $4)
                    """, agent_id, 'api_key', vault_path, key)
                    
            logger.info("Credentials stored securely", agent_id=str(agent_id))
            
        except Exception as e:
            logger.error("Failed to store credentials", error=str(e), agent_id=str(agent_id))
            raise

    async def get_agent_credentials(self, agent_id: UUID) -> Dict[str, str]:
        """Retrieve agent credentials from Vault"""
        if not self.vault_client:
            return {}
            
        async with self.db_manager.postgres_pool.acquire() as conn:
            credentials_refs = await conn.fetch("""
                SELECT vault_path, vault_key FROM agent_credentials 
                WHERE agent_id = $1 AND is_active = true
            """, agent_id)
            
        credentials = {}
        for ref in credentials_refs:
            try:
                secret = self.vault_client.secrets.kv.v2.read_secret_version(
                    path=ref['vault_path']
                )
                if ref['vault_key'] in secret['data']['data']:
                    credentials[ref['vault_key']] = secret['data']['data'][ref['vault_key']]
            except Exception as e:
                logger.error("Failed to retrieve credential", 
                           error=str(e), vault_path=ref['vault_path'])
                
        return credentials

    async def _assign_capabilities(self, conn, agent_id: UUID, capability_names: List[str]):
        """Assign capabilities to an agent"""
        for capability_name in capability_names:
            # Get or create capability
            capability_id = await conn.fetchval("""
                INSERT INTO capabilities (name, category, description)
                VALUES ($1, 'custom', 'Custom capability')
                ON CONFLICT (name) DO UPDATE SET name = capabilities.name
                RETURNING id
            """, capability_name)
            
            # Assign to agent
            await conn.execute("""
                INSERT INTO agent_capabilities (agent_id, capability_id, priority)
                VALUES ($1, $2, 5)
                ON CONFLICT (agent_id, capability_id) DO NOTHING
            """, agent_id, capability_id)

    async def _setup_local_process(self, conn, agent_id: UUID, config: Dict[str, Any]):
        """Set up local process configuration"""
        process_config = LocalProcessConfig(**config.get('process', {}))
        
        await conn.execute("""
            INSERT INTO local_processes (agent_id, port, working_directory, 
                                       command_line, environment_vars, max_restarts)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, agent_id, process_config.port, process_config.working_directory,
            process_config.command_line, json.dumps(process_config.environment_vars),
            process_config.max_restarts)

    async def start_agent(self, agent_id: UUID) -> Dict[str, Any]:
        """Start an agent (particularly for local processes)"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            agent = await conn.fetchrow("""
                SELECT * FROM agents WHERE id = $1
            """, agent_id)
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            if agent['agent_type'] == 'local_process':
                success = await self._start_local_process(agent_id)
                status = 'active' if success else 'failed'
            else:
                # For API-based agents, just mark as active
                status = 'active'
                success = True
            
            # Update agent status
            await conn.execute("""
                UPDATE agents SET status = $1, updated_at = NOW() WHERE id = $2
            """, status, agent_id)
            
            return {
                "agent_id": str(agent_id),
                "status": status,
                "success": success
            }

    async def _start_local_process(self, agent_id: UUID) -> bool:
        """Start a local process for an agent"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            process_config = await conn.fetchrow("""
                SELECT * FROM local_processes WHERE agent_id = $1
            """, agent_id)
            
            if not process_config:
                return False
                
        try:
            # Start the process
            env = dict(process_config['environment_vars'])  # Convert from JSON
            process = subprocess.Popen(
                process_config['command_line'].split(),
                cwd=process_config['working_directory'],
                env=env
            )
            
            # Store process reference
            self.local_processes[str(agent_id)] = process
            
            # Update database
            async with self.db_manager.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE local_processes 
                    SET process_id = $1, status = 'running', started_at = NOW()
                    WHERE agent_id = $2
                """, process.pid, agent_id)
            
            logger.info("Local process started", agent_id=str(agent_id), pid=process.pid)
            return True
            
        except Exception as e:
            logger.error("Failed to start local process", error=str(e), agent_id=str(agent_id))
            return False

    async def stop_agent(self, agent_id: UUID) -> Dict[str, Any]:
        """Stop an agent"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            agent = await conn.fetchrow("""
                SELECT * FROM agents WHERE id = $1
            """, agent_id)
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            if agent['agent_type'] == 'local_process':
                success = await self._stop_local_process(agent_id)
            else:
                success = True
            
            # Update agent status
            await conn.execute("""
                UPDATE agents SET status = 'inactive', updated_at = NOW() WHERE id = $1
            """, agent_id)
            
            return {
                "agent_id": str(agent_id),
                "status": "inactive",
                "success": success
            }

    async def _stop_local_process(self, agent_id: UUID) -> bool:
        """Stop a local process for an agent"""
        agent_id_str = str(agent_id)
        
        if agent_id_str in self.local_processes:
            try:
                process = self.local_processes[agent_id_str]
                process.terminate()
                process.wait(timeout=10)  # Wait up to 10 seconds
                del self.local_processes[agent_id_str]
                
                # Update database
                async with self.db_manager.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE local_processes 
                        SET status = 'stopped', stopped_at = NOW()
                        WHERE agent_id = $1
                    """, agent_id)
                
                logger.info("Local process stopped", agent_id=str(agent_id))
                return True
                
            except Exception as e:
                logger.error("Failed to stop local process", error=str(e), agent_id=str(agent_id))
                return False
        
        return True

    async def get_agents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of registered agents"""
        query = "SELECT * FROM agents"
        params = []
        
        if status:
            query += " WHERE status = $1"
            params.append(status)
            
        query += " ORDER BY created_at DESC"
        
        async with self.db_manager.postgres_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        agents = []
        for row in rows:
            agent_data = dict(row)
            # Parse JSON fields
            agent_data['capabilities'] = json.loads(agent_data['capabilities'])
            agent_data['config'] = json.loads(agent_data['config'])
            agent_data['metadata'] = json.loads(agent_data['metadata'])
            agents.append(agent_data)
            
        return agents

    async def update_usage(self, agent_id: UUID, usage: AgentUsage):
        """Update agent usage statistics"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            await conn.execute("""
                UPDATE agent_usage 
                SET request_count = request_count + $2,
                    token_usage = $3,
                    cost_cents = cost_cents + $4,
                    rate_limit_hits = rate_limit_hits + $5,
                    error_count = error_count + $6,
                    success_count = success_count + $7,
                    updated_at = NOW()
                WHERE agent_id = $1 AND created_date = CURRENT_DATE
            """, agent_id, usage.request_count, json.dumps(usage.token_usage),
                usage.cost_cents, usage.rate_limit_hits, usage.error_count, usage.success_count)

    async def _start_health_monitor(self):
        """Start background health monitoring for agents"""
        asyncio.create_task(self._health_monitor_loop())

    async def _health_monitor_loop(self):
        """Background task to monitor agent health"""
        while True:
            try:
                await self._check_all_agents_health()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error("Health monitor error", error=str(e))
                await asyncio.sleep(60)  # Shorter retry interval on error

    async def _check_all_agents_health(self):
        """Check health of all active agents"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            agents = await conn.fetch("""
                SELECT id, name, agent_type, provider, config 
                FROM agents WHERE status = 'active'
            """)
            
        for agent in agents:
            try:
                health_status = await self._check_agent_health(agent)
                await self._log_health_check(agent['id'], health_status)
            except Exception as e:
                logger.error("Health check failed", agent_id=str(agent['id']), error=str(e))

    async def _check_agent_health(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a specific agent"""
        start_time = time.time()
        
        if agent['agent_type'] == 'local_process':
            # Check if process is still running
            agent_id_str = str(agent['id'])
            if agent_id_str in self.local_processes:
                process = self.local_processes[agent_id_str]
                if process.poll() is None:  # Process is running
                    response_time = int((time.time() - start_time) * 1000)
                    return {
                        "status": "active",
                        "response_time_ms": response_time,
                        "health_data": {"process_running": True}
                    }
                else:
                    return {
                        "status": "failed",
                        "error_message": "Process terminated unexpectedly",
                        "health_data": {"process_running": False}
                    }
            else:
                return {
                    "status": "failed",
                    "error_message": "Process not found in registry",
                    "health_data": {"process_running": False}
                }
        else:
            # For API-based agents, we could ping their endpoints
            # For now, just mark as healthy
            response_time = int((time.time() - start_time) * 1000)
            return {
                "status": "active",
                "response_time_ms": response_time,
                "health_data": {"api_available": True}
            }

    async def _log_health_check(self, agent_id: UUID, health_status: Dict[str, Any]):
        """Log health check results"""
        async with self.db_manager.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_health_logs (agent_id, status, response_time_ms, 
                                             error_message, health_data)
                VALUES ($1, $2, $3, $4, $5)
            """, agent_id, health_status['status'], 
                health_status.get('response_time_ms'),
                health_status.get('error_message'),
                json.dumps(health_status.get('health_data', {})))
            
            # Update agent's last health check
            await conn.execute("""
                UPDATE agents 
                SET last_health_check = NOW(), health_status = $2
                WHERE id = $1
            """, agent_id, health_status['status'])