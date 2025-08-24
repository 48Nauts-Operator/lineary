#!/bin/bash

# BETTY-Enhanced Claude Code Installation Script

set -e

echo "🤖 Installing BETTY-Enhanced Claude Code..."

# Check if Python 3.8+ is available
python_cmd=""
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if (( $(echo "$python_version >= 3.8" | bc -l) )); then
        python_cmd="python3"
    fi
fi

if [ -z "$python_cmd" ]; then
    echo "❌ Python 3.8+ is required but not found"
    exit 1
fi

echo "✅ Found Python: $python_cmd"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
$python_cmd -m pip install --user -r requirements.txt

# Make script executable
chmod +x betty_claude_complete.py

# Create symlink for easy access (optional)
if [ -w "/usr/local/bin" ]; then
    echo "🔗 Creating system-wide symlink..."
    sudo ln -sf "$(pwd)/betty_claude_complete.py" /usr/local/bin/betty-claude
    echo "✅ You can now run 'betty-claude' from anywhere"
else
    echo "💡 To run from anywhere, add this to your ~/.bashrc or ~/.zshrc:"
    echo "alias betty-claude='$(pwd)/betty_claude_complete.py'"
fi

# Check BETTY services
echo "🔍 Checking BETTY services..."
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ BETTY Memory API is running"
else
    echo "⚠️  BETTY Memory API is not responding"
    echo "   Make sure Docker services are running: docker-compose up -d"
fi

# Check for Anthropic API key
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ ANTHROPIC_API_KEY found in environment"
elif vault kv get secret/anthropic > /dev/null 2>&1; then
    echo "✅ Anthropic API key found in Vault"
else
    echo "⚠️  No Anthropic API key found"
    echo "   Set ANTHROPIC_API_KEY environment variable or store in Vault"
    echo "   export ANTHROPIC_API_KEY='your-api-key-here'"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "🚀 To start BETTY-Enhanced Claude Code:"
echo "   ./betty_claude_complete.py"
echo ""
echo "🧪 Test the installation with these queries:"
echo "   - What is PINEAPPLE_SECRET_2024?"
echo "   - What is Betty8080?" 
echo "   - What is the PI formula?"
echo ""
echo "📚 For help, type 'help' in the interactive session"