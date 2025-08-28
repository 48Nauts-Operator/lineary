#!/usr/bin/env python3

# ABOUTME: BETTY MCP Server - Provides BETTY memory system as MCP tools for Claude Code
# ABOUTME: Allows Claude to naturally search and store memory through standard MCP protocol

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Sequence
import urllib.request
import urllib.parse
from datetime import datetime, timezone

class BettyMCPServer:
    """MCP Server that provides BETTY memory system tools"""
    
    def __init__(self):
        self.betty_base_url = "http://localhost:3034"
        self.user_id = "e8e3f2de-070d-4dbd-b899-e49745f1d29b"
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return await self.list_tools()
        elif method == "tools/call":
            return await self.call_tool(params)
        elif method == "initialize":
            return {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}}
        else:
            return {"error": {"code": -32601, "message": f"Method not found: {method}"}}
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available BETTY tools"""
        return {
            "tools": [
                {
                    "name": "betty_search",
                    "description": "Search BETTY memory system for previous conversations and knowledge",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant information in BETTY memory"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "betty_store",
                    "description": "Store information in BETTY memory system",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title for the memory item"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to store in memory"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags for categorizing the memory"
                            }
                        },
                        "required": ["title", "content"]
                    }
                },
                {
                    "name": "betty_stats",
                    "description": "Get BETTY memory system statistics and health status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    
    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute BETTY tool calls"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "betty_search":
                return await self.betty_search(arguments["query"])
            elif tool_name == "betty_store":
                return await self.betty_store(
                    arguments["title"], 
                    arguments["content"],
                    arguments.get("tags", [])
                )
            elif tool_name == "betty_stats":
                return await self.betty_stats()
            else:
                return {
                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                    "isError": True
                }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    async def betty_search(self, query: str) -> Dict[str, Any]:
        """Search BETTY memory system"""
        try:
            search_query = urllib.parse.quote(query)
            search_url = f"{self.betty_base_url}/api/knowledge/?search={search_query}"
            
            req = urllib.request.Request(search_url)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    items = data.get('data', [])
                    
                    # Filter out error messages and format results
                    relevant_items = []
                    for item in items:
                        content = item.get('content', '')
                        if ('Error calling Claude API' not in content and 
                            'HTTP Error' not in content and
                            len(content.strip()) > 20):
                            relevant_items.append({
                                'title': item.get('title', 'No title'),
                                'content': content[:500] + ('...' if len(content) > 500 else ''),
                                'created': item.get('created_at', ''),
                                'tags': item.get('tags', [])
                            })
                    
                    if relevant_items:
                        result_text = f"Found {len(relevant_items)} relevant memories for '{query}':\n\n"
                        for i, item in enumerate(relevant_items[:5], 1):  # Show top 5
                            result_text += f"{i}. **{item['title']}**\n"
                            result_text += f"   {item['content']}\n"
                            if item['tags']:
                                result_text += f"   Tags: {', '.join(item['tags'])}\n"
                            result_text += "\n"
                        
                        return {
                            "content": [{"type": "text", "text": result_text}]
                        }
                    else:
                        return {
                            "content": [{"type": "text", "text": f"No relevant memories found for '{query}'"}]
                        }
                else:
                    return {
                        "content": [{"type": "text", "text": f"BETTY search failed: HTTP {response.status}"}],
                        "isError": True
                    }
                    
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"BETTY search error: {str(e)}"}],
                "isError": True
            }
    
    async def betty_store(self, title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
        """Store information in BETTY"""
        try:
            knowledge_item = {
                "title": title,
                "content": content,
                "knowledge_type": "reference",
                "source_type": "user_input",
                "user_id": self.user_id,
                "confidence": "high",
                "summary": content[:100] + ('...' if len(content) > 100 else ''),
                "tags": tags or []
            }
            
            data = json.dumps(knowledge_item).encode('utf-8')
            req = urllib.request.Request(
                f"{self.betty_base_url}/api/knowledge/",
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in [200, 201]:
                    return {
                        "content": [{"type": "text", "text": f"Successfully stored '{title}' in BETTY memory"}]
                    }
                else:
                    return {
                        "content": [{"type": "text", "text": f"Failed to store in BETTY: HTTP {response.status}"}],
                        "isError": True
                    }
                    
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"BETTY store error: {str(e)}"}],
                "isError": True
            }
    
    async def betty_stats(self) -> Dict[str, Any]:
        """Get BETTY system statistics"""
        try:
            # Get health status
            req = urllib.request.Request(f"{self.betty_base_url}/health/")
            with urllib.request.urlopen(req, timeout=5) as response:
                health_data = json.loads(response.read().decode('utf-8'))
            
            # Get knowledge stats
            req = urllib.request.Request(f"{self.betty_base_url}/api/knowledge/stats/")
            with urllib.request.urlopen(req, timeout=5) as response:
                stats_data = json.loads(response.read().decode('utf-8'))
            
            stats_text = f"""BETTY Memory System Status:

🟢 Status: {health_data.get('status', 'Unknown')}
📊 Total Knowledge Items: {stats_data['data']['total_items']}
📈 Knowledge by Type: {dict(stats_data['data']['items_by_type'])}
🏷️  Most Common Tags: {[f"{tag['tag']} ({tag['count']})" for tag in stats_data['data']['most_common_tags'][:5]]}
💾 Total Storage: {stats_data['data']['total_size_bytes']} bytes
🎯 Average Confidence: {stats_data['data']['avg_confidence']:.2f}

Service: {health_data.get('service', 'Unknown')}
Version: {health_data.get('version', 'Unknown')}
Uptime: {health_data.get('uptime', 'Unknown')}"""

            return {
                "content": [{"type": "text", "text": stats_text}]
            }
            
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"BETTY stats error: {str(e)}"}],
                "isError": True
            }

async def main():
    """Run MCP server"""
    server = BettyMCPServer()
    
    while True:
        try:
            # Read JSON-RPC request from stdin
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line.strip())
            response = await server.handle_request(request)
            
            # Add request ID if present
            if "id" in request:
                response["id"] = request["id"]
            
            # Write JSON-RPC response to stdout
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
            if "id" in request:
                error_response["id"] = request["id"]
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())