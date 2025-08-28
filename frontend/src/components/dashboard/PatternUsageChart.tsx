import React from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Repeat, Clock, TrendingUp, Award } from 'lucide-react'
import { PatternUsageData } from '../../services/api'

interface PatternUsageChartProps {
  data?: PatternUsageData
}

const PatternUsageChart: React.FC<PatternUsageChartProps> = ({ data }) => {
  if (!data) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass-card rounded-2xl p-6"
      >
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </motion.div>
    )
  }

  // Prepare chart data
  const chartData = data.hot_patterns.slice(0, 6).map(pattern => ({
    name: pattern.pattern_name.length > 20 
      ? pattern.pattern_name.substring(0, 20) + '...' 
      : pattern.pattern_name,
    fullName: pattern.pattern_name,
    usage: pattern.usage_count,
    success: Math.round(pattern.success_rate * 100),
    projects: pattern.projects_used.length,
    timeHours: pattern.avg_implementation_time_hours || 0,
    improvement: pattern.performance_improvement || 0,
  }))

  // Top pattern for highlight
  const topPattern = data.hot_patterns[0]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-success-500 to-teal-600 rounded-lg">
            <Repeat className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Pattern Usage & Success Rates
            </h3>
            <p className="text-sm text-gray-500">
              {data.total_patterns_identified} patterns identified • 
              {Math.round(data.time_savings_total_hours)} hours saved
            </p>
          </div>
        </div>

        {/* Success Rate Badge */}
        <div className="flex items-center space-x-2 bg-success-50 px-3 py-1 rounded-full border border-success-200">
          <Award className="w-3 h-3 text-success-600" />
          <span className="text-sm font-medium text-success-700">
            High Success Rate
          </span>
        </div>
      </div>

      {/* Top Pattern Highlight */}
      {topPattern && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-r from-success-50 via-teal-50 to-betty-50 p-4 rounded-lg border border-success-200 mb-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-gray-700 mb-1">
                🏆 Most Successful Pattern
              </h4>
              <p className="text-sm text-gray-600 mb-2">
                {topPattern.pattern_name}
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>Used {topPattern.usage_count}x</span>
                <span>{Math.round(topPattern.success_rate * 100)}% success</span>
                <span>{topPattern.projects_used.join(', ')}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-success-600">
                {Math.round(topPattern.success_rate * 100)}%
              </div>
              <div className="text-xs text-gray-500">success rate</div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Usage Chart */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis 
              dataKey="name" 
              tick={{ fontSize: 11, fill: '#6B7280' }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              tick={{ fontSize: 12, fill: '#6B7280' }}
              axisLine={{ stroke: '#E5E7EB' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(17, 24, 39, 0.9)',
                border: '1px solid rgba(34, 197, 94, 0.2)',
                borderRadius: '8px',
                backdropFilter: 'blur(10px)',
              }}
              labelStyle={{ color: '#F9FAFB' }}
            />
            <Bar 
              dataKey="usage" 
              fill="#10B981" 
              radius={[4, 4, 0, 0]}
              opacity={0.8}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Pattern Categories */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Object.entries(data.success_rate_by_category).map(([category, rate]) => (
          <motion.div
            key={category}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="text-center p-3 bg-white rounded-lg border border-gray-200"
          >
            <div className="text-lg font-semibold text-gray-700">
              {Math.round(rate * 100)}%
            </div>
            <div className="text-xs text-gray-500 capitalize">
              {category.replace('_', ' ')}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Pattern Details */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-600">Pattern Performance</h4>
        {data.hot_patterns.slice(0, 3).map((pattern, index) => (
          <motion.div
            key={pattern.pattern_name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 + index * 0.1 }}
            className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-50 to-white rounded-lg border border-gray-200"
          >
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-700 mb-1">
                {pattern.pattern_name}
              </div>
              <div className="flex items-center space-x-3 text-xs text-gray-500">
                <span className="flex items-center">
                  <Repeat className="w-3 h-3 mr-1" />
                  {pattern.usage_count}x
                </span>
                {pattern.avg_implementation_time_hours && (
                  <span className="flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {pattern.avg_implementation_time_hours}h avg
                  </span>
                )}
                {pattern.performance_improvement && (
                  <span className="flex items-center text-success-600">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    +{Math.round(pattern.performance_improvement)}%
                  </span>
                )}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold text-success-600">
                {Math.round(pattern.success_rate * 100)}%
              </div>
              <div className="text-xs text-gray-500">success</div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

export default PatternUsageChart