// ABOUTME: TypeScript interfaces for Enhanced Task Management System with Git Integration
// ABOUTME: Defines types for tasks, sprints, estimation, and workflow management

// =============================================================================
// CORE TASK INTERFACES
// =============================================================================

export interface EnhancedTask {
  // Core identification
  id: string;
  project_id: string;
  user_id: string;
  session_id?: string;
  
  // Core task information
  title: string;
  description?: string;
  task_type: TaskType;
  priority: number; // 1-5 scale
  status: TaskStatus;
  
  // Git Integration
  git_branch?: string;
  pull_request_url?: string;
  git_status: GitStatus;
  base_branch: string;
  
  // AI Sprint Poker & Estimation
  complexity_score?: number; // 1-13 (Fibonacci)
  story_points?: number;
  confidence_level?: number; // 0.00-1.00
  similar_tasks_analyzed: string[]; // Array of task IDs
  
  // Enhanced Cost Prediction
  estimated_tokens_total?: number;
  estimated_tokens_breakdown: TokenBreakdown;
  estimated_cost?: number;
  actual_cost?: number;
  cost_variance?: number;
  
  // Workflow State Machine
  workflow_state: WorkflowState;
  acceptance_criteria: string[];
  definition_of_done: string[];
  validation_checklist: ValidationItem[];
  
  // Time Tracking & Estimates
  time_estimates: TimeEstimates;
  actual_time_tracked: ActualTimeTracking;
  
  // Dependencies & Relationships
  dependencies: string[]; // Task IDs this depends on
  dependents: string[]; // Task IDs that depend on this
  blockers: TaskBlocker[];
  
  // Sprint Planning Integration
  sprint_id?: string;
  sprint_day?: number; // 1-6
  velocity_impact?: number;
  
  // Legacy compatibility
  legacy_task_id?: string;
  extracted_from: ExtractedFrom;
  
  // Performance & Quality Metrics
  reusability_score: number; // 0.00-1.00
  technical_debt_impact: number; // -1.00 to 1.00
  test_coverage_target?: number; // 0.00-1.00
  
  // Temporal tracking
  created_at: string; // ISO timestamp
  updated_at: string; // ISO timestamp
  started_at?: string; // ISO timestamp
  completed_at?: string; // ISO timestamp
  due_date?: string; // ISO timestamp
  
  // Additional metadata
  metadata: Record<string, any>;
}

// =============================================================================
// ENUMERATION TYPES
// =============================================================================

export type TaskType = 
  | 'feature'
  | 'bug'
  | 'enhancement'
  | 'refactor'
  | 'test'
  | 'docs'
  | 'deployment'
  | 'research'
  | 'maintenance';

export type TaskStatus = 
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'blocked'
  | 'on_hold';

export type GitStatus = 
  | 'not_started'
  | 'branch_created'
  | 'commits_made'
  | 'pr_opened'
  | 'merged'
  | 'conflicts'
  | 'failed';

export type WorkflowState = 
  | 'planning'
  | 'estimation'
  | 'ready'
  | 'implementing'
  | 'code_review'
  | 'testing'
  | 'validation'
  | 'pr_review'
  | 'merging'
  | 'deployed'
  | 'closed'
  | 'blocked';

export type ExtractedFrom = 
  | 'manual'
  | 'conversation'
  | 'api'
  | 'migration'
  | 'automation';

// =============================================================================
// SUPPORTING INTERFACES
// =============================================================================

export interface TokenBreakdown {
  planning: number;
  implementation: number;
  testing: number;
  review: number;
}

export interface TimeEstimates {
  planning_hours: number;
  implementation_hours: number;
  testing_hours: number;
  review_hours: number;
  total_hours: number;
}

export interface ActualTimeTracking {
  planning_minutes: number;
  implementation_minutes: number;
  testing_minutes: number;
  review_minutes: number;
  total_minutes: number;
}

export interface ValidationItem {
  id: string;
  description: string;
  required: boolean;
  completed: boolean;
  validation_type: 'manual' | 'automated' | 'peer_review';
  validator?: string; // User or system that validates
  validated_at?: string; // ISO timestamp
  notes?: string;
}

export interface TaskBlocker {
  id: string;
  type: BlockerType;
  description: string;
  resolution_strategy: string;
  estimated_resolution_time: number; // minutes
  assigned_to?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  resolved_at?: string;
  resolution_notes?: string;
}

export type BlockerType = 
  | 'dependency'
  | 'technical'
  | 'resource'
  | 'external'
  | 'approval'
  | 'information';

// =============================================================================
// GIT INTEGRATION INTERFACES
// =============================================================================

export interface TaskCommit {
  id: string;
  task_id: string;
  commit_hash: string;
  commit_message: string;
  author: string;
  branch: string;
  files_changed: number;
  lines_added: number;
  lines_removed: number;
  commit_timestamp: string;
  ai_generated: boolean;
  created_at: string;
  metadata: Record<string, any>;
}

export interface GitBranchResult {
  branch_name: string;
  base_branch: string;
  created: boolean;
  remote_tracking: boolean;
  error?: string;
}

export interface PullRequestResult {
  url: string;
  title: string;
  description: string;
  labels: string[];
  reviewers: string[];
  automated_checks: AutomatedCheck[];
  error?: string;
}

export interface AutomatedCheck {
  name: string;
  status: 'pending' | 'success' | 'failure' | 'cancelled';
  description: string;
  details_url?: string;
}

export interface MergeValidationResult {
  ready_to_merge: boolean;
  validation_results: ValidationResult[];
  remaining_requirements: string[];
  conflicts_detected: boolean;
  checks_passing: boolean;
}

export interface ValidationResult {
  check_name: string;
  passed: boolean;
  message: string;
  severity: 'error' | 'warning' | 'info';
  auto_fixable: boolean;
}

// =============================================================================
// AI SPRINT POKER INTERFACES
// =============================================================================

export interface TaskEstimate {
  id: string;
  task_id: string;
  estimator_type: EstimatorType;
  model_version?: string;
  estimation_confidence: number;
  complexity_factors: ComplexityFactors;
  token_estimates: TokenEstimate;
  cost_estimates: CostEstimate;
  time_estimates: TimeEstimateDetailed;
  similar_tasks_used: string[];
  risk_factors: string[];
  optimization_opportunities: string[];
  actual_values?: ActualValues;
  accuracy_score?: number;
  created_at: string;
  validated_at?: string;
  metadata: Record<string, any>;
}

export type EstimatorType = 
  | 'ai_sprint_poker'
  | 'historical'
  | 'manual'
  | 'hybrid'
  | 'ml_model';

export interface ComplexityFactors {
  code_footprint_score: number; // 1-5
  integration_complexity: number; // 1-5
  testing_complexity: number; // 1-5
  uncertainty_factor: number; // 1-5
  technical_debt_impact: number; // 1-5
  domain_familiarity: number; // 1-5
}

export interface TokenEstimate {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  model_mix: Record<string, number>; // percentage per model
}

export interface CostEstimate {
  planning: number;
  implementation: number;
  review: number;
  testing: number;
  total: number;
}

export interface TimeEstimateDetailed {
  min_hours: number;
  max_hours: number;
  p90_hours: number; // 90th percentile estimate
  estimated_hours: number;
}

export interface ActualValues {
  actual_cost: number;
  actual_tokens: number;
  actual_hours: number;
  completion_date: string;
}

export interface ComplexityAnalysis {
  overall_complexity: number; // 1-13 Fibonacci
  complexity_factors: ComplexityFactors;
  similar_tasks: SimilarTask[];
  confidence_level: number;
  risk_assessment: RiskAssessment;
}

export interface SimilarTask {
  task_id: string;
  title: string;
  similarity_score: number; // 0.0-1.0
  comparison_factors: string[];
  actual_metrics?: ActualValues;
}

export interface RiskAssessment {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: RiskFactor[];
  mitigation_strategies: string[];
}

export interface RiskFactor {
  factor: string;
  probability: number; // 0.0-1.0
  impact: number; // 1-5
  mitigation: string;
}

// =============================================================================
// SPRINT PLANNING INTERFACES
// =============================================================================

export interface SprintPlanning {
  id: string;
  sprint_id: string;
  project_id: string;
  sprint_name: string;
  sprint_type: SprintType;
  sprint_goal: string;
  start_date: string; // ISO date
  end_date: string; // ISO date
  current_day: number; // 1-6
  day_structure: SprintDayStructure;
  cost_budget: number;
  token_budget: number;
  capacity_hours: number;
  agent_allocation: Record<string, any>;
  success_metrics: SuccessMetric[];
  status: SprintStatus;
  actual_cost?: number;
  actual_tokens?: number;
  actual_hours?: number;
  completion_rate?: number;
  velocity_achieved?: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  metadata: Record<string, any>;
}

export type SprintType = 
  | 'discovery'
  | 'development'
  | 'integration'
  | 'validation'
  | 'deployment'
  | 'retrospective';

export type SprintStatus = 
  | 'planning'
  | 'active'
  | 'completed'
  | 'cancelled'
  | 'on_hold';

export interface SprintDayStructure {
  day_1: SprintDay;
  day_2: SprintDay;
  day_3: SprintDay;
  day_4: SprintDay;
  day_5: SprintDay;
  day_6: SprintDay;
}

export interface SprintDay {
  focus: string;
  allocation: TimeAllocation;
  milestones?: Milestone[];
  planned_tasks?: string[]; // Task IDs
}

export interface TimeAllocation {
  planning?: number; // percentage
  development?: number; // percentage
  testing?: number; // percentage
  review?: number; // percentage
}

export interface Milestone {
  id: string;
  title: string;
  description: string;
  target_day: number;
  completed: boolean;
  completed_at?: string;
}

export interface SuccessMetric {
  metric_name: string;
  target_value: number;
  actual_value?: number;
  unit: string;
  achieved: boolean;
}

export interface SprintTaskAssignment {
  id: string;
  sprint_id: string;
  task_id: string;
  project_id: string;
  planned_day: number;
  planned_order: number;
  estimated_completion_time: string; // Interval
  actual_completion_time?: string; // Interval
  velocity_contribution: number;
  cost_contribution: number;
  assignment_status: AssignmentStatus;
  created_at: string;
  moved_to_sprint_id?: string;
  metadata: Record<string, any>;
}

export type AssignmentStatus = 
  | 'planned'
  | 'active'
  | 'completed'
  | 'moved'
  | 'cancelled';

// =============================================================================
// WORKFLOW AND TRANSITIONS
// =============================================================================

export interface WorkflowTransition {
  id: string;
  task_id: string;
  from_state?: string;
  to_state: string;
  transition_trigger: TransitionTrigger;
  trigger_agent?: string;
  validation_passed: boolean;
  validation_results: ValidationResult[];
  transition_reason?: string;
  automated: boolean;
  session_id?: string;
  git_event_data: Record<string, any>;
  timestamp: string;
  metadata: Record<string, any>;
}

export type TransitionTrigger = 
  | 'automatic'
  | 'manual'
  | 'ai_agent'
  | 'time_based'
  | 'dependency'
  | 'git_event'
  | 'external_api';

export interface WorkflowRule {
  rule_id: string;
  name: string;
  from_states: WorkflowState[];
  to_state: WorkflowState;
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
  enabled: boolean;
}

export interface WorkflowCondition {
  type: 'git_status' | 'time_elapsed' | 'dependency_resolved' | 'approval_received';
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains';
  value: any;
  required: boolean;
}

export interface WorkflowAction {
  type: 'notify' | 'assign' | 'create_branch' | 'run_tests' | 'update_field';
  parameters: Record<string, any>;
  order: number;
}

// =============================================================================
// TASK DEPENDENCIES
// =============================================================================

export interface TaskDependency {
  id: string;
  source_task_id: string;
  target_task_id: string;
  dependency_type: DependencyType;
  dependency_strength: number; // 0.0-1.0
  is_hard_dependency: boolean;
  resolved: boolean;
  resolution_notes?: string;
  created_at: string;
  resolved_at?: string;
  metadata: Record<string, any>;
}

export type DependencyType = 
  | 'blocks'
  | 'requires'
  | 'relates_to'
  | 'conflicts_with'
  | 'enables'
  | 'builds_on';

// =============================================================================
// COST PREDICTION
// =============================================================================

export interface CostPrediction {
  id: string;
  task_id: string;
  prediction_model: string;
  model_confidence: number;
  predicted_cost: number;
  predicted_tokens: number;
  predicted_hours: number;
  cost_breakdown: CostEstimate;
  actual_cost?: number;
  actual_tokens?: number;
  actual_hours?: number;
  cost_variance_percentage?: number;
  token_variance_percentage?: number;
  time_variance_percentage?: number;
  prediction_accuracy?: number;
  historical_basis: string[]; // Similar task IDs
  environmental_factors: Record<string, any>;
  created_at: string;
  validated_at?: string;
  metadata: Record<string, any>;
}

// =============================================================================
// API REQUEST/RESPONSE INTERFACES
// =============================================================================

export interface CreateTaskRequest {
  title: string;
  description?: string;
  task_type: TaskType;
  priority: number;
  project_id: string;
  session_id?: string;
  acceptance_criteria?: string[];
  definition_of_done?: string[];
  dependencies?: string[];
  due_date?: string;
  metadata?: Record<string, any>;
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: number;
  git_branch?: string;
  pull_request_url?: string;
  git_status?: GitStatus;
  workflow_state?: WorkflowState;
  acceptance_criteria?: string[];
  definition_of_done?: string[];
  actual_cost?: number;
  completion_notes?: string;
  metadata?: Record<string, any>;
}

export interface TaskListResponse {
  tasks: EnhancedTask[];
  total: number;
  pagination: {
    page: number;
    limit: number;
    total_pages: number;
  };
  filters_applied: Record<string, any>;
}

export interface TaskEstimationRequest {
  task_id: string;
  force_reestimate?: boolean;
  include_similar_analysis?: boolean;
  estimation_method?: EstimatorType;
  complexity_override?: Partial<ComplexityFactors>;
}

export interface TaskEstimationResponse {
  task_id: string;
  complexity_analysis: ComplexityAnalysis;
  story_point_estimate: number;
  cost_prediction: CostPrediction;
  similar_tasks: SimilarTask[];
  confidence_metrics: {
    overall_confidence: number;
    estimation_reliability: number;
    model_accuracy: number;
  };
  recommendations: string[];
}

// =============================================================================
// DASHBOARD AND REPORTING INTERFACES
// =============================================================================

export interface TaskDashboardData {
  summary: {
    total_tasks: number;
    by_status: Record<TaskStatus, number>;
    by_workflow_state: Record<WorkflowState, number>;
    by_priority: Record<number, number>;
  };
  recent_activity: WorkflowTransition[];
  upcoming_deadlines: EnhancedTask[];
  blocked_tasks: EnhancedTask[];
  sprint_progress: SprintProgressSummary[];
  cost_analysis: CostAnalysisSummary;
  git_integration_status: GitIntegrationSummary;
}

export interface SprintProgressSummary {
  sprint_id: string;
  sprint_name: string;
  current_day: number;
  completion_percentage: number;
  story_points_completed: number;
  story_points_total: number;
  cost_used: number;
  cost_budget: number;
  on_track: boolean;
}

export interface CostAnalysisSummary {
  total_estimated: number;
  total_actual: number;
  variance_percentage: number;
  cost_efficiency_score: number;
  prediction_accuracy: number;
  optimization_opportunities: string[];
}

export interface GitIntegrationSummary {
  active_branches: number;
  pending_prs: number;
  merge_conflicts: number;
  integration_health_score: number;
  recent_merges: TaskCommit[];
}

// =============================================================================
// UTILITY TYPES
// =============================================================================

export type TaskFilter = {
  status?: TaskStatus[];
  workflow_state?: WorkflowState[];
  priority?: number[];
  task_type?: TaskType[];
  git_status?: GitStatus[];
  sprint_id?: string;
  assigned_to?: string;
  created_after?: string;
  created_before?: string;
  due_after?: string;
  due_before?: string;
  has_blockers?: boolean;
  search?: string;
};

export type TaskSortField = 
  | 'created_at'
  | 'updated_at'
  | 'priority'
  | 'story_points'
  | 'estimated_cost'
  | 'due_date'
  | 'title';

export type SortDirection = 'asc' | 'desc';

export interface TaskQueryOptions {
  filters?: TaskFilter;
  sort_by?: TaskSortField;
  sort_direction?: SortDirection;
  page?: number;
  limit?: number;
  include_related?: boolean;
}