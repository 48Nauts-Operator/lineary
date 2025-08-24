# ABOUTME: Authentication service for BETTY Memory System
# ABOUTME: User management, API key operations, and authentication logic with database integration

import structlog
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.auth import (
    User, UserCreateRequest, UserUpdateRequest, PasswordChangeRequest,
    LoginRequest, LoginResponse, TokenRefreshRequest, TokenRefreshResponse,
    APIKey, APIKeyCreateRequest, APIKeyResponse, APIKeyWithSecret,
    ProjectPermission, RefreshToken, AuthAuditLog, CurrentUser,
    UserRole, PermissionLevel, AuthEventType, RateLimit
)
from core.database import DatabaseManager

logger = structlog.get_logger(__name__)

# Global database manager instance - to be set by the application
_db_manager: Optional[DatabaseManager] = None

def set_database_manager(db_manager: DatabaseManager) -> None:
    """Set the global database manager instance"""
    global _db_manager
    _db_manager = db_manager

def get_database_session():
    """Get database session from the global database manager"""
    if not _db_manager:
        raise RuntimeError("Database manager not initialized. Call set_database_manager() first.")
    return _db_manager.get_postgres_session()

class AuthenticationError(Exception):
    """Authentication related errors"""
    pass

class AuthService:
    """Authentication and user management service"""
    
    def __init__(self):
        # Import here to avoid circular imports
        from .jwt_service import jwt_service
        self.jwt_service = jwt_service
    
    async def authenticate_user(self, email: str, password: str, ip_address: str = None) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            async with get_database_session() as db:
                # Get user by email
                query = text("""
                    SELECT user_id, email, full_name, password_hash, role, is_active, 
                           is_verified, failed_login_attempts, locked_until
                    FROM auth_users 
                    WHERE email = :email AND is_active = true
                """)
                result = await db.execute(query, {"email": email})
                user_row = result.fetchone()
                
                if not user_row:
                    await self._log_auth_event(
                        event_type=AuthEventType.FAILED_LOGIN,
                        success=False,
                        ip_address=ip_address,
                        details={"reason": "user_not_found", "email": email}
                    )
                    return None
                
                user_data = dict(user_row._mapping)
                
                # Check if account is locked
                if await self._is_account_locked(user_data["user_id"], db):
                    await self._log_auth_event(
                        user_id=user_data["user_id"],
                        event_type=AuthEventType.FAILED_LOGIN,
                        success=False,
                        ip_address=ip_address,
                        details={"reason": "account_locked"}
                    )
                    raise AuthenticationError("Account is locked due to multiple failed attempts")
                
                # Verify password
                if not self.jwt_service.verify_password(password, user_data["password_hash"]):
                    # Increment failed attempts
                    await self._increment_failed_login_attempts(user_data["user_id"], db)
                    await self._log_auth_event(
                        user_id=user_data["user_id"],
                        event_type=AuthEventType.FAILED_LOGIN,
                        success=False,
                        ip_address=ip_address,
                        details={"reason": "invalid_password"}
                    )
                    return None
                
                # Reset failed attempts on successful login
                await self._reset_failed_login_attempts(user_data["user_id"], ip_address, db)
                
                # Log successful login
                await self._log_auth_event(
                    user_id=user_data["user_id"],
                    event_type=AuthEventType.LOGIN,
                    success=True,
                    ip_address=ip_address,
                    details={"email": email}
                )
                
                return User(**user_data)
                
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Authentication error", email=email, error=str(e))
            return None
    
    async def login_user(self, login_data: LoginRequest, ip_address: str = None) -> LoginResponse:
        """Login user and return tokens"""
        try:
            # Check rate limiting
            if await self._is_rate_limited("login", ip_address):
                raise AuthenticationError("Too many login attempts. Please try again later.")
            
            # Authenticate user
            user = await self.authenticate_user(login_data.email, login_data.password, ip_address)
            if not user:
                raise AuthenticationError("Invalid email or password")
            
            # Get user permissions
            permissions, project_access = await self._get_user_permissions(user.user_id)
            
            # Generate tokens
            access_token = self.jwt_service.generate_access_token(
                user_id=user.user_id,
                email=user.email,
                role=user.role,
                permissions=permissions,
                project_access=project_access
            )
            
            refresh_token = self.jwt_service.generate_refresh_token(user.user_id)
            
            # Store refresh token
            await self._store_refresh_token(
                refresh_token, 
                user.user_id, 
                device_info=None,  # TODO: Extract from user agent
                ip_address=ip_address
            )
            
            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.jwt_service.config.access_token_expire_minutes * 60,
                user=await self._get_user_response(user.user_id)
            )
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Login error", email=login_data.email, error=str(e))
            raise AuthenticationError("Login failed")
    
    async def refresh_token(self, refresh_request: TokenRefreshRequest) -> TokenRefreshResponse:
        """Refresh access token using refresh token"""
        try:
            # Validate refresh token
            payload = self.jwt_service.validate_token(refresh_request.refresh_token, expected_type="refresh")
            user_id = UUID(payload["sub"])
            
            # Check if refresh token exists in database
            async with get_database_session() as db:
                query = text("""
                    SELECT token_id, user_id, is_active, expires_at 
                    FROM auth_refresh_tokens 
                    WHERE token_hash = :token_hash AND user_id = :user_id AND is_active = true
                """)
                token_hash = self.jwt_service.pwd_context.hash(refresh_request.refresh_token)
                result = await db.execute(query, {"token_hash": token_hash, "user_id": user_id})
                
                if not result.fetchone():
                    raise AuthenticationError("Invalid refresh token")
            
            # Get user and permissions
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User account is not active")
            
            permissions, project_access = await self._get_user_permissions(user_id)
            
            # Generate new tokens
            access_token = self.jwt_service.generate_access_token(
                user_id=user.user_id,
                email=user.email,
                role=user.role,
                permissions=permissions,
                project_access=project_access
            )
            
            new_refresh_token = self.jwt_service.generate_refresh_token(user_id)
            
            # Update refresh token in database
            await self._update_refresh_token(refresh_request.refresh_token, new_refresh_token)
            
            # Log token refresh
            await self._log_auth_event(
                user_id=user_id,
                event_type=AuthEventType.TOKEN_REFRESH,
                success=True,
                details={"old_jti": payload.get("jti")}
            )
            
            return TokenRefreshResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=self.jwt_service.config.access_token_expire_minutes * 60
            )
            
        except Exception as e:
            logger.error("Token refresh error", error=str(e))
            raise AuthenticationError("Token refresh failed")
    
    async def logout_user(self, access_token: str, refresh_token: str, user_id: UUID) -> bool:
        """Logout user and blacklist tokens"""
        try:
            # Blacklist access token
            self.jwt_service.blacklist_token(access_token, user_id, "logout")
            
            # Invalidate refresh token
            await self._invalidate_refresh_token(refresh_token)
            
            # Log logout
            await self._log_auth_event(
                user_id=user_id,
                event_type=AuthEventType.LOGOUT,
                success=True
            )
            
            return True
            
        except Exception as e:
            logger.error("Logout error", user_id=str(user_id), error=str(e))
            return False
    
    async def create_user(self, user_data: UserCreateRequest, created_by: UUID = None) -> User:
        """Create a new user account"""
        try:
            async with get_database_session() as db:
                # Check if email already exists
                query = text("SELECT user_id FROM auth_users WHERE email = :email")
                result = await db.execute(query, {"email": user_data.email})
                if result.fetchone():
                    raise ValueError("Email already registered")
                
                # Hash password
                password_hash = self.jwt_service.hash_password(user_data.password)
                
                # Create user
                user_id = uuid4()
                insert_query = text("""
                    INSERT INTO auth_users (user_id, email, full_name, password_hash, role)
                    VALUES (:user_id, :email, :full_name, :password_hash, :role)
                    RETURNING user_id, email, full_name, role, is_active, is_verified, created_at
                """)
                
                result = await db.execute(insert_query, {
                    "user_id": user_id,
                    "email": user_data.email,
                    "full_name": user_data.full_name,
                    "password_hash": password_hash,
                    "role": user_data.role.value
                })
                
                user_row = result.fetchone()
                await db.commit()
                
                # Add project permissions if provided
                if user_data.project_permissions:
                    for project_id, permission_level in user_data.project_permissions.items():
                        await self._grant_project_permission(
                            user_id, project_id, permission_level, created_by, db
                        )
                
                logger.info("User created successfully", user_id=str(user_id), email=user_data.email)
                return User(**dict(user_row._mapping), password_hash=password_hash)
                
        except Exception as e:
            logger.error("User creation error", email=user_data.email, error=str(e))
            raise
    
    async def create_api_key(self, key_data: APIKeyCreateRequest, owner_id: UUID) -> APIKeyWithSecret:
        """Create a new API key"""
        try:
            async with get_database_session() as db:
                # Generate API key
                api_key, key_prefix = self.jwt_service.generate_api_key()
                key_hash = self.jwt_service.hash_api_key(api_key)
                
                # Create API key record
                api_key_id = uuid4()
                insert_query = text("""
                    INSERT INTO auth_api_keys (
                        api_key_id, key_name, key_hash, key_prefix, owner_user_id,
                        scopes, project_access, rate_limit_per_hour, expires_at
                    ) VALUES (
                        :api_key_id, :key_name, :key_hash, :key_prefix, :owner_user_id,
                        :scopes, :project_access, :rate_limit_per_hour, :expires_at
                    ) RETURNING *
                """)
                
                result = await db.execute(insert_query, {
                    "api_key_id": api_key_id,
                    "key_name": key_data.name,
                    "key_hash": key_hash,
                    "key_prefix": key_prefix,
                    "owner_user_id": owner_id,
                    "scopes": key_data.scopes,
                    "project_access": key_data.project_access,
                    "rate_limit_per_hour": key_data.rate_limit_per_hour,
                    "expires_at": key_data.expires_at
                })
                
                api_key_row = result.fetchone()
                await db.commit()
                
                # Log API key creation
                await self._log_auth_event(
                    user_id=owner_id,
                    api_key_id=api_key_id,
                    event_type=AuthEventType.API_KEY_CREATE,
                    success=True,
                    details={"api_key_name": key_data.name}
                )
                
                logger.info("API key created", api_key_id=str(api_key_id), owner_id=str(owner_id))
                
                return APIKeyWithSecret(
                    api_key=api_key,
                    **dict(api_key_row._mapping)
                )
                
        except Exception as e:
            logger.error("API key creation error", owner_id=str(owner_id), error=str(e))
            raise
    
    async def authenticate_api_key(self, api_key: str) -> Optional[CurrentUser]:
        """Authenticate using API key"""
        try:
            async with get_database_session() as db:
                # Find API key by prefix first for efficiency
                key_prefix = api_key.split('_')[0] + '_' if '_' in api_key else api_key[:10]
                
                query = text("""
                    SELECT ak.*, u.email, u.role 
                    FROM auth_api_keys ak
                    JOIN auth_users u ON ak.owner_user_id = u.user_id
                    WHERE ak.key_prefix = :key_prefix AND ak.is_active = true
                    AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
                """)
                
                result = await db.execute(query, {"key_prefix": key_prefix})
                
                for api_key_row in result.fetchall():
                    api_key_data = dict(api_key_row._mapping)
                    
                    # Verify the full API key
                    if self.jwt_service.verify_api_key(api_key, api_key_data["key_hash"]):
                        # Update last used timestamp
                        await self._update_api_key_usage(api_key_data["api_key_id"], db)
                        
                        # Log API access
                        await self._log_auth_event(
                            user_id=api_key_data["owner_user_id"],
                            api_key_id=api_key_data["api_key_id"],
                            event_type=AuthEventType.API_ACCESS,
                            success=True
                        )
                        
                        # Create CurrentUser from API key data
                        project_access = {
                            proj: PermissionLevel.WRITE 
                            for proj in api_key_data["project_access"]
                        }
                        
                        return CurrentUser(
                            user_id=UUID(api_key_data["owner_user_id"]),
                            email=api_key_data["email"],
                            role=UserRole(api_key_data["role"]),
                            permissions=api_key_data["scopes"],
                            project_access=project_access,
                            is_api_key=True,
                            api_key_id=UUID(api_key_data["api_key_id"])
                        )
                
                # No matching API key found
                await self._log_auth_event(
                    event_type=AuthEventType.API_ACCESS,
                    success=False,
                    details={"reason": "invalid_api_key", "key_prefix": key_prefix}
                )
                return None
                
        except Exception as e:
            logger.error("API key authentication error", error=str(e))
            return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        try:
            async with get_database_session() as db:
                query = text("SELECT * FROM auth_users WHERE user_id = :user_id")
                result = await db.execute(query, {"user_id": user_id})
                user_row = result.fetchone()
                
                if user_row:
                    return User(**dict(user_row._mapping))
                return None
                
        except Exception as e:
            logger.error("Get user error", user_id=str(user_id), error=str(e))
            return None
    
    async def _get_user_permissions(self, user_id: UUID) -> Tuple[List[str], Dict[str, PermissionLevel]]:
        """Get user permissions and project access"""
        try:
            async with get_database_session() as db:
                # Get project permissions
                query = text("""
                    SELECT project_id, permission_level 
                    FROM auth_project_permissions 
                    WHERE user_id = :user_id AND is_active = true
                    AND (expires_at IS NULL OR expires_at > NOW())
                """)
                result = await db.execute(query, {"user_id": user_id})
                
                project_access = {}
                permissions = []
                
                for row in result.fetchall():
                    project_id = row.project_id
                    permission_level = PermissionLevel(row.permission_level)
                    project_access[project_id] = permission_level
                    
                    # Add scope-based permissions
                    if permission_level == PermissionLevel.READ:
                        permissions.extend(["knowledge:read", "sessions:read"])
                    elif permission_level == PermissionLevel.WRITE:
                        permissions.extend(["knowledge:read", "knowledge:write", "sessions:read", "sessions:write"])
                    elif permission_level == PermissionLevel.ADMIN:
                        permissions.extend([
                            "knowledge:read", "knowledge:write", "knowledge:admin",
                            "sessions:read", "sessions:write", "sessions:admin",
                            "analytics:read"
                        ])
                
                return list(set(permissions)), project_access
                
        except Exception as e:
            logger.error("Get user permissions error", user_id=str(user_id), error=str(e))
            return [], {}
    
    async def _is_rate_limited(self, limit_type: str, identifier: str, limit: int = 5) -> bool:
        """Check if identifier is rate limited"""
        # TODO: Implement rate limiting logic
        return False
    
    async def _log_auth_event(
        self,
        event_type: AuthEventType,
        success: bool,
        user_id: UUID = None,
        api_key_id: UUID = None,
        ip_address: str = None,
        user_agent: str = None,
        details: Dict[str, Any] = None
    ):
        """Log authentication event"""
        try:
            async with get_database_session() as db:
                query = text("""
                    INSERT INTO auth_audit_log (
                        user_id, api_key_id, event_type, success, 
                        ip_address, user_agent, details
                    ) VALUES (
                        :user_id, :api_key_id, :event_type, :success,
                        :ip_address, :user_agent, :details
                    )
                """)
                
                await db.execute(query, {
                    "user_id": user_id,
                    "api_key_id": api_key_id,
                    "event_type": event_type.value,
                    "success": success,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "details": details or {}
                })
                await db.commit()
                
        except Exception as e:
            logger.error("Failed to log auth event", error=str(e))
    
    # Helper methods would continue here...
    # (Additional helper methods for database operations, account management, etc.)

# Global auth service instance
auth_service = AuthService()