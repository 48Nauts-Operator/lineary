# ABOUTME: JWT-based authentication and security for BETTY Memory System
# ABOUTME: Production-ready authentication with RBAC, rate limiting and security middleware

from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Security, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.responses import JSONResponse
import structlog
from datetime import datetime, timedelta
import hashlib
import secrets
from uuid import UUID
import json

from models.auth import CurrentUser, UserRole, PermissionLevel, AuthEventType
from services.jwt_service import jwt_service
from services.auth_service import auth_service

logger = structlog.get_logger(__name__)

# Security schemes for JWT and API key authentication
jwt_bearer = HTTPBearer(auto_error=False, scheme_name="JWT Bearer")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="API Key")

class SecurityManager:
    """Security utilities for the BETTY Memory System"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate a secure session ID"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256 (for basic security)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return hashlib.sha256(password.encode()).hexdigest() == hashed
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """Sanitize text input by removing potentially harmful content"""
        if not text or not isinstance(text, str):
            return ""
        
        # Limit length
        text = text[:max_length]
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def sanitize_file_path(file_path: str, max_length: int = 500) -> str:
        """Sanitize file path by removing potentially harmful content"""
        if not file_path or not isinstance(file_path, str):
            return ""
        
        # Limit length
        file_path = file_path[:max_length]
        
        # Remove null bytes and control characters except for normal path characters
        file_path = ''.join(char for char in file_path if ord(char) >= 32 or char in '\t')
        
        # Remove dangerous patterns
        dangerous_patterns = ['../', '..\\', '..\\']
        for pattern in dangerous_patterns:
            file_path = file_path.replace(pattern, '')
        
        # Strip whitespace
        file_path = file_path.strip()
        
        return file_path
    
    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """Validate UUID format"""
        import uuid
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Extract client IP address from request"""
        if hasattr(request, 'client') and request.client:
            return request.client.host
        return "unknown"
    
    @staticmethod
    def log_security_event(
        event_type: str,
        details: Dict[str, Any],
        client_ip: str = None,
        user_id: str = None
    ) -> None:
        """Log security-related events"""
        logger.warning(
            "Security event",
            event_type=event_type,
            client_ip=client_ip,
            user_id=user_id,
            **details
        )

async def get_current_user(
    request: Request,
    jwt_credentials: Optional[HTTPAuthorizationCredentials] = Security(jwt_bearer),
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[CurrentUser]:
    """
    Get current authenticated user from JWT token or API key
    Supports both Bearer JWT tokens and X-API-Key header authentication
    """
    client_ip = SecurityManager.get_client_ip(request)
    
    try:
        # Try API key authentication first
        if api_key:
            logger.debug("Attempting API key authentication", key_prefix=api_key[:10])
            current_user = await auth_service.authenticate_api_key(api_key)
            if current_user:
                logger.debug("API key authentication successful", 
                           user_id=str(current_user.user_id),
                           api_key_id=str(current_user.api_key_id))
                return current_user
        
        # Try JWT token authentication
        if jwt_credentials and jwt_credentials.credentials:
            logger.debug("Attempting JWT authentication", 
                        token_prefix=jwt_credentials.credentials[:20])
            
            # Check if token is blacklisted
            if jwt_service.is_token_blacklisted(jwt_credentials.credentials):
                logger.warning("Blacklisted token used", client_ip=client_ip)
                return None
            
            # Validate and extract user info
            current_user = jwt_service.extract_current_user(jwt_credentials.credentials)
            logger.debug("JWT authentication successful", user_id=str(current_user.user_id))
            return current_user
        
        # Development fallback: Check for development API keys
        if api_key and api_key.startswith('betty_dev_test_'):
            dev_user = await _authenticate_dev_api_key(api_key)
            if dev_user:
                logger.info("Development API key authentication successful", user_id=str(dev_user.user_id))
                return dev_user
        
        # No authentication provided
        logger.debug("No authentication credentials provided")
        return None
        
    except ValueError as e:
        logger.warning("Authentication failed", error=str(e), client_ip=client_ip)
        return None
    except Exception as e:
        logger.error("Authentication error", error=str(e), client_ip=client_ip)
        return None

def require_authentication():
    """
    Require authentication for protected endpoints
    Validates JWT tokens or API keys and returns CurrentUser
    """
    def _require_auth(current_user: Optional[CurrentUser] = Depends(get_current_user)) -> CurrentUser:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide a valid Bearer token or X-API-Key header.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return current_user
    
    return _require_auth

def require_permission(permission: str):
    """
    Require specific permission for endpoint access
    Checks user permissions and role-based access
    """
    def permission_checker(
        current_user: CurrentUser = Depends(require_authentication)
    ) -> CurrentUser:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required. Your permissions: {current_user.permissions}"
            )
        return current_user
    
    return permission_checker

def require_permissions(permissions: List[str]):
    """
    Require multiple permissions for endpoint access
    Checks that user has ALL specified permissions
    """
    def permissions_checker(
        current_user: CurrentUser = Depends(require_authentication)
    ) -> CurrentUser:
        missing_permissions = []
        for permission in permissions:
            if not current_user.has_permission(permission):
                missing_permissions.append(permission)
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Insufficient Permissions",
                    "message": f"Missing required permissions: {missing_permissions}",
                    "required_permissions": permissions,
                    "user_permissions": current_user.permissions,
                    "upgrade_info": "Contact administrator to upgrade your permissions"
                }
            )
        return current_user
    
    return permissions_checker

def require_role(required_role: UserRole):
    """
    Require specific role for endpoint access
    Checks user role hierarchy
    """
    def role_checker(
        current_user: CurrentUser = Depends(require_authentication)
    ) -> CurrentUser:
        if not current_user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Insufficient Role",
                    "message": f"Role '{required_role.value}' required",
                    "current_role": current_user.role.value,
                    "required_role": required_role.value
                }
            )
        return current_user
    
    return role_checker

def require_project_access(project_id: str, required_level: PermissionLevel = PermissionLevel.READ):
    """
    Require project-specific access for endpoints
    Validates user has appropriate permission level for the project
    """
    def project_access_checker(
        current_user: CurrentUser = Depends(require_authentication)
    ) -> CurrentUser:
        if not current_user.can_access_project(project_id, required_level):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to project '{project_id}' with level '{required_level.value}'"
            )
        return current_user
    
    return project_access_checker

def require_role(min_role: UserRole):
    """
    Require minimum user role for endpoint access
    Enforces hierarchical role-based access (admin > developer > reader)
    """
    role_hierarchy = {
        UserRole.READER: 1,
        UserRole.DEVELOPER: 2,
        UserRole.ADMIN: 3
    }
    
    def role_checker(
        current_user: CurrentUser = Depends(require_authentication)
    ) -> CurrentUser:
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(min_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{min_role.value}' or higher required. Your role: {current_user.role.value}"
            )
        return current_user
    
    return role_checker

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        self.requests = {
            ip: [req_time for req_time in req_times if req_time > minute_ago]
            for ip, req_times in self.requests.items()
        }
        
        # Check current client
        client_requests = self.requests.get(client_ip, [])
        
        if len(client_requests) >= self.requests_per_minute:
            return False
        
        # Add current request
        client_requests.append(now)
        self.requests[client_ip] = client_requests
        
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

# Security middleware for authentication and rate limiting
class AuthenticationMiddleware:
    """Middleware for JWT authentication and security headers"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Add security headers to response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    security_headers = jwt_service.create_security_headers()
                    
                    for key, value in security_headers.items():
                        headers[key.encode()] = value.encode()
                    
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

# Rate limiting middleware
class RateLimitingMiddleware:
    """Middleware for API rate limiting"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        self.app = app
        self.rate_limiter = RateLimiter(requests_per_minute)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            client_ip = SecurityManager.get_client_ip(request)
            
            if not self.rate_limiter.is_allowed(client_ip):
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60
                    }
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)

# Optional authentication (for endpoints that work with or without auth)
async def get_optional_user(
    request: Request,
    jwt_credentials: Optional[HTTPAuthorizationCredentials] = Security(jwt_bearer),
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, None if not (no error raised)
    Useful for endpoints that provide different functionality based on auth status
    """
    try:
        return await get_current_user(request, jwt_credentials, api_key)
    except Exception:
        return None

async def _authenticate_dev_api_key(api_key: str) -> Optional[CurrentUser]:
    """
    Development-only API key authentication using simple database tables
    This is a temporary solution for testing and should be removed in production
    Returns CurrentUser object for authentication
    """
    try:
        # For development, we'll connect directly to the database
        import os
        import asyncpg
        
        # Use environment variables or defaults matching docker-compose
        postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
        postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
        postgres_db = os.getenv('POSTGRES_DB', 'betty_memory')
        postgres_user = os.getenv('POSTGRES_USER', 'betty')
        postgres_password = os.getenv('POSTGRES_PASSWORD', 'bettypassword')
        
        # Connect to database
        conn = await asyncpg.connect(
            host=postgres_host,
            port=postgres_port,
            database=postgres_db,
            user=postgres_user,
            password=postgres_password
        )
        
        try:
            # Query development API key
            query = """
                SELECT u.user_id, u.email, u.full_name, u.role, k.scopes, k.api_key_id
                FROM dev_users u
                JOIN dev_api_keys k ON u.user_id = k.owner_user_id
                WHERE k.api_key = $1 AND k.is_active = true 
                AND (k.expires_at IS NULL OR k.expires_at > NOW())
            """
            
            row = await conn.fetchrow(query, api_key)
            
            if row:
                # Return CurrentUser object for proper authentication
                from uuid import UUID
                return CurrentUser(
                    user_id=UUID(str(row['user_id'])),
                    email=row['email'],
                    role=UserRole(row['role']),
                    permissions=row['scopes'] or [],
                    project_access={},  # Dev keys have default access
                    is_api_key=True,
                    api_key_id=UUID(str(row['api_key_id'])) if row['api_key_id'] else None
                )
                
        finally:
            await conn.close()
            
        return None
        
    except Exception as e:
        logger.warning("Development API key authentication failed", error=str(e))
        return None