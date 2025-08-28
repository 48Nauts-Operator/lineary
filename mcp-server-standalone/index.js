#!/usr/bin/env node
// ABOUTME: MCP server for Lineary project management integration with Claude
// ABOUTME: Provides tools for managing projects, issues, sprints, and analytics via stdio protocol

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config({ path: path.join(__dirname, '.env') });

// Configuration with fallbacks
const config = {
  apiUrl: process.env.LINEARY_API_URL || 'http://localhost:3134/api',
  apiKey: process.env.LINEARY_API_KEY || null,
  defaultProjectId: process.env.LINEARY_DEFAULT_PROJECT_ID || null
};

// Load config.json if exists
try {
  const configPath = path.join(__dirname, 'config.json');
  if (fs.existsSync(configPath)) {
    const fileConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    Object.assign(config, fileConfig);
  }
} catch (error) {
  // Config file is optional
}

// Log startup info to stderr (visible in Claude logs)
console.error(`🚀 Lineary MCP Server v1.0.0
📡 API URL: ${config.apiUrl}
${config.defaultProjectId ? `📋 Default Project: ${config.defaultProjectId}` : ''}
`);

// Create axios instance with config
const api = axios.create({
  baseURL: config.apiUrl,
  headers: config.apiKey ? { 'Authorization': `Bearer ${config.apiKey}` } : {},
  timeout: 10000
});

// Error handler
const handleError = (error) => {
  if (error.response) {
    return `API Error: ${error.response.status} - ${error.response.data?.error || error.response.statusText}`;
  } else if (error.request) {
    return `Network Error: Could not connect to ${config.apiUrl}`;
  } else {
    return `Error: ${error.message}`;
  }
};

// Create server instance
const server = new Server(
  {
    name: 'lineary',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

// Tool definitions
const TOOLS = [
  // Project Management
  {
    name: 'list_projects',
    description: 'List all projects',
    inputSchema: {
      type: 'object',
      properties: {}
    },
    handler: async () => {
      try {
        const response = await api.get('/projects');
        return { projects: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },
  {
    name: 'create_project',
    description: 'Create a new project',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Project name' },
        description: { type: 'string', description: 'Project description' },
        color: { type: 'string', description: 'Project color (hex)', default: '#8B5CF6' }
      },
      required: ['name']
    },
    handler: async (args) => {
      try {
        const response = await api.post('/projects', args);
        return { project: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },
  {
    name: 'get_project',
    description: 'Get project details',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' }
      },
      required: ['project_id']
    },
    handler: async ({ project_id }) => {
      try {
        const response = await api.get(`/projects/${project_id}`);
        return { project: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },
  {
    name: 'update_project',
    description: 'Update project information',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' },
        name: { type: 'string', description: 'Project name' },
        description: { type: 'string', description: 'Project description' },
        color: { type: 'string', description: 'Project color (hex)' }
      },
      required: ['project_id']
    },
    handler: async ({ project_id, ...updates }) => {
      try {
        const response = await api.put(`/projects/${project_id}`, updates);
        return { project: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },
  {
    name: 'delete_project',
    description: 'Delete a project',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' }
      },
      required: ['project_id']
    },
    handler: async ({ project_id }) => {
      try {
        await api.delete(`/projects/${project_id}`);
        return { success: true, message: 'Project deleted successfully' };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },

  // Issue/Task Management
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
    },
    handler: async (args) => {
      try {
        const params = new URLSearchParams();
        if (args.project_id) params.append('project_id', args.project_id);
        if (args.status) params.append('status', args.status);
        if (args.priority) params.append('priority', args.priority);
        
        const response = await api.get(`/issues?${params.toString()}`);
        return { issues: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
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
        status: { 
          type: 'string', 
          enum: ['backlog', 'todo', 'in_progress', 'in_review', 'done'],
          default: 'todo' 
        },
        priority: { type: 'number', min: 1, max: 5, default: 3 },
        story_points: { type: 'number', description: 'Story points' },
        estimated_hours: { type: 'number', description: 'Estimated hours' }
      },
      required: ['project_id', 'title']
    },
    handler: async (args) => {
      try {
        // Use default project if not specified
        const projectId = args.project_id || config.defaultProjectId;
        if (!projectId) {
          return { error: 'Project ID required and no default project configured' };
        }
        
        const response = await api.post('/issues', { ...args, project_id: projectId });
        return { issue: response.data };
      } catch (error) {
        return { error: handleError(error) };
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
        completion_percentage: { type: 'number', min: 0, max: 100 }
      },
      required: ['issue_id']
    },
    handler: async ({ issue_id, ...updates }) => {
      try {
        const response = await api.put(`/issues/${issue_id}`, updates);
        return { issue: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
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
    },
    handler: async ({ issue_id }) => {
      try {
        await api.delete(`/issues/${issue_id}`);
        return { success: true, message: 'Issue deleted successfully' };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },

  // Sprint Management
  {
    name: 'list_sprints',
    description: 'List all sprints',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Filter by project' }
      }
    },
    handler: async (args) => {
      try {
        const url = args.project_id ? `/sprints?project_id=${args.project_id}` : '/sprints';
        const response = await api.get(url);
        return { sprints: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
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
    },
    handler: async (args) => {
      try {
        const response = await api.post('/sprints', args);
        return { sprint: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },

  // Analytics & Metrics
  {
    name: 'get_analytics',
    description: 'Get project analytics including AI time saved',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' }
      },
      required: ['project_id']
    },
    handler: async ({ project_id }) => {
      try {
        const response = await api.get(`/analytics/dashboard/${project_id}`);
        return { analytics: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },
  {
    name: 'get_activity_heatmap',
    description: 'Get GitHub-style activity heatmap data',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' }
      },
      required: ['project_id']
    },
    handler: async ({ project_id }) => {
      try {
        const response = await api.get(`/analytics/heatmap/${project_id}`);
        return { heatmap: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },

  // Documentation
  {
    name: 'list_docs',
    description: 'List project documentation',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' }
      }
    },
    handler: async (args) => {
      try {
        const url = args.project_id ? `/docs?project_id=${args.project_id}` : '/docs';
        const response = await api.get(url);
        return { documents: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },
  {
    name: 'create_doc',
    description: 'Create a documentation page',
    inputSchema: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Document title' },
        content: { type: 'string', description: 'Markdown content' },
        project_id: { type: 'string', description: 'Project ID' },
        category: { type: 'string', description: 'Document category' }
      },
      required: ['title', 'content']
    },
    handler: async (args) => {
      try {
        const response = await api.post('/docs', args);
        return { document: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },

  // Activity Tracking
  {
    name: 'record_activity',
    description: 'Record project activity',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' },
        activity_type: { type: 'string', description: 'Type of activity' },
        activity_count: { type: 'number', description: 'Activity count', default: 1 }
      },
      required: ['project_id', 'activity_type']
    },
    handler: async (args) => {
      try {
        const response = await api.post('/analytics/activity', args);
        return { success: true, activity: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },
  {
    name: 'record_token_usage',
    description: 'Record AI token usage',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'string', description: 'Project ID' },
        model_name: { type: 'string', description: 'AI model name' },
        prompt_tokens: { type: 'number', description: 'Prompt tokens used' },
        completion_tokens: { type: 'number', description: 'Completion tokens used' },
        total_tokens: { type: 'number', description: 'Total tokens used' },
        cost: { type: 'number', description: 'Cost in USD' }
      },
      required: ['project_id', 'model_name', 'total_tokens']
    },
    handler: async (args) => {
      try {
        const response = await api.post('/analytics/token-usage', args);
        return { success: true, usage: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  },

  // AI Features
  {
    name: 'generate_ai_tasks',
    description: 'AI-powered task breakdown for a feature',
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
    },
    handler: async (args) => {
      try {
        const response = await api.post('/ai/generate-tasks', args);
        return { tasks: response.data };
      } catch (error) {
        return { error: handleError(error) };
      }
    }
  }
];

// Register handlers
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: TOOLS.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema
    }))
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const tool = TOOLS.find(t => t.name === request.params.name);
  
  if (!tool) {
    return {
      content: [{
        type: 'text',
        text: `Unknown tool: ${request.params.name}`
      }]
    };
  }
  
  try {
    const result = await tool.handler(request.params.arguments || {});
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{
        type: 'text',
        text: `Error: ${error.message}`
      }]
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('📡 MCP Server connected via stdio');
}

main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});