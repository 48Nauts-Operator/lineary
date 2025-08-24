import React from 'react'
import { motion } from 'framer-motion'
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { TrendingUp, Database, MessageSquare, Code, FileText, Settings } from 'lucide-react'
import { format } from 'date-fns'
import { KnowledgeGrowthData } from '../../services/api'

interface KnowledgeGrowthChartProps {
  data?: KnowledgeGrowthData
}

const KnowledgeGrowthChart: React.FC<KnowledgeGrowthChartProps> = ({ data }) => {
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
  const chartData = data.daily_growth.map(point => ({
    date: format(new Date(point.timestamp), 'MMM dd'),
    value: point.value,
    dailyIncrement: point.metadata?.daily_increment || 0,
  }))

  // Knowledge type icons
  const typeIcons = {
    conversation: MessageSquare,
    solution: Database,
    code_pattern: Code,
    decision: Settings,
    documentation: FileText,
  }

  // Calculate projections
  const projections = data.projections || {}
  const projectionData = [
    { period: '7 days', value: projections['7_day'] || 0, color: 'bg-betty-500' },
    { period: '30 days', value: projections['30_day'] || 0, color: 'bg-purple-500' },
    { period: '90 days', value: projections['90_day'] || 0, color: 'bg-pink-500' },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-betty-500 to-purple-600 rounded-lg">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Knowledge Base Growth
            </h3>
            <p className="text-sm text-gray-500">
              {data.total_knowledge_items.toLocaleString()} total items • 
              +{Math.round(data.growth_rate_percentage * 10) / 10}% growth rate
            </p>
          </div>
        </div>
        
        {/* Growth Rate Badge */}
        <div className="flex items-center space-x-2 bg-success-50 px-3 py-1 rounded-full border border-success-200">
          <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium text-success-700">
            Growing
          </span>
        </div>
      </div>

      {/* Main Chart */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="knowledgeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12, fill: '#6B7280' }}
              axisLine={{ stroke: '#E5E7EB' }}
            />
            <YAxis 
              tick={{ fontSize: 12, fill: '#6B7280' }}
              axisLine={{ stroke: '#E5E7EB' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(17, 24, 39, 0.9)',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                borderRadius: '8px',
                backdropFilter: 'blur(10px)',
              }}
              labelStyle={{ color: '#F9FAFB' }}
              itemStyle={{ color: '#93C5FD' }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#knowledgeGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Knowledge Types Breakdown */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        {Object.entries(data.knowledge_by_type).map(([type, count]) => {
          const Icon = typeIcons[type as keyof typeof typeIcons] || Database
          const percentage = (count / data.total_knowledge_items) * 100

          return (
            <motion.div
              key={type}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-br from-white to-gray-50 p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className="w-4 h-4 text-betty-600" />
                <span className="text-xs text-gray-500">
                  {Math.round(percentage)}%
                </span>
              </div>
              <div className="text-lg font-semibold text-gray-700">
                {count.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500 capitalize">
                {type.replace('_', ' ')}
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Growth Projections */}
      <div className="border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium text-gray-600 mb-3">Growth Projections</h4>
        <div className="grid grid-cols-3 gap-4">
          {projectionData.map((projection, index) => (
            <motion.div
              key={projection.period}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              className="text-center"
            >
              <div className="text-lg font-semibold text-gray-700">
                {Math.round(projection.value).toLocaleString()}
              </div>
              <div className="text-xs text-gray-500 mb-2">
                {projection.period}
              </div>
              <div className={`h-1 ${projection.color} rounded-full mx-auto`} style={{ width: '60%' }} />
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default KnowledgeGrowthChart