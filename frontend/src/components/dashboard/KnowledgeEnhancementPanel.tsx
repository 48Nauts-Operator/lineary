import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  BookOpen, 
  ThumbsUp, 
  ThumbsDown, 
  AlertCircle,
  CheckCircle,
  XCircle,
  Edit3,
  Save,
  MessageSquare,
  Lightbulb,
  Star,
  Archive,
  RefreshCw
} from 'lucide-react'

// ABOUTME: Interactive knowledge enhancement system for user validation and preservation
// ABOUTME: Allows users to validate, correct, and enhance BETTY's knowledge base with contextual feedback

interface KnowledgeItem {
  id: string
  type: 'pattern' | 'solution' | 'decision' | 'lesson'
  title: string
  description: string
  context: string
  confidence: number
  projectName: string
  timestamp: string
  status: 'pending' | 'validated' | 'rejected' | 'needs_review'
  userFeedback?: string
  tags: string[]
  relatedItems: string[]
}

interface ValidationAction {
  type: 'validate' | 'reject' | 'modify' | 'enhance'
  feedback?: string
  modifications?: Partial<KnowledgeItem>
  importance?: 'low' | 'medium' | 'high' | 'critical'
}

interface KnowledgeEnhancementPanelProps {
  pendingItems?: KnowledgeItem[]
  onValidate?: (itemId: string, action: ValidationAction) => void
}

const KnowledgeEnhancementPanel: React.FC<KnowledgeEnhancementPanelProps> = ({
  pendingItems = [],
  onValidate
}) => {
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null)
  const [editingItem, setEditingItem] = useState<string | null>(null)
  const [feedback, setFeedback] = useState('')
  const [showDetails, setShowDetails] = useState<string | null>(null)

  // Mock data for demonstration
  const mockItems: KnowledgeItem[] = pendingItems.length > 0 ? pendingItems : [
    {
      id: '1',
      type: 'pattern',
      title: 'Database Connection Pool Optimization',
      description: 'Implemented connection pooling with specific configuration that improved performance by 40%',
      context: 'While working on nautBrain project, noticed slow database queries. Applied connection pool with max 20 connections, min 5, and timeout of 30s.',
      confidence: 0.85,
      projectName: 'nautBrain',
      timestamp: '2025-02-04T10:30:00Z',
      status: 'pending',
      tags: ['database', 'performance', 'postgresql'],
      relatedItems: ['jwt-auth-pattern', 'error-handling-middleware']
    },
    {
      id: '2', 
      type: 'solution',
      title: 'React State Management with Custom Hooks',
      description: 'Created reusable state management pattern using custom hooks for form handling',
      context: 'Needed consistent form state management across 137docs. Built useFormState hook with validation and error handling.',
      confidence: 0.92,
      projectName: '137docs',
      timestamp: '2025-02-04T14:15:00Z',
      status: 'pending',
      tags: ['react', 'hooks', 'forms', 'typescript'],
      relatedItems: ['input-validation-pattern']
    },
    {
      id: '3',
      type: 'lesson',
      title: 'Docker Volume Permissions Issue',
      description: 'Learned that Docker volume permissions need explicit user mapping for development environments',
      context: 'Spent 2 hours debugging file permission errors in Betty project. Solution was adding user mapping in docker-compose.',
      confidence: 0.95,
      projectName: 'Betty',
      timestamp: '2025-02-04T16:45:00Z',
      status: 'pending',
      tags: ['docker', 'permissions', 'devops'],
      relatedItems: []
    }
  ]

  const handleValidation = (item: KnowledgeItem, action: ValidationAction) => {
    if (onValidate) {
      onValidate(item.id, action)
    }
    
    // Simulate API call and UI feedback
    console.log(`${action.type} action for item:`, item.title)
    
    // Close any open modals
    setSelectedItem(null)
    setEditingItem(null)
    setFeedback('')
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'pattern': return <Lightbulb className="w-4 h-4" />
      case 'solution': return <CheckCircle className="w-4 h-4" />
      case 'decision': return <MessageSquare className="w-4 h-4" />
      case 'lesson': return <BookOpen className="w-4 h-4" />
      default: return <BookOpen className="w-4 h-4" />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'pattern': return 'text-purple-600 bg-purple-100 border-purple-200'
      case 'solution': return 'text-green-600 bg-green-100 border-green-200' 
      case 'decision': return 'text-blue-600 bg-blue-100 border-blue-200'
      case 'lesson': return 'text-orange-600 bg-orange-100 border-orange-200'
      default: return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-100'
    if (confidence >= 0.7) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg">
            <Star className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Knowledge Enhancement
            </h3>
            <p className="text-sm text-gray-500">
              Help BETTY learn by validating and enhancing captured knowledge
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">
            {mockItems.filter(item => item.status === 'pending').length} pending
          </span>
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <RefreshCw className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Knowledge Items */}
      <div className="space-y-4">
        {mockItems.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-sm transition-all"
          >
            {/* Item Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start space-x-3 flex-1">
                <div className={`p-2 rounded-lg border ${getTypeColor(item.type)}`}>
                  {getTypeIcon(item.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h4 className="font-semibold text-gray-700 truncate">
                      {item.title}
                    </h4>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(item.confidence)}`}>
                      {Math.round(item.confidence * 100)}% confidence
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                    {item.description}
                  </p>
                  
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>{item.projectName}</span>
                    <span>{new Date(item.timestamp).toLocaleDateString()}</span>
                    <span className="capitalize">{item.type}</span>
                  </div>
                </div>
              </div>
              
              {/* Confidence Indicator */}
              <div className="flex items-center space-x-1 ml-4">
                {item.confidence < 0.7 && (
                  <AlertCircle className="w-4 h-4 text-yellow-500" />
                )}
              </div>
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-1 mb-3">
              {item.tags.map(tag => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  #{tag}
                </span>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between">
              <button
                onClick={() => setShowDetails(showDetails === item.id ? null : item.id)}
                className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
              >
                {showDetails === item.id ? 'Hide Details' : 'Show Context'}
              </button>
              
              <div className="flex space-x-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleValidation(item, { type: 'validate', importance: 'high' })}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                >
                  <ThumbsUp className="w-3 h-3" />
                  <span className="text-xs font-medium">Validate</span>
                </motion.button>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setSelectedItem(item)}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                >
                  <Edit3 className="w-3 h-3" />
                  <span className="text-xs font-medium">Enhance</span>
                </motion.button>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleValidation(item, { type: 'reject', feedback: 'Not valuable' })}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                >
                  <ThumbsDown className="w-3 h-3" />
                  <span className="text-xs font-medium">Reject</span>
                </motion.button>
              </div>
            </div>

            {/* Expandable Context */}
            <AnimatePresence>
              {showDetails === item.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 pt-4 border-t border-gray-200"
                >
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Context & Details</h5>
                    <p className="text-sm text-gray-600 mb-3">{item.context}</p>
                    
                    {item.relatedItems.length > 0 && (
                      <div>
                        <h6 className="text-xs font-medium text-gray-500 mb-1">Related Items</h6>
                        <div className="flex flex-wrap gap-1">
                          {item.relatedItems.map(relatedId => (
                            <span
                              key={relatedId}
                              className="px-2 py-0.5 bg-indigo-100 text-indigo-600 rounded text-xs"
                            >
                              {relatedId}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {/* Enhancement Modal */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setSelectedItem(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-800">
                  Enhance Knowledge Item
                </h3>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title
                  </label>
                  <input
                    type="text"
                    defaultValue={selectedItem.title}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    rows={3}
                    defaultValue={selectedItem.description}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Additional Context or Corrections
                  </label>
                  <textarea
                    rows={4}
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Add any corrections, additional context, or improvements..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Importance Level
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                    <option value="medium">Medium - Standard knowledge item</option>
                    <option value="high">High - Important pattern or solution</option>
                    <option value="critical">Critical - Essential for future work</option>
                    <option value="low">Low - Minor detail or observation</option>
                  </select>
                </div>
                
                <div className="flex space-x-3 pt-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleValidation(selectedItem, {
                      type: 'enhance',
                      feedback,
                      importance: 'high'
                    })}
                    className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    <Save className="w-4 h-4" />
                    <span>Save Enhancement</span>
                  </motion.button>
                  
                  <button
                    onClick={() => setSelectedItem(null)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {mockItems.length === 0 && (
        <div className="text-center py-8">
          <Archive className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-600 mb-2">
            All Caught Up!
          </h4>
          <p className="text-gray-500">
            No knowledge items need validation right now.
          </p>
        </div>
      )}
    </motion.div>
  )
}

export default KnowledgeEnhancementPanel