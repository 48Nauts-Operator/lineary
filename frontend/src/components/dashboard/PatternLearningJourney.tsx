import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, 
  Lightbulb, 
  Target, 
  TrendingUp, 
  CheckCircle, 
  ArrowRight,
  Clock,
  Users,
  Zap,
  Brain
} from 'lucide-react'

// ABOUTME: Interactive visualization showing the lifecycle of pattern learning in BETTY
// ABOUTME: From discovery through mastery with user engagement for validation and enhancement

interface PatternStage {
  id: string
  name: string
  icon: React.ComponentType<any>
  color: string
  description: string
  timeInStage?: number
  successRate?: number
  userInteractions?: number
}

interface PatternJourneyItem {
  patternName: string
  currentStage: string
  stages: PatternStage[]
  discoveredAt: string
  lastUpdated: string
  confidenceScore: number
  usageCount: number
  projectsApplied: string[]
  evolutionHistory: Array<{
    stage: string
    timestamp: string
    trigger: string
    outcome: string
  }>
}

interface PatternLearningJourneyProps {
  patterns?: PatternJourneyItem[]
}

const PatternLearningJourney: React.FC<PatternLearningJourneyProps> = ({ patterns = [] }) => {
  const [selectedPattern, setSelectedPattern] = useState<PatternJourneyItem | null>(null)
  const [viewMode, setViewMode] = useState<'overview' | 'detail'>('overview')

  const defaultStages: PatternStage[] = [
    {
      id: 'discovery',
      name: 'Discovery',
      icon: Search,
      color: 'text-blue-500',
      description: 'Pattern detected through code analysis and user interactions'
    },
    {
      id: 'validation',
      name: 'Validation',
      icon: Lightbulb,
      color: 'text-yellow-500', 
      description: 'Testing pattern effectiveness across different contexts'
    },
    {
      id: 'optimization',
      name: 'Optimization',
      icon: Target,
      color: 'text-orange-500',
      description: 'Refining pattern based on success metrics and feedback'
    },
    {
      id: 'integration',
      name: 'Integration',
      icon: TrendingUp,
      color: 'text-purple-500',
      description: 'Applying pattern across projects with confidence'
    },
    {
      id: 'mastery',
      name: 'Mastery',
      icon: CheckCircle,
      color: 'text-green-500',
      description: 'Pattern fully validated and automatically suggested'
    }
  ]

  // Mock data for demonstration
  const mockPatterns: PatternJourneyItem[] = patterns.length > 0 ? patterns : [
    {
      patternName: 'JWT Authentication Middleware',
      currentStage: 'mastery',
      stages: defaultStages,
      discoveredAt: '2025-01-15T10:30:00Z',
      lastUpdated: '2025-02-01T14:20:00Z',
      confidenceScore: 0.95,
      usageCount: 12,
      projectsApplied: ['137docs', 'nautBrain', 'Betty'],
      evolutionHistory: [
        {
          stage: 'discovery',
          timestamp: '2025-01-15T10:30:00Z',
          trigger: 'Repeated JWT implementation patterns detected',
          outcome: 'Pattern identified with 78% similarity across projects'
        },
        {
          stage: 'validation', 
          timestamp: '2025-01-18T09:15:00Z',
          trigger: 'User validated effectiveness in 137docs',
          outcome: 'Success rate improved to 85%'
        },
        {
          stage: 'mastery',
          timestamp: '2025-02-01T14:20:00Z',
          trigger: 'Consistent 95%+ success across all applications',
          outcome: 'Auto-suggest enabled for authentication tasks'
        }
      ]
    },
    {
      patternName: 'Database Connection Pooling',
      currentStage: 'optimization',
      stages: defaultStages,
      discoveredAt: '2025-01-20T16:45:00Z', 
      lastUpdated: '2025-02-03T11:30:00Z',
      confidenceScore: 0.72,
      usageCount: 5,
      projectsApplied: ['nautBrain', 'Betty'],
      evolutionHistory: []
    },
    {
      patternName: 'React Component State Management',
      currentStage: 'validation',
      stages: defaultStages,
      discoveredAt: '2025-01-25T08:20:00Z',
      lastUpdated: '2025-02-04T16:15:00Z', 
      confidenceScore: 0.68,
      usageCount: 3,
      projectsApplied: ['137docs'],
      evolutionHistory: []
    }
  ]

  const getStageIndex = (stageName: string) => {
    return defaultStages.findIndex(stage => stage.id === stageName)
  }

  const getStageProgress = (currentStage: string) => {
    const currentIndex = getStageIndex(currentStage)
    return ((currentIndex + 1) / defaultStages.length) * 100
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
          <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Pattern Learning Journey
            </h3>
            <p className="text-sm text-gray-500">
              How BETTY discovers, validates, and masters patterns over time
            </p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setViewMode('overview')}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'overview' 
                ? 'bg-purple-100 text-purple-700' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setViewMode('detail')}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'detail' 
                ? 'bg-purple-100 text-purple-700' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Details
          </button>
        </div>
      </div>

      {/* Stage Legend */}
      <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gradient-to-r from-gray-50 to-purple-50 rounded-lg">
        {defaultStages.map((stage, index) => {
          const Icon = stage.icon
          return (
            <div key={stage.id} className="flex items-center space-x-2">
              <Icon className={`w-4 h-4 ${stage.color}`} />
              <span className="text-sm font-medium text-gray-600">{stage.name}</span>
              {index < defaultStages.length - 1 && (
                <ArrowRight className="w-3 h-3 text-gray-400 ml-2" />
              )}
            </div>
          )
        })}
      </div>

      {viewMode === 'overview' ? (
        /* Pattern Cards Overview */
        <div className="space-y-4">
          {mockPatterns.map((pattern, index) => {
            const currentStageIndex = getStageIndex(pattern.currentStage)
            const progress = getStageProgress(pattern.currentStage)
            const currentStageData = defaultStages[currentStageIndex]
            
            return (
              <motion.div
                key={pattern.patternName}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-all cursor-pointer"
                onClick={() => setSelectedPattern(pattern)}
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-1">
                      {pattern.patternName}
                    </h4>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {new Date(pattern.discoveredAt).toLocaleDateString()}
                      </span>
                      <span className="flex items-center">
                        <Target className="w-3 h-3 mr-1" />
                        {pattern.usageCount} uses
                      </span>
                      <span className="flex items-center">
                        <Users className="w-3 h-3 mr-1" />
                        {pattern.projectsApplied.length} projects
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center space-x-2 mb-1">
                      {currentStageData && (
                        <>
                          <currentStageData.icon className={`w-4 h-4 ${currentStageData.color}`} />
                          <span className="text-sm font-medium text-gray-600">
                            {currentStageData.name}
                          </span>
                        </>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {Math.round(pattern.confidenceScore * 100)}% confidence
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ delay: 0.3 + index * 0.1, duration: 0.8 }}
                    className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
                  />
                </div>

                {/* Stage Indicators */}
                <div className="flex justify-between">
                  {defaultStages.map((stage, stageIndex) => {
                    const Icon = stage.icon
                    const isActive = stageIndex <= currentStageIndex
                    const isCurrent = stageIndex === currentStageIndex
                    
                    return (
                      <div
                        key={stage.id}
                        className={`flex flex-col items-center transition-all ${
                          isActive ? 'opacity-100' : 'opacity-30'
                        }`}
                      >
                        <div className={`p-1.5 rounded-full mb-1 ${
                          isCurrent 
                            ? 'bg-purple-100 border-2 border-purple-500' 
                            : isActive 
                              ? 'bg-green-100 border-2 border-green-500'
                              : 'bg-gray-100 border-2 border-gray-300'
                        }`}>
                          <Icon className={`w-3 h-3 ${
                            isCurrent 
                              ? 'text-purple-600' 
                              : isActive 
                                ? 'text-green-600'
                                : 'text-gray-400'
                          }`} />
                        </div>
                        <span className="text-xs text-gray-500">{stage.name}</span>
                      </div>
                    )
                  })}
                </div>
              </motion.div>
            )
          })}
        </div>
      ) : (
        /* Detailed Timeline View */
        <div className="space-y-6">
          {mockPatterns.map((pattern, index) => (
            <motion.div
              key={pattern.patternName}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.2 }}
              className="bg-white p-6 rounded-lg border border-gray-200"
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold text-gray-700">
                  {pattern.patternName}
                </h4>
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium text-gray-600">
                    {Math.round(pattern.confidenceScore * 100)}% Confidence
                  </span>
                </div>
              </div>

              {/* Evolution Timeline */}
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-200 to-pink-200"></div>
                
                {pattern.evolutionHistory.map((event, eventIndex) => {
                  const stageData = defaultStages.find(s => s.id === event.stage)
                  const Icon = stageData?.icon || Search
                  
                  return (
                    <motion.div
                      key={eventIndex}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * eventIndex }}
                      className="relative flex items-start space-x-4 pb-6"
                    >
                      <div className={`p-2 rounded-full bg-white border-2 border-purple-500 z-10`}>
                        <Icon className="w-4 h-4 text-purple-600" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="font-medium text-gray-700 capitalize">
                            {event.stage} Stage
                          </h5>
                          <span className="text-xs text-gray-500">
                            {new Date(event.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-2">
                          <strong>Trigger:</strong> {event.trigger}
                        </p>
                        
                        <p className="text-sm text-green-600">
                          <strong>Outcome:</strong> {event.outcome}
                        </p>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          ))}
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
              className="bg-white rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-800">
                  {selectedPattern.patternName}
                </h3>
                <button
                  onClick={() => setSelectedPattern(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              {/* Pattern details content would go here */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-sm text-gray-500">Usage Count</div>
                    <div className="text-lg font-semibold text-gray-700">
                      {selectedPattern.usageCount}
                    </div>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-sm text-gray-500">Success Rate</div>
                    <div className="text-lg font-semibold text-gray-700">
                      {Math.round(selectedPattern.confidenceScore * 100)}%
                    </div>
                  </div>
                </div>
                
                <div>
                  <div className="text-sm text-gray-500 mb-2">Applied in Projects</div>
                  <div className="flex flex-wrap gap-2">
                    {selectedPattern.projectsApplied.map(project => (
                      <span
                        key={project}
                        className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-sm"
                      >
                        {project}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default PatternLearningJourney