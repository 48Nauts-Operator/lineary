// ABOUTME: Guardian Monitor Component - Real-time monitoring of Betty Guardian activity
// ABOUTME: Displays statistics, recent activity, and charts for the main dashboard

import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface GuardianStats {
  total_requests: number;
  blocked_count: number;
  warned_count: number;
  approved_count: number;
  avg_response_time: number;
}

interface GuardianActivity {
  id: string;
  timestamp: string;
  tool_name: string;
  decision: string;
  rule_triggered?: string;
  reason?: string;
  response_time_ms?: number;
}

const GuardianMonitor: React.FC = () => {
  const [stats, setStats] = useState<GuardianStats | null>(null);
  const [activities, setActivities] = useState<GuardianActivity[]>([]);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch Guardian stats
  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:4002/api/guardian/stats?timeRange=24h');
      const data = await response.json();
      if (data.success && data.stats?.summary) {
        setStats(data.stats.summary);
      }
    } catch (err) {
      console.error('Failed to fetch Guardian stats:', err);
    }
  };

  // Fetch recent activity
  const fetchActivity = async () => {
    try {
      const response = await fetch('http://localhost:4002/api/guardian/activity?limit=10');
      const data = await response.json();
      if (data.success) {
        setActivities(data.activities);
      }
    } catch (err) {
      console.error('Failed to fetch Guardian activity:', err);
    }
  };

  // Fetch timeline data
  const fetchTimeline = async () => {
    try {
      const response = await fetch('http://localhost:4002/api/guardian/timeline?hours=6');
      const data = await response.json();
      if (data.success) {
        // Convert timeline object to array for chart
        const chartData = Object.entries(data.timeline).map(([hour, counts]: [string, any]) => ({
          time: new Date(hour).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          blocked: counts.blocked || 0,
          warned: counts.warned || 0,
          approved: counts.approved || 0
        })).reverse();
        setTimeline(chartData);
      }
    } catch (err) {
      console.error('Failed to fetch timeline:', err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchStats(), fetchActivity(), fetchTimeline()]);
      setLoading(false);
    };

    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'block':
      case 'blocked':
        return <Shield className="w-4 h-4 text-red-400" />;
      case 'warn':
      case 'warned':
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      default:
        return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'block':
      case 'blocked':
        return 'text-red-400';
      case 'warn':
      case 'warned':
        return 'text-yellow-400';
      default:
        return 'text-green-400';
    }
  };

  // Pie chart data
  const pieData = stats ? [
    { name: 'Blocked', value: stats.blocked_count || 0, color: '#ef4444' },
    { name: 'Warned', value: stats.warned_count || 0, color: '#eab308' },
    { name: 'Approved', value: stats.approved_count || 0, color: '#22c55e' }
  ].filter(d => d.value > 0) : [];

  if (loading) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-lg border-purple-500/20 p-6">
        <div className="flex items-center justify-center">
          <Activity className="w-6 h-6 text-purple-400 animate-pulse" />
          <span className="ml-2 text-gray-400">Loading Guardian data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Shield className="w-8 h-8 text-purple-400" />
        <h2 className="text-2xl font-bold text-white">Betty Guardian Monitor</h2>
      </div>

      {/* Stats divs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800/50 backdrop-blur-lg border-purple-500/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Requests</p>
              <p className="text-2xl font-bold text-white">
                {stats?.total_requests || 0}
              </p>
            </div>
            <Activity className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-lg border-red-500/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Blocked</p>
              <p className="text-2xl font-bold text-red-400">
                {stats?.blocked_count || 0}
              </p>
            </div>
            <Shield className="w-8 h-8 text-red-400" />
          </div>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-lg border-yellow-500/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Warned</p>
              <p className="text-2xl font-bold text-yellow-400">
                {stats?.warned_count || 0}
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-yellow-400" />
          </div>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-lg border-green-500/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Approved</p>
              <p className="text-2xl font-bold text-green-400">
                {stats?.approved_count || 0}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline Chart */}
        <div className="bg-gray-800/50 backdrop-blur-lg border-purple-500/20 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Activity Timeline (6h)</h3>
          {timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #4b5563' }}
                  labelStyle={{ color: '#d1d5db' }}
                />
                <Line type="monotone" dataKey="blocked" stroke="#ef4444" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="warned" stroke="#eab308" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="approved" stroke="#22c55e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-8">No timeline data available</p>
          )}
        </div>

        {/* Decision Distribution */}
        <div className="bg-gray-800/50 backdrop-blur-lg border-purple-500/20 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Decision Distribution</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #4b5563' }}
                  labelStyle={{ color: '#d1d5db' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-8">No decision data available</p>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-gray-800/50 backdrop-blur-lg border-purple-500/20 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {activities.length > 0 ? (
            activities.map((activity) => (
              <div key={activity.id} className="flex items-start gap-3 p-3 bg-gray-700/30 rounded-lg">
                {getDecisionIcon(activity.decision)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{activity.tool_name}</span>
                    <span className={`text-sm ${getDecisionColor(activity.decision)}`}>
                      {activity.decision.toUpperCase()}
                    </span>
                    {activity.rule_triggered && (
                      <span className="text-xs text-purple-400 bg-purple-900/30 px-2 py-1 rounded">
                        {activity.rule_triggered}
                      </span>
                    )}
                  </div>
                  {activity.reason && (
                    <p className="text-sm text-gray-400 mt-1">{activity.reason}</p>
                  )}
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-xs text-gray-500">
                      {new Date(activity.timestamp).toLocaleString()}
                    </span>
                    {activity.response_time_ms && (
                      <span className="text-xs text-gray-500">
                        {activity.response_time_ms}ms
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-400 text-center py-4">No recent activity</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default GuardianMonitor;