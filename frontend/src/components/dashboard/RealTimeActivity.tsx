import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Clock, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { RealTimeActivityData } from '../../services/api'

interface RealTimeActivityProps {
  data?: RealTimeActivityData
}

const RealTimeActivity: React.FC<RealTimeActivityProps> = ({ data }) => {
  if (!data) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass-card rounded-2xl p-6"
      >
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </motion.div>
    )
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'border-l-warning-500 bg-warning-50'
      case 'critical':
        return 'border-l-error-500 bg-error-50'
      default:
        return 'border-l-betty-500 bg-betty-50'
    }
  }

  const getActivityTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      knowledge_created: 'Knowledge Created',
      pattern_matched: 'Pattern Matched',
      cross_project_recommendation: 'Cross-Project Insight',
      context_loaded: 'Context Loaded',
      solution_reused: 'Solution Reused',
      knowledge_search: 'Knowledge Search',
      pattern_discovered: 'Pattern Discovered',
      performance_improvement: 'Performance Boost',
    }
    return labels[type] || type.replace('_', ' ')
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-pink-500 to-rose-600 rounded-lg relative">
            <Activity className="w-5 h-5 text-white" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-success-500 rounded-full animate-ping" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Real-Time Activity
            </h3>
            <p className="text-sm text-gray-500">
              {Math.round(data.activity_rate_per_hour)} events/hour • 
              {data.most_active_project} most active
            </p>
          </div>
        </div>

        {/* Live Indicator */}
        <div className="flex items-center space-x-2 bg-success-50 px-3 py-1 rounded-full border border-success-200">
          <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
          <span className="text-sm font-medium text-success-700">Live</span>
        </div>
      </div>

      {/* Recent Patterns Discovered */}
      {data.recent_patterns_discovered.length > 0 && (
        <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
            <span className="mr-2">🔍</span>
            Recent Pattern Discoveries
          </h4>
          <div className="space-y-1">
            {data.recent_patterns_discovered.slice(0, 3).map((pattern, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="text-xs text-gray-600 flex items-center"
              >
                <div className="w-1 h-1 bg-purple-400 rounded-full mr-2" />
                {pattern}
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Activity Feed */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        <AnimatePresence>
          {data.activities.slice(0, 10).map((activity, index) => (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              transition={{ delay: index * 0.05 }}
              className={`activity-item border-l-4 ${getPriorityColor(activity.priority)}`}
            >
              <div className="flex items-start space-x-3">
                {/* Icon */}
                <div className="flex-shrink-0 mt-1">
                  <span className="text-lg">{activity.icon}</span>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-gray-700 truncate">
                      {activity.title}
                    </h4>
                    <div className="flex items-center space-x-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      <span>
                        {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                    {activity.description}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                        {getActivityTypeLabel(activity.activity_type)}
                      </span>
                      {activity.project_name && (
                        <span className="text-xs bg-betty-100 text-betty-700 px-2 py-0.5 rounded-full">
                          {activity.project_name}
                        </span>
                      )}
                    </div>
                    
                    {activity.priority === 'high' && (
                      <AlertCircle className="w-3 h-3 text-warning-500" />
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Activity Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-semibold text-gray-700">
              {data.activities.length}
            </div>
            <div className="text-xs text-gray-500">Recent Events</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-purple-600">
              {data.recent_patterns_discovered.length}
            </div>
            <div className="text-xs text-gray-500">New Patterns</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-success-600">
              {Math.round(data.activity_rate_per_hour)}
            </div>
            <div className="text-xs text-gray-500">Events/Hour</div>
          </div>
        </div>
      </div>

      {/* System Alerts */}
      {data.system_alerts.length > 0 && (
        <div className="mt-4 p-3 bg-warning-50 border border-warning-200 rounded-lg">
          <h4 className="text-sm font-medium text-warning-700 mb-2 flex items-center">
            <AlertCircle className="w-4 h-4 mr-1" />
            System Alerts
          </h4>
          <div className="space-y-1">
            {data.system_alerts.map((alert, index) => (
              <div key={index} className="text-xs text-warning-600">
                {alert.message || JSON.stringify(alert)}
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}

export default RealTimeActivity