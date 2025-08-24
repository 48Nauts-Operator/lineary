# Lineary MCP Server for Claude Desktop

This directory contains the MCP (Model Context Protocol) server for integrating Lineary project management directly into Claude Desktop.

## Quick Start

### 1. Install Dependencies

```bash
pip3 install aiohttp asyncio
```

### 2. Configure Claude Desktop

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lineary": {
      "command": "python3",
      "args": ["/path/to/AI-Linear/lineary-mcp-server.py"],
      "env": {
        "LINEARY_API_URL": "https://ai-linear.blockonauts.io/api"
      }
    }
  }
}
```

### 3. Start Lineary Services

```bash
docker-compose up -d
```

### 4. Restart Claude Desktop

The Lineary MCP server will now be available in Claude.

## Available Tools

Once configured, you can use these natural language commands in Claude:

### Project Management
- "Create a new project called 'Mobile App'"
- "List all projects"
- "Show project details"

### Issue Management
- "Create an issue: Implement user authentication"
- "List all in-progress issues"
- "Update issue #123 to done"
- "Show issues with priority 1"

### Sprint Management
- "Create a 2-week sprint starting today"
- "Add issues #123, #124, #125 to sprint"
- "Show current sprint status"

### AI Features
- "Generate tasks for implementing shopping cart feature"
- "Break down 'user authentication' into tasks"
- "Create a complex feature breakdown for video streaming"

## MCP Resources

The server provides these resources you can query:

- `lineary://projects` - All projects
- `lineary://issues/active` - Active issues
- `lineary://issues/todo` - Todo issues
- `lineary://sprints/current` - Current sprint
- `lineary://health` - System health

## Example Usage in Claude

```
You: Create a new project for our Q4 features
Claude: I'll create a new project for Q4 features...
[Creates project using MCP]

You: Generate tasks for implementing OAuth integration
Claude: I'll break down the OAuth integration feature...
[Generates 5 tasks with story points]

You: Show all active issues
Claude: Here are the currently active issues...
[Lists in-progress issues]
```

## Testing the MCP Server

Test the server directly:

```bash
# Test initialization
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 lineary-mcp-server.py

# List available tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 lineary-mcp-server.py
```

## Troubleshooting

### Check Logs
```bash
tail -f /tmp/lineary-mcp.log
```

### Enable Debug Mode
```bash
export LINEARY_DEBUG=true
python3 lineary-mcp-server.py
```

### Verify API Connection
```bash
curl https://ai-linear.blockonauts.io/api/health
```

## API Endpoints Used

The MCP server communicates with these Lineary API endpoints:

- `GET/POST /api/projects` - Project management
- `GET/POST/PATCH /api/issues` - Issue management
- `GET/POST /api/sprints` - Sprint management
- `GET /api/health` - Health check

## Development

To modify the MCP server:

1. Edit `lineary-mcp-server.py`
2. Test changes locally
3. Restart Claude Desktop to reload

## Support

For issues or questions:
- Check the main documentation in `/docs`
- Review the MCP installation guide
- Check API health at https://ai-linear.blockonauts.io/api/health