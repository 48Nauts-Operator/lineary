# ABOUTME: HashiCorp Vault client integration for BETTY Multi-Agent Platform
# ABOUTME: Manages secure credential storage and retrieval for all agent providers

import hvac
import structlog
import asyncio
from typing import Dict, Any, Optional
from core.config import get_settings

logger = structlog.get_logger(__name__)

class VaultClient:
    """HashiCorp Vault client for secure credential management"""
    
    def __init__(self, vault_url: str = "https://vault.blockonauts.io:8200"):
        self.vault_url = vault_url
        self.client = None
        self.authenticated = False
        self.settings = get_settings()
        
    async def initialize(self, auth_method: str = "token", **auth_params) -> bool:
        """Initialize Vault client and authenticate"""
        try:
            self.client = hvac.Client(url=self.vault_url)
            
            # Support different authentication methods
            if auth_method == "token":
                token = auth_params.get("token") or getattr(self.settings, 'vault_token', None)
                if not token:
                    logger.error("Vault token not provided")
                    return False
                self.client.token = token
                
            elif auth_method == "userpass":
                username = auth_params.get("username")
                password = auth_params.get("password")
                if not username or not password:
                    logger.error("Username/password not provided for Vault auth")
                    return False
                    
                self.client.auth.userpass.login(
                    username=username,
                    password=password
                )
                
            elif auth_method == "approle":
                role_id = auth_params.get("role_id")
                secret_id = auth_params.get("secret_id")
                if not role_id or not secret_id:
                    logger.error("Role ID/Secret ID not provided for Vault auth")
                    return False
                    
                self.client.auth.approle.login(
                    role_id=role_id,
                    secret_id=secret_id
                )
            
            # Verify authentication
            if self.client.is_authenticated():
                self.authenticated = True
                logger.info("Successfully authenticated with Vault", url=self.vault_url)
                
                # Ensure BETTY mount exists
                await self._ensure_betty_mount()
                return True
            else:
                logger.error("Vault authentication failed")
                return False
                
        except Exception as e:
            logger.error("Failed to initialize Vault client", error=str(e))
            return False
    
    async def _ensure_betty_mount(self):
        """Ensure the BETTY secrets mount exists"""
        try:
            mounts = self.client.sys.list_auth_methods()
            
            # Check if kv mount exists for BETTY
            if 'betty/' not in self.client.sys.list_mounted_secrets_engines():
                # Create KV v2 mount for BETTY
                self.client.sys.enable_secrets_engine(
                    backend_type='kv',
                    path='betty',
                    options={'version': '2'}
                )
                logger.info("Created BETTY secrets mount in Vault")
            
        except Exception as e:
            logger.warning("Could not ensure BETTY mount exists", error=str(e))
    
    async def store_agent_credentials(self, agent_id: str, credentials: Dict[str, str]) -> bool:
        """Store agent credentials securely in Vault"""
        if not self.authenticated:
            logger.error("Vault client not authenticated")
            return False
            
        try:
            path = f"betty/agents/{agent_id}"
            
            # Store credentials with metadata
            secret_data = {
                "data": credentials,
                "metadata": {
                    "agent_id": agent_id,
                    "created_by": "betty-agent-service",
                    "version": "1"
                }
            }
            
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=credentials
            )
            
            logger.info("Agent credentials stored in Vault", agent_id=agent_id, path=path)
            return True
            
        except Exception as e:
            logger.error("Failed to store agent credentials", agent_id=agent_id, error=str(e))
            return False
    
    async def get_agent_credentials(self, agent_id: str) -> Dict[str, str]:
        """Retrieve agent credentials from Vault"""
        if not self.authenticated:
            logger.error("Vault client not authenticated")
            return {}
            
        try:
            path = f"betty/agents/{agent_id}"
            
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            
            if response and 'data' in response and 'data' in response['data']:
                credentials = response['data']['data']
                logger.debug("Retrieved agent credentials", agent_id=agent_id)
                return credentials
            else:
                logger.warning("No credentials found for agent", agent_id=agent_id)
                return {}
                
        except hvac.exceptions.InvalidPath:
            logger.warning("Credentials not found for agent", agent_id=agent_id)
            return {}
        except Exception as e:
            logger.error("Failed to retrieve agent credentials", agent_id=agent_id, error=str(e))
            return {}
    
    async def update_agent_credentials(self, agent_id: str, credentials: Dict[str, str]) -> bool:
        """Update existing agent credentials"""
        return await self.store_agent_credentials(agent_id, credentials)
    
    async def delete_agent_credentials(self, agent_id: str) -> bool:
        """Delete agent credentials from Vault"""
        if not self.authenticated:
            logger.error("Vault client not authenticated")
            return False
            
        try:
            path = f"betty/agents/{agent_id}"
            
            # Delete all versions of the secret
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)
            
            logger.info("Agent credentials deleted from Vault", agent_id=agent_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete agent credentials", agent_id=agent_id, error=str(e))
            return False
    
    async def list_agent_credentials(self) -> list[str]:
        """List all agent IDs that have stored credentials"""
        if not self.authenticated:
            logger.error("Vault client not authenticated")
            return []
            
        try:
            # List all secrets under betty/agents/
            response = self.client.secrets.kv.v2.list_secrets(path="betty/agents")
            
            if response and 'data' in response and 'keys' in response['data']:
                agent_ids = response['data']['keys']
                return agent_ids
            else:
                return []
                
        except Exception as e:
            logger.error("Failed to list agent credentials", error=str(e))
            return []
    
    async def store_provider_config(self, provider: str, config: Dict[str, Any]) -> bool:
        """Store provider-specific configuration"""
        if not self.authenticated:
            return False
            
        try:
            path = f"betty/providers/{provider}"
            
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=config
            )
            
            logger.info("Provider config stored", provider=provider)
            return True
            
        except Exception as e:
            logger.error("Failed to store provider config", provider=provider, error=str(e))
            return False
    
    async def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Retrieve provider-specific configuration"""
        if not self.authenticated:
            return {}
            
        try:
            path = f"betty/providers/{provider}"
            
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            
            if response and 'data' in response and 'data' in response['data']:
                return response['data']['data']
            else:
                return {}
                
        except hvac.exceptions.InvalidPath:
            return {}
        except Exception as e:
            logger.error("Failed to get provider config", provider=provider, error=str(e))
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Check Vault connectivity and authentication status"""
        try:
            if not self.client:
                return {"status": "error", "message": "Client not initialized"}
            
            # Check if we can reach Vault
            health = self.client.sys.read_health_status()
            
            return {
                "status": "healthy" if self.authenticated else "unauthenticated",
                "vault_url": self.vault_url,
                "authenticated": self.authenticated,
                "vault_health": health
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "vault_url": self.vault_url,
                "authenticated": False
            }

# Global Vault client instance
vault_client = VaultClient()