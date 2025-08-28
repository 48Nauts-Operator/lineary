# Lineary MCP Server for Claude Code

MCP server for integrating Lineary project management into Claude Code.

## Installation

Install the Lineary MCP server in Claude Code with one command:

```bash
claude mcp add lineary -s user -- node /home/jarvis/projects/AI-Linear/mcp-server/index.js
```

Or if you have npm linked it (already done):

```bash
claude mcp add lineary -s user -- mcp-server-lineary
```

## Verify Installation

```bash
claude mcp list
```

You should see `lineary` in the list.

## Available Tools

Once configured, type `/mcp` in Claude Code to see the Lineary tools:

- **create_project** - Create a new project
- **create_issue** - Create a new task/issue
- **list_projects** - List all projects
- **list_issues** - List issues with filters
- **update_issue** - Update issue status
- **delete_issue** - Delete an issue
- **create_sprint** - Create a new sprint
- **generate_ai_tasks** - AI-powered task breakdown

## Usage Examples

In Claude Code, you can use natural language:

```
"Create a new project called Mobile App"
"List all projects"
"Create an issue: Fix login bug with priority 1"
"Show all in-progress issues"
"Update issue abc123 to done"
"Generate tasks for implementing user authentication"
```

## Resources

The MCP server provides these resources:

- `lineary://projects` - All projects
- `lineary://issues/active` - Active issues
- `lineary://issues/todo` - Todo issues
- `lineary://health` - System health

## Testing

Test the server directly:
```bash
# Test with stdio
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node index.js
```

## Requirements

- Node.js 18+
- Running Lineary backend at https://ai-linear.blockonauts.io/api

## Troubleshooting

1. **Server not appearing in /mcp**
   - Restart Claude Code with the MCP server configured
   - Check the server is executable: `chmod +x index.js`

2. **Connection errors**
   - Verify Lineary backend is running: `curl https://ai-linear.blockonauts.io/api/health`
   - Check Docker containers: `docker-compose ps`

3. **Debug mode**
   ```bash
   export LINEARY_API_URL=https://ai-linear.blockonauts.io/api
   node index.js
   ```