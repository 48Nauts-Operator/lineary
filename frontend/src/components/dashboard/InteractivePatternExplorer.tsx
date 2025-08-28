import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search,
  Filter,
  Layers,
  GitBranch,
  Code,
  Clock,
  TrendingUp,
  Users,
  Star,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  Tag,
  Zap,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

// ABOUTME: Interactive pattern exploration interface showing pattern relationships and evolution
// ABOUTME: Allows users to dive deep into pattern hierarchies, connections, and usage contexts

interface PatternNode {
  id: string
  name: string
  type: 'parent' | 'child' | 'sibling'
  category: string
  description: string
  usageCount: number
  successRate: number
  projects: string[]
  tags: string[]
  createdAt: string
  lastUsed: string
  codeExamples: Array<{
    file: string
    snippet: string
    project: string
  }>
  relatedPatterns: string[]
  evolutionStages: Array<{
    stage: string
    date: string
    changes: string[]
  }>
  metrics: {
    timesSaved: number
    averageImplementationTime: number
    errorReduction: number
    performanceImprovement?: number
  }
}

interface PatternConnection {
  from: string
  to: string
  strength: number
  type: 'derives_from' | 'used_with' | 'conflicts_with' | 'enhances'
  context: string
}

interface InteractivePatternExplorerProps {
  patterns?: PatternNode[]
  connections?: PatternConnection[]
  onPatternSelect?: (patternId: string) => void
}

const InteractivePatternExplorer: React.FC<InteractivePatternExplorerProps> = ({
  patterns = [],
  connections = [],
  onPatternSelect
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedPattern, setSelectedPattern] = useState<PatternNode | null>(null)
  const [expandedPatterns, setExpandedPatterns] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'list' | 'network' | 'timeline'>('list')
  const [sortBy, setSortBy] = useState<'usage' | 'success' | 'recent' | 'name'>('usage')

  // Mock patterns data
  const mockPatterns: PatternNode[] = patterns.length > 0 ? patterns : [
    {
      id: 'jwt-auth',
      name: 'JWT Authentication Middleware',
      type: 'parent',
      category: 'Authentication',
      description: 'Comprehensive JWT-based authentication system with token refresh and role-based access control',
      usageCount: 15,
      successRate: 0.95,
      projects: ['137docs', 'nautBrain', 'Betty'],
      tags: ['security', 'middleware', 'jwt', 'authentication'],
      createdAt: '2025-01-15',
      lastUsed: '2025-02-04',
      codeExamples: [
        {
          file: 'middleware/auth.js',
          snippet: 'const authenticateToken = (req, res, next) => {\n  const token = req.headers.authorization?.split(\' \')[1]\n  if (!token) return res.status(401).json({ error: \'No token\' })\n  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {\n    if (err) return res.status(403).json({ error: \'Invalid token\' })\n    req.user = user\n    next()\n  })\n}',
          project: '137docs'
        }
      ],
      relatedPatterns: ['role-based-auth', 'token-refresh', 'session-management'],
      evolutionStages: [
        {
          stage: 'Basic JWT',
          date: '2025-01-15',
          changes: ['Simple token verification', 'Basic user payload']
        },
        {
          stage: 'Role Integration',
          date: '2025-01-22',
          changes: ['Added role-based access', 'Permission checking']
        },
        {
          stage: 'Refresh Tokens',
          date: '2025-01-28',
          changes: ['Token refresh mechanism', 'Secure token rotation']
        }
      ],
      metrics: {
        timesSaved: 48,
        averageImplementationTime: 2.5,
        errorReduction: 87,
        performanceImprovement: 15
      }
    },
    {
      id: 'db-connection-pool',
      name: 'Database Connection Pooling',
      type: 'parent',
      category: 'Database',
      description: 'Optimized database connection management for high-performance applications',
      usageCount: 8,
      successRate: 0.91,
      projects: ['nautBrain', 'Betty'],
      tags: ['database', 'performance', 'postgresql', 'optimization'],
      createdAt: '2025-01-20',
      lastUsed: '2025-02-03',
      codeExamples: [
        {
          file: 'config/database.js',
          snippet: 'const pool = new Pool({\n  user: process.env.DB_USER,\n  host: process.env.DB_HOST,\n  database: process.env.DB_NAME,\n  password: process.env.DB_PASSWORD,\n  port: process.env.DB_PORT,\n  max: 20,\n  min: 5,\n  idleTimeoutMillis: 30000\n})',
          project: 'nautBrain'
        }
      ],
      relatedPatterns: ['query-optimization', 'connection-retry', 'database-monitoring'],
      evolutionStages: [
        {
          stage: 'Basic Pool', 
          date: '2025-01-20',
          changes: ['Simple connection pooling', 'Basic configuration']
        },
        {
          stage: 'Optimized Pool',
          date: '2025-01-25',
          changes: ['Tuned pool sizes', 'Added timeout handling']
        }
      ],
      metrics: {
        timesSaved: 24,
        averageImplementationTime: 1.5,
        errorReduction: 73,
        performanceImprovement: 45
      }
    },
    {
      id: 'react-state-hooks',
      name: 'Custom React State Hooks',
      type: 'parent',
      category: 'Frontend',
      description: 'Reusable state management patterns using custom React hooks',
      usageCount: 12,
      successRate: 0.88,
      projects: ['137docs', 'Betty'],
      tags: ['react', 'hooks', 'state', 'typescript'],
      createdAt: '2025-01-25',
      lastUsed: '2025-02-04',
      codeExamples: [
        {
          file: 'hooks/useFormState.ts',
          snippet: 'export const useFormState = <T>(initialState: T) => {\n  const [state, setState] = useState(initialState)\n  const [errors, setErrors] = useState<Record<string, string>>({})\n  const [isSubmitting, setIsSubmitting] = useState(false)\n  \n  const updateField = (field: keyof T, value: any) => {\n    setState(prev => ({ ...prev, [field]: value }))\n    if (errors[field as string]) {\n      setErrors(prev => ({ ...prev, [field]: undefined }))\n    }\n  }\n  \n  return { state, errors, isSubmitting, updateField, setErrors, setIsSubmitting }\n}',
          project: '137docs'
        }
      ],
      relatedPatterns: ['form-validation', 'error-handling', 'loading-states'],
      evolutionStages: [
        {
          stage: 'Basic Hook',
          date: '2025-01-25',
          changes: ['Simple state management', 'Form handling']
        },
        {
          stage: 'Validation Integration',
          date: '2025-01-30',
          changes: ['Added error handling', 'Validation support']
        }
      ],
      metrics: {
        timesSaved: 32,
        averageImplementationTime: 1.8,
        errorReduction: 65
      }
    }
  ]

  // Mock connections data
  const mockConnections: PatternConnection[] = connections.length > 0 ? connections : [
    {
      from: 'jwt-auth',
      to: 'db-connection-pool',
      strength: 0.7,
      type: 'used_with',
      context: 'Authentication middleware often needs database access for user verification'
    },
    {
      from: 'react-state-hooks',
      to: 'jwt-auth',
      strength: 0.8,
      type: 'used_with',
      context: 'Frontend authentication state management'
    }
  ]

  // Filter and sort patterns
  const filteredPatterns = useMemo(() => {
    let filtered = mockPatterns.filter(pattern => {
      const matchesSearch = pattern.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           pattern.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      const matchesCategory = selectedCategory === 'all' || pattern.category === selectedCategory
      return matchesSearch && matchesCategory
    })

    // Sort patterns
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'usage':
          return b.usageCount - a.usageCount
        case 'success':
          return b.successRate - a.successRate
        case 'recent':
          return new Date(b.lastUsed).getTime() - new Date(a.lastUsed).getTime()
        case 'name':
          return a.name.localeCompare(b.name)
        default:
          return 0
      }
    })

    return filtered
  }, [searchTerm, selectedCategory, sortBy])

  // Get unique categories
  const categories = useMemo(() => {
    const cats = ['all', ...new Set(mockPatterns.map(p => p.category))]
    return cats
  }, [])

  const toggleExpanded = (patternId: string) => {
    const newExpanded = new Set(expandedPatterns)
    if (newExpanded.has(patternId)) {
      newExpanded.delete(patternId)
    } else {
      newExpanded.add(patternId)
    }
    setExpandedPatterns(newExpanded)
  }

  const getUsageColor = (count: number) => {
    if (count >= 10) return 'text-green-600 bg-green-100'
    if (count >= 5) return 'text-yellow-600 bg-yellow-100'
    return 'text-gray-600 bg-gray-100'
  }

  const getSuccessColor = (rate: number) => {
    if (rate >= 0.9) return 'text-green-600 bg-green-100'
    if (rate >= 0.8) return 'text-yellow-600 bg-yellow-100'
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
          <div className="p-2 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Pattern Explorer
            </h3>
            <p className="text-sm text-gray-500">
              Explore pattern relationships and evolution
            </p>
          </div>
        </div>
        
        {/* View Mode Selector */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {(['list', 'network', 'timeline'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === mode
                  ? 'bg-white text-cyan-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex-1 min-w-64">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search patterns by name or tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            />
          </div>
        </div>
        
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>
              {cat === 'all' ? 'All Categories' : cat}
            </option>
          ))}
        </select>
        
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
        >
          <option value="usage">Sort by Usage</option>
          <option value="success">Sort by Success Rate</option>
          <option value="recent">Sort by Recent</option>
          <option value="name">Sort by Name</option>
        </select>
      </div>

      {/* Patterns List */}
      <div className="space-y-4">
        {filteredPatterns.map((pattern, index) => (
          <motion.div
            key={pattern.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-sm transition-all"
          >
            {/* Pattern Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start space-x-3 flex-1">
                <button
                  onClick={() => toggleExpanded(pattern.id)}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                >
                  {expandedPatterns.has(pattern.id) ? (
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  )}
                </button>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h4 className="font-semibold text-gray-700 cursor-pointer hover:text-cyan-600"
                        onClick={() => setSelectedPattern(pattern)}>
                      {pattern.name}
                    </h4>
                    <span className="px-2 py-0.5 bg-cyan-100 text-cyan-700 rounded text-xs font-medium">
                      {pattern.category}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                    {pattern.description}
                  </p>
                  
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span className="flex items-center">
                      <GitBranch className="w-3 h-3 mr-1" />
                      {pattern.projects.join(', ')}
                    </span>
                    <span className="flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      {new Date(pattern.lastUsed).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Metrics */}
              <div className="flex items-center space-x-4 ml-4">
                <div className="text-center">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getUsageColor(pattern.usageCount)}`}>
                    {pattern.usageCount}x
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Used</div>
                </div>
                <div className="text-center">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getSuccessColor(pattern.successRate)}`}>
                    {Math.round(pattern.successRate * 100)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Success</div>
                </div>
              </div>
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-1 mb-3">
              {pattern.tags.map(tag => (
                <span
                  key={tag}
                  className="flex items-center px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  <Tag className="w-3 h-3 mr-1" />
                  {tag}
                </span>
              ))}
            </div>

            {/* Expandable Details */}
            <AnimatePresence>
              {expandedPatterns.has(pattern.id) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 pt-4 border-t border-gray-200"
                >
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Code Example */}
                    <div>
                      <h5 className="font-medium text-gray-700 mb-2 flex items-center">
                        <Code className="w-4 h-4 mr-1" />
                        Code Example
                      </h5>
                      {pattern.codeExamples[0] && (
                        <div className="bg-gray-900 text-gray-100 p-3 rounded-lg text-xs overflow-x-auto">
                          <div className="text-green-400 mb-2">// {pattern.codeExamples[0].file}</div>
                          <pre className="whitespace-pre-wrap">{pattern.codeExamples[0].snippet}</pre>
                        </div>
                      )}
                    </div>

                    {/* Metrics */}
                    <div>
                      <h5 className="font-medium text-gray-700 mb-2 flex items-center">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        Impact Metrics
                      </h5>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                          <div className="text-lg font-bold text-green-600">
                            {pattern.metrics.timesSaved}h
                          </div>
                          <div className="text-xs text-gray-600">Time Saved</div>
                        </div>
                        <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                          <div className="text-lg font-bold text-blue-600">
                            {pattern.metrics.averageImplementationTime}h
                          </div>
                          <div className="text-xs text-gray-600">Avg Implementation</div>
                        </div>
                        <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                          <div className="text-lg font-bold text-purple-600">
                            -{pattern.metrics.errorReduction}%
                          </div>
                          <div className="text-xs text-gray-600">Error Reduction</div>
                        </div>
                        {pattern.metrics.performanceImprovement && (
                          <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
                            <div className="text-lg font-bold text-orange-600">
                              +{pattern.metrics.performanceImprovement}%
                            </div>
                            <div className="text-xs text-gray-600">Performance</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Evolution Timeline */}
                  <div className="mt-4">
                    <h5 className="font-medium text-gray-700 mb-3 flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      Evolution Timeline
                    </h5>
                    <div className="space-y-3">
                      {pattern.evolutionStages.map((stage, stageIndex) => (
                        <div key={stageIndex} className="flex items-start space-x-3">
                          <div className="p-1 bg-cyan-500 rounded-full flex-shrink-0 mt-1">
                            <div className="w-2 h-2 bg-white rounded-full"></div>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <h6 className="font-medium text-gray-700">{stage.stage}</h6>
                              <span className="text-xs text-gray-500">
                                {new Date(stage.date).toLocaleDateString()}
                              </span>
                            </div>
                            <ul className="text-sm text-gray-600 space-y-1">
                              {stage.changes.map((change, changeIndex) => (
                                <li key={changeIndex} className="flex items-start space-x-2">
                                  <CheckCircle className="w-3 h-3 text-green-500 mt-0.5 flex-shrink-0" />
                                  <span>{change}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Related Patterns */}
                  {pattern.relatedPatterns.length > 0 && (
                    <div className="mt-4">
                      <h5 className="font-medium text-gray-700 mb-2 flex items-center">
                        <Layers className="w-4 h-4 mr-1" />
                        Related Patterns
                      </h5>
                      <div className="flex flex-wrap gap-2">
                        {pattern.relatedPatterns.map(relatedId => (
                          <span
                            key={relatedId}
                            className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-sm hover:bg-indigo-200 cursor-pointer transition-colors"
                          >
                            {relatedId}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {filteredPatterns.length === 0 && (
        <div className="text-center py-8">
          <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-600 mb-2">
            No Patterns Found
          </h4>
          <p className="text-gray-500">
            Try adjusting your search terms or filters
          </p>
        </div>
      )}

      {/* Pattern Detail Modal */}
      <AnimatePresence>
        {selectedPattern && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setSelectedPattern(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-2">
                    {selectedPattern.name}
                  </h3>
                  <p className="text-gray-600">{selectedPattern.description}</p>
                </div>
                <button
                  onClick={() => setSelectedPattern(null)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ✕
                </button>
              </div>
              
              {/* Pattern content would be expanded here */}
              <div className="text-center py-8 text-gray-500">
                Full pattern details would be displayed here...
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default InteractivePatternExplorer