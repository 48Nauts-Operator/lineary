import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Bell,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle,
  BookOpen,
  ArrowRight,
  Lightbulb,
  Code,
  GitBranch,
  Database,
  Shield,
  Zap,
  X,
  ExternalLink
} from 'lucide-react'

// ABOUTME: Intelligent reminder system that surfaces relevant past solutions and patterns
// ABOUTME: Proactively suggests knowledge based on current context and similar scenarios

interface Reminder {
  id: string
  type: 'similar_solution' | 'pattern_suggestion' | 'lesson_learned' | 'optimization_opportunity' | 'security_concern'
  title: string
  description: string
  relevanceScore: number
  contextMatch: string
  originalProject: string
  originalDate: string
  suggestedAction?: string
  relatedCode?: string
  tags: string[]
  timesSeen: number
  lastDismissed?: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
}

interface IntelligentRemindersProps {
  reminders?: Reminder[]
  currentContext?: {
    project: string
    currentTask: string
    recentFiles: string[]
    keywords: string[]
  }
  onDismiss?: (reminderId: string, reason?: string) => void
  onApply?: (reminderId: string) => void
}

const IntelligentReminders: React.FC<IntelligentRemindersProps> = ({
  reminders = [],
  currentContext,
  onDismiss,
  onApply
}) => {
  const [dismissedItems, setDismissedItems] = useState<Set<string>>(new Set())
  const [expandedItem, setExpandedItem] = useState<string | null>(null)
  const [filterPriority, setFilterPriority] = useState<string>('all')

  // Mock data for demonstration
  const mockReminders: Reminder[] = reminders.length > 0 ? reminders : [
    {
      id: '1',
      type: 'similar_solution',
      title: 'JWT Authentication Pattern Available',
      description: 'You\'ve implemented JWT authentication successfully in 137docs. The same pattern could solve your current authentication task.',
      relevanceScore: 0.94,
      contextMatch: 'Detected authentication-related code and imports',
      originalProject: '137docs', 
      originalDate: '2025-01-15',
      suggestedAction: 'Apply JWT middleware pattern with token refresh',
      relatedCode: 'middleware/auth.js, utils/jwt.js',
      tags: ['authentication', 'jwt', 'security', 'middleware'],
      timesSeen: 3,
      priority: 'high'
    },
    {
      id: '2',
      type: 'pattern_suggestion',
      title: 'Database Connection Pool Optimization',
      description: 'Similar database performance issues were resolved in nautBrain using connection pooling configuration.',
      relevanceScore: 0.87,
      contextMatch: 'Database queries and performance concerns detected',
      originalProject: 'nautBrain',
      originalDate: '2025-01-22',
      suggestedAction: 'Implement connection pool with max 20 connections',
      relatedCode: 'config/database.js',
      tags: ['database', 'performance', 'postgresql', 'optimization'],
      timesSeen: 1,
      priority: 'medium'
    },
    {
      id: '3',
      type: 'lesson_learned',
      title: 'Docker Volume Permission Issue',
      description: 'Previously spent 2 hours debugging file permissions. Remember to check user mapping in docker-compose.',
      relevanceScore: 0.92,
      contextMatch: 'Docker-related files and permission errors detected',
      originalProject: 'Betty',
      originalDate: '2025-02-01',
      suggestedAction: 'Add user: "${UID}:${GID}" to docker-compose services',
      tags: ['docker', 'permissions', 'devops', 'debugging'],
      timesSeen: 2,
      priority: 'high'
    },
    {
      id: '4',
      type: 'security_concern',
      title: 'Input Validation Missing',
      description: 'Form inputs detected without validation. Previous security issues occurred in 137docs from unvalidated inputs.',
      relevanceScore: 0.78,
      contextMatch: 'Form components without validation schemas',
      originalProject: '137docs',
      originalDate: '2025-01-28',
      suggestedAction: 'Add Zod validation schemas for all form inputs',
      relatedCode: 'schemas/validation.js',
      tags: ['security', 'validation', 'forms', 'zod'],
      timesSeen: 1,
      priority: 'urgent'
    },
    {
      id: '5',
      type: 'optimization_opportunity',
      title: 'React Re-render Optimization',
      description: 'Detected similar component structure that benefited from React.memo and useMemo optimization in previous projects.',
      relevanceScore: 0.71,
      contextMatch: 'Complex React components with frequent re-renders',
      originalProject: '137docs',
      originalDate: '2025-01-18',
      suggestedAction: 'Apply React.memo and optimize expensive calculations',
      tags: ['react', 'performance', 'optimization', 'memo'],
      timesSeen: 4,
      priority: 'low'
    }
  ]

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'similar_solution': return <Lightbulb className="w-4 h-4" />
      case 'pattern_suggestion': return <Target className="w-4 h-4" />
      case 'lesson_learned': return <BookOpen className="w-4 h-4" />
      case 'optimization_opportunity': return <Zap className="w-4 h-4" />
      case 'security_concern': return <Shield className="w-4 h-4" />
      default: return <Bell className="w-4 h-4" />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'similar_solution': return 'text-green-600 bg-green-100 border-green-200'
      case 'pattern_suggestion': return 'text-blue-600 bg-blue-100 border-blue-200'
      case 'lesson_learned': return 'text-orange-600 bg-orange-100 border-orange-200'
      case 'optimization_opportunity': return 'text-purple-600 bg-purple-100 border-purple-200'
      case 'security_concern': return 'text-red-600 bg-red-100 border-red-200'
      default: return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'text-red-700 bg-red-100 border-red-300'
      case 'high': return 'text-orange-700 bg-orange-100 border-orange-300'
      case 'medium': return 'text-yellow-700 bg-yellow-100 border-yellow-300'
      case 'low': return 'text-gray-600 bg-gray-100 border-gray-300'
      default: return 'text-gray-600 bg-gray-100 border-gray-300'
    }
  }

  const handleDismiss = (reminderId: string, reason?: string) => {
    setDismissedItems(prev => new Set([...prev, reminderId]))
    if (onDismiss) {
      onDismiss(reminderId, reason)
    }
  }

  const handleApply = (reminderId: string) => {
    if (onApply) {
      onApply(reminderId)
    }
  }

  const filteredReminders = mockReminders
    .filter(reminder => !dismissedItems.has(reminder.id))
    .filter(reminder => filterPriority === 'all' || reminder.priority === filterPriority)
    .sort((a, b) => {
      const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 }
      return priorityOrder[b.priority] - priorityOrder[a.priority] || b.relevanceScore - a.relevanceScore
    })

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-amber-500 to-orange-600 rounded-lg">
            <Bell className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Intelligent Reminders
            </h3>
            <p className="text-sm text-gray-500">
              Relevant solutions and patterns from your past work
            </p>
          </div>
        </div>
        
        {/* Priority Filter */}
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
          className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
        >
          <option value="all">All Priorities</option>
          <option value="urgent">Urgent</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Current Context Display */}
      {currentContext && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg mb-6 border border-blue-200">
          <h4 className="font-medium text-blue-800 mb-2">Current Context</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-blue-600 font-medium">Project:</span>
              <span className="ml-2 text-blue-800">{currentContext.project}</span>
            </div>
            <div>
              <span className="text-blue-600 font-medium">Task:</span>
              <span className="ml-2 text-blue-800">{currentContext.currentTask}</span>
            </div>
          </div>
          {currentContext.keywords.length > 0 && (
            <div className="mt-2">
              <span className="text-blue-600 font-medium text-sm">Keywords:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {currentContext.keywords.map(keyword => (
                  <span
                    key={keyword}
                    className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Reminders List */}
      <div className="space-y-4">
        {filteredReminders.map((reminder, index) => (
          <motion.div
            key={reminder.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-sm transition-all"
          >
            {/* Reminder Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start space-x-3 flex-1">
                <div className={`p-2 rounded-lg border ${getTypeColor(reminder.type)}`}>
                  {getTypeIcon(reminder.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h4 className="font-semibold text-gray-700">
                      {reminder.title}
                    </h4>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getPriorityColor(reminder.priority)}`}>
                      {reminder.priority}
                    </span>
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                      {Math.round(reminder.relevanceScore * 100)}% match
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">
                    {reminder.description}
                  </p>
                  
                  <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                    <span className="flex items-center">
                      <GitBranch className="w-3 h-3 mr-1" />
                      {reminder.originalProject}
                    </span>
                    <span className="flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      {new Date(reminder.originalDate).toLocaleDateString()}
                    </span>
                    <span>Seen {reminder.timesSeen}x</span>
                  </div>
                  
                  {/* Context Match */}
                  <div className="bg-yellow-50 border border-yellow-200 p-2 rounded text-xs text-yellow-800 mb-3">
                    <strong>Why this is relevant:</strong> {reminder.contextMatch}
                  </div>
                </div>
              </div>
              
              {/* Dismiss Button */}
              <button
                onClick={() => handleDismiss(reminder.id)}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-1 mb-3">
              {reminder.tags.map(tag => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  #{tag}
                </span>
              ))}
            </div>

            {/* Suggested Action */}
            {reminder.suggestedAction && (
              <div className="bg-green-50 border border-green-200 p-3 rounded-lg mb-3">
                <div className="flex items-start space-x-2">
                  <Target className="w-4 h-4 text-green-600 mt-0.5" />
                  <div>
                    <h5 className="text-sm font-medium text-green-800 mb-1">
                      Suggested Action
                    </h5>
                    <p className="text-sm text-green-700">
                      {reminder.suggestedAction}
                    </p>
                    {reminder.relatedCode && (
                      <p className="text-xs text-green-600 mt-1">
                        <Code className="w-3 h-3 inline mr-1" />
                        Related: {reminder.relatedCode}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between">
              <button
                onClick={() => setExpandedItem(expandedItem === reminder.id ? null : reminder.id)}
                className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
              >
                {expandedItem === reminder.id ? 'Hide Details' : 'View Details'}
              </button>
              
              <div className="flex space-x-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleApply(reminder.id)}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                >
                  <CheckCircle className="w-3 h-3" />
                  <span className="text-xs font-medium">Apply</span>
                </motion.button>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {/* Open related content */}}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span className="text-xs font-medium">View Original</span>
                </motion.button>
                
                <button
                  onClick={() => handleDismiss(reminder.id, 'not_relevant')}
                  className="text-xs text-gray-500 hover:text-gray-700 px-2"
                >
                  Not Relevant
                </button>
              </div>
            </div>

            {/* Expandable Details */}
            <AnimatePresence>
              {expandedItem === reminder.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 pt-4 border-t border-gray-200"
                >
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Additional Context</h5>
                    <div className="space-y-2 text-sm text-gray-600">
                      <div>
                        <strong>Original Context:</strong> This pattern was discovered while working on {reminder.originalProject} and has been successfully applied {reminder.timesSeen} times.
                      </div>
                      <div>
                        <strong>Success Rate:</strong> 95% success rate when applied in similar contexts
                      </div>
                      <div>
                        <strong>Time Savings:</strong> Estimated 2-4 hours saved by applying this pattern
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {filteredReminders.length === 0 && (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-600 mb-2">
            All Clear!
          </h4>
          <p className="text-gray-500">
            No relevant reminders for your current context.
          </p>
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-lg font-semibold text-gray-700">
            {mockReminders.length}
          </div>
          <div className="text-xs text-gray-500">Total Reminders</div>
        </div>
        <div>
          <div className="text-lg font-semibold text-amber-600">
            {mockReminders.filter(r => r.priority === 'high' || r.priority === 'urgent').length}
          </div>
          <div className="text-xs text-gray-500">High Priority</div>
        </div>
        <div>
          <div className="text-lg font-semibold text-green-600">
            {Math.round(mockReminders.reduce((acc, r) => acc + r.relevanceScore, 0) / mockReminders.length * 100)}%
          </div>
          <div className="text-xs text-gray-500">Avg Relevance</div>
        </div>
      </div>
    </motion.div>
  )
}

export default IntelligentReminders