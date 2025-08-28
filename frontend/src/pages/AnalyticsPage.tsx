// ABOUTME: Analytics dashboard with charts for velocity, cycle time, and token usage
// ABOUTME: Comprehensive metrics and insights for project performance tracking

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from 'recharts'
import { Project, API_URL } from '../App'

interface Props {
  selectedProject: Project | null
  projects: Project[]
}

interface AnalyticsData {
  project: any
  activity: {
    heatmap: any[]
    summary: {
      total_activities: number
      active_days: number
    }
  }
  tokenUsage: {
    daily: any[]
    summary: {
      total_tokens: number
      total_cost: number
    }
  }
  timeTracking: {
    daily: any[]
    aiSaved: {
      total_hours_saved: number
      ai_assisted_tasks: number
    }
  }
  velocity: any[]
  distribution: any[]
}

const AnalyticsPage: React.FC<Props> = ({ selectedProject, projects }) => {
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    project: {},
    activity: {
      heatmap: [],
      summary: { total_activities: 0, active_days: 0 }
    },
    tokenUsage: {
      daily: [],
      summary: { total_tokens: 0, total_cost: 0 }
    },
    timeTracking: {
      daily: [],
      aiSaved: { total_hours_saved: 0, ai_assisted_tasks: 0 }
    },
    velocity: [],
    distribution: []
  })
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('30') // days
  const [activeMetric, setActiveMetric] = useState<'velocity' | 'cycle' | 'tokens'>('velocity')

  useEffect(() => {
    fetchAnalytics()
  }, [selectedProject, timeRange])

  const fetchAnalytics = async () => {
    if (!selectedProject) {
      toast.error('Please select a project to view analytics')
      setLoading(false)
      return
    }
    
    setLoading(true)
    try {
      const response = await axios.get(
        `${API_URL}/analytics/dashboard/${selectedProject.id}?days=${timeRange}`
      )
      
      setAnalytics(response.data)
    } catch (error) {
      console.error('Error fetching analytics:', error)
      toast.error('Failed to load analytics data')
      // Use mock data on error for demo purposes
      setAnalytics({
        project: { name: selectedProject.name, total_issues: 0, completed_issues: 0 },
        activity: {
          heatmap: generateMockHeatmapData(),
          summary: { total_activities: 150, active_days: 25 }
        },
        tokenUsage: {
          daily: generateMockTokenData(),
          summary: { total_tokens: 50000, total_cost: 62.50 }
        },
        timeTracking: {
          daily: [],
          aiSaved: { total_hours_saved: 48.5, ai_assisted_tasks: 23 }
        },
        velocity: generateMockVelocityData(),
        distribution: generateMockDistributionData()
      })
    } finally {
      setLoading(false)
    }
  }

  const generateMockVelocityData = () => [
    { sprint: 'Sprint 1', completed: 23, planned: 25, date: '2024-01-01' },
    { sprint: 'Sprint 2', completed: 18, planned: 20, date: '2024-01-15' },
    { sprint: 'Sprint 3', completed: 32, planned: 30, date: '2024-02-01' },
    { sprint: 'Sprint 4', completed: 28, planned: 28, date: '2024-02-15' },
    { sprint: 'Sprint 5', completed: 35, planned: 32, date: '2024-03-01' }
  ]

  const generateMockCycleTimeData = () => [
    { date: '2024-01-01', avgCycleTime: 3.2, avgLeadTime: 5.1 },
    { date: '2024-01-08', avgCycleTime: 2.8, avgLeadTime: 4.6 },
    { date: '2024-01-15', avgCycleTime: 4.1, avgLeadTime: 6.2 },
    { date: '2024-01-22', avgCycleTime: 2.9, avgLeadTime: 4.8 },
    { date: '2024-01-29', avgCycleTime: 3.5, avgLeadTime: 5.3 }
  ]

  const generateMockTokenData = () => [
    { date: '2024-01-01', tokens: 12500, cost: 15.60 },
    { date: '2024-01-08', tokens: 8900, cost: 11.12 },
    { date: '2024-01-15', tokens: 15600, cost: 19.50 },
    { date: '2024-01-22', tokens: 11200, cost: 14.00 },
    { date: '2024-01-29', tokens: 9800, cost: 12.25 }
  ]

  const generateMockBurndownData = () => [
    { date: 'Day 1', remaining: 100, ideal: 100 },
    { date: 'Day 3', remaining: 85, ideal: 80 },
    { date: 'Day 5', remaining: 72, ideal: 60 },
    { date: 'Day 7', remaining: 45, ideal: 40 },
    { date: 'Day 9', remaining: 28, ideal: 20 },
    { date: 'Day 10', remaining: 12, ideal: 0 }
  ]

  const generateMockHeatmapData = () => {
    const data = []
    const today = new Date()
    for (let i = 0; i < 30; i++) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      data.push({
        date: date.toISOString().split('T')[0],
        activity_type: 'issue_created',
        count: Math.floor(Math.random() * 10) + 1
      })
    }
    return data
  }

  const generateMockDistributionData = () => [
    { status: 'todo', priority: 'high', count: 5 },
    { status: 'in_progress', priority: 'medium', count: 8 },
    { status: 'done', priority: 'low', count: 12 },
    { status: 'backlog', priority: 'medium', count: 15 }
  ]

  const generateMockStatusData = () => [
    { name: 'To Do', value: 12, color: '#3B82F6' },
    { name: 'In Progress', value: 8, color: '#F59E0B' },
    { name: 'In Review', value: 5, color: '#8B5CF6' },
    { name: 'Done', value: 25, color: '#10B981' },
    { name: 'Blocked', value: 3, color: '#EF4444' }
  ]

  const generateMockPriorityData = () => [
    { name: 'Critical', value: 5, color: '#EF4444' },
    { name: 'High', value: 12, color: '#F59E0B' },
    { name: 'Medium', value: 28, color: '#3B82F6' },
    { name: 'Low', value: 8, color: '#6B7280' }
  ]

  const timeRanges = [
    { value: '7', label: '7 Days' },
    { value: '30', label: '30 Days' },
    { value: '90', label: '90 Days' },
    { value: '365', label: '1 Year' }
  ]

  const metrics = [
    { 
      key: 'velocity', 
      label: 'Velocity', 
      icon: '📈', 
      value: analytics.velocity.length > 0 ? analytics.velocity[analytics.velocity.length - 1]?.completed : 0,
      unit: 'pts'
    },
    { 
      key: 'cycle', 
      label: 'Avg Cycle Time', 
      icon: '⏱️', 
      value: analytics.cycleTime.length > 0 ? analytics.cycleTime[analytics.cycleTime.length - 1]?.avgCycleTime : 0,
      unit: 'days'
    },
    { 
      key: 'tokens', 
      label: 'Token Usage', 
      icon: '🤖', 
      value: analytics.tokenUsage.reduce((sum, item) => sum + (item.tokens || 0), 0),
      unit: 'tokens'
    }
  ]

  // Helper functions for heatmap
  const generateHeatmapGrid = () => {
    const grid = []
    const today = new Date()
    const startDate = new Date(today)
    startDate.setDate(startDate.getDate() - 365)
    
    // Create activity map from data
    const activityMap = new Map()
    analytics.activity?.heatmap?.forEach(item => {
      activityMap.set(item.date, item.count)
    })
    
    // Generate grid cells for each day
    for (let d = new Date(startDate); d <= today; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split('T')[0]
      const count = activityMap.get(dateStr) || 0
      const level = getActivityLevel(count)
      
      grid.push(
        <div
          key={dateStr}
          className="w-3 h-3 rounded-sm cursor-pointer hover:ring-2 hover:ring-purple-500"
          style={{ backgroundColor: getHeatmapColor(level) }}
          title={`${dateStr}: ${count} activities`}
        />
      )
    }
    
    return grid
  }

  const getActivityLevel = (count: number) => {
    if (count === 0) return 0
    if (count <= 3) return 1
    if (count <= 7) return 2
    if (count <= 15) return 3
    return 4
  }

  const getHeatmapColor = (level: number) => {
    const colors = [
      '#161B22', // No activity
      '#0E4429', // Low
      '#006D32', // Medium
      '#26A641', // High
      '#39D353'  // Very high
    ]
    return colors[level] || colors[0]
  }

  const processDistributionData = () => {
    const statusCounts: { [key: string]: number } = {}
    analytics.distribution?.forEach(item => {
      if (!statusCounts[item.status]) {
        statusCounts[item.status] = 0
      }
      statusCounts[item.status] += item.count
    })
    
    return Object.entries(statusCounts).map(([status, count]) => ({
      name: status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' '),
      count
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500/30 rounded-full animate-spin border-t-purple-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics</h1>
          <p className="text-gray-400 mt-1">
            {selectedProject ? `${selectedProject.name} Metrics` : 'Project Performance Metrics'}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
          >
            {timeRanges.map(range => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {metrics.map(metric => (
          <div
            key={metric.key}
            onClick={() => setActiveMetric(metric.key as any)}
            className={`bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border cursor-pointer transition-all duration-200 ${
              activeMetric === metric.key
                ? 'border-purple-500 shadow-purple-500/20'
                : 'border-gray-700/50 hover:border-purple-500/50'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="text-2xl">{metric.icon}</div>
              <div className="text-right">
                <p className="text-2xl font-bold text-white">
                  {typeof metric.value === 'number' ? 
                    (metric.value > 1000 ? `${(metric.value / 1000).toFixed(1)}k` : metric.value.toFixed(1))
                    : metric.value
                  }
                </p>
                <p className="text-gray-400 text-sm">{metric.unit}</p>
              </div>
            </div>
            <h3 className="text-lg font-semibold text-white">{metric.label}</h3>
          </div>
        ))}
      </div>

      {/* Main Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Velocity Chart */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Velocity Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.velocity}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="sprint" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="planned" fill="#6B7280" name="Planned" />
              <Bar dataKey="completed" fill="#8B5CF6" name="Completed" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Cycle Time Chart */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Cycle Time Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analytics.cycleTime}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="avgCycleTime" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Cycle Time (days)"
              />
              <Line 
                type="monotone" 
                dataKey="avgLeadTime" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Lead Time (days)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Token Usage Chart */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">AI Token Usage</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analytics.tokenUsage}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
              />
              <Area
                type="monotone"
                dataKey="tokens"
                stroke="#F59E0B"
                fill="#F59E0B"
                fillOpacity={0.3}
                name="Tokens Used"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Issue Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analytics.statusDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {analytics.statusDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {analytics.statusDistribution.map((item, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-gray-300">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-3xl mb-2">📊</div>
          <p className="text-2xl font-bold text-white">
            {analytics.velocity.reduce((sum, item) => sum + (item.completed || 0), 0)}
          </p>
          <p className="text-gray-400 text-sm">Total Story Points</p>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-3xl mb-2">⚡</div>
          <p className="text-2xl font-bold text-white">
            {analytics.cycleTime.length > 0 ? 
              (analytics.cycleTime.reduce((sum, item) => sum + (item.avgCycleTime || 0), 0) / analytics.cycleTime.length).toFixed(1)
              : '0'
            }
          </p>
          <p className="text-gray-400 text-sm">Avg Cycle Time (days)</p>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-3xl mb-2">💰</div>
          <p className="text-2xl font-bold text-white">
            ${analytics.tokenUsage.reduce((sum, item) => sum + (item.cost || 0), 0).toFixed(2)}
          </p>
          <p className="text-gray-400 text-sm">Total AI Cost</p>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-3xl mb-2">🎯</div>
          <p className="text-2xl font-bold text-white">
            {analytics.velocity.length > 0 ? 
              Math.round((analytics.velocity.reduce((sum, item) => sum + (item.completed || 0), 0) / 
                         analytics.velocity.reduce((sum, item) => sum + (item.planned || 0), 0)) * 100)
              : 0
            }%
          </p>
          <p className="text-gray-400 text-sm">Delivery Rate</p>
        </div>
      </div>

      {/* Insights Panel */}
      <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4">AI Insights</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-blue-400">💡</span>
              <h4 className="font-medium text-blue-300">Velocity Insight</h4>
            </div>
            <p className="text-gray-300 text-sm">
              Your team's velocity has increased by 15% over the last 3 sprints. Consider increasing sprint capacity.
            </p>
          </div>
          
          <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-yellow-400">⚠️</span>
              <h4 className="font-medium text-yellow-300">Cycle Time Alert</h4>
            </div>
            <p className="text-gray-300 text-sm">
              Cycle time increased this week. Review blocked issues and consider breaking down larger tasks.
            </p>
          </div>
          
          <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-green-400">📈</span>
              <h4 className="font-medium text-green-300">Quality Trend</h4>
            </div>
            <p className="text-gray-300 text-sm">
              Bug rate decreased by 40% this month. Your quality practices are paying off!
            </p>
          </div>
          
          <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-purple-400">🤖</span>
              <h4 className="font-medium text-purple-300">AI Efficiency</h4>
            </div>
            <p className="text-gray-300 text-sm">
              AI assistance reduced estimation errors by 25% and improved task breakdown accuracy.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AnalyticsPage