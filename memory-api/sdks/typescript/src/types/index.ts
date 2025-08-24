/**
 * BETTY Memory System TypeScript SDK - Type Definitions
 * 
 * Complete type definitions for all BETTY API requests, responses, and data models.
 * Provides full type safety and IDE support for the BETTY Memory System v2.0 API.
 */

// Base types
export interface BaseResponse<T = any> {
  success: boolean;
  message?: string;
  api_version?: string;
  execution_time_ms?: number;
  timestamp?: string;
  request_id?: string;
  data?: T;
}

export interface ErrorDetails {
  error_code?: string;
  field_errors?: Record<string, string[]>;
  missing_permissions?: string[];
  suggestion?: string;
  documentation_url?: string;
}

export interface ErrorResponse extends BaseResponse {
  success: false;
  error: string;
  details?: ErrorDetails;
}

// Search types
export type SearchType = 'semantic' | 'keyword' | 'hybrid';

export type FilterOperator = 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'contains';

export interface Filter {
  field: string;
  operator: FilterOperator;
  value: string | number | boolean | Array<string | number | boolean>;
}

export interface TimeRange {
  start?: string;
  end?: string;
}

// Knowledge types
export interface KnowledgeMetadata {
  tags?: string[];
  quality_score?: number;
  source?: string;
  language?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  knowledge_type: string;
  project_id?: string;
  metadata?: KnowledgeMetadata;
}

export interface SearchResult extends KnowledgeItem {
  similarity_score: number;
  ranking_score: number;
  highlights?: string[];
  search_perspective?: string;
  project_context?: {
    project_id: string;
    project_name: string;
    connection_type: string;
  };
}

// Advanced Search types
export interface AdvancedSearchRequest {
  query: string;
  searchType?: SearchType;
  similarityThreshold?: number;
  maxResults?: number;
  filters?: Filter[];
  timeRange?: TimeRange;
  rankingAlgorithm?: string;
  includeMetadata?: boolean;
  groupBy?: string;
  projectIds?: string[];
}

export interface QueryAnalysis {
  search_type_used: string;
  semantic_expansion?: string[];
  filters_applied: number;
  execution_time_ms: number;
}

export interface SearchFacets {
  knowledge_type?: Record<string, number>;
  tags?: Record<string, number>;
  projects?: Record<string, number>;
}

export interface AdvancedSearchData {
  results: SearchResult[];
  total_results: number;
  query_analysis: QueryAnalysis;
  facets?: SearchFacets;
}

export interface AdvancedSearchResponse extends BaseResponse<AdvancedSearchData> {}

// Pattern matching types
export type PatternType = 'path' | 'subgraph' | 'temporal' | 'anomaly' | 'community' | 'centrality';

export interface NodeConstraint {
  knowledge_type?: string;
  tags?: string[];
  metadata_filters?: Record<string, any>;
}

export interface PatternDefinition {
  pathStructure?: string;
  relationshipTypes?: string[];
  nodeConstraints?: Record<string, NodeConstraint>;
  temporalWindow?: string;
  algorithmParams?: Record<string, any>;
}

export interface PatternMatchRequest {
  patternType: PatternType;
  patternDefinition?: PatternDefinition;
  maxDepth?: number;
  minConfidence?: number;
  maxResults?: number;
  projectIds?: string[];
}

export interface PatternNode {
  id: string;
  title: string;
  type: string;
  role: string;
}

export interface PatternRelationship {
  from: string;
  to: string;
  type: string;
  strength: number;
}

export interface Pattern {
  pattern_id: string;
  pattern_type: string;
  confidence_score: number;
  support_count: number;
  nodes: PatternNode[];
  relationships: PatternRelationship[];
  pattern_description: string;
  examples: string[];
}

export interface PatternAnalysis {
  strongest_pattern?: string;
  most_frequent_relationship?: string;
  pattern_distribution: Record<string, number>;
}

export interface PatternMatchData {
  patterns: Pattern[];
  total_patterns: number;
  analysis: PatternAnalysis;
}

export interface PatternMatchResponse extends BaseResponse<PatternMatchData> {}

// Semantic clustering types
export type ClusteringAlgorithm = 'hierarchical' | 'kmeans' | 'dbscan' | 'spectral' | 'gaussian_mixture';

export interface SemanticClusteringRequest {
  algorithm?: ClusteringAlgorithm;
  numClusters?: number;
  autoClusters?: boolean;
  minClusterSize?: number;
  maxClusterSize?: number;
  similarityThreshold?: number;
  projectIds?: string[];
  knowledgeTypes?: string[];
  useContent?: boolean;
  useMetadata?: boolean;
  useRelationships?: boolean;
  includeVisualization?: boolean;
  includeTopics?: boolean;
  maxItemsPerCluster?: number;
}

export interface ClusterTopic {
  term: string;
  weight: number;
}

export interface RepresentativeItem {
  id: string;
  title: string;
  similarity_to_centroid: number;
}

export interface ClusterCharacteristics {
  avg_quality_score: number;
  primary_knowledge_types: string[];
  time_range?: TimeRange;
}

export interface Cluster {
  cluster_id: number;
  label: string;
  size: number;
  centroid_score: number;
  coherence_score: number;
  items: string[];
  representative_items: RepresentativeItem[];
  topics: ClusterTopic[];
  characteristics: ClusterCharacteristics;
}

export interface QualityMetrics {
  silhouette_score: number;
  davies_bouldin_score: number;
  calinski_harabasz_score: number;
}

export interface VisualizationData {
  type: string;
  data_url: string;
}

export interface SemanticClusteringData {
  clusters: Cluster[];
  clusters_count: number;
  algorithm_used: string;
  quality_metrics: QualityMetrics;
  visualization?: VisualizationData;
}

export interface SemanticClusteringResponse extends BaseResponse<SemanticClusteringData> {}

// Batch operation types
export type OperationStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface ValidationRules {
  minContentLength?: number;
  maxContentLength?: number;
  requiredFields?: string[];
  contentFilters?: string[];
}

export interface ProcessingOptions {
  generateEmbeddings?: boolean;
  autoCategorize?: boolean;
  extractEntities?: boolean;
  detectLanguage?: boolean;
  qualityScoring?: boolean;
}

export interface SourceConfig {
  filePath?: string;
  url?: string;
  connectionString?: string;
  apiEndpoint?: string;
  encoding?: string;
  headers?: Record<string, string>;
}

export interface BatchImportRequest {
  sourceType: string;
  format: string;
  sourceConfig: SourceConfig;
  targetProjectId: string;
  duplicateHandling?: string;
  validationRules?: ValidationRules;
  processingOptions?: ProcessingOptions;
  batchSize?: number;
  maxErrors?: number;
  notifyWebhook?: string;
}

export interface BatchOperationData {
  operation_id: string;
  status: OperationStatus;
  estimated_total_items?: number;
  estimated_duration_seconds?: number;
  created_at: string;
  progress_url: string;
  websocket_url?: string;
}

export interface BatchImportResponse extends BaseResponse<BatchOperationData> {}

export interface ProgressPhase {
  name: string;
  status: string;
  progress_percentage: number;
  duration_seconds?: number;
  estimated_duration_seconds?: number;
}

export interface ProgressStatistics {
  avg_processing_time_per_item: number;
  memory_usage_mb: number;
  cpu_usage_percentage: number;
}

export interface ProgressError {
  item_id?: string;
  error_message: string;
  error_code?: string;
  timestamp: string;
}

export interface ProgressData {
  operation_id: string;
  status: OperationStatus;
  progress_percentage: number;
  processed_items: number;
  successful_items: number;
  failed_items: number;
  total_items: number;
  current_phase: string;
  phase_progress: number;
  estimated_time_remaining?: number;
  throughput_items_per_second: number;
  started_at: string;
  updated_at: string;
  phases: ProgressPhase[];
  statistics: ProgressStatistics;
  recent_errors: ProgressError[];
}

export interface ProgressResponse extends BaseResponse<ProgressData> {}

// WebSocket types
export interface WebSocketMessage<T = any> {
  type: string;
  id?: string;
  timestamp: string;
  data: T;
}

export type WebSocketEventType = 
  | 'progress_update'
  | 'operation_completed'
  | 'operation_failed'
  | 'search_results'
  | 'collaboration_update'
  | 'system_notification'
  | 'error';

// Cross-project types
export interface ProjectConnection {
  connection_id: string;
  source_project_id: string;
  target_project_id: string;
  connection_type: string;
  status: string;
  permissions: Record<string, boolean>;
  created_at: string;
}

export interface ProjectBreakdown {
  results: number;
  max_score: number;
}

export interface CrossProjectSearchData extends AdvancedSearchData {
  project_breakdown: Record<string, ProjectBreakdown>;
  search_statistics: Record<string, any>;
}

export interface CrossProjectSearchResponse extends BaseResponse<CrossProjectSearchData> {}

export interface CrossProjectSearchRequest extends AdvancedSearchRequest {
  projectIds?: string[];
  maxResultsPerProject?: number;
  maxTotalResults?: number;
  mergeStrategy?: string;
  includeProjectContext?: boolean;
}

// Knowledge management types
export interface AddKnowledgeRequest {
  title: string;
  content: string;
  knowledgeType?: string;
  projectId?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface UpdateKnowledgeRequest {
  title?: string;
  content?: string;
  knowledgeType?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

// Webhook types
export interface WebhookRequest {
  name: string;
  url: string;
  events: string[];
  secret?: string;
  active?: boolean;
  retryConfig?: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
  };
  filters?: {
    projectIds?: string[];
    userIds?: string[];
    conditions?: Filter[];
  };
  headers?: Record<string, string>;
}

export interface WebhookData {
  webhook_id: string;
  name: string;
  url: string;
  events: string[];
  secret_configured: boolean;
  active: boolean;
  created_at: string;
  test_url: string;
}

export interface WebhookResponse extends BaseResponse<WebhookData> {}

export interface WebhookStatistics {
  webhook_id: string;
  statistics: {
    total_deliveries: number;
    successful_deliveries: number;
    failed_deliveries: number;
    success_rate: number;
    avg_response_time_ms: number;
    last_delivery?: string;
    last_successful_delivery?: string;
    last_failed_delivery?: string;
  };
  recent_deliveries: Array<{
    delivery_id: string;
    event_type: string;
    status: string;
    response_code: number;
    response_time_ms: number;
    delivered_at: string;
  }>;
  error_summary: {
    timeout_errors: number;
    network_errors: number;
    server_errors: number;
    most_common_error?: string;
  };
}

export interface WebhookStatsResponse extends BaseResponse<WebhookStatistics> {}

// Utility types
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export interface RequestConfig {
  method: HttpMethod;
  url: string;
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  timeout?: number;
}

export interface ResponseConfig<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  config: RequestConfig;
}

// Event emitter types for WebSocket
export interface WebSocketEventMap {
  open: [];
  close: [code: number, reason: string];
  error: [error: Error];
  message: [message: WebSocketMessage];
  [key: string]: any[];
}