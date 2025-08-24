#!/usr/bin/env python3

import json
import sys
import urllib.request
import urllib.parse

def betty_search(query):
    """Search BETTY memory system"""
    try:
        search_query = urllib.parse.quote(query)
        search_url = f"http://localhost:8001/api/knowledge/?search={search_query}"
        
        req = urllib.request.Request(search_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get('data', [])
                
                # Filter relevant items
                results = []
                for item in items:
                    content = item.get('content', '')
                    if ('Error calling Claude API' not in content and 
                        'HTTP Error' not in content and
                        len(content.strip()) > 20):
                        results.append({
                            'title': item.get('title', 'No title'),
                            'content': content[:300] + ('...' if len(content) > 300 else ''),
                            'tags': item.get('tags', [])
                        })
                
                if results:
                    output = f"Found {len(results)} memories for '{query}':\n\n"
                    for i, item in enumerate(results[:5], 1):
                        output += f"{i}. {item['title']}\n   {item['content']}\n\n"
                    return output
                else:
                    return f"No memories found for '{query}'"
            else:
                return f"BETTY search failed: HTTP {response.status}"
                
    except Exception as e:
        return f"BETTY error: {str(e)}"

def handle_request(request):
    """Handle MCP request"""
    method = request.get("method")
    
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            }
        }
    
    elif method == "tools/list":
        return {
            "tools": [
                {
                    "name": "betty_search",
                    "description": "Search BETTY memory system for previous conversations",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
    
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "betty_search":
            result = betty_search(arguments.get("query", ""))
            return {
                "content": [{"type": "text", "text": result}]
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True
            }
    
    else:
        return {
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

def main():
    """Main MCP server loop"""
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            
            # Add JSON-RPC fields
            response["jsonrpc"] = "2.0"
            if "id" in request:
                response["id"] = request["id"]
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": request.get("id") if 'request' in locals() else None
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()