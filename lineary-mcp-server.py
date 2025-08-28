#!/usr/bin/env python3
"""
Lineary MCP Server - AI-Powered Project Management for Claude
Integrates Lineary project management directly into Claude Desktop
"""

import json
import sys
import asyncio
import aiohttp
from typing import Dict, List, Any
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('LINEARY_DEBUG') == 'true' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/lineary-mcp.log'), logging.StreamHandler()]
)
logger = logging.getLogger('lineary-mcp')

class LinearyMCPServer:
    def __init__(self):
        self.api_url = os.getenv('LINEARY_API_URL', 'https://ai-linear.blockonauts.io/api')
        logger.info(f"Lineary MCP Server initialized - API: {self.api_url}")
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')
        
        logger.debug(f"Handling request: {method} with params: {params}")
        
        try:
            handlers = {
                'initialize': self.initialize,
                'tools/list': self.list_tools,
                'tools/call': self.call_tool,
                'resources/list': self.list_resources,
                'resources/read': self.read_resource,
            }
            
            handler = handlers.get(method)
            if handler:
                result = await handler(params)
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': result
                }
            
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {'code': -32601, 'message': f'Method not found: {method}'}
            }
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {'code': -32603, 'message': str(e)}
            }
    
    async def initialize(self, params: Dict) -> Dict[str, Any]:
        """Initialize the MCP server"""
        return {
            'protocolVersion': '0.1.0',
            'capabilities': {
                'tools': {},
                'resources': {}
            },
            'serverInfo': {
                'name': 'lineary-mcp',
                'version': '1.0.0'
            }
        }
    
    async def list_tools(self, params: Dict) -> Dict[str, Any]:
        """List available Lineary tools"""
        return {
            'tools': [
                {
                    'name': 'create_project',
                    'description': 'Create a new project in Lineary',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string', 'description': 'Project name'},
                            'description': {'type': 'string', 'description': 'Project description'},
                            'color': {'type': 'string', 'description': 'Project color (hex)', 'default': '#8B5CF6'}
                        },
                        'required': ['name']
                    }
                },
                {
                    'name': 'create_issue',
                    'description': 'Create a new issue/task in a project',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'project_id': {'type': 'string', 'description': 'Project ID'},
                            'title': {'type': 'string', 'description': 'Issue title'},
                            'description': {'type': 'string', 'description': 'Issue description'},
                            'priority': {'type': 'number', 'minimum': 1, 'maximum': 5, 'default': 3},
                            'status': {
                                'type': 'string',
                                'enum': ['backlog', 'todo', 'in_progress', 'in_review', 'done'],
                                'default': 'todo'
                            },
                            'story_points': {'type': 'number', 'description': 'Story points'},
                            'estimated_hours': {'type': 'number', 'description': 'Estimated hours'},
                            'ai_prompt': {'type': 'string', 'description': 'AI implementation prompt'}
                        },
                        'required': ['project_id', 'title']
                    }
                },
                {
                    'name': 'list_projects',
                    'description': 'List all projects',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {}
                    }
                },
                {
                    'name': 'list_issues',
                    'description': 'List issues/tasks',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'project_id': {'type': 'string', 'description': 'Filter by project'},
                            'status': {'type': 'string', 'description': 'Filter by status'},
                            'priority': {'type': 'number', 'description': 'Filter by priority'}
                        }
                    }
                },
                {
                    'name': 'update_issue',
                    'description': 'Update an issue status or details',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'issue_id': {'type': 'string', 'description': 'Issue ID'},
                            'status': {'type': 'string', 'enum': ['backlog', 'todo', 'in_progress', 'in_review', 'done']},
                            'completion_percentage': {'type': 'number', 'minimum': 0, 'maximum': 100},
                            'token_cost': {'type': 'number', 'description': 'AI token cost'}
                        },
                        'required': ['issue_id']
                    }
                },
                {
                    'name': 'create_sprint',
                    'description': 'Create a new sprint',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string', 'description': 'Sprint name'},
                            'project_id': {'type': 'string', 'description': 'Project ID'},
                            'start_date': {'type': 'string', 'description': 'Start date (ISO format)'},
                            'end_date': {'type': 'string', 'description': 'End date (ISO format)'}
                        },
                        'required': ['name', 'project_id']
                    }
                },
                {
                    'name': 'add_to_sprint',
                    'description': 'Add issues to a sprint',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'sprint_id': {'type': 'string', 'description': 'Sprint ID'},
                            'issue_ids': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Issue IDs to add'}
                        },
                        'required': ['sprint_id', 'issue_ids']
                    }
                },
                {
                    'name': 'generate_ai_tasks',
                    'description': 'Generate AI-powered task breakdown for a feature',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'project_id': {'type': 'string', 'description': 'Project ID'},
                            'feature_description': {'type': 'string', 'description': 'Feature to break down'},
                            'complexity': {'type': 'string', 'enum': ['simple', 'medium', 'complex'], 'default': 'medium'}
                        },
                        'required': ['project_id', 'feature_description']
                    }
                }
            ]
        }
    
    async def call_tool(self, params: Dict) -> Dict[str, Any]:
        """Execute a Lineary tool"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        
        tool_handlers = {
            'create_project': self.create_project,
            'create_issue': self.create_issue,
            'list_projects': self.list_projects,
            'list_issues': self.list_issues,
            'update_issue': self.update_issue,
            'create_sprint': self.create_sprint,
            'add_to_sprint': self.add_to_sprint,
            'generate_ai_tasks': self.generate_ai_tasks,
        }
        
        handler = tool_handlers.get(tool_name)
        if handler:
            try:
                result = await handler(arguments)
                return {
                    'content': [{
                        'type': 'text',
                        'text': json.dumps(result, indent=2)
                    }]
                }
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {
                    'content': [{
                        'type': 'text',
                        'text': f"Error: {str(e)}"
                    }]
                }
        
        return {'error': f'Unknown tool: {tool_name}'}
    
    async def create_project(self, args: Dict) -> Dict:
        """Create a new project"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/projects",
                json={
                    'name': args['name'],
                    'description': args.get('description', ''),
                    'color': args.get('color', '#8B5CF6'),
                    'icon': 'folder'
                }
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    return {
                        'success': True,
                        'project': data,
                        'message': f"Project '{args['name']}' created successfully"
                    }
                return {'success': False, 'error': f"Failed to create project: {response.status}"}
    
    async def create_issue(self, args: Dict) -> Dict:
        """Create a new issue"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/issues",
                json={
                    'project_id': args['project_id'],
                    'title': args['title'],
                    'description': args.get('description', ''),
                    'priority': args.get('priority', 3),
                    'status': args.get('status', 'todo'),
                    'story_points': args.get('story_points'),
                    'estimated_hours': args.get('estimated_hours'),
                    'ai_prompt': args.get('ai_prompt')
                }
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    return {
                        'success': True,
                        'issue': data,
                        'message': f"Issue '{args['title']}' created"
                    }
                return {'success': False, 'error': f"Failed to create issue: {response.status}"}
    
    async def list_projects(self, args: Dict) -> Dict:
        """List all projects"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/projects") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'projects': data.get('projects', []),
                        'count': len(data.get('projects', []))
                    }
                return {'success': False, 'error': 'Failed to fetch projects'}
    
    async def list_issues(self, args: Dict) -> Dict:
        """List issues"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/issues") as response:
                if response.status == 200:
                    data = await response.json()
                    issues = data if isinstance(data, list) else data.get('issues', [])
                    
                    # Apply filters
                    if args.get('project_id'):
                        issues = [i for i in issues if i['project_id'] == args['project_id']]
                    if args.get('status'):
                        issues = [i for i in issues if i['status'] == args['status']]
                    if args.get('priority'):
                        issues = [i for i in issues if i['priority'] == args['priority']]
                    
                    return {
                        'success': True,
                        'issues': issues,
                        'count': len(issues)
                    }
                return {'success': False, 'error': 'Failed to fetch issues'}
    
    async def update_issue(self, args: Dict) -> Dict:
        """Update an issue"""
        async with aiohttp.ClientSession() as session:
            update_data = {}
            if 'status' in args:
                update_data['status'] = args['status']
            if 'completion_percentage' in args:
                update_data['completion_percentage'] = args['completion_percentage']
            if 'token_cost' in args:
                update_data['token_cost'] = args['token_cost']
            
            async with session.patch(
                f"{self.api_url}/issues/{args['issue_id']}",
                json=update_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'issue': data,
                        'message': 'Issue updated successfully'
                    }
                return {'success': False, 'error': 'Failed to update issue'}
    
    async def create_sprint(self, args: Dict) -> Dict:
        """Create a new sprint"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/sprints",
                json={
                    'name': args['name'],
                    'project_id': args['project_id'],
                    'start_date': args.get('start_date', datetime.now().isoformat()),
                    'end_date': args.get('end_date', (datetime.now() + timedelta(days=14)).isoformat())
                }
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    return {
                        'success': True,
                        'sprint': data,
                        'message': f"Sprint '{args['name']}' created"
                    }
                return {'success': False, 'error': 'Failed to create sprint'}
    
    async def add_to_sprint(self, args: Dict) -> Dict:
        """Add issues to sprint"""
        async with aiohttp.ClientSession() as session:
            for issue_id in args['issue_ids']:
                async with session.patch(
                    f"{self.api_url}/issues/{issue_id}",
                    json={'sprint_id': args['sprint_id']}
                ) as response:
                    if response.status != 200:
                        return {'success': False, 'error': f'Failed to add issue {issue_id}'}
            
            return {
                'success': True,
                'message': f"Added {len(args['issue_ids'])} issues to sprint"
            }
    
    async def generate_ai_tasks(self, args: Dict) -> Dict:
        """Generate AI-powered task breakdown"""
        complexity_map = {
            'simple': {'design': 2, 'backend': 3, 'frontend': 3, 'test': 1},
            'medium': {'design': 3, 'backend': 5, 'frontend': 5, 'test': 2},
            'complex': {'design': 5, 'backend': 8, 'frontend': 8, 'test': 3}
        }
        
        points = complexity_map.get(args.get('complexity', 'medium'), complexity_map['medium'])
        
        tasks = [
            {
                'title': f"Design: {args['feature_description']}",
                'description': f"Create design mockups, user flows, and specifications for {args['feature_description']}",
                'story_points': points['design'],
                'priority': 1
            },
            {
                'title': f"Backend: {args['feature_description']}",
                'description': f"Implement API endpoints, database schema, and business logic for {args['feature_description']}",
                'story_points': points['backend'],
                'priority': 2
            },
            {
                'title': f"Frontend: {args['feature_description']}",
                'description': f"Build UI components, integrate with API, and implement user interactions for {args['feature_description']}",
                'story_points': points['frontend'],
                'priority': 2
            },
            {
                'title': f"Testing: {args['feature_description']}",
                'description': f"Write unit tests, integration tests, and perform QA for {args['feature_description']}",
                'story_points': points['test'],
                'priority': 3
            },
            {
                'title': f"Documentation: {args['feature_description']}",
                'description': f"Write user documentation and update API docs for {args['feature_description']}",
                'story_points': 1,
                'priority': 4
            }
        ]
        
        # Create the tasks
        created_tasks = []
        async with aiohttp.ClientSession() as session:
            for task in tasks:
                async with session.post(
                    f"{self.api_url}/issues",
                    json={
                        'project_id': args['project_id'],
                        'title': task['title'],
                        'description': task['description'],
                        'story_points': task['story_points'],
                        'priority': task['priority'],
                        'status': 'backlog'
                    }
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        created_tasks.append(data)
        
        return {
            'success': True,
            'tasks_created': len(created_tasks),
            'tasks': created_tasks,
            'total_story_points': sum(t['story_points'] for t in tasks),
            'message': f"Generated {len(created_tasks)} tasks for '{args['feature_description']}'"
        }
    
    async def list_resources(self, params: Dict) -> Dict[str, Any]:
        """List available Lineary resources"""
        return {
            'resources': [
                {
                    'uri': 'lineary://projects',
                    'name': 'All Projects',
                    'description': 'List of all projects in Lineary',
                    'mimeType': 'application/json'
                },
                {
                    'uri': 'lineary://issues/active',
                    'name': 'Active Issues',
                    'description': 'Currently in-progress issues',
                    'mimeType': 'application/json'
                },
                {
                    'uri': 'lineary://issues/todo',
                    'name': 'Todo Issues',
                    'description': 'Issues ready to work on',
                    'mimeType': 'application/json'
                },
                {
                    'uri': 'lineary://sprints/current',
                    'name': 'Current Sprint',
                    'description': 'Active sprint information',
                    'mimeType': 'application/json'
                },
                {
                    'uri': 'lineary://analytics',
                    'name': 'Analytics',
                    'description': 'Project analytics and metrics',
                    'mimeType': 'application/json'
                },
                {
                    'uri': 'lineary://health',
                    'name': 'System Health',
                    'description': 'Lineary system health status',
                    'mimeType': 'application/json'
                }
            ]
        }
    
    async def read_resource(self, params: Dict) -> Dict[str, Any]:
        """Read a Lineary resource"""
        uri = params.get('uri')
        
        try:
            async with aiohttp.ClientSession() as session:
                if uri == 'lineary://projects':
                    async with session.get(f"{self.api_url}/projects") as response:
                        data = await response.json() if response.status == 200 else {'error': 'Failed'}
                        return {
                            'contents': [{
                                'uri': uri,
                                'mimeType': 'application/json',
                                'text': json.dumps(data, indent=2)
                            }]
                        }
                
                elif uri == 'lineary://issues/active':
                    async with session.get(f"{self.api_url}/issues") as response:
                        data = await response.json() if response.status == 200 else []
                        active = [i for i in data if i.get('status') == 'in_progress']
                        return {
                            'contents': [{
                                'uri': uri,
                                'mimeType': 'application/json',
                                'text': json.dumps({'issues': active, 'count': len(active)}, indent=2)
                            }]
                        }
                
                elif uri == 'lineary://issues/todo':
                    async with session.get(f"{self.api_url}/issues") as response:
                        data = await response.json() if response.status == 200 else []
                        todo = [i for i in data if i.get('status') == 'todo']
                        return {
                            'contents': [{
                                'uri': uri,
                                'mimeType': 'application/json',
                                'text': json.dumps({'issues': todo, 'count': len(todo)}, indent=2)
                            }]
                        }
                
                elif uri == 'lineary://health':
                    async with session.get(f"{self.api_url}/health") as response:
                        health = {
                            'api': 'healthy' if response.status == 200 else 'unhealthy',
                            'timestamp': datetime.now().isoformat()
                        }
                        return {
                            'contents': [{
                                'uri': uri,
                                'mimeType': 'application/json',
                                'text': json.dumps(health, indent=2)
                            }]
                        }
                
                return {'error': f'Unknown resource: {uri}'}
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return {
                'contents': [{
                    'uri': uri,
                    'mimeType': 'application/json',
                    'text': json.dumps({'error': str(e)}, indent=2)
                }]
            }

async def main():
    """Main MCP server loop"""
    server = LinearyMCPServer()
    logger.info("Lineary MCP Server started")
    
    # MCP communication over stdin/stdout
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    while True:
        try:
            # Read line from stdin
            line = await reader.readline()
            if not line:
                break
            
            # Parse JSON-RPC request
            request = json.loads(line.decode())
            logger.debug(f"Received request: {request}")
            
            # Handle request
            response = await server.handle_request(request)
            
            # Send response
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            error_response = {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32700,
                    'message': 'Parse error'
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Server error: {e}")
            error_response = {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Lineary MCP Server stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)