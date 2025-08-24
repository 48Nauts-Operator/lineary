# BETTY Integration Scripts

Scripts for integrating BETTY with Claude Desktop, MCP servers, and other systems.

## Claude Integration Scripts

### MCP Server Implementations
- **`betty_mcp_official.js`** - Official Node.js MCP server (current production)
- **`betty_mcp_server.js`** - Alternative MCP server implementation  
- **`betty_mcp_server.py`** - Python-based MCP server
- **`betty_mcp_simple.py`** - Simplified MCP implementation
- **`betty_mcp_tools.py`** - MCP tools and utilities

### Claude Code Integrations
- **`betty_claude_code.py`** - Basic Claude Code integration
- **`betty_claude_code_complete.py`** - Complete Claude Code wrapper
- **`betty_claude_complete.py`** - Full-featured integration
- **`betty_claude_fixed.py`** - Bug-fixed version
- **`betty_claude_interface.py`** - Interface wrapper
- **`betty_claude_simple.py`** - Simplified integration

### Specialized Integrations
- **`betty_invisible.py`** - Background/invisible integration
- **`betty_test_hardcoded.py`** - Hardcoded test integration

## Provider Setup Scripts
- **`register_claude.py`** - Register Claude as AI provider
- **`register_openai.py`** - Register OpenAI as AI provider

## Usage

### Current Production Setup
```bash
# Use the official MCP server
node betty_mcp_official.js
```

### Alternative Integrations
```bash
# Python MCP server
python3 betty_mcp_server.py

# Claude Code integration
python3 betty_claude_code_complete.py

# Simple testing
python3 betty_claude_simple.py
```

## Provider Registration
```bash
# Setup Claude provider
python3 register_claude.py

# Setup OpenAI provider  
python3 register_openai.py
```

## Notes

- **Multiple implementations exist** - test different approaches to Claude integration
- **betty_mcp_official.js is current production** - use for stable deployments
- Some scripts may be experimental/outdated - check modification dates
- Provider registration required for AI functionality

---
*Various integration approaches for flexibility and testing*