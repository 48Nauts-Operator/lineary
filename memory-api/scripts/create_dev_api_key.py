#!/usr/bin/env python3
"""
Development API Key Generator for BETTY Memory System
Creates an API key for testing the VSCode extension with the test user.

This script safely generates an API key using the existing authentication infrastructure
without bypassing any security mechanisms.
"""

import asyncio
import sys
import os
from uuid import UUID
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from the memory-api
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings
from core.database import DatabaseManager
from models.auth import APIKeyCreateRequest
from services.auth_service import AuthService

# Test user details (from the instructions)
TEST_USER_ID = UUID("487a5680-f22c-4337-bd63-d59a06d1c949")
TEST_USER_EMAIL = "andre@test.com"

async def create_development_api_key():
    """Create a development API key for the test user."""
    
    print("🔧 BETTY Development API Key Generator")
    print("=" * 50)
    
    try:
        # Initialize settings and database
        settings = get_settings()
        print(f"📊 Connecting to database: {settings.postgres_host}:{settings.postgres_port}")
        
        # Initialize database manager
        db_manager = DatabaseManager(settings)
        await db_manager.initialize()
        
        # Monkey patch the auth service to use our database manager
        import services.auth_service
        services.auth_service.get_database_session = lambda: DatabaseSessionWrapper(db_manager)
        
        # Initialize auth service
        auth_service = AuthService()
        
        # Verify test user exists
        print(f"👤 Verifying test user: {TEST_USER_EMAIL}")
        test_user = await auth_service.get_user_by_id(TEST_USER_ID)
        if not test_user:
            print(f"❌ Test user not found: {TEST_USER_EMAIL}")
            print("Please ensure the test user exists in the database.")
            return
        
        if not test_user.is_active:
            print(f"❌ Test user is not active: {TEST_USER_EMAIL}")
            return
        
        print(f"✅ Test user found: {test_user.full_name} ({test_user.email})")
        
        # Create API key request with appropriate scopes for VSCode extension testing
        api_key_request = APIKeyCreateRequest(
            name="VSCode Extension Development Key",
            scopes=[
                "sessions:read",     # Read chat sessions
                "sessions:write",    # Create and update sessions  
                "knowledge:read",    # Read stored knowledge
                "knowledge:write",   # Write knowledge entries
            ],
            project_access=[],  # No specific project restrictions for dev
            expires_at=datetime.now() + timedelta(days=30),  # Expire in 30 days
            rate_limit_per_hour=2000  # Higher limit for development
        )
        
        print("\n🔑 Creating API key with scopes:")
        for scope in api_key_request.scopes:
            print(f"   - {scope}")
        
        # Create the API key
        api_key_with_secret = await auth_service.create_api_key(
            api_key_request, 
            TEST_USER_ID
        )
        
        print("\n✅ API Key created successfully!")
        print("=" * 50)
        print(f"🆔 API Key ID: {api_key_with_secret.api_key_id}")
        print(f"📛 Name: {api_key_with_secret.name}")
        print(f"🔤 Prefix: {api_key_with_secret.key_prefix}")
        print(f"⏰ Expires: {api_key_with_secret.expires_at}")
        print(f"🚦 Rate Limit: {api_key_with_secret.rate_limit_per_hour}/hour")
        
        print("\n" + "=" * 50)
        print("🔐 DEVELOPMENT API KEY (save this - it won't be shown again):")
        print("=" * 50)
        print(api_key_with_secret.api_key)
        print("=" * 50)
        
        print("\n📋 Usage in VSCode Extension:")
        print(f"   Set X-API-Key header to: {api_key_with_secret.api_key}")
        print(f"   Or use Authorization: Bearer {api_key_with_secret.api_key}")
        
        print("\n🧪 Test the API key with:")
        print(f"   curl -H 'X-API-Key: {api_key_with_secret.api_key}' \\")
        print(f"        http://localhost:3034/api/memory/sessions")
        
        print("\n⚠️  Security Note:")
        print("   This is a DEVELOPMENT key with elevated permissions.")
        print("   Do NOT use in production. The key expires in 30 days.")
        
    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up database connections
        if 'db_manager' in locals():
            await db_manager.close()

class DatabaseSessionWrapper:
    """Wrapper that provides session-like interface for database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def __aenter__(self):
        self.session = await self.db_manager.get_postgres_session().__aenter__()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.session.__aexit__(exc_type, exc_val, exc_tb)

if __name__ == "__main__":
    asyncio.run(create_development_api_key())