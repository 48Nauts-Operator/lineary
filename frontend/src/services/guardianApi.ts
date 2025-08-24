// ABOUTME: API service for Betty Guardian system management
// ABOUTME: Handles Guardian rules, monitoring, statistics, and activity tracking

import axios from 'axios';

// Guardian API types
export interface GuardianRule {
  id: string;
  category: string;
  pattern: string;
  action: 'block' | 'warn' | 'log';
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface GuardianActivity {
  id: string;
  timestamp: string;
  tool_name: string;
  rule_id?: string;
  decision: 'approve' | 'block' | 'warn';
  reason: string;
  user_agent?: string;
  session_id?: string;
  metadata?: Record<string, any>;
}

export interface GuardianStats {
  total_requests: number;
  blocked_requests: number;
  warned_requests: number;
  approved_requests: number;
  block_rate: number;
  warn_rate: number;
  top_blocked_tools: Array<{ tool: string; count: number }>;
  top_triggered_rules: Array<{ rule_id: string; rule_description: string; count: number }>;
  activity_by_hour: Array<{ hour: string; blocked: number; warned: number; approved: number }>;
}

export interface GuardianTimelineData {
  date: string;
  blocked: number;
  warned: number;
  approved: number;
  total: number;
}

// Guardian API configuration
const GUARDIAN_API_BASE = 'http://localhost:4002/api/guardian';

const guardianApi = axios.create({
  baseURL: GUARDIAN_API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handling for Guardian API
guardianApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Guardian API Error:', error);
    if (error.response?.status === 404) {
      throw new Error('Guardian service not available. Please ensure Betty Guardian is running on port 4002.');
    }
    throw error;
  }
);

// Guardian API endpoints
export const guardianApiService = {
  // Rules management
  getRules: async (): Promise<GuardianRule[]> => {
    const response = await guardianApi.get('/rules');
    return response.data.rules || response.data;
  },

  createRule: async (rule: Omit<GuardianRule, 'id' | 'created_at' | 'updated_at'>): Promise<GuardianRule> => {
    const response = await guardianApi.post('/rules', rule);
    return response.data.rule || response.data;
  },

  updateRule: async (id: string, rule: Partial<GuardianRule>): Promise<GuardianRule> => {
    const response = await guardianApi.put(`/rules/${id}`, rule);
    return response.data.rule || response.data;
  },

  deleteRule: async (id: string): Promise<void> => {
    await guardianApi.delete(`/rules/${id}`);
  },

  toggleRule: async (id: string, enabled: boolean): Promise<GuardianRule> => {
    const response = await guardianApi.patch(`/rules/${id}/toggle`, { enabled });
    return response.data.rule || response.data;
  },

  testRule: async (pattern: string, testInput: string): Promise<{ matches: boolean; explanation: string }> => {
    const response = await guardianApi.post('/rules/test', { pattern, test_input: testInput });
    return response.data;
  },

  // Monitoring and statistics
  getStats: async (hours = 24): Promise<GuardianStats> => {
    const response = await guardianApi.get(`/stats?hours=${hours}`);
    return response.data.stats || response.data;
  },

  getActivity: async (limit = 50, offset = 0): Promise<{ activities: GuardianActivity[]; total: number }> => {
    const response = await guardianApi.get(`/activity?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  getTimeline: async (days = 7): Promise<GuardianTimelineData[]> => {
    const response = await guardianApi.get(`/timeline?days=${days}`);
    return response.data.timeline || response.data;
  },

  // Real-time monitoring
  getRecentDecisions: async (limit = 10): Promise<GuardianActivity[]> => {
    const response = await guardianApi.get(`/activity/recent?limit=${limit}`);
    return response.data.activities || response.data;
  },

  // Health check
  checkHealth: async (): Promise<{ status: string; version: string }> => {
    const response = await guardianApi.get('/health');
    return response.data;
  },
};

export default guardianApiService;