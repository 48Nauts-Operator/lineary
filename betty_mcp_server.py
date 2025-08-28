#!/usr/bin/env python3
# ABOUTME: MCP server for Lineary Betty integration
# ABOUTME: Provides Claude Desktop access to centralized Betty Memory System

import asyncio
import json
import sys
import urllib.request
import urllib.parse
from typing import Any, Sequence

# MCP server implementation
class StdioMCPServer:
    def __init__(self):
        self.betty_base_url = "http://localhost:3034"
        self.user_id = "e8e3f2de-070d-4dbd-b899-e49745f1d29b"
        self.project_id = "lineary-project"
    
    async def run(self):
        """Main server loop"""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                message = json.loads(line.strip())
                response = await self.handle_message(message)
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
    
    async def handle_message(self, message: dict) -> dict:
        """Handle incoming MCP message"""
        method = message.get("method")
        params = message.get("params", {})
        request_id = message.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "betty-lineary-mcp",
                        "version": "2.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "betty_search_lineary",
                            "description": "Search Lineary knowledge in Betty Memory System",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Search query for Lineary knowledge"
                                    }
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "betty_store_lineary",
                            "description": "Store Lineary development knowledge in Betty",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string",
                                        "description": "Title of the knowledge item"
                                    },
                                    "content": {
                                        "type": "string", 
                                        "description": "Detailed content/insight to store"
                                    },
                                    "knowledge_type": {
                                        "type": "string",
                                        "description": "Type: development, bug_fix, architecture, etc."
                                    },
                                    "tags": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Additional tags for categorization"
                                    }
                                },
                                "required": ["title", "content"]
                            }
                        },
                        {
                            "name": "betty_cross_project_insights",
                            "description": "Get insights from other projects via Betty v2.0",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Query to find similar patterns across projects"
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "betty_search_lineary":
                result = await self.betty_search(arguments.get("query", ""))
            elif tool_name == "betty_store_lineary":
                result = await self.betty_store(
                    arguments.get("title", ""),
                    arguments.get("content", ""),
                    arguments.get("knowledge_type", "development"),
                    arguments.get("tags", [])
                )
            elif tool_name == "betty_cross_project_insights":
                result = await self.betty_cross_project(arguments.get("query", ""))
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def betty_search(self, query: str) -> str:
        """Search Betty for Lineary knowledge"""
        try:
            search_data = {
                "query": query,
                "user_id": self.user_id,
                "k": 5,
                "search_type": "hybrid",
                "project_filter": self.project_id
            }
            
            data = json.dumps(search_data).encode('utf-8')
            search_url = f"{self.betty_base_url}/api/knowledge/search"
            
            req = urllib.request.Request(
                search_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'data' in result and result['data']:
                    results_text = f"Found {len(result['data'])} Lineary knowledge items:\n\n"
                    for i, item in enumerate(result['data'][:5], 1):
                        results_text += f"{i}. {item['title']}\n"
                        results_text += f"   Type: {item['knowledge_type']}\n"
                        results_text += f"   Content: {item['content'][:200]}...\n"
                        if 'tags' in item:
                            results_text += f"   Tags: {', '.join(item['tags'])}\n"
                        results_text += "\n"
                    return results_text
                else:
                    return f"No Lineary knowledge found for query: {query}"
                    
        except Exception as e:
            return f"Error searching Betty: {str(e)}"
    
    async def betty_store(self, title: str, content: str, knowledge_type: str = "development", tags: list = None) -> str:
        """Store knowledge in Betty"""
        try:
            if tags is None:
                tags = []
            
            store_data = {
                "title": f"Lineary - {title}",
                "content": content,
                "knowledge_type": knowledge_type,
                "tags": ["lineary", "development"] + tags,
                "user_id": self.user_id,
                "project_id": self.project_id
            }
            
            data = json.dumps(store_data).encode('utf-8')
            store_url = f"{self.betty_base_url}/api/knowledge/create"
            
            req = urllib.request.Request(
                store_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return f"Successfully stored Lineary knowledge: {title}"
                
        except Exception as e:
            return f"Error storing knowledge in Betty: {str(e)}"
    
    async def betty_cross_project(self, query: str) -> str:
        """Get cross-project insights via Betty v2.0"""
        try:
            search_data = {
                "query": query,
                "user_id": self.user_id,
                "include_projects": "all",
                "similarity_threshold": 0.7
            }
            
            data = json.dumps(search_data).encode('utf-8')
            search_url = f"{self.betty_base_url}/api/v2/cross-project/search"
            
            req = urllib.request.Request(
                search_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'data' in result and 'results' in result['data'] and result['data']['results']:
                    results_text = f"Cross-project insights for '{query}':\n\n"
                    for i, item in enumerate(result['data']['results'][:3], 1):
                        results_text += f"{i}. Project: {item['project_id']}\n"
                        results_text += f"   Pattern: {item['title']}\n"
                        results_text += f"   Relevance: {item['score']:.2f}\n"
                        results_text += f"   Insight: {item['content'][:150]}...\n\n"
                    return results_text
                else:
                    return f"No cross-project insights found for: {query}"
                    
        except Exception as e:
            return f"Error getting cross-project insights: {str(e)}"


async def main():
    server = StdioMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())