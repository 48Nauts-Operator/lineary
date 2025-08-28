import React from 'react'
import { motion } from 'framer-motion'
import { Brain, Target, Search, Lightbulb, TrendingUp } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts'
import { IntelligenceMetricsData } from '../../services/api'

interface IntelligenceMetricsProps {
  data?: IntelligenceMetricsData
}

const IntelligenceMetrics: React.FC<IntelligenceMetricsProps> = ({ data }) => {
  if (!data) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass-card rounded-2xl p-6"
      >
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </motion.div>
    )
  }

  // Prepare chart data for intelligence growth
  const chartData = data.intelligence_growth_trend.map(point => ({
    date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    score: point.value,
  }))

  const metrics = [
    {
      title: 'Overall Intelligence',
      value: data.overall_intelligence_score,
      max: 10,
      icon: Brain,
      color: 'betty',
      description: 'Comprehensive intelligence assessment',
    },
    {
      title: 'Pattern Recognition',
      value: data.pattern_recognition_accuracy * 100,
      max: 100,
      icon: Target,
      color: 'success',
      description: 'Accuracy in identifying patterns',
      suffix: '%',
    },
    {
      title: 'Search Accuracy',
      value: data.search_response_accuracy * 100,
      max: 100,
      icon: Search,
      color: 'purple',
      description: 'Relevance of search results',
      suffix: '%',
    },
    {
      title: 'Context Relevance',
      value: data.context_relevance_score * 100,
      max: 100,
      icon: Lightbulb,
      color: 'warning',
      description: 'Quality of contextual understanding',
      suffix: '%',
    },
  ]

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'betty':
        return {
          bg: 'bg-betty-500',
          text: 'text-betty-600',
          light: 'bg-betty-100',
        }
      case 'success':
        return {
          bg: 'bg-success-500',
          text: 'text-success-600',
          light: 'bg-success-100',
        }
      case 'purple':
        return {
          bg: 'bg-purple-500',
          text: 'text-purple-600',
          light: 'bg-purple-100',
        }
      case 'warning':
        return {
          bg: 'bg-warning-500',
          text: 'text-warning-600',
          light: 'bg-warning-100',
        }
      default:
        return {
          bg: 'bg-gray-500',
          text: 'text-gray-600',
          light: 'bg-gray-100',
        }
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Intelligence Metrics
            </h3>
            <p className="text-sm text-gray-500">
              Quality assessment of BETTY's capabilities
            </p>
          </div>
        </div>

        {/* Overall Score Badge */}
        <div className="text-center">
          <div className="text-2xl font-bold text-indigo-600">
            {Math.round(data.overall_intelligence_score * 10) / 10}
          </div>
          <div className="text-xs text-gray-500">/ 10</div>
        </div>
      </div>

      {/* Intelligence Growth Chart */}
      <div className="h-32 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 10, fill: '#6B7280' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#6366F1"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3, fill: '#6366F1' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Metric Cards */}
      <div className="space-y-4 mb-6">
        {metrics.map((metric, index) => {
          const colors = getColorClasses(metric.color)
          const Icon = metric.icon
          const percentage = (metric.value / metric.max) * 100

          return (
            <motion.div
              key={metric.title}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 + index * 0.1 }}
              className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Icon className={`w-4 h-4 ${colors.text}`} />
                  <span className="text-sm font-medium text-gray-700">
                    {metric.title}
                  </span>
                </div>
                <span className="text-sm font-semibold text-gray-700">
                  {Math.round(metric.value * 10) / 10}{metric.suffix || ''}
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ delay: 0.8 + index * 0.1, duration: 0.5 }}
                  className={`h-2 rounded-full ${colors.bg}`}
                />
              </div>
              
              <p className="text-xs text-gray-500">
                {metric.description}
              </p>
            </motion.div>
          )
        })}
      </div>

      {/* Performance Improvements */}
      <div className="border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium text-gray-600 mb-3 flex items-center">
          <TrendingUp className="w-4 h-4 mr-1 text-success-500" />
          Performance Improvements
        </h4>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-success-50 rounded-lg border border-success-200">
            <div className="text-lg font-semibold text-success-600">
              +{Math.round(data.problem_solving_speed_improvement)}%
            </div>
            <div className="text-xs text-gray-600">
              Problem Solving Speed
            </div>
          </div>
          
          <div className="text-center p-3 bg-betty-50 rounded-lg border border-betty-200">
            <div className="text-lg font-semibold text-betty-600">
              {Math.round(data.knowledge_reuse_rate * 100)}%
            </div>
            <div className="text-xs text-gray-600">
              Knowledge Reuse Rate
            </div>
          </div>
        </div>
      </div>

      {/* Quality Score */}
      <div className="mt-4 p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-700">
              Knowledge Quality Score
            </h4>
            <p className="text-xs text-gray-500">
              Assessment of knowledge base quality
            </p>
          </div>
          <div className="text-right">
            <div className="text-xl font-bold text-indigo-600">
              {Math.round(data.knowledge_quality_score * 10) / 10}
            </div>
            <div className="text-xs text-gray-500">/ 10</div>
          </div>
        </div>
      </div>

      {/* Cross-Project Applicability */}
      <div className="mt-3 p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-700">
              Cross-Project Applicability
            </h4>
            <p className="text-xs text-gray-500">
              How well knowledge applies across projects
            </p>
          </div>
          <div className="text-right">
            <div className="text-xl font-bold text-purple-600">
              {Math.round(data.cross_project_applicability * 100)}%
            </div>
            <div className="text-xs text-gray-500">applicability</div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default IntelligenceMetrics