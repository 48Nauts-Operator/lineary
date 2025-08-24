// ABOUTME: Activity timeline component for tracking issue activities and changes
// ABOUTME: Displays chronological history of issue updates, status changes, and comments

import React from 'react'
import { format } from 'date-fns'
import { Activity } from '../App'

interface Props {
  activities: Activity[]
}

const ActivityTimeline: React.FC<Props> = ({ activities }) => {
  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'created':
        return '✨'
      case 'updated':
        return '📝'
      case 'status_changed':
        return '🔄'
      case 'comment':
        return '💬'
      default:
        return '📋'
    }
  }

  const getActivityColor = (type: Activity['type']) => {
    switch (type) {
      case 'created':
        return 'text-green-400'
      case 'updated':
        return 'text-blue-400'
      case 'status_changed':
        return 'text-purple-400'
      case 'comment':
        return 'text-yellow-400'
      default:
        return 'text-gray-400'
    }
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📋</div>
        <h3 className="text-xl font-semibold text-white mb-2">No Activity Yet</h3>
        <p className="text-gray-400">
          Activity will appear here as changes are made to this issue
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white mb-6">Activity Timeline</h3>
      
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-700"></div>
        
        <div className="space-y-6">
          {activities.map((activity, index) => (
            <div key={activity.id} className="relative flex items-start space-x-4">
              {/* Timeline dot */}
              <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full bg-gray-800 border-2 ${getActivityColor(activity.type)} border-current`}>
                <span className="text-lg">{getActivityIcon(activity.type)}</span>
              </div>
              
              {/* Activity content */}
              <div className="flex-1 min-w-0 pb-6">
                <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className={`font-medium capitalize ${getActivityColor(activity.type)}`}>
                      {activity.type.replace('_', ' ')}
                    </h4>
                    <time className="text-xs text-gray-400">
                      {format(new Date(activity.created_at), 'MMM dd, yyyy HH:mm')}
                    </time>
                  </div>
                  
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {activity.description}
                  </p>
                  
                  {/* Metadata */}
                  {activity.metadata && (
                    <div className="mt-3 p-3 bg-gray-800/50 rounded border border-gray-600">
                      <details className="text-xs text-gray-400">
                        <summary className="cursor-pointer hover:text-gray-300">
                          View Details
                        </summary>
                        <pre className="mt-2 text-xs overflow-x-auto">
                          {JSON.stringify(activity.metadata, null, 2)}
                        </pre>
                      </details>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {activities.length > 0 && (
        <div className="text-center pt-4 border-t border-gray-700">
          <p className="text-sm text-gray-400">
            {activities.length} activity record{activities.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}
    </div>
  )
}

export default ActivityTimeline