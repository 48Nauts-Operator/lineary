#!/bin/bash

# Lineary MCP Installation for Claude Code
# This script configures Lineary MCP server for Claude Code

echo "======================================="
echo "Lineary MCP Server Setup for Claude Code"
echo "======================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MCP_SERVER_PATH="$SCRIPT_DIR/lineary-mcp-server.py"

# Check if MCP server exists
if [ ! -f "$MCP_SERVER_PATH" ]; then
    echo "❌ Error: lineary-mcp-server.py not found at $MCP_SERVER_PATH"
    exit 1
fi

# Make MCP server executable
chmod +x "$MCP_SERVER_PATH"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -q aiohttp asyncio psycopg2-binary

# Create a launcher script for Claude Code
cat > "$SCRIPT_DIR/launch-lineary-mcp.sh" << EOF
#!/bin/bash
# Launcher script for Lineary MCP in Claude Code

export LINEARY_API_URL="https://ai-linear.blockonauts.io/api"
export LINEARY_DEBUG="false"

python3 "$MCP_SERVER_PATH"
EOF

chmod +x "$SCRIPT_DIR/launch-lineary-mcp.sh"

echo ""
echo "✅ Lineary MCP server is ready!"
echo ""
echo "To use Lineary MCP in Claude Code, you need to:"
echo ""
echo "1. Add it to your Claude Code MCP configuration"
echo "   The MCP server is located at:"
echo "   $MCP_SERVER_PATH"
echo ""
echo "2. Or launch Claude Code with the MCP server:"
echo "   claude --mcp-server lineary:python3:$MCP_SERVER_PATH"
echo ""
echo "3. Alternative: Set environment variable before starting Claude Code:"
echo "   export CLAUDE_MCP_SERVERS='lineary:python3:$MCP_SERVER_PATH'"
echo "   claude"
echo ""
echo "Available MCP Tools once configured:"
echo "  - create_project: Create new projects"
echo "  - create_issue: Create tasks/issues"
echo "  - list_projects: List all projects"
echo "  - list_issues: List issues with filters"
echo "  - update_issue: Update issue status"
echo "  - create_sprint: Create sprints"
echo "  - generate_ai_tasks: AI-powered task breakdown"
echo ""
echo "Test the MCP server directly:"
echo "  echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}' | python3 $MCP_SERVER_PATH"
echo ""