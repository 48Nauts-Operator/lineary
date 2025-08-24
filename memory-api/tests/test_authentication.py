# ABOUTME: Comprehensive authentication system tests for BETTY Memory System
# ABOUTME: Tests JWT tokens, API keys, RBAC permissions and security features

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import FastAPI
import jwt

# Import our authentication components
from ..main import app
from ..models.auth import UserRole, PermissionLevel, LoginRequest, UserCreateRequest
from ..services.jwt_service import jwt_service  
from ..services.auth_service import auth_service
from ..config.security_config import get_security_config, validate_security_implementation

# Test client
client = TestClient(app)

class TestJWTService:
    """Test JWT token generation and validation"""
    
    def test_generate_access_token(self):
        """Test access token generation"""
        user_id = uuid4()
        email = "test@example.com"
        role = UserRole.DEVELOPER
        permissions = ["knowledge:read", "knowledge:write"]
        
        token = jwt_service.generate_access_token(
            user_id=user_id,
            email=email,
            role=role, 
            permissions=permissions
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Verify token payload
        payload = jwt_service.validate_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["role"] == role.value
        assert payload["permissions"] == permissions
    
    def test_generate_refresh_token(self):
        """Test refresh token generation"""
        user_id = uuid4()
        
        token = jwt_service.generate_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token payload
        payload = jwt_service.validate_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["token_type"] == "refresh"
    
    def test_token_expiration(self):
        """Test token expiration validation"""
        user_id = uuid4()
        
        # Create expired token (hack the service temporarily)
        original_expire = jwt_service.config.access_token_expire_minutes
        jwt_service.config.access_token_expire_minutes = -1  # Already expired
        
        token = jwt_service.generate_access_token(
            user_id=user_id,
            email="test@example.com",
            role=UserRole.DEVELOPER
        )
        
        # Restore original config
        jwt_service.config.access_token_expire_minutes = original_expire
        
        # Validate should fail
        with pytest.raises(ValueError, match="Token has expired"):
            jwt_service.validate_token(token)
    
    def test_invalid_token(self):
        """Test invalid token handling"""
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(ValueError, match="Invalid token"):
            jwt_service.validate_token(invalid_token)
    
    def test_api_key_generation(self):
        """Test API key generation"""
        api_key, prefix = jwt_service.generate_api_key()
        
        assert api_key.startswith("betty_")
        assert prefix == "betty_"
        assert len(api_key) > 50  # Should be long enough
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        
        hashed = jwt_service.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        
        # Verify correct password
        assert jwt_service.verify_password(password, hashed)
        
        # Verify incorrect password
        assert not jwt_service.verify_password("WrongPassword", hashed)

class TestAuthenticationAPI:
    """Test authentication API endpoints"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.test_user_email = "test@betty.memory"
        self.test_user_password = "TestPassword123!"
        
    def test_health_endpoint(self):
        """Test authentication health endpoint"""
        response = client.get("/auth/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "betty-auth"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_token_validation_without_token(self):
        """Test protected endpoints without token"""
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_token_validation_with_invalid_token(self):
        """Test protected endpoints with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

class TestPermissionSystem:
    """Test role-based access control and permissions"""
    
    def test_permission_hierarchy(self):
        """Test role permission hierarchy"""
        from ..models.auth import CurrentUser
        
        # Admin user
        admin_user = CurrentUser(
            user_id=uuid4(),
            email="admin@test.com",
            role=UserRole.ADMIN,
            permissions=["knowledge:read", "knowledge:write", "knowledge:admin"],
            project_access={}
        )
        
        # Developer user  
        dev_user = CurrentUser(
            user_id=uuid4(),
            email="dev@test.com",
            role=UserRole.DEVELOPER,
            permissions=["knowledge:read", "knowledge:write"],
            project_access={}
        )
        
        # Reader user
        reader_user = CurrentUser(
            user_id=uuid4(),
            email="reader@test.com", 
            role=UserRole.READER,
            permissions=["knowledge:read"],
            project_access={}
        )
        
        # Test admin permissions
        assert admin_user.has_permission("knowledge:admin")
        assert admin_user.has_permission("knowledge:write")
        assert admin_user.has_permission("knowledge:read")
        
        # Test developer permissions  
        assert not dev_user.has_permission("knowledge:admin")
        assert dev_user.has_permission("knowledge:write")
        assert dev_user.has_permission("knowledge:read")
        
        # Test reader permissions
        assert not reader_user.has_permission("knowledge:admin")
        assert not reader_user.has_permission("knowledge:write")
        assert reader_user.has_permission("knowledge:read")
    
    def test_project_access_control(self):
        """Test project-scoped access control"""
        from ..models.auth import CurrentUser
        
        user = CurrentUser(
            user_id=uuid4(),
            email="user@test.com",
            role=UserRole.DEVELOPER,
            permissions=["knowledge:read", "knowledge:write"],
            project_access={
                "project1": PermissionLevel.ADMIN,
                "project2": PermissionLevel.WRITE,
                "project3": PermissionLevel.READ
            }
        )
        
        # Test admin access to project1
        assert user.can_access_project("project1", PermissionLevel.READ)
        assert user.can_access_project("project1", PermissionLevel.WRITE) 
        assert user.can_access_project("project1", PermissionLevel.ADMIN)
        
        # Test write access to project2
        assert user.can_access_project("project2", PermissionLevel.READ)
        assert user.can_access_project("project2", PermissionLevel.WRITE)
        assert not user.can_access_project("project2", PermissionLevel.ADMIN)
        
        # Test read access to project3
        assert user.can_access_project("project3", PermissionLevel.READ)
        assert not user.can_access_project("project3", PermissionLevel.WRITE)
        assert not user.can_access_project("project3", PermissionLevel.ADMIN)
        
        # Test no access to project4
        assert not user.can_access_project("project4", PermissionLevel.READ)

class TestSecurityFeatures:
    """Test security features and OWASP compliance"""
    
    def test_security_headers(self):
        """Test security headers are applied"""
        response = client.get("/auth/health")
        headers = response.headers
        
        # Check essential security headers
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
    
    def test_owasp_compliance(self):
        """Test OWASP Top 10 compliance"""
        validation_results = validate_security_implementation()
        
        # Check that key OWASP controls are implemented
        assert "A01_Broken_Access_Control" in validation_results
        assert "A02_Cryptographic_Failures" in validation_results
        assert "A03_Injection" in validation_results
        
        # Check access control implementation
        access_control = validation_results["A01_Broken_Access_Control"]
        assert "JWT-based authentication" in str(access_control["implemented"])
        
        # Check cryptographic controls
        crypto = validation_results["A02_Cryptographic_Failures"]
        assert "bcrypt for password hashing" in str(crypto["implemented"])
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # This would require more complex setup with real rate limiting
        # For now, test that the rate limiter class works
        from ..core.security import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=2)
        
        # First request should be allowed
        assert limiter.is_allowed("192.168.1.1")
        
        # Second request should be allowed  
        assert limiter.is_allowed("192.168.1.1")
        
        # Third request should be blocked
        assert not limiter.is_allowed("192.168.1.1")
        
        # Different IP should still be allowed
        assert limiter.is_allowed("192.168.1.2")
    
    def test_input_validation(self):
        """Test input validation and sanitization"""
        from ..core.security import SecurityManager
        
        # Test input sanitization
        dangerous_input = "<script>alert('xss')</script>\x00\x01malicious"
        clean_input = SecurityManager.sanitize_input(dangerous_input)
        
        assert "<script>" not in clean_input
        assert "\x00" not in clean_input
        assert "\x01" not in clean_input
        
        # Test path sanitization
        dangerous_path = "../../../etc/passwd\x00"
        clean_path = SecurityManager.sanitize_file_path(dangerous_path)
        
        assert "../" not in clean_path
        assert "\x00" not in clean_path

class TestAPIKeyAuthentication:
    """Test API key authentication functionality"""
    
    def test_api_key_token_generation(self):
        """Test API key JWT token generation"""
        api_key_id = uuid4()
        owner_id = uuid4()
        scopes = ["knowledge:read", "sessions:read"]
        project_access = ["project1", "project2"]
        
        token = jwt_service.generate_api_key_token(
            api_key_id=api_key_id,
            owner_id=owner_id,
            scopes=scopes,
            project_access=project_access
        )
        
        assert token is not None
        
        # Validate token
        payload = jwt_service.validate_token(token)
        assert payload["sub"] == str(api_key_id)
        assert payload["key_id"] == str(api_key_id)
        assert payload["owner_id"] == str(owner_id)
        assert payload["scopes"] == scopes
        assert payload["project_access"] == project_access
        assert payload["token_type"] == "api_key"

# Test configuration
def test_security_configuration():
    """Test security configuration settings"""
    config = get_security_config("development")
    
    assert config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert config.MAX_FAILED_LOGIN_ATTEMPTS == 10  # Development is more permissive
    assert config.PASSWORD_MIN_LENGTH >= 8
    assert config.BCRYPT_ROUNDS >= 12
    
    # Test production config
    prod_config = get_security_config("production") 
    assert prod_config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 15  # Stricter
    assert prod_config.MAX_FAILED_LOGIN_ATTEMPTS == 5

# Integration test
@pytest.mark.asyncio
async def test_full_authentication_flow():
    """Test complete authentication flow"""
    # This test would require database setup and more complex testing infrastructure
    # For now, test the components individually
    
    # Test JWT service
    user_id = uuid4()
    token = jwt_service.generate_access_token(
        user_id=user_id,
        email="test@example.com", 
        role=UserRole.DEVELOPER
    )
    
    # Test token validation
    payload = jwt_service.validate_token(token)
    assert payload["sub"] == str(user_id)
    
    # Test current user extraction
    current_user = jwt_service.extract_current_user(token)
    assert current_user.user_id == user_id
    assert current_user.role == UserRole.DEVELOPER

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])