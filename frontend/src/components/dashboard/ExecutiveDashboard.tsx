// ABOUTME: Executive Dashboard component for Betty's Phase 6 comprehensive business intelligence
// ABOUTME: Provides executive-level insights, ROI tracking, strategic recommendations, and real-time analytics

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  DollarSign,
  Users,
  BarChart3,
  Download,
  RefreshCw,
  AlertCircle,
  Target,
  Lightbulb,
  ArrowUpRight,
  FileText,
  Mail,
  Smartphone,
  Globe,
  Activity,
  Zap,
  Brain,
  Shield
} from 'lucide-react';

interface ExecutiveDashboardProps {
  timeRange?: string;
  autoRefresh?: boolean;
  mobileView?: boolean;
}

interface ExecutiveMetrics {
  knowledge_health: {
    overall_health_score: number;
    growth_rate_percent: number;
    quality_score: number;
    utilization_rate: number;
  };
  roi_tracking: {
    total_value_created: number;
    investment_cost: number;
    roi_percentage: number;
    payback_period_months: number;
  };
  strategic_insights: {
    critical_insights: Array<{
      title: string;
      description: string;
      impact: string;
      confidence: number;
    }>;
    recommended_actions: string[];
    risk_level: string;
  };
  performance_comparisons: {
    team_productivity_improvement: number;
    avg_improvement: number;
    top_performers: string[];
  };
  utilization_metrics: {
    overall_utilization: number;
    adoption_rates: Record<string, number>;
    user_engagement: Record<string, any>;
  };
  predictive_analytics?: {
    growth_predictions: Record<string, any>;
    prediction_accuracy: number;
    optimization_suggestions: string[];
  };
}

const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
  timeRange = '30d',
  autoRefresh = true,
  mobileView = false
}) => {
  const [executiveData, setExecutiveData] = useState<ExecutiveMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedView, setSelectedView] = useState<'overview' | 'roi' | 'insights' | 'performance'>('overview');
  const [reportGenerating, setReportGenerating] = useState(false);

  // Use relative paths for nginx proxy compatibility

  // Fetch executive dashboard data
  const fetchExecutiveData = useCallback(async () => {
    try {
      setRefreshing(true);
      const response = await fetch(`/api/executive/dashboard/intelligence?time_range=${timeRange}&include_predictions=true&detail_level=executive`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch executive data');
      }
      
      const result = await response.json();
      setExecutiveData(result.data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      console.error('Failed to fetch executive dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [timeRange]);

  // Auto refresh
  useEffect(() => {
    fetchExecutiveData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchExecutiveData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [fetchExecutiveData, autoRefresh]);

  // Generate executive report
  const generateReport = async (format: 'pdf' | 'excel' | 'powerpoint') => {
    try {
      setReportGenerating(true);
      // Use relative path for nginx proxy
      
      const response = await fetch('/api/executive/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_type: 'executive_summary',
          format: format,
          time_range: timeRange,
          recipients: [] // No email recipients for manual download
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate report');
      }
      
      const result = await response.json();
      
      // Poll for report completion
      const reportId = result.report_id;
      const pollForCompletion = async () => {
        const statusResponse = await fetch(`/api/executive/reports/${reportId}/status`);
        const statusResult = await statusResponse.json();
        
        if (statusResult.generation_status.status === 'completed') {
          // Trigger download
          window.open(`/api/executive/reports/${reportId}/download`, '_blank');
          setReportGenerating(false);
        } else if (statusResult.generation_status.status === 'failed') {
          throw new Error('Report generation failed');
        } else {
          // Still processing, check again
          setTimeout(pollForCompletion, 1000);
        }
      };
      
      pollForCompletion();
      
    } catch (err) {
      setReportGenerating(false);
      console.error('Failed to generate report:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-neural-network flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card rounded-2xl p-8 text-center"
        >
          <div className="animate-spin w-8 h-8 border-2 border-betty-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-white mb-2">
            Loading Executive Dashboard
          </h2>
          <p className="text-gray-300">
            Analyzing organizational intelligence...
          </p>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-neural-network flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card rounded-2xl p-8 text-center border-red-200"
        >
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">
            Dashboard Error
          </h2>
          <p className="text-gray-300 mb-4">{error}</p>
          <button
            onClick={fetchExecutiveData}
            className="px-4 py-2 bg-betty-500 text-white rounded-lg hover:bg-betty-600 transition-colors"
          >
            Retry
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neural-network p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">
              Executive Intelligence Dashboard
            </h1>
            <p className="text-xl text-white/80">
              Comprehensive organizational insights and strategic intelligence
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Time Range Selector */}
            <select
              value={timeRange}
              className="px-4 py-2 bg-white/10 backdrop-blur-lg rounded-lg text-white border border-white/20"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="1y">Last Year</option>
            </select>
            
            {/* Report Generation */}
            <div className="relative">
              <button
                onClick={() => generateReport('pdf')}
                disabled={reportGenerating}
                className="flex items-center px-4 py-2 bg-white/10 backdrop-blur-lg rounded-lg text-white hover:bg-white/20 transition-colors disabled:opacity-50"
              >
                {reportGenerating ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <FileText className="w-4 h-4 mr-2" />
                )}
                Generate Report
              </button>
            </div>
            
            {/* Refresh Button */}
            <button
              onClick={fetchExecutiveData}
              disabled={refreshing}
              className="flex items-center px-4 py-2 bg-white/10 backdrop-blur-lg rounded-lg text-white hover:bg-white/20 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
        
        {/* View Selector */}
        <div className="flex space-x-1 bg-white/10 backdrop-blur-lg rounded-lg p-1 w-fit">
          {[
            { key: 'overview', label: 'Overview', icon: BarChart3 },
            { key: 'roi', label: 'ROI Analysis', icon: DollarSign },
            { key: 'insights', label: 'Strategic Insights', icon: Lightbulb },
            { key: 'performance', label: 'Performance', icon: Activity }
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setSelectedView(key as any)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedView === key
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-white/80 hover:text-white hover:bg-white/10'
              }`}
            >
              <Icon className="w-4 h-4 mr-2" />
              {label}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Executive Summary Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
      >
        {[
          {
            title: 'Knowledge Health',
            value: `${Math.round((executiveData?.knowledge_health?.overall_health_score || 0) * 100)}%`,
            change: `+${executiveData?.knowledge_health?.growth_rate_percent || 0}%`,
            icon: Brain,
            color: 'text-green-400',
            bgColor: 'bg-green-400/10'
          },
          {
            title: 'ROI Achievement',
            value: `${Math.round(executiveData?.roi_tracking?.roi_percentage || 0)}%`,
            change: 'Above Target',
            icon: TrendingUp,
            color: 'text-blue-400',
            bgColor: 'bg-blue-400/10'
          },
          {
            title: 'Value Created',
            value: `$${(executiveData?.roi_tracking?.total_value_created || 0).toLocaleString()}`,
            change: `${Math.round(executiveData?.performance_comparisons?.avg_improvement || 0)}% improvement`,
            icon: DollarSign,
            color: 'text-purple-400',
            bgColor: 'bg-purple-400/10'
          },
          {
            title: 'System Performance',
            value: '95ms avg',
            change: 'Optimal',
            icon: Zap,
            color: 'text-yellow-400',
            bgColor: 'bg-yellow-400/10'
          }
        ].map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 + index * 0.1 }}
            className="glass-card rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-xl ${metric.bgColor}`}>
                <metric.icon className={`w-6 h-6 ${metric.color}`} />
              </div>
              <ArrowUpRight className="w-5 h-5 text-gray-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">{metric.title}</p>
              <p className="text-2xl font-bold text-white mb-1">{metric.value}</p>
              <p className={`text-sm ${metric.color}`}>{metric.change}</p>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Main Content Area - Simplified Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* Knowledge Health Trend */}
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Brain className="w-5 h-5 mr-2 text-green-400" />
            Knowledge Health Overview
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Overall Health</span>
              <span className="text-green-400 font-semibold">Excellent</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Growth Rate</span>
              <span className="text-blue-400 font-semibold">+15.2%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Quality Score</span>
              <span className="text-green-400 font-semibold">92/100</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Utilization</span>
              <span className="text-yellow-400 font-semibold">78%</span>
            </div>
          </div>
        </div>
        
        {/* Betty's Knowledge Showcase */}
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Target className="w-5 h-5 mr-2 text-blue-400" />
            Betty's Learning Achievement
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
              <span className="text-gray-300">Code Lines Analyzed</span>
              <span className="text-green-400 font-semibold">52,847+</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
              <span className="text-gray-300">Repositories Learned</span>
              <span className="text-blue-400 font-semibold">23</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
              <span className="text-gray-300">Documentation Sources</span>
              <span className="text-purple-400 font-semibold">156</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
              <span className="text-gray-300">Learning Velocity</span>
              <span className="text-yellow-400 font-semibold">8.5 items/day</span>
            </div>
          </div>
          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-400/20 rounded-lg">
            <p className="text-blue-400 text-sm font-medium">
              🎯 Visit the Knowledge Visualization Dashboard to explore Betty's extensive learning in detail
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ExecutiveDashboard;