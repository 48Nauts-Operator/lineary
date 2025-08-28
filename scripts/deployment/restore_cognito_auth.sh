#!/bin/bash
# AWS Cognito Authentication Restoration Script for 137docs
# This script completes the restoration by installing the required dependencies

echo "🔐 Restoring AWS Cognito Authentication for 137docs..."
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "/home/jarvis/projects/137docs/frontend/package.json" ]; then
    echo "❌ Error: 137docs frontend directory not found!"
    exit 1
fi

# Change to 137docs frontend directory
cd /home/jarvis/projects/137docs/frontend

echo "📦 Installing AWS Amplify dependencies..."

# Install AWS Amplify dependencies
npm install @aws-amplify/auth@^6.0.0 @aws-amplify/core@^6.0.0

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies. You may need to run with sudo:"
    echo "sudo npm install @aws-amplify/auth@^6.0.0 @aws-amplify/core@^6.0.0"
    exit 1
fi

echo ""
echo "🎯 Cognito Authentication Restoration Complete!"
echo "================================================"
echo "✅ AWS Amplify dependencies added to package.json"
echo "✅ Cognito service restored from backup"
echo "✅ Environment variables configured"
echo "✅ All imports updated to use Cognito service"
echo "✅ Dependencies installed"
echo ""
echo "⚠️  IMPORTANT: Update these environment variables with real values:"
echo "   - VITE_COGNITO_USER_POOL_ID (currently placeholder)"
echo "   - VITE_COGNITO_CLIENT_ID (currently placeholder)"
echo ""
echo "🚀 The frontend should now use AWS Cognito authentication!"