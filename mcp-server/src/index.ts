#!/usr/bin/env node
// ABOUTME: MCP server for Lineary project management system
// ABOUTME: Provides tools for issue, project, and sprint management via MCP

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { 
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import axios from "axios";

// Configuration
const API_BASE = process.env.AI_LINEAR_API_URL || "http://localhost:3134/api";
const API_TIMEOUT = 30000;

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_BASE,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Create MCP server instance
const server = new Server({
  name: "lineary",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {},
    resources: {},
    prompts: {}
  }
});

// ============ TOOL SCHEMAS ============

const ListProjectsSchema = z.object({});

const CreateProjectSchema = z.object({
  name: z.string().describe("Project name"),
  description: z.string().describe("Project description"),
  color: z.string().optional().describe("Project color (hex code)"),
  icon: z.string().optional().describe("Project icon")
});

const ListIssuesSchema = z.object({
  project_id: z.string().optional().describe("Filter by project ID"),
  sprint_id: z.string().optional().describe("Filter by sprint ID"),
  parent_id: z.string().optional().describe("Filter by parent issue ID")
});

const CreateIssueSchema = z.object({
  title: z.string().describe("Issue title"),
  description: z.string().describe("Issue description"),
  project_id: z.string().describe("Project ID"),
  priority: z.number().min(1).max(5).optional().describe("Priority (1-5)"),
  parent_issue_id: z.string().optional().describe("Parent issue ID for sub-tasks"),
  depends_on: z.array(z.string()).optional().describe("Array of issue IDs this depends on"),
  start_date: z.string().optional().describe("Start date (ISO format)"),
  end_date: z.string().optional().describe("End date (ISO format)"),
  ai_prompt: z.string().optional().describe("AI prompt for this issue")
});

const UpdateIssueSchema = z.object({
  issue_id: z.string().describe("Issue ID to update"),
  title: z.string().optional().describe("New title"),
  description: z.string().optional().describe("New description"),
  status: z.enum(['backlog', 'todo', 'in_progress', 'review', 'done', 'cancelled']).optional(),
  priority: z.number().min(1).max(5).optional(),
  completion_scope: z.number().min(0).max(100).optional().describe("Completion percentage")
});

const AddCommentSchema = z.object({
  issue_id: z.string().describe("Issue ID"),
  content: z.string().describe("Comment content"),
  comment_type: z.enum(['comment', 'request']).optional().describe("Type of comment"),
  auto_create_subtask: z.boolean().optional().describe("Auto-create subtask from request")
});

const CreateSprintSchema = z.object({
  name: z.string().describe("Sprint name"),
  project_id: z.string().describe("Project ID"),
  start_date: z.string().describe("Start date (ISO format)"),
  end_date: z.string().describe("End date (ISO format)"),
  issue_ids: z.array(z.string()).optional().describe("Initial issue IDs to add")
});

const AddTagSchema = z.object({
  issue_id: z.string().describe("Issue ID"),
  tag: z.string().describe("Tag name")
});

const CreateTestCaseSchema = z.object({
  issue_id: z.string().describe("Issue ID"),
  title: z.string().describe("Test case title"),
  given_steps: z.array(z.string()).describe("Given steps (Gherkin format)"),
  when_steps: z.array(z.string()).describe("When steps (Gherkin format)"),
  then_steps: z.array(z.string()).describe("Then steps (Gherkin format)"),
  priority: z.number().min(1).max(5).optional()
});

// ============ TOOL HANDLERS ============

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "list_projects",
        description: "List all projects",
        inputSchema: {
          type: "object",
          properties: {}
        }
      },
      {
        name: "create_project",
        description: "Create a new project",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "Project name" },
            description: { type: "string", description: "Project description" },
            color: { type: "string", description: "Project color (hex)" },
            icon: { type: "string", description: "Project icon" }
          },
          required: ["name", "description"]
        }
      },
      {
        name: "list_issues",
        description: "List issues with optional filters",
        inputSchema: {
          type: "object",
          properties: {
            project_id: { type: "string", description: "Filter by project ID" },
            sprint_id: { type: "string", description: "Filter by sprint ID" },
            parent_id: { type: "string", description: "Filter by parent issue ID" }
          }
        }
      },
      {
        name: "create_issue",
        description: "Create a new issue",
        inputSchema: {
          type: "object",
          properties: {
            title: { type: "string", description: "Issue title" },
            description: { type: "string", description: "Issue description" },
            project_id: { type: "string", description: "Project ID" },
            priority: { type: "number", description: "Priority (1-5)" },
            parent_issue_id: { type: "string", description: "Parent issue ID" },
            depends_on: { type: "array", items: { type: "string" }, description: "Dependency issue IDs" },
            start_date: { type: "string", description: "Start date (ISO)" },
            end_date: { type: "string", description: "End date (ISO)" },
            ai_prompt: { type: "string", description: "AI prompt for this issue" }
          },
          required: ["title", "description", "project_id"]
        }
      },
      {
        name: "update_issue",
        description: "Update an existing issue",
        inputSchema: {
          type: "object",
          properties: {
            issue_id: { type: "string", description: "Issue ID to update" },
            title: { type: "string", description: "New title" },
            description: { type: "string", description: "New description" },
            status: { 
              type: "string", 
              enum: ["backlog", "todo", "in_progress", "review", "done", "cancelled"],
              description: "Issue status" 
            },
            priority: { type: "number", description: "Priority (1-5)" },
            completion_scope: { type: "number", description: "Completion percentage (0-100)" }
          },
          required: ["issue_id"]
        }
      },
      {
        name: "add_comment",
        description: "Add a comment to an issue",
        inputSchema: {
          type: "object",
          properties: {
            issue_id: { type: "string", description: "Issue ID" },
            content: { type: "string", description: "Comment content" },
            comment_type: { 
              type: "string", 
              enum: ["comment", "request"],
              description: "Type of comment" 
            },
            auto_create_subtask: { 
              type: "boolean", 
              description: "Auto-create subtask from request" 
            }
          },
          required: ["issue_id", "content"]
        }
      },
      {
        name: "create_sprint",
        description: "Create a new sprint",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "Sprint name" },
            project_id: { type: "string", description: "Project ID" },
            start_date: { type: "string", description: "Start date (ISO format)" },
            end_date: { type: "string", description: "End date (ISO format)" },
            issue_ids: { 
              type: "array", 
              items: { type: "string" },
              description: "Initial issue IDs" 
            }
          },
          required: ["name", "project_id", "start_date", "end_date"]
        }
      },
      {
        name: "add_tag",
        description: "Add a tag to an issue",
        inputSchema: {
          type: "object",
          properties: {
            issue_id: { type: "string", description: "Issue ID" },
            tag: { type: "string", description: "Tag name" }
          },
          required: ["issue_id", "tag"]
        }
      },
      {
        name: "create_test_case",
        description: "Create a test case for an issue using Gherkin format",
        inputSchema: {
          type: "object",
          properties: {
            issue_id: { type: "string", description: "Issue ID" },
            title: { type: "string", description: "Test case title" },
            given_steps: { 
              type: "array", 
              items: { type: "string" },
              description: "Given steps" 
            },
            when_steps: { 
              type: "array", 
              items: { type: "string" },
              description: "When steps" 
            },
            then_steps: { 
              type: "array", 
              items: { type: "string" },
              description: "Then steps" 
            },
            priority: { type: "number", description: "Priority (1-5)" }
          },
          required: ["issue_id", "title", "given_steps", "when_steps", "then_steps"]
        }
      }
    ]
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "list_projects": {
        const response = await api.get('/projects');
        return {
          content: [{
            type: "text",
            text: JSON.stringify(response.data.projects, null, 2)
          }]
        };
      }

      case "create_project": {
        const params = CreateProjectSchema.parse(args);
        const response = await api.post('/projects', params);
        return {
          content: [{
            type: "text",
            text: `Project created successfully: ${JSON.stringify(response.data, null, 2)}`
          }]
        };
      }

      case "list_issues": {
        const params = ListIssuesSchema.parse(args);
        const queryParams = new URLSearchParams();
        if (params.project_id) queryParams.append('project_id', params.project_id);
        if (params.sprint_id) queryParams.append('sprint_id', params.sprint_id);
        if (params.parent_id) queryParams.append('parent_id', params.parent_id);
        
        const response = await api.get(`/issues?${queryParams.toString()}`);
        return {
          content: [{
            type: "text",
            text: JSON.stringify(response.data, null, 2)
          }]
        };
      }

      case "create_issue": {
        const params = CreateIssueSchema.parse(args);
        const response = await api.post('/issues', params);
        return {
          content: [{
            type: "text",
            text: `Issue created successfully: ${JSON.stringify(response.data, null, 2)}`
          }]
        };
      }

      case "update_issue": {
        const params = UpdateIssueSchema.parse(args);
        const { issue_id, ...updates } = params;
        const response = await api.patch(`/issues/${issue_id}`, updates);
        return {
          content: [{
            type: "text",
            text: `Issue updated successfully: ${JSON.stringify(response.data, null, 2)}`
          }]
        };
      }

      case "add_comment": {
        const params = AddCommentSchema.parse(args);
        const { issue_id, ...commentData } = params;
        const response = await api.post(`/issues/${issue_id}/comments`, commentData);
        return {
          content: [{
            type: "text",
            text: `Comment added successfully: ${JSON.stringify(response.data, null, 2)}`
          }]
        };
      }

      case "create_sprint": {
        const params = CreateSprintSchema.parse(args);
        const response = await api.post('/sprints', params);
        return {
          content: [{
            type: "text",
            text: `Sprint created successfully: ${JSON.stringify(response.data, null, 2)}`
          }]
        };
      }

      case "add_tag": {
        const params = AddTagSchema.parse(args);
        const { issue_id, tag } = params;
        const response = await api.post(`/issues/${issue_id}/tags`, { tag });
        return {
          content: [{
            type: "text",
            text: `Tag added successfully to issue ${issue_id}`
          }]
        };
      }

      case "create_test_case": {
        const params = CreateTestCaseSchema.parse(args);
        const { issue_id, ...testCaseData } = params;
        const response = await api.post(`/issues/${issue_id}/test-cases`, testCaseData);
        return {
          content: [{
            type: "text",
            text: `Test case created successfully: ${JSON.stringify(response.data, null, 2)}`
          }]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [{
        type: "text",
        text: `Error: ${error.message}\n${error.response?.data ? JSON.stringify(error.response.data, null, 2) : ''}`
      }],
      isError: true
    };
  }
});

// ============ RESOURCES ============

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "lineary://projects",
        name: "All Projects",
        description: "List of all projects in Lineary",
        mimeType: "application/json"
      },
      {
        uri: "lineary://issues",
        name: "All Issues",
        description: "List of all issues across projects",
        mimeType: "application/json"
      },
      {
        uri: "lineary://sprints",
        name: "Active Sprints",
        description: "List of active sprints",
        mimeType: "application/json"
      }
    ]
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  try {
    switch (uri) {
      case "lineary://projects": {
        const response = await api.get('/projects');
        return {
          contents: [{
            uri,
            mimeType: "application/json",
            text: JSON.stringify(response.data.projects, null, 2)
          }]
        };
      }

      case "lineary://issues": {
        const response = await api.get('/issues');
        return {
          contents: [{
            uri,
            mimeType: "application/json",
            text: JSON.stringify(response.data, null, 2)
          }]
        };
      }

      case "lineary://sprints": {
        const response = await api.get('/sprints?status=active');
        return {
          contents: [{
            uri,
            mimeType: "application/json",
            text: JSON.stringify(response.data, null, 2)
          }]
        };
      }

      default:
        throw new Error(`Unknown resource: ${uri}`);
    }
  } catch (error: any) {
    throw new Error(`Failed to read resource: ${error.message}`);
  }
});

// ============ PROMPTS ============

server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: "sprint_planning",
        description: "Generate sprint planning based on backlog",
        arguments: [
          {
            name: "project_id",
            description: "Project ID for sprint planning",
            required: true
          },
          {
            name: "sprint_duration",
            description: "Sprint duration in days",
            required: false
          }
        ]
      },
      {
        name: "issue_breakdown",
        description: "Break down a large issue into sub-tasks",
        arguments: [
          {
            name: "issue_title",
            description: "Title of the issue to break down",
            required: true
          },
          {
            name: "issue_description",
            description: "Description of the issue",
            required: true
          }
        ]
      },
      {
        name: "test_generation",
        description: "Generate test cases for an issue",
        arguments: [
          {
            name: "issue_title",
            description: "Issue title",
            required: true
          },
          {
            name: "issue_description",
            description: "Issue description",
            required: true
          },
          {
            name: "acceptance_criteria",
            description: "Acceptance criteria",
            required: false
          }
        ]
      }
    ]
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "sprint_planning":
      return {
        messages: [{
          role: "user",
          content: {
            type: "text",
            text: `Generate a sprint plan for project ${args?.project_id || '[PROJECT_ID]'} with ${args?.sprint_duration || '14'} day duration.
            
Analyze the backlog and suggest:
1. Which issues to include in the sprint
2. Estimated story points
3. Dependencies to consider
4. Risk factors
5. Sprint goals and objectives`
          }
        }]
      };

    case "issue_breakdown":
      return {
        messages: [{
          role: "user",
          content: {
            type: "text",
            text: `Break down this issue into smaller, manageable sub-tasks:

Title: ${args?.issue_title || '[ISSUE_TITLE]'}
Description: ${args?.issue_description || '[ISSUE_DESCRIPTION]'}

Please provide:
1. List of sub-tasks with clear titles and descriptions
2. Dependencies between sub-tasks
3. Estimated effort for each sub-task
4. Suggested priority order
5. Acceptance criteria for each sub-task`
          }
        }]
      };

    case "test_generation":
      return {
        messages: [{
          role: "user",
          content: {
            type: "text",
            text: `Generate comprehensive test cases for this issue:

Title: ${args?.issue_title || '[ISSUE_TITLE]'}
Description: ${args?.issue_description || '[ISSUE_DESCRIPTION]'}
Acceptance Criteria: ${args?.acceptance_criteria || 'Not specified'}

Generate test cases in Gherkin format (Given/When/Then) covering:
1. Happy path scenarios
2. Edge cases
3. Error handling
4. Performance considerations
5. Security aspects (if applicable)`
          }
        }]
      };

    default:
      throw new Error(`Unknown prompt: ${name}`);
  }
});

// ============ MAIN EXECUTION ============

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error("Lineary MCP Server running on stdio");
  console.error(`API Base URL: ${API_BASE}`);
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});