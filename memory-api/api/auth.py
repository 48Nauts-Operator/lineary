# ABOUTME: Authentication API endpoints for BETTY Memory System
# ABOUTME: JWT login/logout, token refresh, user management and API key operations

from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime
import structlog

from models.auth import (
    LoginRequest, LoginResponse, TokenRefreshRequest, TokenRefreshResponse,
    UserCreateRequest, UserUpdateRequest, UserResponse, PasswordChangeRequest,
    APIKeyCreateRequest, APIKeyResponse, APIKeyWithSecret,
    CurrentUser, AuthEventType, UserRole
)
from core.security import (
    require_authentication, require_permission, require_role, 
    get_current_user, jwt_bearer, SecurityManager
)
from services.auth_service import auth_service
from services.jwt_service import jwt_service

logger = structlog.get_logger(__name__)
router = APIRouter()

# Authentication endpoints

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request
) -> LoginResponse:
    """
    Authenticate user with email and password
    Returns JWT access token and refresh token
    """
    try:
        client_ip = SecurityManager.get_client_ip(request)
        response = await auth_service.login_user(login_data, client_ip)
        
        logger.info("User login successful", 
                   email=login_data.email, 
                   client_ip=client_ip)
        return response
        
    except Exception as e:
        logger.error("Login failed", 
                    email=login_data.email, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    request: Request
) -> TokenRefreshResponse:
    """
    Refresh access token using refresh token
    Returns new access token and refresh token
    """
    try:
        client_ip = SecurityManager.get_client_ip(request)
        response = await auth_service.refresh_token(refresh_data)
        
        logger.info("Token refresh successful", client_ip=client_ip)
        return response
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer),
    current_user: CurrentUser = Depends(require_authentication)
) -> dict:
    """
    Logout user and blacklist current tokens
    Requires both access token and refresh token
    """
    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token required for logout"
            )
        
        # TODO: Get refresh token from request body or cookie
        # For now, just blacklist the access token
        success = await auth_service.logout_user(
            access_token=credentials.credentials,
            refresh_token="",  # Would get from request
            user_id=current_user.user_id
        )
        
        if success:
            logger.info("User logout successful", user_id=str(current_user.user_id))
            return {"message": "Successfully logged out"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Logout error", user_id=str(current_user.user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(require_authentication)
) -> UserResponse:
    """Get current authenticated user information"""
    try:
        # Get full user details from database
        user = await auth_service.get_user_by_id(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get project permissions
        _, project_access = await auth_service._get_user_permissions(current_user.user_id)
        
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            project_permissions=[
                {"project_id": k, "permission_level": v, "granted_at": user.created_at, "is_active": True}
                for k, v in project_access.items()
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get user info error", user_id=str(current_user.user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

# User management endpoints (admin only)

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN))
) -> UserResponse:
    """Create a new user account (admin only)"""
    try:
        new_user = await auth_service.create_user(user_data, current_user.user_id)
        
        logger.info("User created by admin", 
                   new_user_id=str(new_user.user_id),
                   created_by=str(current_user.user_id))
        
        return UserResponse(
            user_id=new_user.user_id,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            last_login_at=new_user.last_login_at,
            created_at=new_user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("User creation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN))
) -> UserResponse:
    """Update user information (admin only)"""
    try:
        # TODO: Implement user update logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User update not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User update error", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser = Depends(require_authentication)
) -> dict:
    """Change user password"""
    try:
        # TODO: Implement password change logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Password change not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change error", user_id=str(current_user.user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

# API Key management endpoints

@router.post("/api-keys", response_model=APIKeyWithSecret)
async def create_api_key(
    key_data: APIKeyCreateRequest,
    current_user: CurrentUser = Depends(require_authentication)
) -> APIKeyWithSecret:
    """Create a new API key for the authenticated user"""
    try:
        api_key = await auth_service.create_api_key(key_data, current_user.user_id)
        
        logger.info("API key created", 
                   api_key_id=str(api_key.api_key_id),
                   owner_id=str(current_user.user_id))
        
        return api_key
        
    except Exception as e:
        logger.error("API key creation error", 
                    owner_id=str(current_user.user_id), 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed"
        )

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: CurrentUser = Depends(require_authentication)
) -> List[APIKeyResponse]:
    """List all API keys for the authenticated user"""
    try:
        # TODO: Implement API key listing
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="API key listing not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API key listing error", user_id=str(current_user.user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key listing failed"
        )

@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    current_user: CurrentUser = Depends(require_authentication)
) -> dict:
    """Revoke an API key"""
    try:
        # TODO: Implement API key revocation
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="API key revocation not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API key revocation error", 
                    api_key_id=api_key_id, 
                    user_id=str(current_user.user_id), 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key revocation failed"
        )

# Token validation endpoint

@router.get("/validate-token")
async def validate_token(
    current_user: CurrentUser = Depends(require_authentication)
) -> dict:
    """Validate the current token and return user info"""
    return {
        "valid": True,
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "role": current_user.role.value,
        "permissions": current_user.permissions,
        "project_access": {k: v.value for k, v in current_user.project_access.items()},
        "is_api_key": current_user.is_api_key
    }

# Health check endpoint (no auth required)

@router.get("/health")
async def auth_health() -> dict:
    """Health check for authentication service"""
    try:
        # Basic health checks
        return {
            "status": "healthy",
            "service": "betty-auth",
            "jwt_service": "operational",
            "auth_service": "operational",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Auth health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "betty-auth",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }