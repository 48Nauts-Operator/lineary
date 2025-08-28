import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Clock, AlertCircle, RefreshCw, Search, Filter } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface ActivityEvent {
  id: string
  activity_type: string
  title: string
  description: string
  project_name: string
  timestamp: string
  metadata?: any
  priority?: string
  icon?: string
}

interface LiveDataStats {
  total_events: number
  events_per_hour: number
  active_projects: string[]
  recent_patterns: string[]
}

const LiveDataDashboard: React.FC = () => {
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [stats, setStats] = useState<LiveDataStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAutoRefresh, setIsAutoRefresh] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterProject, setFilterProject] = useState<string>('all')

  // Fetch real-time activity data
  const fetchActivityData = async () => {
    try {
      console.log('Fetching live data from Betty API...')
      const response = await fetch('/api/analytics/real-time-activity?limit=100')
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Received data from Betty:', data)
      
      if (data.success && data.data) {
        const activities = data.data.activities || []
        console.log(`Processing ${activities.length} activities`)
        setEvents(activities)
        setStats({
          total_events: activities.length,
          events_per_hour: Math.round(data.data.activity_rate_per_hour || 0),
          active_projects: data.data.most_active_project ? [data.data.most_active_project] : [],
          recent_patterns: data.data.recent_patterns_discovered || []
        })
      } else {
        console.warn('No data in response:', data)
      }
      setIsLoading(false)
    } catch (error) {
      console.error('Failed to fetch activity data:', error)
      // Show empty state instead of stuck loading
      setEvents([])
      setStats({
        total_events: 0,
        events_per_hour: 0,
        active_projects: [],
        recent_patterns: []
      })
      setIsLoading(false)
    }
  }

  // Auto-refresh every 60 seconds (changed from 5 seconds to reduce load)
  useEffect(() => {
    fetchActivityData()
    
    let interval: ReturnType<typeof setInterval> | null = null
    if (isAutoRefresh) {
      interval = setInterval(() => {
        console.log('Auto-refreshing data...')
        fetchActivityData()
      }, 60000) // Changed to 60 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isAutoRefresh])

  // Filter events based on search and project
  const filteredEvents = events.filter(event => {
    const matchesSearch = searchQuery === '' || 
      event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.description.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesProject = filterProject === 'all' || event.project_name === filterProject
    
    return matchesSearch && matchesProject
  })

  // Get unique projects for filter dropdown
  const uniqueProjects = Array.from(new Set(events.map(e => e.project_name)))

  const getActivityIcon = (type: string) => {
    const icons: Record<string, string> = {
      knowledge_created: '📝',
      pattern_matched: '🔍',
      cross_project_recommendation: '🔗',
      context_loaded: '📚',
      solution_reused: '♻️',
      knowledge_search: '🔎',
      pattern_discovered: '✨',
      performance_improvement: '⚡',
      knowledge_conversation_created: '💬',
      knowledge_solution_created: '💡',
      knowledge_decision_created: '🎯',
      knowledge_code_pattern_created: '🔧'
    }
    return icons[type] || '📌'
  }

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high':
        return 'border-l-warning-500 bg-warning-50'
      case 'critical':
        return 'border-l-error-500 bg-error-50'
      default:
        return 'border-l-betty-500 bg-betty-50'
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-neural-network p-8">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-2xl p-8 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-betty-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-700">Loading Live Data Stream...</h2>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neural-network p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-r from-pink-500 to-rose-600 rounded-lg relative">
                <Activity className="w-6 h-6 text-white" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-success-500 rounded-full animate-ping" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">Live Data Stream</h1>
                <p className="text-sm text-gray-600">
                  Real-time knowledge activity from BETTY Memory System
                </p>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center space-x-4">
              {/* Auto Refresh Toggle */}
              <button
                onClick={() => setIsAutoRefresh(!isAutoRefresh)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  isAutoRefresh 
                    ? 'bg-success-100 text-success-700 border border-success-300' 
                    : 'bg-gray-100 text-gray-600 border border-gray-300'
                }`}
              >
                <RefreshCw className={`w-4 h-4 ${isAutoRefresh ? 'animate-spin' : ''}`} />
                <span className="text-sm font-medium">
                  {isAutoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
                </span>
              </button>

              {/* Manual Refresh */}
              <button
                onClick={fetchActivityData}
                className="p-2 bg-white hover:bg-gray-50 rounded-lg border border-gray-300 transition-colors"
              >
                <RefreshCw className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>

          {/* Live Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white rounded-lg p-3 border border-gray-200">
              <div className="text-2xl font-bold text-gray-800">{stats?.total_events || 0}</div>
              <div className="text-xs text-gray-500">Total Events</div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-gray-200">
              <div className="text-2xl font-bold text-purple-600">
                {Math.round(stats?.events_per_hour || 0)}
              </div>
              <div className="text-xs text-gray-500">Events/Hour</div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-gray-200">
              <div className="text-2xl font-bold text-success-600">
                {stats?.active_projects?.length || 0}
              </div>
              <div className="text-xs text-gray-500">Active Projects</div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-gray-200">
              <div className="text-2xl font-bold text-betty-600">
                {stats?.recent_patterns?.length || 0}
              </div>
              <div className="text-xs text-gray-500">Patterns Found</div>
            </div>
          </div>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-2xl p-4"
        >
          <div className="flex items-center space-x-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search events..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white rounded-lg border border-gray-300 focus:border-betty-500 focus:outline-none"
              />
            </div>

            {/* Project Filter */}
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-600" />
              <select
                value={filterProject}
                onChange={(e) => setFilterProject(e.target.value)}
                className="px-4 py-2 bg-white rounded-lg border border-gray-300 focus:border-betty-500 focus:outline-none"
              >
                <option value="all">All Projects</option>
                {uniqueProjects.map(project => (
                  <option key={project} value={project}>{project}</option>
                ))}
              </select>
            </div>
          </div>
        </motion.div>

        {/* Events Stream */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-700">Activity Stream</h2>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
            </div>
          </div>

          {/* Events List */}
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            <AnimatePresence>
              {filteredEvents.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Activity className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium mb-2">Waiting for new knowledge items...</p>
                  <p className="text-sm">Knowledge captured by Betty will appear here</p>
                  <button
                    onClick={fetchActivityData}
                    className="mt-4 px-4 py-2 bg-betty-500 text-white rounded-lg hover:bg-betty-600 transition-colors"
                  >
                    Refresh Now
                  </button>
                </div>
              ) : (
                filteredEvents.map((event, index) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.02 }}
                    className={`activity-item border-l-4 ${getPriorityColor(event.priority)} p-4 rounded-lg`}
                  >
                    <div className="flex items-start space-x-3">
                      {/* Icon */}
                      <div className="flex-shrink-0 text-2xl">
                        {event.icon || getActivityIcon(event.activity_type)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-medium text-gray-800 truncate">
                            {event.title}
                          </h4>
                          <div className="flex items-center space-x-1 text-xs text-gray-500">
                            <Clock className="w-3 h-3" />
                            <span>
                              {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                          {event.description}
                        </p>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                              {event.activity_type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-xs bg-betty-100 text-betty-700 px-2 py-0.5 rounded-full">
                              {event.project_name}
                            </span>
                          </div>

                          {event.priority === 'high' && (
                            <AlertCircle className="w-3 h-3 text-warning-500" />
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Recent Patterns */}
        {stats?.recent_patterns && stats.recent_patterns.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card rounded-2xl p-6"
          >
            <h3 className="text-lg font-semibold text-gray-700 mb-4">Recent Pattern Discoveries</h3>
            <div className="grid grid-cols-2 gap-3">
              {stats.recent_patterns.map((pattern, index) => (
                <div
                  key={index}
                  className="bg-gradient-to-r from-purple-50 to-pink-50 p-3 rounded-lg border border-purple-200"
                >
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">✨</span>
                    <span className="text-sm text-gray-700">{pattern}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default LiveDataDashboard