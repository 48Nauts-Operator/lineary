# Installing Lineary MCP Server in Claude Code

## Quick Installation

### Option 1: Using Local Package (Recommended)
Since the package is already linked locally, you can install it with:

```bash
claude mcp add lineary -s user -- npx -y @lineary/mcp-server
```

### Option 2: Direct Path Installation
Using the local path directly:

```bash
claude mcp add lineary -s user -- node /home/jarvis/projects/AI-Linear/mcp-server/index.js
```

### Option 3: Using npm link (Already Done)
The package is already linked globally, so you can use:

```bash
claude mcp add lineary -s user -- mcp-server-lineary
```

## Verify Installation

After adding the MCP server, verify it's installed:

```bash
claude mcp list
```

You should see `lineary` in the list of installed MCP servers.

## Using the MCP Server

Once installed, in Claude Code you can:

1. Type `/mcp` to see all available MCP servers including Lineary
2. Use natural language to interact with Lineary:
   - "Create a new project called Mobile App"
   - "List all projects" 
   - "Create an issue: Implement user authentication"
   - "Show all in-progress issues"
   - "Generate tasks for shopping cart feature"

## Available Tools

- `create_project` - Create a new project
- `create_issue` - Create a new issue/task
- `list_projects` - List all projects
- `list_issues` - List issues with filters
- `update_issue` - Update issue status
- `delete_issue` - Delete an issue
- `create_sprint` - Create a new sprint
- `generate_ai_tasks` - AI-powered task breakdown

## Removing the MCP Server

If you need to remove it:

```bash
claude mcp remove lineary
```

## Troubleshooting

### MCP server not showing up
1. Make sure you've added it with `claude mcp add`
2. Check it's in the list: `claude mcp list`
3. Restart Claude Code if needed

### Connection errors
1. Verify the Lineary backend is running:
   ```bash
   curl https://ai-linear.blockonauts.io/api/health
   ```

2. Check Docker containers:
   ```bash
   docker-compose ps
   ```

### Debug the MCP server
Test it directly:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node /home/jarvis/projects/AI-Linear/mcp-server/index.js
```

## Publishing to npm (Optional)

If you want to publish this package to npm for easier distribution:

1. Create an npm account at https://www.npmjs.com
2. Login: `npm login`
3. Publish: `cd mcp-server && npm publish --access public`
4. Then anyone can use: `claude mcp add lineary -s user -- npx -y @lineary/mcp-server`