#!/usr/bin/env python3
"""
Simple Development API Key Generator for BETTY Memory System
Uses the admin API endpoints to create an API key for the test user.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

# Test user credentials (from the instructions)
TEST_USER_EMAIL = "andre@test.com"
TEST_USER_PASSWORD = "testpassword123"  # You may need to set this in the database

# API base URL
API_BASE_URL = "http://localhost:3034"

async def create_development_api_key():
    """Create a development API key using the API endpoints."""
    
    print("🔧 BETTY Development API Key Generator (API Method)")
    print("=" * 55)
    
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Login to get an access token
            print(f"🔑 Logging in as: {TEST_USER_EMAIL}")
            
            login_response = await client.post(
                f"{API_BASE_URL}/api/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                }
            )
            
            if login_response.status_code != 200:
                print(f"❌ Login failed: {login_response.status_code}")
                print(f"Response: {login_response.text}")
                
                # Try to check if user exists and suggest password setup
                print("\n💡 Note: You may need to set up the test user password.")
                print("   Run this SQL in the database:")
                print("   UPDATE auth_users SET password_hash = '$2b$12$...' WHERE email = 'andre@test.com';")
                return
            
            login_data = login_response.json()
            access_token = login_data["access_token"]
            print("✅ Login successful!")
            
            # Step 2: Create API key
            print("\n🔑 Creating development API key...")
            
            api_key_request = {
                "name": "VSCode Extension Development Key",
                "scopes": [
                    "sessions:read",
                    "sessions:write", 
                    "knowledge:read",
                    "knowledge:write"
                ],
                "project_access": [],
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "rate_limit_per_hour": 2000
            }
            
            api_key_response = await client.post(
                f"{API_BASE_URL}/api/auth/api-keys",
                json=api_key_request,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if api_key_response.status_code != 201:
                print(f"❌ API key creation failed: {api_key_response.status_code}")
                print(f"Response: {api_key_response.text}")
                return
            
            api_key_data = api_key_response.json()
            api_key = api_key_data["data"]["api_key"]
            
            print("✅ API Key created successfully!")
            print("=" * 55)
            print(f"🆔 API Key ID: {api_key_data['data']['api_key_id']}")
            print(f"📛 Name: {api_key_data['data']['name']}")
            print(f"🔤 Prefix: {api_key_data['data']['key_prefix']}")
            print(f"⏰ Expires: {api_key_data['data']['expires_at']}")
            print(f"🚦 Rate Limit: {api_key_data['data']['rate_limit_per_hour']}/hour")
            
            print("\n" + "=" * 55)
            print("🔐 DEVELOPMENT API KEY (save this securely):")
            print("=" * 55)
            print(api_key)
            print("=" * 55)
            
            print("\n📋 Usage in VSCode Extension:")
            print(f"   Set X-API-Key header to: {api_key}")
            
            print("\n🧪 Test the API key:")
            print(f"   curl -H 'X-API-Key: {api_key}' \\")
            print(f"        {API_BASE_URL}/api/memory/sessions")
            
            # Step 3: Test the API key
            print("\n🔍 Testing the API key...")
            test_response = await client.get(
                f"{API_BASE_URL}/api/memory/sessions",
                headers={"X-API-Key": api_key}
            )
            
            if test_response.status_code == 200:
                print("✅ API key test successful!")
                sessions_data = test_response.json()
                print(f"   Found {len(sessions_data.get('data', []))} sessions")
            else:
                print(f"⚠️  API key test returned: {test_response.status_code}")
                print(f"   Response: {test_response.text}")
            
            print("\n⚠️  Security Notes:")
            print("   - This is a DEVELOPMENT key with elevated permissions")
            print("   - Do NOT use in production environments")
            print("   - The key expires in 30 days")
            print("   - Store the key securely - it won't be shown again")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_development_api_key())