// ABOUTME: Real-time memory correctness monitoring dashboard for Betty Memory System
// ABOUTME: Displays pattern integrity, cross-database consistency, and system health metrics

import React, { useState, useEffect, useMemo } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Activity, Database, 
         RefreshCw, TrendingUp, TrendingDown, Shield, Zap } from 'lucide-react';

// Types for Memory Correctness monitoring
interface DatabaseHealthMetrics {
  database_type: string;
  status: 'healthy' | 'warning' | 'critical' | 'corrupted' | 'unknown';
  connection_healthy: boolean;
  response_time_ms: number;
  error_rate_percent: number;
  last_check: string;
  metadata?: Record<string, any>;
}

interface MemoryHealthStatus {
  health_id: string;
  project_id: string;
  overall_health: 'healthy' | 'warning' | 'critical' | 'corrupted' | 'unknown';
  system_uptime_hours: number;
  database_health: Record<string, DatabaseHealthMetrics>;
  pattern_integrity_average: number;
  consistency_score: number;
  error_rate_last_hour: number;
  performance_degradation: boolean;
  active_corruptions: number;
  recovery_operations_running: number;
  last_full_validation?: string;
  next_scheduled_check: string;
  alerts: string[];
  recommendations: string[];
  timestamp: string;
}

interface SystemMetrics {
  timestamp: string;
  system_uptime_hours: number;
  validation_metrics: {
    average_validation_time_ms: number;
    pattern_accuracy_percent: number;
    consistency_score_percent: number;
    validations_last_hour: number;
    validations_successful: number;
    validations_failed: number;
  };
  database_performance: {
    postgresql_avg_response_ms: number;
    neo4j_avg_response_ms: number;
    qdrant_avg_response_ms: number;
    redis_avg_response_ms: number;
  };
  reliability_metrics: {
    pattern_integrity_average: number;
    cross_database_consistency: number;
    error_rate_last_hour: number;
    corruption_incidents_today: number;
    recovery_success_rate: number;
  };
}

interface MemoryCorrectnessMonitorProps {
  projectId: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const MemoryCorrectnessMonitor: React.FC<MemoryCorrectnessMonitorProps> = ({
  projectId,
  autoRefresh = true,
  refreshInterval = 30000 // 30 seconds
}) => {
  const [healthStatus, setHealthStatus] = useState<MemoryHealthStatus | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Use relative paths for nginx proxy compatibility

  // Fetch health status from API
  const fetchHealthStatus = async () => {
    try {
      const response = await fetch(`/api/v2/memory-correctness/health/${projectId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setHealthStatus(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch health status:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Fetch system metrics from API
  const fetchSystemMetrics = async () => {
    try {
      const response = await fetch(`/api/v2/memory-correctness/metrics/system?project_id=${projectId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setSystemMetrics(data);
    } catch (err) {
      console.error('Failed to fetch system metrics:', err);
    }
  };

  // Initial data fetch
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await Promise.all([fetchHealthStatus(), fetchSystemMetrics()]);
      setLoading(false);
      setLastRefresh(new Date());
    };

    fetchData();
  }, [projectId]);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      await Promise.all([fetchHealthStatus(), fetchSystemMetrics()]);
      setLastRefresh(new Date());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, projectId]);

  // Manual refresh handler
  const handleRefresh = async () => {
    setLoading(true);
    await Promise.all([fetchHealthStatus(), fetchSystemMetrics()]);
    setLoading(false);
    setLastRefresh(new Date());
  };

  // Status color mapping
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      case 'critical': return 'text-red-600 bg-red-50';
      case 'corrupted': return 'text-purple-600 bg-purple-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // Status icon mapping
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5" />;
      case 'warning': return <AlertTriangle className="w-5 h-5" />;
      case 'critical': case 'corrupted': return <XCircle className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  // Performance score calculation
  const performanceScore = useMemo(() => {
    if (!healthStatus || !systemMetrics) return 0;
    
    const integrityScore = healthStatus.pattern_integrity_average;
    const consistencyScore = healthStatus.consistency_score;
    const accuracyScore = systemMetrics.validation_metrics.pattern_accuracy_percent;
    const errorPenalty = Math.max(0, 100 - (healthStatus.error_rate_last_hour * 10));
    
    return Math.round((integrityScore + consistencyScore + accuracyScore + errorPenalty) / 4);
  }, [healthStatus, systemMetrics]);

  if (loading && !healthStatus) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Memory Correctness Monitor</h3>
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />
            <span className="text-sm text-gray-500">Loading...</span>
          </div>
        </div>
        <div className="animate-pulse space-y-4">
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error && !healthStatus) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Memory Correctness Monitor</h3>
          <button
            onClick={handleRefresh}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">Failed to load memory correctness data: {error}</span>
          </div>
        </div>
      </div>
    );
  }

  if (!healthStatus) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Shield className="w-6 h-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Memory Correctness Monitor</h3>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(healthStatus.overall_health)}`}>
            {getStatusIcon(healthStatus.overall_health)}
            <span className="ml-1 capitalize">{healthStatus.overall_health}</span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 transition-colors flex items-center space-x-1"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600 font-medium">Pattern Integrity</p>
              <p className="text-2xl font-bold text-green-700">{healthStatus.pattern_integrity_average.toFixed(2)}%</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600 font-medium">Consistency Score</p>
              <p className="text-2xl font-bold text-blue-700">{healthStatus.consistency_score.toFixed(2)}%</p>
            </div>
            <Database className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className={`p-4 rounded-lg ${performanceScore >= 95 ? 'bg-green-50' : performanceScore >= 90 ? 'bg-yellow-50' : 'bg-red-50'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${performanceScore >= 95 ? 'text-green-600' : performanceScore >= 90 ? 'text-yellow-600' : 'text-red-600'}`}>
                Performance Score
              </p>
              <p className={`text-2xl font-bold ${performanceScore >= 95 ? 'text-green-700' : performanceScore >= 90 ? 'text-yellow-700' : 'text-red-700'}`}>
                {performanceScore}/100
              </p>
            </div>
            {performanceScore >= 95 ? (
              <TrendingUp className="w-8 h-8 text-green-500" />
            ) : (
              <TrendingDown className="w-8 h-8 text-red-500" />
            )}
          </div>
        </div>

        <div className={`p-4 rounded-lg ${healthStatus.error_rate_last_hour < 1 ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${healthStatus.error_rate_last_hour < 1 ? 'text-green-600' : 'text-red-600'}`}>
                Error Rate (1h)
              </p>
              <p className={`text-2xl font-bold ${healthStatus.error_rate_last_hour < 1 ? 'text-green-700' : 'text-red-700'}`}>
                {healthStatus.error_rate_last_hour.toFixed(2)}%
              </p>
            </div>
            <Activity className={`w-8 h-8 ${healthStatus.error_rate_last_hour < 1 ? 'text-green-500' : 'text-red-500'}`} />
          </div>
        </div>
      </div>

      {/* Database Health Grid */}
      <div className="mb-6">
        <h4 className="text-md font-medium text-gray-900 mb-3">Database Health Status</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(healthStatus.database_health).map(([dbType, metrics]) => (
            <div key={dbType} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h5 className="text-sm font-medium text-gray-700 capitalize">{dbType}</h5>
                <div className={`p-1 rounded ${getStatusColor(metrics.status)}`}>
                  {getStatusIcon(metrics.status)}
                </div>
              </div>
              <div className="space-y-1 text-xs text-gray-600">
                <div className="flex justify-between">
                  <span>Response Time:</span>
                  <span className={metrics.response_time_ms < 100 ? 'text-green-600' : 'text-red-600'}>
                    {metrics.response_time_ms.toFixed(1)}ms
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Error Rate:</span>
                  <span className={metrics.error_rate_percent < 1 ? 'text-green-600' : 'text-red-600'}>
                    {metrics.error_rate_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Connection:</span>
                  <span className={metrics.connection_healthy ? 'text-green-600' : 'text-red-600'}>
                    {metrics.connection_healthy ? 'Healthy' : 'Failed'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Statistics */}
      {systemMetrics && (
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">System Performance</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <p className="font-medium text-gray-700 mb-2">Validation Metrics</p>
                <div className="space-y-1 text-gray-600">
                  <div className="flex justify-between">
                    <span>Avg Validation Time:</span>
                    <span className={systemMetrics.validation_metrics.average_validation_time_ms < 100 ? 'text-green-600' : 'text-red-600'}>
                      {systemMetrics.validation_metrics.average_validation_time_ms.toFixed(1)}ms
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Pattern Accuracy:</span>
                    <span className="text-green-600">
                      {systemMetrics.validation_metrics.pattern_accuracy_percent.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Validations (1h):</span>
                    <span>{systemMetrics.validation_metrics.validations_last_hour.toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <p className="font-medium text-gray-700 mb-2">Database Performance</p>
                <div className="space-y-1 text-gray-600">
                  <div className="flex justify-between">
                    <span>PostgreSQL:</span>
                    <span>{systemMetrics.database_performance.postgresql_avg_response_ms.toFixed(1)}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Neo4j:</span>
                    <span>{systemMetrics.database_performance.neo4j_avg_response_ms.toFixed(1)}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Qdrant:</span>
                    <span>{systemMetrics.database_performance.qdrant_avg_response_ms.toFixed(1)}ms</span>
                  </div>
                </div>
              </div>
              
              <div>
                <p className="font-medium text-gray-700 mb-2">Reliability</p>
                <div className="space-y-1 text-gray-600">
                  <div className="flex justify-between">
                    <span>Consistency:</span>
                    <span className="text-green-600">
                      {systemMetrics.reliability_metrics.cross_database_consistency.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recovery Rate:</span>
                    <span className="text-green-600">
                      {systemMetrics.reliability_metrics.recovery_success_rate.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Corruptions Today:</span>
                    <span className={systemMetrics.reliability_metrics.corruption_incidents_today === 0 ? 'text-green-600' : 'text-red-600'}>
                      {systemMetrics.reliability_metrics.corruption_incidents_today}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Active Issues */}
      {(healthStatus.active_corruptions > 0 || healthStatus.alerts.length > 0) && (
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">Active Issues</h4>
          <div className="space-y-2">
            {healthStatus.active_corruptions > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-center">
                  <XCircle className="w-4 h-4 text-red-500 mr-2" />
                  <span className="text-red-700 font-medium">
                    {healthStatus.active_corruptions} active corruption{healthStatus.active_corruptions !== 1 ? 's' : ''} detected
                  </span>
                </div>
              </div>
            )}
            {healthStatus.alerts.map((alert, index) => (
              <div key={index} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="flex items-center">
                  <AlertTriangle className="w-4 h-4 text-yellow-500 mr-2" />
                  <span className="text-yellow-700">{alert}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {healthStatus.recommendations.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-3">Recommendations</h4>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <ul className="space-y-2">
              {healthStatus.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start">
                  <Zap className="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                  <span className="text-blue-700 text-sm">{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoryCorrectnessMonitor;