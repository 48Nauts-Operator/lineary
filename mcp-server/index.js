#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';

const API_URL = process.env.LINEARY_API_URL || 'https://ai-linear.blockonauts.io/api';

class LinearyMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'lineary-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'create_project',
          description: 'Create a new project in Lineary',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Project name' },
              description: { type: 'string', description: 'Project description' },
              color: { type: 'string', description: 'Project color (hex)', default: '#8B5CF6' }
            },
            required: ['name']
          }
        },
        {
          name: 'create_issue',
          description: 'Create a new issue/task in a project',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: 'Project ID' },
              title: { type: 'string', description: 'Issue title' },
              description: { type: 'string', description: 'Issue description' },
              priority: { type: 'number', minimum: 1, maximum: 5, default: 3 },
              status: {
                type: 'string',
                enum: ['backlog', 'todo', 'in_progress', 'in_review', 'done'],
                default: 'todo'
              },
              story_points: { type: 'number', description: 'Story points' },
              estimated_hours: { type: 'number', description: 'Estimated hours' }
            },
            required: ['project_id', 'title']
          }
        },
        {
          name: 'list_projects',
          description: 'List all projects',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        },
        {
          name: 'list_issues',
          description: 'List issues/tasks with optional filters',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: 'Filter by project' },
              status: { type: 'string', description: 'Filter by status' },
              priority: { type: 'number', description: 'Filter by priority' }
            }
          }
        },
        {
          name: 'update_issue',
          description: 'Update an issue status or details',
          inputSchema: {
            type: 'object',
            properties: {
              issue_id: { type: 'string', description: 'Issue ID' },
              status: { 
                type: 'string', 
                enum: ['backlog', 'todo', 'in_progress', 'in_review', 'done'] 
              },
              completion_percentage: { type: 'number', minimum: 0, maximum: 100 }
            },
            required: ['issue_id']
          }
        },
        {
          name: 'delete_issue',
          description: 'Delete an issue',
          inputSchema: {
            type: 'object',
            properties: {
              issue_id: { type: 'string', description: 'Issue ID to delete' }
            },
            required: ['issue_id']
          }
        },
        {
          name: 'create_sprint',
          description: 'Create a new sprint',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Sprint name' },
              project_id: { type: 'string', description: 'Project ID' },
              start_date: { type: 'string', description: 'Start date (ISO format)' },
              end_date: { type: 'string', description: 'End date (ISO format)' }
            },
            required: ['name', 'project_id']
          }
        },
        {
          name: 'generate_ai_tasks',
          description: 'Generate AI-powered task breakdown for a feature',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: 'Project ID' },
              feature_description: { type: 'string', description: 'Feature to break down' },
              complexity: { 
                type: 'string', 
                enum: ['simple', 'medium', 'complex'], 
                default: 'medium' 
              }
            },
            required: ['project_id', 'feature_description']
          }
        }
      ]
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case 'create_project':
          return await this.createProject(args);
        case 'create_issue':
          return await this.createIssue(args);
        case 'list_projects':
          return await this.listProjects(args);
        case 'list_issues':
          return await this.listIssues(args);
        case 'update_issue':
          return await this.updateIssue(args);
        case 'delete_issue':
          return await this.deleteIssue(args);
        case 'create_sprint':
          return await this.createSprint(args);
        case 'generate_ai_tasks':
          return await this.generateAITasks(args);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });

    // List available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: 'lineary://projects',
          name: 'All Projects',
          description: 'List of all projects in Lineary',
          mimeType: 'application/json'
        },
        {
          uri: 'lineary://issues/active',
          name: 'Active Issues',
          description: 'Currently in-progress issues',
          mimeType: 'application/json'
        },
        {
          uri: 'lineary://issues/todo',
          name: 'Todo Issues',
          description: 'Issues ready to work on',
          mimeType: 'application/json'
        },
        {
          uri: 'lineary://health',
          name: 'System Health',
          description: 'Lineary system health status',
          mimeType: 'application/json'
        }
      ]
    }));

    // Read resources
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;
      return await this.readResource(uri);
    });
  }

  async createProject(args) {
    try {
      const response = await fetch(`${API_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: args.name,
          description: args.description || '',
          color: args.color || '#8B5CF6',
          icon: 'folder'
        })
      });

      const data = await response.json();
      
      return {
        content: [
          {
            type: 'text',
            text: response.ok 
              ? `✅ Project "${args.name}" created successfully!\nID: ${data.id}\nSlug: ${data.slug}`
              : `❌ Failed to create project: ${data.error || response.statusText}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          { type: 'text', text: `❌ Error creating project: ${error.message}` }
        ]
      };
    }
  }

  async createIssue(args) {
    try {
      const response = await fetch(`${API_URL}/issues`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: args.project_id,
          title: args.title,
          description: args.description || '',
          priority: args.priority || 3,
          status: args.status || 'todo',
          story_points: args.story_points,
          estimated_hours: args.estimated_hours
        })
      });

      const data = await response.json();
      
      return {
        content: [
          {
            type: 'text',
            text: response.ok 
              ? `✅ Issue "${args.title}" created!\nID: ${data.id}\nStatus: ${data.status}\nPriority: ${data.priority}`
              : `❌ Failed to create issue: ${data.error || response.statusText}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          { type: 'text', text: `❌ Error creating issue: ${error.message}` }
        ]
      };
    }
  }

  async listProjects() {
    try {
      const response = await fetch(`${API_URL}/projects`);
      const data = await response.json();
      const projects = data.projects || [];

      if (projects.length === 0) {
        return {
          content: [
            { type: 'text', text: '📋 No projects found. Create your first project to get started!' }
          ]
        };
      }

      const projectList = projects.map(p => 
        `• ${p.name} (ID: ${p.id.slice(0, 8)}...)\n  ${p.description || 'No description'}\n  Color: ${p.color}`
      ).join('\n\n');

      return {
        content: [
          {
            type: 'text',
            text: `📁 **Projects (${projects.length})**\n\n${projectList}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          { type: 'text', text: `❌ Error fetching projects: ${error.message}` }
        ]
      };
    }
  }

  async listIssues(args) {
    try {
      const response = await fetch(`${API_URL}/issues`);
      const data = await response.json();
      let issues = Array.isArray(data) ? data : (data.issues || []);

      // Apply filters
      if (args.project_id) {
        issues = issues.filter(i => i.project_id === args.project_id);
      }
      if (args.status) {
        issues = issues.filter(i => i.status === args.status);
      }
      if (args.priority) {
        issues = issues.filter(i => i.priority === args.priority);
      }

      if (issues.length === 0) {
        return {
          content: [
            { type: 'text', text: '📋 No issues found matching the criteria.' }
          ]
        };
      }

      const statusEmojis = {
        backlog: '📦',
        todo: '📝',
        in_progress: '🔄',
        in_review: '👀',
        done: '✅'
      };

      const issueList = issues.map(i => 
        `${statusEmojis[i.status] || '❓'} **${i.title}**\n  ID: ${i.id.slice(0, 8)}...\n  Status: ${i.status} | Priority: ${i.priority} | Points: ${i.story_points || '-'}`
      ).join('\n\n');

      return {
        content: [
          {
            type: 'text',
            text: `📋 **Issues (${issues.length})**\n\n${issueList}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          { type: 'text', text: `❌ Error fetching issues: ${error.message}` }
        ]
      };
    }
  }

  async updateIssue(args) {
    try {
      const updateData = {};
      if (args.status) updateData.status = args.status;
      if (args.completion_percentage !== undefined) {
        updateData.completion_percentage = args.completion_percentage;
      }

      const response = await fetch(`${API_URL}/issues/${args.issue_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      });

      const data = await response.json();
      
      return {
        content: [
          {
            type: 'text',
            text: response.ok 
              ? `✅ Issue updated successfully!\n${args.status ? `New status: ${args.status}` : ''}${args.completion_percentage !== undefined ? `\nCompletion: ${args.completion_percentage}%` : ''}`
              : `❌ Failed to update issue: ${data.error || response.statusText}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          { type: 'text', text: `❌ Error updating issue: ${error.message}` }
        ]
      };
    }
  }

  async deleteIssue(args) {
    try {
      const response = await fetch(`${API_URL}/issues/${args.issue_id}`, {
        method: 'DELETE'
      });

      return {
        content: [
          {
            type: 'text',
            text: response.ok 
              ? `✅ Issue deleted successfully!`
              : `❌ Failed to delete issue: ${response.statusText}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          { type: 'text', text: `❌ Error deleting issue: ${error.message}` }
        ]
      };
    }
  }

  async createSprint(args) {
    try {
      const startDate = args.start_date || new Date().toISOString();
      const endDate = args.end_date || new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString();

      const response = await fetch(`${API_URL}/sprints`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: args.name,
          project_id: args.project_id,
          start_date: startDate,
          end_date: endDate
        })
      });

      const data = await response.json();
      
      return {
        content: [
          {
            type: 'text',
            text: response.ok 
              ? `✅ Sprint "${args.name}" created!\nID: ${data.id}\nDuration: ${startDate.split('T')[0]} to ${endDate.split('T')[0]}`
              : `❌ Failed to create sprint: ${data.error || response.statusText}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          { type: 'text', text: `❌ Error creating sprint: ${error.message}` }
        ]
      };
    }
  }

  async generateAITasks(args) {
    const complexityMap = {
      simple: { design: 2, backend: 3, frontend: 3, test: 1 },
      medium: { design: 3, backend: 5, frontend: 5, test: 2 },
      complex: { design: 5, backend: 8, frontend: 8, test: 3 }
    };
    
    const points = complexityMap[args.complexity || 'medium'];
    
    const tasks = [
      {
        title: `Design: ${args.feature_description}`,
        description: `Create design mockups and specifications`,
        story_points: points.design,
        priority: 1
      },
      {
        title: `Backend: ${args.feature_description}`,
        description: `Implement API endpoints and business logic`,
        story_points: points.backend,
        priority: 2
      },
      {
        title: `Frontend: ${args.feature_description}`,
        description: `Build UI components and interactions`,
        story_points: points.frontend,
        priority: 2
      },
      {
        title: `Testing: ${args.feature_description}`,
        description: `Write tests and perform QA`,
        story_points: points.test,
        priority: 3
      }
    ];

    try {
      const createdTasks = [];
      
      for (const task of tasks) {
        const response = await fetch(`${API_URL}/issues`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_id: args.project_id,
            title: task.title,
            description: task.description,
            story_points: task.story_points,
            priority: task.priority,
            status: 'backlog'
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          createdTasks.push(data);
        }
      }

      const totalPoints = tasks.reduce((sum, t) => sum + t.story_points, 0);
      const taskList = createdTasks.map(t => `• ${t.title}`).join('\n');

      return {
        content: [
          {
            type: 'text',
            text: `✅ Generated ${createdTasks.length} tasks for "${args.feature_description}"\n\nTasks created:\n${taskList}\n\nTotal story points: ${totalPoints}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          { type: 'text', text: `❌ Error generating tasks: ${error.message}` }
        ]
      };
    }
  }

  async readResource(uri) {
    try {
      switch (uri) {
        case 'lineary://projects': {
          const response = await fetch(`${API_URL}/projects`);
          const data = await response.json();
          return {
            contents: [
              {
                uri,
                mimeType: 'application/json',
                text: JSON.stringify(data, null, 2)
              }
            ]
          };
        }

        case 'lineary://issues/active': {
          const response = await fetch(`${API_URL}/issues`);
          const data = await response.json();
          const issues = Array.isArray(data) ? data : (data.issues || []);
          const active = issues.filter(i => i.status === 'in_progress');
          return {
            contents: [
              {
                uri,
                mimeType: 'application/json',
                text: JSON.stringify({ issues: active, count: active.length }, null, 2)
              }
            ]
          };
        }

        case 'lineary://issues/todo': {
          const response = await fetch(`${API_URL}/issues`);
          const data = await response.json();
          const issues = Array.isArray(data) ? data : (data.issues || []);
          const todo = issues.filter(i => i.status === 'todo');
          return {
            contents: [
              {
                uri,
                mimeType: 'application/json',
                text: JSON.stringify({ issues: todo, count: todo.length }, null, 2)
              }
            ]
          };
        }

        case 'lineary://health': {
          const response = await fetch(`${API_URL}/health`);
          const health = {
            api: response.ok ? 'healthy' : 'unhealthy',
            timestamp: new Date().toISOString()
          };
          return {
            contents: [
              {
                uri,
                mimeType: 'application/json',
                text: JSON.stringify(health, null, 2)
              }
            ]
          };
        }

        default:
          throw new Error(`Unknown resource: ${uri}`);
      }
    } catch (error) {
      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify({ error: error.message }, null, 2)
          }
        ]
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Lineary MCP server running on stdio');
  }
}

// Start the server
const server = new LinearyMCPServer();
server.run().catch(console.error);