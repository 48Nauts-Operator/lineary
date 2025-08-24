// ABOUTME: GraphQL schema definitions for Lineary
// ABOUTME: Defines types, queries, and mutations for the API

import { gql } from 'apollo-server-express';

export const typeDefs = gql`
  scalar DateTime
  scalar JSON

  type Project {
    id: ID!
    name: String!
    description: String
    slug: String!
    color: String!
    icon: String!
    is_active: Boolean!
    created_at: DateTime!
    updated_at: DateTime!
    issues: [Issue!]!
    sprints: [Sprint!]!
  }

  type Issue {
    id: ID!
    project_id: ID!
    title: String!
    description: String
    status: IssueStatus!
    priority: Int!
    story_points: Int
    estimated_hours: Float
    actual_hours: Float
    assignee: String
    labels: [String!]!
    branch_name: String
    worktree_path: String
    ai_complexity_score: JSON
    ai_estimation: JSON
    ai_review: JSON
    ai_tests_generated: Boolean!
    ai_docs_generated: Boolean!
    created_at: DateTime!
    updated_at: DateTime!
    completed_at: DateTime
    project: Project!
  }

  type Sprint {
    id: ID!
    project_id: ID!
    name: String!
    goal: String
    duration_hours: Int!
    start_date: DateTime
    end_date: DateTime
    status: SprintStatus!
    velocity: Int
    created_at: DateTime!
    updated_at: DateTime!
    project: Project!
    issues: [Issue!]!
  }

  type TaskEstimation {
    story_points: Int!
    estimated_hours: Float!
    confidence: Int!
    complexity_score: JSON!
    reasoning: [String!]!
    suggested_subtasks: [String!]!
    risks: [String!]!
  }

  type CapacityAnalysis {
    recommended: [ID!]!
    total_points: Int!
    total_hours: Float!
    confidence: Int!
  }

  type QualityReport {
    overall_score: Int!
    lint: JSON
    format: JSON
    types: JSON
    security: JSON
    tests: JSON
    coverage: JSON
    complexity: JSON
  }

  type ActivityLog {
    id: ID!
    entity_type: String!
    entity_id: ID!
    action: String!
    user_id: String
    metadata: JSON
    created_at: DateTime!
  }

  enum IssueStatus {
    backlog
    todo
    in_progress
    in_review
    done
    cancelled
  }

  enum SprintStatus {
    planned
    active
    completed
    cancelled
  }

  input CreateProjectInput {
    name: String!
    description: String
    color: String
    icon: String
  }

  input UpdateProjectInput {
    name: String
    description: String
    color: String
    icon: String
    is_active: Boolean
  }

  input CreateIssueInput {
    project_id: ID!
    title: String!
    description: String
    assignee: String
    labels: [String!]
    priority: Int
  }

  input UpdateIssueInput {
    title: String
    description: String
    status: IssueStatus
    priority: Int
    story_points: Int
    estimated_hours: Float
    actual_hours: Float
    assignee: String
    labels: [String!]
  }

  input CreateSprintInput {
    project_id: ID!
    name: String!
    goal: String
    duration_hours: Int!
  }

  type Query {
    # Projects
    projects: [Project!]!
    project(id: ID!): Project
    
    # Issues
    issues(project_id: ID): [Issue!]!
    issue(id: ID!): Issue
    
    # Sprints
    sprints(project_id: ID): [Sprint!]!
    sprint(id: ID!): Sprint
    
    # Activity
    activityLog(entity_type: String, entity_id: ID, limit: Int): [ActivityLog!]!
    
    # Analytics
    projectStats(project_id: ID!): JSON
    sprintStats(sprint_id: ID!): JSON
  }

  type Mutation {
    # Projects
    createProject(input: CreateProjectInput!): Project!
    updateProject(id: ID!, input: UpdateProjectInput!): Project!
    deleteProject(id: ID!): Boolean!
    
    # Issues
    createIssue(input: CreateIssueInput!): Issue!
    updateIssue(id: ID!, input: UpdateIssueInput!): Issue!
    deleteIssue(id: ID!): Boolean!
    estimateIssue(id: ID!): TaskEstimation!
    
    # Sprints
    createSprint(input: CreateSprintInput!): Sprint!
    addIssuesToSprint(sprint_id: ID!, issue_ids: [ID!]!): CapacityAnalysis!
    startSprint(id: ID!): Sprint!
    completeSprint(id: ID!): Sprint!
    
    # AI Features
    reviewCode(issue_id: ID!): JSON!
    generateTests(issue_id: ID!, file_path: String!): JSON!
    runQualityCheck(issue_id: ID!): QualityReport!
    
    # Capacity Planning
    analyzeCapacity(available_hours: Float!, issue_ids: [ID!]!): CapacityAnalysis!
  }

  type Subscription {
    issueCreated: Issue!
    issueUpdated: Issue!
    sprintCreated: Sprint!
    sprintUpdated: Sprint!
    qualityCheckCompleted: JSON!
    codeReviewCompleted: JSON!
  }
`;