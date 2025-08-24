import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Clock,
  TrendingUp,
  Calendar,
  Zap,
  BookOpen,
  Code,
  GitBranch,
  Star,
  Activity
} from 'lucide-react'
import { useLearningTimeline } from '../../hooks/useKnowledgeVisualization'

const LearningTimelineView: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'quarter' | 'year'>('month')
  const [selectedCategory, setSelectedCategory] = useState<string>('')

  const {
    data: timelineEvents,
    isLoading,
    error
  } = useLearningTimeline(
    undefined, // startDate 
    undefined, // endDate
    selectedCategory || undefined,
    100
  )

  const getEventIcon = (eventType: string) => {
    const icons: Record<string, any> = {
      'code_analysis': Code,
      'documentation_ingested': BookOpen,
      'pattern_discovered': Star,
      'repository_analyzed': GitBranch,
      'knowledge_connected': Zap,
      'expertise_gained': TrendingUp,
      'default': Activity
    }
    return icons[eventType] || icons.default
  }

  const getEventColor = (eventType: string): string => {
    const colors: Record<string, string> = {
      'code_analysis': 'betty-400',
      'documentation_ingested': 'purple-400', 
      'pattern_discovered': 'pink-400',
      'repository_analyzed': 'green-400',
      'knowledge_connected': 'blue-400',
      'expertise_gained': 'orange-400'
    }
    return colors[eventType] || 'white'
  }

  const getImpactLabel = (score: number): string => {
    if (score >= 4) return 'High Impact'
    if (score >= 3) return 'Medium Impact'
    if (score >= 2) return 'Low Impact'
    return 'Minimal Impact'
  }

  // Group events by date
  const groupedEvents = timelineEvents?.reduce((groups, event) => {
    const date = new Date(event.timestamp).toDateString()
    if (!groups[date]) groups[date] = []
    groups[date].push(event)
    return groups
  }, {} as Record<string, typeof timelineEvents>) || {}

  const sortedDates = Object.keys(groupedEvents).sort((a, b) => 
    new Date(b).getTime() - new Date(a).getTime()
  )

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center space-x-4 animate-pulse">
            <div className="w-10 h-10 bg-white/10 rounded-full"></div>
            <div className="flex-1">
              <div className="w-64 h-4 bg-white/10 rounded mb-2"></div>
              <div className="w-48 h-3 bg-white/10 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-morphism border border-red-500/20 rounded-lg p-8 text-center">
        <Clock className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-red-400 text-lg font-semibold mb-2">Failed to Load Timeline</h3>
        <p className="text-white/60">{error.message || 'An unexpected error occurred'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header and Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Learning Timeline</h2>
          <p className="text-white/70">
            {timelineEvents?.length || 0} learning events tracked
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value as any)}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-betty-400 transition-colors"
          >
            <option value="week">Past Week</option>
            <option value="month">Past Month</option>
            <option value="quarter">Past Quarter</option>
            <option value="year">Past Year</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-betty-400 transition-colors"
          >
            <option value="">All Categories</option>
            <option value="code_analysis">Code Analysis</option>
            <option value="documentation">Documentation</option>
            <option value="patterns">Pattern Discovery</option>
            <option value="repositories">Repository Analysis</option>
            <option value="connections">Knowledge Connections</option>
          </select>
        </div>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-betty-400 via-purple-400 to-pink-400 opacity-30"></div>

        <div className="space-y-8">
          {sortedDates.map((date, dateIndex) => (
            <motion.div
              key={date}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: dateIndex * 0.1 }}
            >
              {/* Date Header */}
              <div className="relative flex items-center mb-4">
                <div className="absolute left-6 w-4 h-4 bg-betty-400 rounded-full border-4 border-gray-900 z-10"></div>
                <div className="ml-16">
                  <h3 className="text-white font-semibold text-lg">
                    {new Date(date).toLocaleDateString('en-US', { 
                      weekday: 'long',
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </h3>
                  <p className="text-white/60 text-sm">
                    {groupedEvents[date].length} events
                  </p>
                </div>
              </div>

              {/* Events for this date */}
              <div className="ml-16 space-y-4">
                {groupedEvents[date].map((event, eventIndex) => {
                  const Icon = getEventIcon(event.event_type)
                  const color = getEventColor(event.event_type)
                  
                  return (
                    <motion.div
                      key={eventIndex}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: (dateIndex * 0.1) + (eventIndex * 0.05) }}
                      className="glass-morphism border border-white/10 rounded-lg p-4 hover:border-white/20 transition-colors"
                    >
                      <div className="flex items-start space-x-4">
                        <div className={`p-2 bg-${color}/10 rounded-lg flex-shrink-0`}>
                          <Icon className={`w-5 h-5 text-${color}`} />
                        </div>

                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-white font-medium">{event.description}</h4>
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 bg-${color}/10 text-${color} text-xs rounded-full`}>
                                {getImpactLabel(event.impact_score)}
                              </span>
                              <span className="text-white/40 text-xs">
                                {new Date(event.timestamp).toLocaleTimeString('en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-white/60 text-sm capitalize">
                              {event.knowledge_area.replace('_', ' ')}
                            </span>
                            <div className="flex items-center space-x-1">
                              {[...Array(5)].map((_, i) => (
                                <Star
                                  key={i}
                                  className={`w-3 h-3 ${
                                    i < event.impact_score
                                      ? `text-${color} fill-current`
                                      : 'text-white/20'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Timeline Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Activity className="w-6 h-6 text-betty-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {timelineEvents?.length || 0}
          </div>
          <div className="text-sm text-white/60">Total Events</div>
        </div>

        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <TrendingUp className="w-6 h-6 text-green-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {timelineEvents?.filter(e => e.impact_score >= 4).length || 0}
          </div>
          <div className="text-sm text-white/60">High Impact</div>
        </div>

        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Clock className="w-6 h-6 text-purple-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {timelineEvents ? 
              (timelineEvents.reduce((sum, e) => sum + e.impact_score, 0) / timelineEvents.length).toFixed(1) 
              : '0.0'
            }
          </div>
          <div className="text-sm text-white/60">Avg Impact</div>
        </div>

        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Calendar className="w-6 h-6 text-pink-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {Object.keys(groupedEvents).length}
          </div>
          <div className="text-sm text-white/60">Active Days</div>
        </div>
      </div>

      {timelineEvents?.length === 0 && (
        <div className="text-center py-12">
          <Clock className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <h3 className="text-white/60 text-lg font-medium mb-2">No timeline events</h3>
          <p className="text-white/40">
            Learning events will appear here as Betty processes new knowledge
          </p>
        </div>
      )}
    </div>
  )
}

export default LearningTimelineView