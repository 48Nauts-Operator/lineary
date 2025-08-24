import React from 'react'
import { motion } from 'framer-motion'
import { Server, Zap, Database, Cpu, HardDrive, Wifi } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts'
import { SystemPerformanceData } from '../../services/api'

interface SystemPerformanceProps {
  data?: SystemPerformanceData
}

const SystemPerformance: React.FC<SystemPerformanceProps> = ({ data }) => {
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
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </motion.div>
    )
  }

  // Prepare chart data
  const chartData = data.performance_trends.slice(-12).map((point, index) => ({
    time: `${index}h`,
    responseTime: point.value,
  }))

  // Key metrics
  const performanceMetrics = [
    {
      title: 'Response Time',
      value: `${Math.round(data.average_response_time_ms)}ms`,
      icon: Zap,
      color: 'betty',
      status: data.average_response_time_ms < 100 ? 'excellent' : data.average_response_time_ms < 200 ? 'good' : 'warning',
    },
    {
      title: 'Context Loading',
      value: `${Math.round(data.context_loading_time_ms)}ms`,
      icon: Database,
      color: 'success',
      status: data.context_loading_time_ms < 100 ? 'excellent' : 'good',
    },
    {
      title: 'Search Speed',
      value: `${Math.round(data.search_response_time_ms)}ms`,
      icon: Server,
      color: 'purple',
      status: data.search_response_time_ms < 200 ? 'excellent' : 'good',
    },
  ]

  // Resource utilization
  const resourceMetrics = [
    {
      title: 'CPU Usage',
      value: Math.round(data.resource_utilization.cpu_usage * 100),
      icon: Cpu,
      color: 'warning',
    },
    {
      title: 'Memory Usage',
      value: Math.round(data.resource_utilization.memory_usage * 100),
      icon: HardDrive,
      color: 'error',
    },
    {
      title: 'Network I/O',
      value: Math.round(data.resource_utilization.network_io * 100),
      icon: Wifi,
      color: 'success',
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'text-success-600 bg-success-50 border-success-200'
      case 'good':
        return 'text-betty-600 bg-betty-50 border-betty-200'
      case 'warning':
        return 'text-warning-600 bg-warning-50 border-warning-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getResourceColor = (value: number) => {
    if (value < 50) return 'bg-success-500'
    if (value < 75) return 'bg-warning-500'
    return 'bg-error-500'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.7 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-lg">
            <Server className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              System Performance
            </h3>
            <p className="text-sm text-gray-500">
              {Math.round(data.system_uptime_percentage * 100)}% uptime • 
              {Math.round(data.error_rate * 100 * 100) / 100}% error rate
            </p>
          </div>
        </div>

        {/* Health Status */}
        <div className={`px-3 py-1 rounded-full border ${
          data.database_health_score > 0.9 
            ? 'text-success-600 bg-success-50 border-success-200'
            : 'text-warning-600 bg-warning-50 border-warning-200'
        }`}>
          <span className="text-sm font-medium">
            {data.database_health_score > 0.9 ? 'Healthy' : 'Monitoring'}
          </span>
        </div>
      </div>

      {/* Performance Trends Chart */}
      <div className="h-24 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 10, fill: '#6B7280' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide />
            <Line
              type="monotone"
              dataKey="responseTime"
              stroke="#10B981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 2, fill: '#10B981' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Performance Metrics */}
      <div className="space-y-3 mb-6">
        {performanceMetrics.map((metric, index) => {
          const Icon = metric.icon

          return (
            <motion.div
              key={metric.title}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 + index * 0.1 }}
              className={`flex items-center justify-between p-3 rounded-lg border ${getStatusColor(metric.status)}`}
            >
              <div className="flex items-center space-x-2">
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {metric.title}
                </span>
              </div>
              <span className="text-sm font-semibold">
                {metric.value}
              </span>
            </motion.div>
          )
        })}
      </div>

      {/* Resource Utilization */}
      <div className="border-t border-gray-200 pt-4 mb-6">
        <h4 className="text-sm font-medium text-gray-600 mb-3">Resource Utilization</h4>
        <div className="space-y-3">
          {resourceMetrics.map((resource, index) => {
            const Icon = resource.icon

            return (
              <motion.div
                key={resource.title}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.9 + index * 0.1 }}
                className="flex items-center justify-between"
              >
                <div className="flex items-center space-x-2 flex-1">
                  <Icon className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600">{resource.title}</span>
                </div>
                
                <div className="flex items-center space-x-2 flex-1">
                  <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-20">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${resource.value}%` }}
                      transition={{ delay: 1 + index * 0.1, duration: 0.5 }}
                      className={`h-2 rounded-full ${getResourceColor(resource.value)}`}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-700 min-w-10 text-right">
                    {resource.value}%
                  </span>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Throughput Metrics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-3 bg-betty-50 rounded-lg border border-betty-200">
          <div className="text-lg font-semibold text-betty-600">
            {data.throughput_metrics.requests_per_second || 0}
          </div>
          <div className="text-xs text-gray-600">req/sec</div>
        </div>
        
        <div className="text-center p-3 bg-success-50 rounded-lg border border-success-200">
          <div className="text-lg font-semibold text-success-600">
            {Math.round((data.throughput_metrics.cache_hit_rate || 0) * 100)}%
          </div>
          <div className="text-xs text-gray-600">cache hit</div>
        </div>
      </div>

      {/* System Stats */}
      <div className="mt-4 p-3 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg border border-emerald-200">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-sm font-semibold text-emerald-600">
              {data.knowledge_ingestion_rate_per_hour || 0}/hr
            </div>
            <div className="text-xs text-gray-600">Knowledge Ingestion</div>
          </div>
          <div>
            <div className="text-sm font-semibold text-teal-600">
              {Math.round(data.database_health_score * 100)}%
            </div>
            <div className="text-xs text-gray-600">DB Health</div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default SystemPerformance