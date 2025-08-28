# ABOUTME: Vault integration for Betty's Execution Safety & Guardrails Framework
# ABOUTME: Enterprise-grade secret management with automatic rotation and secure credential handling

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import base64
import secrets
import structlog
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import aiohttp
import asyncio
from cryptography.fernet import Fernet

from core.vault_client import vault_client
from core.audit_compliance import compliance_orchestrator, AuditEventType, AuditSeverity

logger = structlog.get_logger(__name__)

class SecretType(Enum):
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    API_KEY = "api_key"
    DATABASE_CREDENTIAL = "database_credential"
    SERVICE_CERTIFICATE = "service_certificate"
    AGENT_CREDENTIAL = "agent_credential"
    PATTERN_SIGNATURE_KEY = "pattern_signature_key"

class SecretStatus(Enum):
    ACTIVE = "active"
    ROTATING = "rotating"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"

@dataclass
class SecretMetadata:
    """Metadata for secrets stored in Vault"""
    id: UUID = field(default_factory=uuid4)
    secret_type: SecretType = SecretType.API_KEY
    path: str = ""
    status: SecretStatus = SecretStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    rotation_interval_days: int = 90
    last_rotated: Optional[datetime] = None
    rotation_count: int = 0
    
    # Usage tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    # Security attributes
    requires_approval: bool = False
    approved_users: Set[UUID] = field(default_factory=set)
    approved_services: Set[str] = field(default_factory=set)
    
    # Audit trail
    created_by: Optional[UUID] = None
    last_modified_by: Optional[UUID] = None
    
    def should_rotate(self) -> bool:
        """Check if secret should be rotated"""
        if not self.last_rotated:
            return datetime.utcnow() - self.created_at > timedelta(days=self.rotation_interval_days)
        
        return datetime.utcnow() - self.last_rotated > timedelta(days=self.rotation_interval_days)
    
    def is_expired(self) -> bool:
        """Check if secret has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def update_access(self):
        """Update access tracking"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

class VaultSecretManager:
    """Enhanced secret management with Vault integration"""
    
    def __init__(self):
        self.secret_metadata: Dict[str, SecretMetadata] = {}
        self.vault_client = vault_client
        self.secret_paths = {
            SecretType.JWT_SECRET: "betty/auth/jwt_secrets",
            SecretType.ENCRYPTION_KEY: "betty/encryption/keys",
            SecretType.API_KEY: "betty/api/keys",
            SecretType.DATABASE_CREDENTIAL: "betty/database/credentials",
            SecretType.SERVICE_CERTIFICATE: "betty/certificates/services",
            SecretType.AGENT_CREDENTIAL: "betty/agents/credentials",
            SecretType.PATTERN_SIGNATURE_KEY: "betty/patterns/signature_keys"
        }
        self.rotation_lock = asyncio.Lock()
    
    async def store_secret(
        self,
        secret_type: SecretType,
        secret_name: str,
        secret_value: Any,
        user_id: Optional[UUID] = None,
        metadata_overrides: Optional[Dict[str, Any]] = None
    ) -> SecretMetadata:
        """Store secret in Vault with metadata"""
        
        # Create secret metadata
        metadata = SecretMetadata(
            secret_type=secret_type,
            path=f"{self.secret_paths[secret_type]}/{secret_name}",
            created_by=user_id
        )
        
        # Apply metadata overrides
        if metadata_overrides:
            for key, value in metadata_overrides.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
        
        # Prepare secret data for Vault
        secret_data = {
            "value": secret_value,
            "metadata": {
                "id": str(metadata.id),
                "secret_type": secret_type.value,
                "created_at": metadata.created_at.isoformat(),
                "created_by": str(user_id) if user_id else None,
                "rotation_interval_days": metadata.rotation_interval_days
            }
        }
        
        try:
            # Store in Vault
            await self.vault_client.write_secret(metadata.path, secret_data)
            
            # Store metadata locally
            self.secret_metadata[metadata.path] = metadata
            
            # Log audit event
            await compliance_orchestrator.log_audit_event(
                AuditEventType.SYSTEM_CONFIGURATION,
                f"Secret stored in Vault: {secret_name}",
                user_id=user_id,
                severity=AuditSeverity.INFO,
                metadata={
                    "secret_type": secret_type.value,
                    "secret_path": metadata.path,
                    "vault_operation": "store"
                }
            )
            
            logger.info("Secret stored in Vault",
                       secret_name=secret_name,
                       secret_type=secret_type.value,
                       path=metadata.path)
            
            return metadata
            
        except Exception as e:
            logger.error("Failed to store secret in Vault",
                        secret_name=secret_name,
                        error=str(e))
            
            # Log audit event for failure
            await compliance_orchestrator.log_audit_event(
                AuditEventType.SYSTEM_CONFIGURATION,
                f"Failed to store secret in Vault: {secret_name}",
                user_id=user_id,
                severity=AuditSeverity.ERROR,
                metadata={
                    "error": str(e),
                    "secret_type": secret_type.value,
                    "vault_operation": "store_failed"
                }
            )
            
            raise
    
    async def retrieve_secret(
        self,
        secret_path: str,
        user_id: Optional[UUID] = None,
        service_name: Optional[str] = None
    ) -> Optional[Any]:
        """Retrieve secret from Vault with access control"""
        
        # Check if we have metadata for this secret
        if secret_path not in self.secret_metadata:
            # Try to load metadata from Vault
            await self._load_secret_metadata(secret_path)
        
        metadata = self.secret_metadata.get(secret_path)
        if not metadata:
            logger.warning("Secret metadata not found", secret_path=secret_path)
            return None
        
        # Check if secret is expired or revoked
        if metadata.status == SecretStatus.REVOKED:
            logger.warning("Attempted access to revoked secret", secret_path=secret_path)
            return None
        
        if metadata.is_expired():
            logger.warning("Attempted access to expired secret", secret_path=secret_path)
            return None
        
        # Check access permissions
        if metadata.requires_approval:
            if user_id and user_id not in metadata.approved_users:
                logger.warning("Unauthorized secret access attempt",
                             secret_path=secret_path,
                             user_id=str(user_id))
                return None
            
            if service_name and service_name not in metadata.approved_services:
                logger.warning("Unauthorized service secret access attempt",
                             secret_path=secret_path,
                             service_name=service_name)
                return None
        
        try:
            # Retrieve from Vault
            secret_data = await self.vault_client.read_secret(secret_path)
            if not secret_data:
                return None
            
            # Update access tracking
            metadata.update_access()
            
            # Log audit event
            await compliance_orchestrator.log_audit_event(
                AuditEventType.DATA_ACCESS,
                f"Secret accessed from Vault: {secret_path}",
                user_id=user_id,
                severity=AuditSeverity.INFO,
                metadata={
                    "secret_type": metadata.secret_type.value,
                    "secret_path": secret_path,
                    "service_name": service_name,
                    "vault_operation": "retrieve",
                    "access_count": metadata.access_count
                }
            )
            
            logger.debug("Secret retrieved from Vault",
                        secret_path=secret_path,
                        access_count=metadata.access_count)
            
            return secret_data.get("value")
            
        except Exception as e:
            logger.error("Failed to retrieve secret from Vault",
                        secret_path=secret_path,
                        error=str(e))
            
            # Log audit event for failure
            await compliance_orchestrator.log_audit_event(
                AuditEventType.DATA_ACCESS,
                f"Failed to retrieve secret from Vault: {secret_path}",
                user_id=user_id,
                severity=AuditSeverity.ERROR,
                metadata={
                    "error": str(e),
                    "secret_path": secret_path,
                    "vault_operation": "retrieve_failed"
                }
            )
            
            return None
    
    async def rotate_secret(
        self,
        secret_path: str,
        user_id: Optional[UUID] = None,
        force: bool = False
    ) -> bool:
        """Rotate secret with automatic generation"""
        
        async with self.rotation_lock:
            metadata = self.secret_metadata.get(secret_path)
            if not metadata:
                logger.error("Cannot rotate secret: metadata not found", secret_path=secret_path)
                return False
            
            # Check if rotation is needed
            if not force and not metadata.should_rotate():
                logger.info("Secret rotation not needed", secret_path=secret_path)
                return True
            
            # Set rotation status
            original_status = metadata.status
            metadata.status = SecretStatus.ROTATING
            
            try:
                # Generate new secret based on type
                new_secret = await self._generate_new_secret(metadata.secret_type)
                
                # Create new secret data
                secret_data = {
                    "value": new_secret,
                    "metadata": {
                        "id": str(metadata.id),
                        "secret_type": metadata.secret_type.value,
                        "created_at": metadata.created_at.isoformat(),
                        "last_rotated": datetime.utcnow().isoformat(),
                        "rotation_count": metadata.rotation_count + 1,
                        "rotated_by": str(user_id) if user_id else None
                    }
                }
                
                # Store rotated secret in Vault
                await self.vault_client.write_secret(secret_path, secret_data)
                
                # Update metadata
                metadata.status = SecretStatus.ACTIVE
                metadata.last_rotated = datetime.utcnow()
                metadata.rotation_count += 1
                metadata.last_modified_by = user_id
                
                # Log audit event
                await compliance_orchestrator.log_audit_event(
                    AuditEventType.SYSTEM_CONFIGURATION,
                    f"Secret rotated in Vault: {secret_path}",
                    user_id=user_id,
                    severity=AuditSeverity.INFO,
                    metadata={
                        "secret_type": metadata.secret_type.value,
                        "secret_path": secret_path,
                        "rotation_count": metadata.rotation_count,
                        "vault_operation": "rotate"
                    }
                )
                
                logger.info("Secret rotated successfully",
                           secret_path=secret_path,
                           rotation_count=metadata.rotation_count)
                
                return True
                
            except Exception as e:
                # Restore original status on failure
                metadata.status = original_status
                
                logger.error("Failed to rotate secret",
                            secret_path=secret_path,
                            error=str(e))
                
                # Log audit event for failure
                await compliance_orchestrator.log_audit_event(
                    AuditEventType.SYSTEM_CONFIGURATION,
                    f"Failed to rotate secret: {secret_path}",
                    user_id=user_id,
                    severity=AuditSeverity.ERROR,
                    metadata={
                        "error": str(e),
                        "secret_path": secret_path,
                        "vault_operation": "rotate_failed"
                    }
                )
                
                return False
    
    async def revoke_secret(
        self,
        secret_path: str,
        user_id: Optional[UUID] = None,
        reason: str = ""
    ) -> bool:
        """Revoke secret access"""
        
        metadata = self.secret_metadata.get(secret_path)
        if not metadata:
            return False
        
        # Update metadata
        metadata.status = SecretStatus.REVOKED
        metadata.last_modified_by = user_id
        
        try:
            # Delete from Vault
            await self.vault_client.delete_secret(secret_path)
            
            # Log audit event
            await compliance_orchestrator.log_audit_event(
                AuditEventType.SYSTEM_CONFIGURATION,
                f"Secret revoked: {secret_path}",
                user_id=user_id,
                severity=AuditSeverity.WARNING,
                metadata={
                    "secret_type": metadata.secret_type.value,
                    "secret_path": secret_path,
                    "reason": reason,
                    "vault_operation": "revoke"
                }
            )
            
            logger.warning("Secret revoked",
                          secret_path=secret_path,
                          reason=reason)
            
            return True
            
        except Exception as e:
            logger.error("Failed to revoke secret",
                        secret_path=secret_path,
                        error=str(e))
            return False
    
    async def _generate_new_secret(self, secret_type: SecretType) -> str:
        """Generate new secret based on type"""
        
        if secret_type == SecretType.JWT_SECRET:
            # Generate 64-byte JWT secret
            return base64.urlsafe_b64encode(secrets.token_bytes(64)).decode()
        
        elif secret_type == SecretType.ENCRYPTION_KEY:
            # Generate Fernet key
            return base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        
        elif secret_type == SecretType.API_KEY:
            # Generate API key with prefix
            return f"betty_{secrets.token_urlsafe(48)}"
        
        elif secret_type == SecretType.DATABASE_CREDENTIAL:
            # Generate secure password
            return secrets.token_urlsafe(32)
        
        else:
            # Default secure token
            return secrets.token_urlsafe(64)
    
    async def _load_secret_metadata(self, secret_path: str):
        """Load secret metadata from Vault"""
        try:
            secret_data = await self.vault_client.read_secret(secret_path)
            if secret_data and "metadata" in secret_data:
                vault_metadata = secret_data["metadata"]
                
                metadata = SecretMetadata(
                    id=UUID(vault_metadata.get("id", str(uuid4()))),
                    secret_type=SecretType(vault_metadata.get("secret_type", SecretType.API_KEY.value)),
                    path=secret_path,
                    created_at=datetime.fromisoformat(vault_metadata.get("created_at", datetime.utcnow().isoformat())),
                    rotation_interval_days=vault_metadata.get("rotation_interval_days", 90)
                )
                
                if vault_metadata.get("last_rotated"):
                    metadata.last_rotated = datetime.fromisoformat(vault_metadata["last_rotated"])
                    metadata.rotation_count = vault_metadata.get("rotation_count", 0)
                
                self.secret_metadata[secret_path] = metadata
                
        except Exception as e:
            logger.debug("Could not load metadata from Vault", secret_path=secret_path, error=str(e))
    
    async def rotate_all_expired_secrets(self, user_id: Optional[UUID] = None) -> Dict[str, bool]:
        """Rotate all secrets that are due for rotation"""
        
        results = {}
        
        for secret_path, metadata in self.secret_metadata.items():
            if metadata.should_rotate() and metadata.status == SecretStatus.ACTIVE:
                success = await self.rotate_secret(secret_path, user_id)
                results[secret_path] = success
        
        successful_rotations = sum(1 for success in results.values() if success)
        total_rotations = len(results)
        
        logger.info("Automatic secret rotation completed",
                   successful_rotations=successful_rotations,
                   total_rotations=total_rotations)
        
        return results
    
    async def get_secret_inventory(self) -> Dict[str, Any]:
        """Get inventory of all managed secrets"""
        
        inventory = {
            "total_secrets": len(self.secret_metadata),
            "by_type": {},
            "by_status": {},
            "rotation_needed": 0,
            "expired_secrets": 0,
            "high_access_secrets": []
        }
        
        for metadata in self.secret_metadata.values():
            # Count by type
            secret_type = metadata.secret_type.value
            inventory["by_type"][secret_type] = inventory["by_type"].get(secret_type, 0) + 1
            
            # Count by status
            status = metadata.status.value
            inventory["by_status"][status] = inventory["by_status"].get(status, 0) + 1
            
            # Check rotation needs
            if metadata.should_rotate():
                inventory["rotation_needed"] += 1
            
            # Check expiry
            if metadata.is_expired():
                inventory["expired_secrets"] += 1
            
            # Identify high-access secrets
            if metadata.access_count > 1000:
                inventory["high_access_secrets"].append({
                    "path": metadata.path,
                    "type": secret_type,
                    "access_count": metadata.access_count,
                    "last_accessed": metadata.last_accessed.isoformat() if metadata.last_accessed else None
                })
        
        return inventory

class SecurityKeyGenerator:
    """Generate security keys for different components"""
    
    @staticmethod
    async def generate_jwt_secret(vault_manager: VaultSecretManager, user_id: Optional[UUID] = None) -> str:
        """Generate and store JWT secret"""
        
        secret_name = "default"
        jwt_secret = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode()
        
        metadata = await vault_manager.store_secret(
            SecretType.JWT_SECRET,
            secret_name,
            jwt_secret,
            user_id,
            {"rotation_interval_days": 90}
        )
        
        return metadata.path
    
    @staticmethod
    async def generate_encryption_key(
        vault_manager: VaultSecretManager,
        key_name: str,
        user_id: Optional[UUID] = None
    ) -> str:
        """Generate and store encryption key"""
        
        encryption_key = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        
        metadata = await vault_manager.store_secret(
            SecretType.ENCRYPTION_KEY,
            key_name,
            encryption_key,
            user_id,
            {"rotation_interval_days": 30}  # More frequent rotation for encryption keys
        )
        
        return metadata.path
    
    @staticmethod
    async def generate_agent_credential(
        vault_manager: VaultSecretManager,
        agent_id: str,
        user_id: Optional[UUID] = None
    ) -> str:
        """Generate and store agent credential"""
        
        # Generate RSA key pair for agent (simplified)
        agent_secret = {
            "agent_id": agent_id,
            "private_key": base64.urlsafe_b64encode(secrets.token_bytes(2048)).decode(),
            "public_key": base64.urlsafe_b64encode(secrets.token_bytes(512)).decode(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        metadata = await vault_manager.store_secret(
            SecretType.AGENT_CREDENTIAL,
            agent_id,
            json.dumps(agent_secret),
            user_id,
            {"rotation_interval_days": 60}
        )
        
        return metadata.path
    
    @staticmethod
    async def generate_pattern_signature_key(
        vault_manager: VaultSecretManager,
        pattern_source: str,
        user_id: Optional[UUID] = None
    ) -> str:
        """Generate and store pattern signature key"""
        
        signature_key = {
            "source": pattern_source,
            "private_key": base64.urlsafe_b64encode(secrets.token_bytes(2048)).decode(),
            "public_key": base64.urlsafe_b64encode(secrets.token_bytes(512)).decode(),
            "algorithm": "RSA-SHA256"
        }
        
        metadata = await vault_manager.store_secret(
            SecretType.PATTERN_SIGNATURE_KEY,
            pattern_source.replace("/", "_"),
            json.dumps(signature_key),
            user_id,
            {"rotation_interval_days": 180}  # Less frequent rotation for signing keys
        )
        
        return metadata.path

class VaultSecurityIntegration:
    """Main integration class for Vault with Betty's security framework"""
    
    def __init__(self):
        self.vault_manager = VaultSecretManager()
        self.key_generator = SecurityKeyGenerator()
        self.rotation_scheduler_running = False
    
    async def initialize_security_secrets(self, user_id: Optional[UUID] = None) -> Dict[str, str]:
        """Initialize core security secrets"""
        
        secret_paths = {}
        
        # Generate JWT secret
        jwt_path = await self.key_generator.generate_jwt_secret(self.vault_manager, user_id)
        secret_paths["jwt_secret"] = jwt_path
        
        # Generate master encryption key
        encryption_path = await self.key_generator.generate_encryption_key(
            self.vault_manager, "master_key", user_id
        )
        secret_paths["master_encryption_key"] = encryption_path
        
        # Generate pattern signature key
        signature_path = await self.key_generator.generate_pattern_signature_key(
            self.vault_manager, "betty_official", user_id
        )
        secret_paths["pattern_signature_key"] = signature_path
        
        logger.info("Core security secrets initialized",
                   secret_count=len(secret_paths))
        
        return secret_paths
    
    async def start_rotation_scheduler(self):
        """Start automatic secret rotation scheduler"""
        
        if self.rotation_scheduler_running:
            return
        
        self.rotation_scheduler_running = True
        
        async def rotation_task():
            while self.rotation_scheduler_running:
                try:
                    # Run rotation every 24 hours
                    await asyncio.sleep(24 * 3600)
                    
                    if self.rotation_scheduler_running:
                        results = await self.vault_manager.rotate_all_expired_secrets()
                        
                        if results:
                            successful = sum(1 for success in results.values() if success)
                            total = len(results)
                            
                            await compliance_orchestrator.log_audit_event(
                                AuditEventType.SYSTEM_CONFIGURATION,
                                f"Automatic secret rotation: {successful}/{total} successful",
                                severity=AuditSeverity.INFO,
                                metadata={
                                    "rotation_results": results,
                                    "scheduler": "automatic"
                                }
                            )
                        
                except Exception as e:
                    logger.error("Error in rotation scheduler", error=str(e))
                    await asyncio.sleep(3600)  # Wait 1 hour before retry
        
        # Start background task
        asyncio.create_task(rotation_task())
        
        logger.info("Secret rotation scheduler started")
    
    async def stop_rotation_scheduler(self):
        """Stop automatic secret rotation scheduler"""
        self.rotation_scheduler_running = False
        logger.info("Secret rotation scheduler stopped")
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get Vault security metrics"""
        
        inventory = await self.vault_manager.get_secret_inventory()
        
        return {
            "vault_integration": {
                "total_secrets_managed": inventory["total_secrets"],
                "secrets_by_type": inventory["by_type"],
                "secrets_by_status": inventory["by_status"],
                "rotation_needed": inventory["rotation_needed"],
                "expired_secrets": inventory["expired_secrets"],
                "scheduler_running": self.rotation_scheduler_running
            },
            "last_updated": datetime.utcnow().isoformat()
        }

# Global Vault security integration
vault_security_integration = VaultSecurityIntegration()