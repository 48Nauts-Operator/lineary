/**
 * BETTY Memory System TypeScript SDK - Main Client
 * 
 * This module provides the main BettyClient class for interacting with
 * the BETTY Memory System v2.0 API with full TypeScript support.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { EventEmitter } from 'eventemitter3';

import { BettyConfig, BettyClientOptions } from '../config/BettyConfig';
import { 
  BettyAPIError, 
  AuthenticationError, 
  PermissionError,
  RateLimitError,
  ValidationError 
} from '../errors/BettyErrors';

import {
  AdvancedSearchRequest,
  AdvancedSearchResponse,
  PatternMatchRequest,
  PatternMatchResponse,
  SemanticClusteringRequest,
  SemanticClusteringResponse,
  BatchImportRequest,
  BatchImportResponse,
  ProgressResponse,
  CrossProjectSearchRequest,
  CrossProjectSearchResponse,
  AddKnowledgeRequest,
  UpdateKnowledgeRequest,
  BaseResponse,
  WebhookRequest,
  WebhookResponse,
  WebhookStatsResponse,
  HttpMethod,
  RequestConfig
} from '../types';

import { validateJwtToken, formatFilters, generateRequestId } from '../utils';

/**
 * Main client for BETTY Memory System v2.0 API.
 * 
 * Provides complete access to all BETTY v2.0 features including:
 * - Advanced search with semantic, keyword, and hybrid modes
 * - Pattern matching and discovery in knowledge graphs
 * - Semantic clustering of knowledge items
 * - Batch operations with progress tracking
 * - Cross-project intelligence and knowledge transfer
 * - Real-time WebSocket connections
 * - Comprehensive error handling with retries
 * 
 * @example
 * ```typescript
 * const client = new BettyClient({
 *   apiKey: 'your-jwt-token',
 *   baseUrl: 'http://localhost:3034/api/v2'
 * });
 * 
 * const results = await client.advancedSearch({
 *   query: 'machine learning optimization',
 *   searchType: 'hybrid',
 *   maxResults: 20
 * });
 * ```
 */
export class BettyClient extends EventEmitter {
  private config: BettyConfig;
  private httpClient: AxiosInstance;
  private requestQueue: Map<string, Promise<any>> = new Map();

  /**
   * Initialize BETTY client.
   * 
   * @param options - Client configuration options
   */
  constructor(options: BettyClientOptions) {
    super();
    
    this.config = new BettyConfig(options);
    
    // Validate API key if provided
    if (this.config.apiKey) {
      try {
        validateJwtToken(this.config.apiKey);
      } catch (error) {
        throw new AuthenticationError(`Invalid JWT token: ${error.message}`);
      }
    }
    
    // Create HTTP client
    this.httpClient = this.createHttpClient();
    
    this.emit('client_initialized', { config: this.config.toSafeObject() });
  }

  /**
   * Create configured HTTP client instance.
   */
  private createHttpClient(): AxiosInstance {
    const client = axios.create({
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout * 1000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': `betty-typescript-sdk/2.0.0`,
        'Accept': 'application/json',
        ...this.config.customHeaders
      },
      maxRedirects: 3,
      validateStatus: () => true, // Handle all status codes manually
    });

    // Request interceptor
    client.interceptors.request.use(
      (config) => {
        // Add authorization header
        if (this.config.apiKey) {
          config.headers = config.headers || {};
          config.headers['Authorization'] = `Bearer ${this.config.apiKey}`;
        }
        
        // Add request ID for tracking
        const requestId = generateRequestId();
        config.headers = config.headers || {};
        config.headers['X-Request-ID'] = requestId;
        
        // Log request if enabled
        if (this.config.logRequests) {
          console.log(`[BETTY] ${config.method?.toUpperCase()} ${config.url}`, {
            requestId,
            data: config.data
          });
        }
        
        this.emit('request_start', { config, requestId });
        return config;
      },
      (error) => {
        this.emit('request_error', { error });
        return Promise.reject(error);
      }
    );

    // Response interceptor
    client.interceptors.response.use(
      (response) => {
        const requestId = response.config.headers?.['X-Request-ID'] as string;
        
        if (this.config.logRequests) {
          console.log(`[BETTY] Response ${response.status}`, {
            requestId,
            status: response.status,
            data: response.data
          });
        }
        
        this.emit('response_received', { 
          response, 
          requestId,
          status: response.status 
        });
        
        return response;
      },
      (error) => {
        const requestId = error.config?.headers?.['X-Request-ID'] as string;
        
        this.emit('response_error', { 
          error, 
          requestId,
          status: error.response?.status 
        });
        
        return Promise.reject(error);
      }
    );

    return client;
  }

  /**
   * Make HTTP request with error handling and retries.
   */
  private async makeRequest<T = any>(
    method: HttpMethod,
    endpoint: string,
    data?: any,
    params?: Record<string, any>
  ): Promise<T> {
    const url = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
    
    // Check for existing request with same parameters (deduplication)
    const requestKey = `${method}:${url}:${JSON.stringify({ data, params })}`;
    
    if (this.config.enableRequestDeduplication && this.requestQueue.has(requestKey)) {
      return this.requestQueue.get(requestKey)!;
    }
    
    const requestPromise = this.executeRequest<T>(method, url, data, params);
    
    if (this.config.enableRequestDeduplication) {
      this.requestQueue.set(requestKey, requestPromise);
      
      // Clean up after request completes
      requestPromise.finally(() => {
        this.requestQueue.delete(requestKey);
      });
    }
    
    return requestPromise;
  }

  /**
   * Execute HTTP request with retry logic.
   */
  private async executeRequest<T>(
    method: HttpMethod,
    url: string,
    data?: any,
    params?: Record<string, any>
  ): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 1; attempt <= this.config.maxRetries + 1; attempt++) {
      try {
        const config: AxiosRequestConfig = {
          method,
          url,
          data,
          params
        };
        
        const response: AxiosResponse = await this.httpClient.request(config);
        
        // Handle successful responses
        if (response.status >= 200 && response.status < 300) {
          return response.data;
        }
        
        // Handle error responses
        const error = this.createErrorFromResponse(response);
        
        // Don't retry certain errors
        if (!this.shouldRetryError(error) || attempt > this.config.maxRetries) {
          throw error;
        }
        
        lastError = error;
        
        // Calculate retry delay
        const delay = this.calculateRetryDelay(attempt, error);
        await this.sleep(delay);
        
        this.emit('retry_attempt', { 
          attempt, 
          error, 
          delay, 
          method, 
          url 
        });
        
      } catch (error) {
        if (error instanceof BettyAPIError) {
          // Re-throw API errors as-is
          lastError = error;
          
          if (!this.shouldRetryError(error) || attempt > this.config.maxRetries) {
            throw error;
          }
        } else {
          // Handle network errors
          lastError = new BettyAPIError(`Network error: ${error.message}`);
          
          if (attempt > this.config.maxRetries) {
            throw lastError;
          }
        }
        
        // Calculate retry delay for network errors
        const delay = this.calculateRetryDelay(attempt);
        await this.sleep(delay);
        
        this.emit('retry_attempt', { 
          attempt, 
          error: lastError, 
          delay, 
          method, 
          url 
        });
      }
    }
    
    throw lastError!;
  }

  /**
   * Create appropriate error from HTTP response.
   */
  private createErrorFromResponse(response: AxiosResponse): BettyAPIError {
    const { status, data } = response;
    const message = data?.message || 'API request failed';
    const details = data?.details || {};
    const requestId = data?.request_id;
    
    switch (status) {
      case 401:
        return new AuthenticationError(message, details, requestId);
        
      case 403:
        return new PermissionError(
          message,
          details.missing_permissions || [],
          details.user_permissions || [],
          details,
          requestId
        );
        
      case 422:
        return new ValidationError(
          message,
          details.field_errors || {},
          details,
          requestId
        );
        
      case 429:
        return new RateLimitError(
          message,
          details.retry_after,
          details.limit_info || {},
          details,
          requestId
        );
        
      default:
        return new BettyAPIError(
          message,
          status,
          details,
          requestId
        );
    }
  }

  /**
   * Determine if error should trigger retry.
   */
  private shouldRetryError(error: Error): boolean {
    // Retry server errors and rate limits
    if (error instanceof RateLimitError) return true;
    
    if (error instanceof BettyAPIError) {
      return error.statusCode ? error.statusCode >= 500 : false;
    }
    
    // Retry network errors
    return true;
  }

  /**
   * Calculate retry delay with exponential backoff.
   */
  private calculateRetryDelay(attempt: number, error?: Error): number {
    // Use retry-after header for rate limits
    if (error instanceof RateLimitError && error.retryAfter) {
      return error.retryAfter * 1000; // Convert to milliseconds
    }
    
    // Exponential backoff
    const baseDelay = this.config.retryDelay * 1000; // Convert to ms
    const delay = baseDelay * Math.pow(this.config.retryBackoffFactor, attempt - 1);
    
    // Add jitter to prevent thundering herd
    const jitter = Math.random() * 0.1 * delay;
    
    return Math.min(delay + jitter, this.config.maxRetryDelay * 1000);
  }

  /**
   * Sleep for specified milliseconds.
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Advanced Search Methods

  /**
   * Perform advanced search with semantic, keyword, or hybrid modes.
   */
  async advancedSearch(request: AdvancedSearchRequest): Promise<AdvancedSearchResponse> {
    const requestData = {
      query: request.query,
      search_type: request.searchType || 'hybrid',
      similarity_threshold: request.similarityThreshold || 0.7,
      max_results: request.maxResults || 20,
      ranking_algorithm: request.rankingAlgorithm || 'bm25_semantic_hybrid',
      include_metadata: request.includeMetadata !== false,
      ...request.timeRange && { time_range: request.timeRange },
      ...request.groupBy && { group_by: request.groupBy },
      ...request.projectIds && { project_ids: request.projectIds },
      ...request.filters && { filters: formatFilters(request.filters) }
    };

    return this.makeRequest<AdvancedSearchResponse>('POST', 'query/advanced-search', requestData);
  }

  /**
   * Find patterns in knowledge graphs using advanced algorithms.
   */
  async patternMatching(request: PatternMatchRequest): Promise<PatternMatchResponse> {
    const requestData = {
      pattern_type: request.patternType,
      max_depth: request.maxDepth || 5,
      min_confidence: request.minConfidence || 0.6,
      max_results: request.maxResults || 50,
      ...request.patternDefinition && { pattern_definition: request.patternDefinition },
      ...request.projectIds && { project_ids: request.projectIds }
    };

    return this.makeRequest<PatternMatchResponse>('POST', 'query/pattern-match', requestData);
  }

  /**
   * Organize knowledge items into semantic clusters.
   */
  async semanticClustering(request: SemanticClusteringRequest): Promise<SemanticClusteringResponse> {
    const requestData = {
      algorithm: request.algorithm || 'hierarchical',
      auto_clusters: request.autoClusters !== false,
      min_cluster_size: request.minClusterSize || 5,
      max_cluster_size: request.maxClusterSize || 100,
      similarity_threshold: request.similarityThreshold || 0.6,
      use_content: request.useContent !== false,
      use_metadata: request.useMetadata !== false,
      use_relationships: request.useRelationships || false,
      include_visualization: request.includeVisualization || false,
      include_topics: request.includeTopics !== false,
      max_items_per_cluster: request.maxItemsPerCluster || 100,
      ...request.numClusters && { num_clusters: request.numClusters },
      ...request.projectIds && { project_ids: request.projectIds },
      ...request.knowledgeTypes && { knowledge_types: request.knowledgeTypes }
    };

    return this.makeRequest<SemanticClusteringResponse>('POST', 'query/semantic-clusters', requestData);
  }

  // Batch Operation Methods

  /**
   * Start batch import operation with progress tracking.
   */
  async batchImport(request: BatchImportRequest): Promise<BatchImportResponse> {
    const requestData = {
      source_type: request.sourceType,
      format: request.format,
      source_config: request.sourceConfig,
      target_project_id: request.targetProjectId,
      duplicate_handling: request.duplicateHandling || 'skip',
      batch_size: request.batchSize || 100,
      max_errors: request.maxErrors || 50,
      ...request.validationRules && { validation_rules: request.validationRules },
      ...request.processingOptions && { processing_options: request.processingOptions },
      ...request.notifyWebhook && { notify_webhook: request.notifyWebhook }
    };

    return this.makeRequest<BatchImportResponse>('POST', 'batch/knowledge/import', requestData);
  }

  /**
   * Get progress of a batch operation.
   */
  async getBatchProgress(operationId: string): Promise<ProgressResponse> {
    return this.makeRequest<ProgressResponse>('GET', `batch/operations/${operationId}/progress`);
  }

  /**
   * Track batch operation progress with polling.
   * Returns an async generator that yields progress updates.
   */
  async* trackProgress(operationId: string, pollInterval = 5000): AsyncGenerator<ProgressResponse['data'], void, unknown> {
    while (true) {
      try {
        const progress = await this.getBatchProgress(operationId);
        
        if (progress.success && progress.data) {
          yield progress.data;
          
          // Stop if operation is finished
          if (['completed', 'failed', 'cancelled'].includes(progress.data.status)) {
            break;
          }
        } else {
          throw new BettyAPIError(`Failed to get progress: ${progress.message}`);
        }
        
        // Wait before next poll
        await this.sleep(pollInterval);
        
      } catch (error) {
        this.emit('progress_error', { operationId, error });
        throw error;
      }
    }
  }

  // Cross-Project Intelligence Methods

  /**
   * Search across multiple connected projects.
   */
  async crossProjectSearch(request: CrossProjectSearchRequest): Promise<CrossProjectSearchResponse> {
    const requestData = {
      query: request.query,
      search_type: request.searchType || 'hybrid',
      similarity_threshold: request.similarityThreshold || 0.7,
      max_results_per_project: request.maxResultsPerProject || 20,
      max_total_results: request.maxTotalResults || 100,
      merge_strategy: request.mergeStrategy || 'relevance',
      include_project_context: request.includeProjectContext !== false,
      ...request.projectIds && { project_ids: request.projectIds },
      ...request.filters && { filters: formatFilters(request.filters) }
    };

    return this.makeRequest<CrossProjectSearchResponse>('POST', 'cross-project/search', requestData);
  }

  // Knowledge Management Methods

  /**
   * Add a new knowledge item.
   */
  async addKnowledge(request: AddKnowledgeRequest): Promise<BaseResponse> {
    const requestData = {
      title: request.title,
      content: request.content,
      knowledge_type: request.knowledgeType || 'document',
      ...request.projectId && { project_id: request.projectId },
      ...((request.tags || request.metadata) && {
        metadata: {
          ...request.metadata,
          ...request.tags && { tags: request.tags }
        }
      })
    };

    return this.makeRequest<BaseResponse>('POST', 'knowledge/add', requestData);
  }

  /**
   * Get a knowledge item by ID.
   */
  async getKnowledge(knowledgeId: string): Promise<BaseResponse> {
    return this.makeRequest<BaseResponse>('GET', `knowledge/${knowledgeId}`);
  }

  /**
   * Update a knowledge item.
   */
  async updateKnowledge(knowledgeId: string, request: UpdateKnowledgeRequest): Promise<BaseResponse> {
    const requestData: any = {};
    
    if (request.title !== undefined) requestData.title = request.title;
    if (request.content !== undefined) requestData.content = request.content;
    if (request.knowledgeType !== undefined) requestData.knowledge_type = request.knowledgeType;
    
    if (request.tags !== undefined || request.metadata !== undefined) {
      requestData.metadata = {
        ...request.metadata,
        ...request.tags !== undefined && { tags: request.tags }
      };
    }

    return this.makeRequest<BaseResponse>('PUT', `knowledge/${knowledgeId}`, requestData);
  }

  /**
   * Delete a knowledge item.
   */
  async deleteKnowledge(knowledgeId: string): Promise<BaseResponse> {
    return this.makeRequest<BaseResponse>('DELETE', `knowledge/${knowledgeId}`);
  }

  // Webhook Management Methods

  /**
   * Register a new webhook.
   */
  async registerWebhook(request: WebhookRequest): Promise<WebhookResponse> {
    return this.makeRequest<WebhookResponse>('POST', 'webhooks/register', request);
  }

  /**
   * List user's webhooks.
   */
  async listWebhooks(): Promise<BaseResponse> {
    return this.makeRequest<BaseResponse>('GET', 'webhooks/list');
  }

  /**
   * Get webhook details.
   */
  async getWebhook(webhookId: string): Promise<WebhookResponse> {
    return this.makeRequest<WebhookResponse>('GET', `webhooks/${webhookId}`);
  }

  /**
   * Update webhook configuration.
   */
  async updateWebhook(webhookId: string, request: Partial<WebhookRequest>): Promise<WebhookResponse> {
    return this.makeRequest<WebhookResponse>('PUT', `webhooks/${webhookId}`, request);
  }

  /**
   * Delete webhook.
   */
  async deleteWebhook(webhookId: string): Promise<BaseResponse> {
    return this.makeRequest<BaseResponse>('DELETE', `webhooks/${webhookId}`);
  }

  /**
   * Test webhook endpoint.
   */
  async testWebhook(request: { url: string; secret?: string }): Promise<BaseResponse> {
    return this.makeRequest<BaseResponse>('POST', 'webhooks/test', request);
  }

  /**
   * Get webhook statistics.
   */
  async getWebhookStats(webhookId: string): Promise<WebhookStatsResponse> {
    return this.makeRequest<WebhookStatsResponse>('GET', `webhooks/${webhookId}/stats`);
  }

  // Utility Methods

  /**
   * Check API health status.
   */
  async healthCheck(): Promise<BaseResponse> {
    return this.makeRequest<BaseResponse>('GET', '../../health');
  }

  /**
   * Get API version information.
   */
  async getApiVersion(): Promise<BaseResponse> {
    return this.makeRequest<BaseResponse>('GET', '../version/info');
  }

  /**
   * Get client configuration (safe version without sensitive data).
   */
  getConfig(): Record<string, any> {
    return this.config.toSafeObject();
  }

  /**
   * Update client configuration.
   */
  updateConfig(options: Partial<BettyClientOptions>): void {
    this.config = new BettyConfig({ ...this.config.toObject(), ...options });
    
    // Recreate HTTP client with new config
    this.httpClient = this.createHttpClient();
    
    this.emit('config_updated', { config: this.config.toSafeObject() });
  }

  /**
   * Dispose client and cleanup resources.
   */
  dispose(): void {
    this.requestQueue.clear();
    this.removeAllListeners();
    
    this.emit('client_disposed');
  }
}