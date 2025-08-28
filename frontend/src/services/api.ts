import axios from 'axios'

// Global error handler type declaration
declare global {
  interface Window {
    bettyErrorHandler?: (errorInfo: any) => void;
  }
}

// Types for API responses
export interface ApiResponse<T> {
  message: string
  data: T
  timestamp?: string
}

export interface TimeSeriesDataPoint {
  timestamp: string
  value: number
  metadata?: Record<string, any>
}

export interface KnowledgeGrowthData {
  total_knowledge_items: number
  daily_growth: TimeSeriesDataPoint[]
  growth_rate_percentage: number
  knowledge_by_type: Record<string, number>
  knowledge_by_project: Record<string, number>
  conversations_captured: number
  decisions_documented: number
  solutions_preserved: number
  code_patterns_identified: number
  projections: Record<string, number>
}

export interface ProjectNetworkNode {
  project_id: string
  project_name: string
  knowledge_count: number
  connection_strength: number
  color: string
  size: number
}

export interface ProjectConnection {
  source_project_id: string
  target_project_id: string
  connection_type: string
  strength: number
  shared_patterns: string[]
  usage_count: number
}

export interface CrossProjectIntelligenceData {
  project_nodes: ProjectNetworkNode[]
  connections: ProjectConnection[]
  hot_connection_paths: Array<{
    path: string
    pattern: string
    reuse_count: number
    success_rate: number
  }>
  network_density: number
  most_connected_project: string
  knowledge_flow_direction: Record<string, any>
  cross_project_reuse_rate: number
}

export interface PatternUsageItem {
  pattern_name: string
  pattern_type: string
  usage_count: number
  success_rate: number
  projects_used: string[]
  avg_implementation_time_hours: number | null
  last_used: string
  performance_improvement: number | null
}

export interface PatternUsageData {
  hot_patterns: PatternUsageItem[]
  pattern_success_trends: TimeSeriesDataPoint[]
  total_patterns_identified: number
  reuse_frequency: Record<string, number>
  time_savings_total_hours: number
  success_rate_by_category: Record<string, number>
}

export interface ActivityFeedItem {
  id: string
  activity_type: string
  title: string
  description: string
  project_name: string | null
  timestamp: string
  metadata?: Record<string, any>
  priority: string
  icon: string
}

export interface RealTimeActivityData {
  activities: ActivityFeedItem[]
  activity_rate_per_hour: number
  most_active_project: string
  recent_patterns_discovered: string[]
  system_alerts: Array<Record<string, any>>
}

export interface IntelligenceMetricsData {
  overall_intelligence_score: number
  knowledge_quality_score: number
  cross_project_applicability: number
  pattern_recognition_accuracy: number
  context_relevance_score: number
  search_response_accuracy: number
  intelligence_growth_trend: TimeSeriesDataPoint[]
  problem_solving_speed_improvement: number
  knowledge_reuse_rate: number
}

export interface SystemPerformanceData {
  average_response_time_ms: number
  context_loading_time_ms: number
  knowledge_ingestion_rate_per_hour: number
  search_response_time_ms: number
  database_health_score: number
  system_uptime_percentage: number
  performance_trends: TimeSeriesDataPoint[]
  error_rate: number
  resource_utilization: Record<string, number>
  throughput_metrics: Record<string, number>
}

export interface DashboardSummaryData {
  total_knowledge_items: number
  growth_rate_daily: number
  intelligence_score: number
  system_health_status: string
  conversations_today: number
  patterns_reused_today: number
  cross_project_connections: number
  avg_response_time_ms: number
  trending_patterns: string[]
  most_active_project: string
  recent_achievements: string[]
  system_alerts: Array<Record<string, any>>
  performance_warnings: string[]
  knowledge_growth_7d: number[]
  performance_trend_24h: number[]
  activity_trend_24h: number[]
}

// Configure axios for remote server with nginx proxy
const api = axios.create({
  // Use relative URLs so nginx can proxy to betty_memory_api:8000
  baseURL: '', // This makes all requests relative to current domain
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
api.interceptors.request.use((config) => {
  // Add Betty API key for development
  config.headers['X-API-Key'] = 'betty_dev_key_123'
  
  // Add auth token if available (for future use)
  // const token = localStorage.getItem('auth_token')
  // if (token) {
  //   config.headers.Authorization = `Bearer ${token}`
  // }
  return config
})

// Enhanced error logging function
const logError = (error: any) => {
  const errorInfo = {
    timestamp: new Date().toISOString(),
    url: error.config?.url || 'unknown',
    method: error.config?.method || 'unknown',
    status: error.response?.status,
    statusText: error.response?.statusText,
    message: error.message,
    code: error.code,
    data: error.response?.data
  }

  // Log to console with structured format
  console.group('🔴 BETTY API Error')
  console.error('Error Details:', errorInfo)
  console.error('Full Error Object:', error)
  console.groupEnd()

  // Store in local storage for debugging (keep last 10 errors)
  try {
    const storedErrors = JSON.parse(localStorage.getItem('betty_api_errors') || '[]')
    storedErrors.unshift(errorInfo)
    localStorage.setItem('betty_api_errors', JSON.stringify(storedErrors.slice(0, 10)))
  } catch (e) {
    console.warn('Could not store error in localStorage:', e)
  }

  // Send to error reporting service if available
  if (window.bettyErrorHandler) {
    window.bettyErrorHandler(errorInfo)
  }

  // Send to backend error tracking (don't await to avoid blocking)
  sendErrorToBackend(errorInfo).catch(console.warn)

  return errorInfo
}

// Response interceptor for enhanced error handling
api.interceptors.response.use(
  (response) => {
    // Log successful responses in development
    if (typeof window !== 'undefined') {
      console.log(`✅ API Success: ${response.config.method?.toUpperCase()} ${response.config.url} (${response.status})`)
    }
    return response
  },
  (error) => {
    const errorInfo = logError(error)
    
    // Enhance error with additional context
    error.bettyErrorInfo = errorInfo
    error.userMessage = getUserFriendlyMessage(error)
    
    return Promise.reject(error)
  }
)

// Generate user-friendly error messages
const getUserFriendlyMessage = (error: any): string => {
  if (error.code === 'NETWORK_ERROR') {
    return 'Unable to connect to BETTY services. Please check your connection.'
  }
  
  if (error.response?.status === 404) {
    return 'The requested BETTY service endpoint was not found.'
  }
  
  if (error.response?.status >= 500) {
    return 'BETTY services are experiencing technical difficulties. Please try again later.'
  }
  
  if (error.response?.status === 401) {
    return 'Authentication required. Please check your credentials.'
  }
  
  if (error.response?.status === 403) {
    return 'Access denied. You may not have permission to access this resource.'
  }
  
  if (error.message?.includes('timeout')) {
    return 'Request timed out. BETTY services may be slow to respond.'
  }
  
  return error.response?.data?.message || error.message || 'An unexpected error occurred.'
}

// Send error to backend tracking system
const sendErrorToBackend = async (errorInfo: any): Promise<void> => {
  try {
    // Use relative path to work with nginx proxy
    await fetch('/api/errors/log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        error_type: errorInfo.code || 'API_ERROR',
        message: errorInfo.message,
        url: errorInfo.url,
        method: errorInfo.method,
        status: errorInfo.status,
        user_agent: navigator.userAgent,
        additional_info: {
          timestamp: errorInfo.timestamp,
          statusText: errorInfo.statusText,
          data: errorInfo.data
        }
      })
    })
  } catch (e) {
    // Silently fail to avoid recursive errors
    console.debug('Could not send error to backend:', e)
  }
}

// Analytics API endpoints - Updated to use working V2 endpoints
export const analyticsApi = {
  // Use working API endpoints via nginx proxy
  getSystemPerformance: (_hours = 24) =>
    api.get<{ message: string; timestamp: string; data: any }>('/api/analytics/system-performance'),

  // System health check
  getSystemHealth: () =>
    api.get<{ status: string; timestamp: string }>('/api/health/'),

  // Intelligence metrics from analytics API
  getIntelligenceMetrics: () =>
    api.get<{ message: string; timestamp: string; data: any }>('/api/analytics/intelligence-metrics'),

  // Knowledge growth statistics
  getKnowledgeGrowth: (_days = 30) =>
    api.get<{ message: string; timestamp: string; data: any }>('/api/analytics/knowledge-growth'),

  // Cross-project connections
  getCrossProjectConnections: () =>
    api.get<{ message: string; timestamp: string; data: any }>('/api/analytics/cross-project-connections'),

  // Mock pattern usage for now
  getPatternUsage: (_limit = 20) =>
    Promise.resolve({
      data: {
        message: 'Pattern usage data (V2.0)',
        timestamp: new Date().toISOString(),
        data: {
          hot_patterns: [
            {
              pattern_name: 'Authentication Pattern',
              pattern_type: 'security',
              usage_count: 5,
              success_rate: 0.95,
              projects_used: ['betty-auth', '137docs'],
              avg_implementation_time_hours: 2.5,
              last_used: new Date().toISOString(),
              performance_improvement: 0.3
            },
            {
              pattern_name: 'API Integration Pattern',
              pattern_type: 'integration',
              usage_count: 3,
              success_rate: 0.87,
              projects_used: ['betty-integration'],
              avg_implementation_time_hours: 4.0,
              last_used: new Date().toISOString(),
              performance_improvement: 0.2
            }
          ],
          pattern_success_trends: [],
          total_patterns_identified: 2,
          reuse_frequency: { 'weekly': 2, 'monthly': 8 },
          time_savings_total_hours: 12.5,
          success_rate_by_category: { 'security': 0.95, 'integration': 0.87 }
        }
      }
    }),

  // Real API call for real-time activity
  getRealTimeActivity: (limit = 50) =>
    api.get(`/api/analytics/real-time-activity?limit=${limit}`),

  // Dashboard summary from analytics API
  getDashboardSummary: () =>
    api.get<{ message: string; timestamp: string; data: DashboardSummaryData }>('/api/analytics/dashboard-summary'),

  refreshCache: () =>
    api.post('/analytics/refresh-cache'),
}

// Health check endpoint
export const healthApi = {
  checkHealth: () =>
    api.get<{ status: string; timestamp: string }>('/api/health/'),
}

// Error tracking endpoints
export const errorApi = {
  logError: (errorData: any) =>
    api.post('/errors/log', errorData),
  
  getErrorLogs: (params: { limit?: number; offset?: number; error_type?: string; since_hours?: number } = {}) =>
    api.get('/errors/logs', { params }),
  
  getErrorSummary: (hours = 24) =>
    api.get(`/errors/summary?hours=${hours}`),
  
  clearErrorLogs: () =>
    api.delete('/errors/logs?confirm=true'),
  
  getErrorTrackingHealth: () =>
    api.get('/errors/health-check')
}

// Sprint Management API endpoints
export const sprintApi = {
  // List all sprints
  listSprints: () =>
    api.get('/api/sprints/list'),
  
  // Get active sprint
  getActiveSprint: () =>
    api.get('/api/sprints/active'),
  
  // Start new sprint
  startSprint: (data: { title: string; duration_type: string; tasks: string[] }) =>
    api.post('/api/sprints/start', data),
  
  // Complete sprint
  completeSprint: (sprintId: string) =>
    api.post(`/api/sprints/${sprintId}/complete`),
  
  // Update sprint
  updateSprint: (sprintId: string, data: any) =>
    api.put(`/api/sprints/${sprintId}`, data)
}

// Agent Tracking API endpoints
export const agentApi = {
  // Get agent usage statistics
  getUsageStats: () =>
    api.get('/api/agent-tracking/usage'),
  
  // Log agent activity
  logActivity: (data: { agent_type: string; task: string; tokens_used: number; cost: number }) =>
    api.post('/api/agent-tracking/log', data),
  
  // Get agent performance metrics
  getPerformanceMetrics: (agentType?: string) =>
    api.get(`/api/agent-tracking/performance${agentType ? `?agent_type=${agentType}` : ''}`),
  
  // Get cost breakdown
  getCostBreakdown: (timeframe = '7d') =>
    api.get(`/api/agent-tracking/costs?timeframe=${timeframe}`)
}

export default api