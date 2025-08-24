# ABOUTME: JWT token management service for BETTY Memory System
# ABOUTME: Handles token generation, validation, refresh and blacklisting with Vault integration

import jwt
import secrets
import structlog
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union, List
from uuid import UUID, uuid4
from passlib.context import CryptContext

from models.auth import (
    JWTPayload, APIKeyPayload, TokenType, UserRole, PermissionLevel, 
    CurrentUser, AuthSecurityConfig, TokenBlacklist
)
from core.vault_client import vault_client
from core.config import get_settings

logger = structlog.get_logger(__name__)

class JWTService:
    """JWT token management service with Vault integration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        self.issuer = "betty-memory-api"
        self.audience = "betty-memory-api"
        
        # Security configuration (will be loaded from Vault in production)
        self.config = AuthSecurityConfig(
            jwt_secret_key=self._get_jwt_secret(),
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )
    
    def _get_jwt_secret(self) -> str:
        """Get JWT secret from Vault or generate a secure default"""
        try:
            # In production, get from Vault
            if vault_client.authenticated:
                config = vault_client.get_provider_config("betty-auth")
                if config and "jwt_secret" in config:
                    return config["jwt_secret"]
                    
            # Development fallback - generate a secure secret
            secret = secrets.token_urlsafe(64)
            logger.warning("Using generated JWT secret - configure Vault for production", 
                          secret_length=len(secret))
            return secret
            
        except Exception as e:
            logger.error("Failed to get JWT secret", error=str(e))
            # Fallback to a secure default
            return secrets.token_urlsafe(64)
    
    def generate_access_token(
        self, 
        user_id: UUID, 
        email: str, 
        role: UserRole,
        permissions: List[str] = None,
        project_access: Dict[str, PermissionLevel] = None
    ) -> str:
        """Generate JWT access token for authenticated user"""
        try:
            now = datetime.now(timezone.utc)
            exp_time = now + timedelta(minutes=self.config.access_token_expire_minutes)
            jti = str(uuid4())
            
            payload = JWTPayload(
                sub=str(user_id),
                email=email,
                role=role,
                permissions=permissions or [],
                project_access=project_access or {},
                iat=int(now.timestamp()),
                exp=int(exp_time.timestamp()),
                jti=jti,
                iss=self.issuer,
                aud=self.audience,
                token_type=TokenType.ACCESS
            )
            
            token = jwt.encode(
                payload.model_dump(),
                self.config.jwt_secret_key,
                algorithm=self.algorithm
            )
            
            logger.debug("Generated access token", user_id=str(user_id), jti=jti)
            return token
            
        except Exception as e:
            logger.error("Failed to generate access token", user_id=str(user_id), error=str(e))
            raise ValueError(f"Token generation failed: {str(e)}")
    
    def generate_refresh_token(self, user_id: UUID) -> str:
        """Generate JWT refresh token for token renewal"""
        try:
            now = datetime.now(timezone.utc)
            exp_time = now + timedelta(days=self.config.refresh_token_expire_days)
            jti = str(uuid4())
            
            payload = {
                "sub": str(user_id),
                "iat": int(now.timestamp()),
                "exp": int(exp_time.timestamp()),
                "jti": jti,
                "iss": self.issuer,
                "aud": self.audience,
                "token_type": TokenType.REFRESH.value
            }
            
            token = jwt.encode(
                payload,
                self.config.jwt_secret_key,
                algorithm=self.algorithm
            )
            
            logger.debug("Generated refresh token", user_id=str(user_id), jti=jti)
            return token
            
        except Exception as e:
            logger.error("Failed to generate refresh token", user_id=str(user_id), error=str(e))
            raise ValueError(f"Refresh token generation failed: {str(e)}")
    
    def generate_api_key_token(
        self,
        api_key_id: UUID,
        owner_id: UUID,
        scopes: List[str] = None,
        project_access: List[str] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        """Generate JWT token for API key authentication"""
        try:
            now = datetime.now(timezone.utc)
            jti = str(uuid4())
            
            payload = APIKeyPayload(
                sub=str(api_key_id),
                key_id=api_key_id,
                owner_id=owner_id,
                scopes=scopes or [],
                project_access=project_access or [],
                iat=int(now.timestamp()),
                exp=int(expires_at.timestamp()) if expires_at else None,
                jti=jti,
                iss=self.issuer,
                aud=self.audience
            )
            
            token = jwt.encode(
                payload.model_dump(exclude_none=True),
                self.config.jwt_secret_key,
                algorithm=self.algorithm
            )
            
            logger.debug("Generated API key token", api_key_id=str(api_key_id), jti=jti)
            return token
            
        except Exception as e:
            logger.error("Failed to generate API key token", api_key_id=str(api_key_id), error=str(e))
            raise ValueError(f"API key token generation failed: {str(e)}")
    
    def validate_token(self, token: str, expected_type: Optional[TokenType] = None) -> Dict[str, Any]:
        """Validate and decode JWT token"""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            
            # Check token type if specified
            if expected_type and payload.get("token_type") != expected_type.value:
                raise jwt.InvalidTokenError(f"Invalid token type. Expected {expected_type.value}")
            
            logger.debug("Token validated successfully", 
                        jti=payload.get("jti"), 
                        token_type=payload.get("token_type"))
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.debug("Invalid token", error=str(e))
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error("Token validation error", error=str(e))
            raise ValueError(f"Token validation failed: {str(e)}")
    
    def extract_current_user(self, token: str) -> CurrentUser:
        """Extract current user information from access token"""
        try:
            payload = self.validate_token(token, TokenType.ACCESS)
            
            return CurrentUser(
                user_id=UUID(payload["sub"]),
                email=payload["email"],
                role=UserRole(payload["role"]),
                permissions=payload.get("permissions", []),
                project_access={
                    k: PermissionLevel(v) for k, v in payload.get("project_access", {}).items()
                },
                is_api_key=False
            )
            
        except Exception as e:
            logger.error("Failed to extract current user", error=str(e))
            raise ValueError(f"User extraction failed: {str(e)}")
    
    def extract_api_key_info(self, token: str) -> CurrentUser:
        """Extract API key information from token"""
        try:
            payload = self.validate_token(token)
            
            if payload.get("token_type") != "api_key":
                raise ValueError("Token is not an API key")
            
            return CurrentUser(
                user_id=UUID(payload["owner_id"]),
                email="",  # API keys don't have emails
                role=UserRole.DEVELOPER,  # Default role for API keys
                permissions=payload.get("scopes", []),
                project_access={
                    proj: PermissionLevel.WRITE for proj in payload.get("project_access", [])
                },
                is_api_key=True,
                api_key_id=UUID(payload["key_id"])
            )
            
        except Exception as e:
            logger.error("Failed to extract API key info", error=str(e))
            raise ValueError(f"API key extraction failed: {str(e)}")
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted (this would query database in real implementation)"""
        # TODO: Implement database check
        # This is a placeholder - in real implementation, this would check the database
        return False
    
    def blacklist_token(
        self, 
        token: str, 
        user_id: UUID, 
        reason: str = "logout"
    ) -> bool:
        """Add token to blacklist"""
        try:
            payload = self.validate_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            token_type = payload.get("token_type", "access")
            
            if not jti or not exp:
                logger.error("Invalid token payload for blacklisting", payload_keys=list(payload.keys()))
                return False
            
            # TODO: Save to database
            blacklist_entry = TokenBlacklist(
                jti=jti,
                user_id=user_id,
                token_type=TokenType(token_type),
                expires_at=datetime.fromtimestamp(exp, timezone.utc),
                reason=reason
            )
            
            logger.info("Token blacklisted", jti=jti, user_id=str(user_id), reason=reason)
            return True
            
        except Exception as e:
            logger.error("Failed to blacklist token", user_id=str(user_id), error=str(e))
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_api_key(self) -> tuple[str, str]:
        """Generate API key and return (key, prefix)"""
        # Generate a secure random key
        key_part = secrets.token_urlsafe(48)
        prefix = "betty_"
        full_key = f"{prefix}{key_part}"
        
        return full_key, prefix
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return self.pwd_context.hash(api_key)
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash"""
        return self.pwd_context.verify(api_key, hashed_key)
    
    def get_token_expiry_info(self, token: str) -> Dict[str, Any]:
        """Get token expiry information without full validation"""
        try:
            # Decode without verification to get expiry info
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get("exp")
            iat = payload.get("iat")
            
            if not exp:
                return {"valid": False, "error": "No expiry time in token"}
            
            exp_time = datetime.fromtimestamp(exp, timezone.utc)
            iat_time = datetime.fromtimestamp(iat, timezone.utc) if iat else None
            now = datetime.now(timezone.utc)
            
            return {
                "valid": True,
                "expires_at": exp_time,
                "issued_at": iat_time,
                "is_expired": now > exp_time,
                "expires_in_seconds": (exp_time - now).total_seconds(),
                "jti": payload.get("jti"),
                "token_type": payload.get("token_type")
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def create_security_headers(self) -> Dict[str, str]:
        """Create security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

# Global JWT service instance
jwt_service = JWTService()