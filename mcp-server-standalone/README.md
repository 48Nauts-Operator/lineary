# Lineary MCP Server

Connect Claude to your Lineary project management instance for AI-powered task management, analytics, and automation.

## 🚀 Quick Start

### 1. Download and Install

```bash
# Clone just the MCP server directory
git clone --depth 1 --filter=blob:none --sparse https://github.com/48Nauts-Operator/lineary.git
cd lineary
git sparse-checkout set mcp-server-standalone
cd mcp-server-standalone

# Install dependencies
npm install
```

Or download directly:
```bash
curl -L https://github.com/48Nauts-Operator/lineary/archive/refs/heads/feature/mcp-server-standalone.zip -o lineary-mcp.zip
unzip lineary-mcp.zip
cd lineary-feature-mcp-server-standalone/mcp-server-standalone
npm install
```

### 2. Configure

Choose one of these configuration methods:

#### Option A: Environment Variables (.env file)
```bash
cp .env.example .env
# Edit .env with your settings
```

#### Option B: Config File (config.json)
```bash
cp config.example.json config.json
# Edit config.json with your settings
```

### 3. Add to Claude

```bash
# For remote Lineary instance (your case)
claude mcp add lineary -s user -- node /path/to/lineary/mcp-server-standalone/index.js

# Example with full path
claude mcp add lineary -s user -- node ~/Downloads/lineary-mcp/index.js
```

## 📋 Configuration Options

### For Remote Server (Default)
If your Lineary is hosted on a remote server:

```json
{
  "apiUrl": "https://ai-linear.blockonauts.io/api"
}
```

### For Local Development
If Lineary is running on your local machine:

```json
{
  "apiUrl": "http://localhost:3134/api"
}
```

### For SSH Tunnel
If you're using SSH port forwarding:

```bash
# First, create SSH tunnel
ssh -L 3134:localhost:3134 user@your-server

# Then use local config
{
  "apiUrl": "http://localhost:3134/api"
}
```

## 🛠️ Available Tools

### Project Management
- `list_projects` - List all projects
- `create_project` - Create a new project
- `get_project` - Get project details
- `update_project` - Update project information
- `delete_project` - Delete a project

### Issue/Task Management
- `list_issues` - List issues with filters
- `create_issue` - Create a new issue
- `update_issue` - Update issue status, priority, etc.
- `delete_issue` - Delete an issue

### Sprint Management
- `list_sprints` - List all sprints
- `create_sprint` - Create a new sprint

### Analytics & Metrics
- `get_analytics` - Get project analytics including AI time saved
- `get_activity_heatmap` - Get GitHub-style activity heatmap

### Documentation
- `list_docs` - List project documentation
- `create_doc` - Create documentation pages

### Activity Tracking
- `record_activity` - Record project activity
- `record_token_usage` - Track AI token usage

## 💡 Usage Examples

Once installed, you can use these commands in Claude:

```
"List all my Lineary projects"
"Create a new issue in project X for implementing user authentication"
"Show me the analytics for my main project"
"Update issue #123 to in-progress status"
"Generate documentation for the API endpoints"
```

## 🔧 Troubleshooting

### Connection Issues
1. Verify Lineary is running:
   ```bash
   curl https://ai-linear.blockonauts.io/api/health
   ```

2. Check MCP server logs:
   ```bash
   claude mcp logs lineary
   ```

3. Test configuration:
   ```bash
   node index.js
   # Should show: "🚀 Lineary MCP Server v1.0.0"
   ```

### Common Problems

**"Cannot connect to API"**
- Check your `apiUrl` in config
- Ensure Lineary backend is running
- Verify network connectivity

**"Unauthorized"**
- Check if your Lineary instance requires authentication
- Add `apiKey` to configuration if needed

**"Project not found"**
- Verify project ID is correct
- Use `list_projects` to see available projects

## 📦 What's Included

```
mcp-server-standalone/
├── index.js           # Main MCP server
├── package.json       # Dependencies
├── config.example.json # Example configuration
├── .env.example       # Example environment variables
└── README.md          # This file
```

## 🔄 Updating

To update to the latest version:

```bash
git pull origin feature/mcp-server-standalone
npm install
```

## 🤝 Support

- **Issues**: https://github.com/48Nauts-Operator/lineary/issues
- **Documentation**: https://ai-linear.blockonauts.io/docs

## 📄 License

MIT License - See LICENSE file in the main repository

---

Made with ❤️ for Claude + Lineary integration