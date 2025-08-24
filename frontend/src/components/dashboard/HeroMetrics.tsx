import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Brain, Zap, CheckCircle, ArrowUpRight } from 'lucide-react'
import { DashboardSummaryData } from '../../services/api'

interface HeroMetricsProps {
  data?: DashboardSummaryData
}

const HeroMetrics: React.FC<HeroMetricsProps> = ({ data }) => {
  const metrics = [
    {
      title: 'Knowledge Items',
      value: data?.total_knowledge_items?.toLocaleString() || '0',
      change: `+${Math.round((data?.growth_rate_daily || 0) * 10) / 10}%`,
      changeLabel: 'daily growth',
      icon: Brain,
      color: 'betty',
      sparkline: data?.knowledge_growth_7d || [],
    },
    {
      title: 'Intelligence Score',
      value: `${Math.round((data?.intelligence_score || 0) * 10) / 10}/10`,
      change: '+2.3%',
      changeLabel: 'vs last week',
      icon: Zap,
      color: 'purple',
      trend: 'up',
    },
    {
      title: 'Response Time',
      value: `${Math.round(data?.avg_response_time_ms || 0)}ms`,
      change: '-15.2%',
      changeLabel: 'improvement',
      icon: TrendingUp,
      color: 'success',
      sparkline: data?.performance_trend_24h?.slice(-7) || [],
    },
    {
      title: 'System Health',
      value: data?.system_health_status === 'operational' ? 'Optimal' : 'Checking',
      change: '99.85%',
      changeLabel: 'uptime',
      icon: CheckCircle,
      color: 'success',
      pulse: data?.system_health_status === 'operational',
    },
  ]

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'betty':
        return {
          gradient: 'from-betty-500 to-betty-600',
          text: 'text-betty-600',
          bg: 'bg-betty-50',
          border: 'border-betty-200',
        }
      case 'purple':
        return {
          gradient: 'from-purple-500 to-purple-600',
          text: 'text-purple-600',
          bg: 'bg-purple-50',
          border: 'border-purple-200',
        }
      case 'success':
        return {
          gradient: 'from-success-500 to-success-600',
          text: 'text-success-600',
          bg: 'bg-success-50',
          border: 'border-success-200',
        }
      default:
        return {
          gradient: 'from-gray-500 to-gray-600',
          text: 'text-gray-600',
          bg: 'bg-gray-50',
          border: 'border-gray-200',
        }
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {metrics.map((metric, index) => {
        const colors = getColorClasses(metric.color)
        const Icon = metric.icon

        return (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.02, y: -2 }}
            className={`hero-metric ${colors.border} relative overflow-hidden group cursor-pointer`}
          >
            {/* Background Gradient */}
            <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
            
            {/* Content */}
            <div className="relative z-10">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className={`p-2 ${colors.bg} rounded-lg ${metric.pulse ? 'animate-pulse-glow' : ''}`}>
                  <Icon className={`w-5 h-5 ${colors.text}`} />
                </div>
                <ArrowUpRight className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>

              {/* Value */}
              <div className="mb-2">
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {metric.value}
                </div>
                <div className="text-sm font-medium text-gray-500">
                  {metric.title}
                </div>
              </div>

              {/* Change Indicator */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <span className={`text-sm font-medium ${
                    metric.change.startsWith('+') || metric.change.includes('improvement') 
                      ? 'text-success-600' 
                      : metric.change.startsWith('-') 
                        ? 'text-success-600' // Negative response time is good
                        : 'text-gray-600'
                  }`}>
                    {metric.change}
                  </span>
                  <span className="text-xs text-gray-500">
                    {metric.changeLabel}
                  </span>
                </div>

                {/* Mini Sparkline */}
                {metric.sparkline && metric.sparkline.length > 0 && (
                  <div className="flex items-end space-x-0.5 h-6">
                    {metric.sparkline.slice(-7).map((value, i) => {
                      const maxValue = Math.max(...metric.sparkline!)
                      const height = Math.max(2, (value / maxValue) * 20)
                      return (
                        <div
                          key={i}
                          className={`w-1 bg-gradient-to-t ${colors.gradient} rounded-full opacity-70`}
                          style={{ height: `${height}px` }}
                        />
                      )
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Hover Effect */}
            <div className="absolute inset-0 border-2 border-transparent group-hover:border-white/20 rounded-2xl transition-colors" />
          </motion.div>
        )
      })}
    </div>
  )
}

export default HeroMetrics