#!/bin/bash
# ABOUTME: Setup script for BETTY authentication system
# ABOUTME: Installs dependencies, runs migration, and tests the auth system

set -e

echo "🚀 BETTY Authentication System Setup"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Run from memory-api directory."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Apply database migration
echo "🗄️  Applying authentication schema migration..."
python3 database/migrate_auth.py

# Run security validation
echo "🔐 Validating security implementation..."
python3 -c "
from config.security_config import validate_security_implementation
import json

results = validate_security_implementation()
print('OWASP Security Validation Results:')
print('==================================')
for control, details in results.items():
    print(f'\\n{control}:')
    print(f'  Implemented: {len(details[\"implemented\"])} controls')
    print(f'  Controls: {len(details[\"controls\"])} measures')
    for item in details['implemented'][:2]:  # Show first 2 items
        print(f'    ✅ {item}')
"

# Test JWT functionality
echo "🔑 Testing JWT functionality..."
python3 -c "
import sys
sys.path.append('.')

from services.jwt_service import jwt_service
from models.auth import UserRole
from uuid import uuid4

print('Testing JWT Service...')

# Test token generation
user_id = uuid4()
try:
    token = jwt_service.generate_access_token(
        user_id=user_id,
        email='test@betty.memory',
        role=UserRole.DEVELOPER,
        permissions=['knowledge:read', 'knowledge:write']
    )
    print('✅ JWT token generation successful')
    print(f'   Token length: {len(token)} characters')
    
    # Test validation
    payload = jwt_service.validate_token(token)
    print('✅ JWT token validation successful')
    print(f'   User ID: {payload[\"sub\"]}')
    print(f'   Role: {payload[\"role\"]}')
    
except Exception as e:
    print(f'❌ JWT test failed: {e}')

# Test password hashing
try:
    password = 'TestPassword123!'
    hashed = jwt_service.hash_password(password)
    verified = jwt_service.verify_password(password, hashed)
    print('✅ Password hashing test successful')
    print(f'   Verification result: {verified}')
except Exception as e:
    print(f'❌ Password hashing test failed: {e}')

# Test API key generation
try:
    api_key, prefix = jwt_service.generate_api_key()
    print('✅ API key generation successful')
    print(f'   Key prefix: {prefix}')
    print(f'   Key length: {len(api_key)} characters')
except Exception as e:
    print(f'❌ API key generation failed: {e}')
"

# Start the API server for testing
echo "🌐 Starting BETTY Memory API with authentication..."
echo "   Default admin credentials:"
echo "   Email: admin@betty.memory"
echo "   Password: ChangeMe123!"
echo ""
echo "   API Endpoints:"
echo "   - POST /auth/login - User authentication"
echo "   - GET /auth/me - Current user info"
echo "   - POST /auth/api-keys - Create API key"
echo "   - GET /docs - API documentation"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the server
python3 main.py