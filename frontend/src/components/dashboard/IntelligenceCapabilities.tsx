import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain,
  Target,
  Zap,
  Network,
  Search,
  BookOpen,
  TrendingUp,
  Shield,
  Code,
  GitBranch,
  Clock,
  Award,
  Eye,
  Cpu,
  Database,
  CheckCircle
} from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Area, AreaChart } from 'recharts'

// ABOUTME: Visualization of BETTY's actual intelligence capabilities beyond basic metrics  
// ABOUTME: Shows what BETTY can do, has learned, and how it's growing as an AI assistant

interface Capability {
  name: string
  current: number
  potential: number
  trend: 'improving' | 'stable' | 'declining'
  description: string
  examples: string[]
  icon: React.ComponentType<any>
}

interface IntelligenceInsight {
  id: string
  category: string
  title: string
  description: string
  confidence: number
  evidenceCount: number
  impact: 'high' | 'medium' | 'low'
  timeframe: string
}

interface IntelligenceCapabilitiesProps {
  capabilities?: Capability[]
  insights?: IntelligenceInsight[]
}

const IntelligenceCapabilities: React.FC<IntelligenceCapabilitiesProps> = ({
  capabilities = [],
  insights = []
}) => {
  const [selectedCapability, setSelectedCapability] = useState<Capability | null>(null)
  const [viewMode, setViewMode] = useState<'radar' | 'timeline' | 'insights'>('radar')

  // Default capabilities data
  const defaultCapabilities: Capability[] = capabilities.length > 0 ? capabilities : [
    {
      name: 'Pattern Recognition',
      current: 87,
      potential: 95,
      trend: 'improving',
      description: 'Ability to identify recurring patterns in code, architecture, and problem-solving approaches',
      examples: [
        'Detected JWT authentication pattern across 3 projects',
        'Identified database optimization opportunities',
        'Recognized React component structure patterns'
      ],
      icon: Target
    },
    {
      name: 'Cross-Project Knowledge',
      current: 78,
      potential: 90,
      trend: 'improving',
      description: 'Connecting knowledge and solutions across different projects and domains',
      examples: [
        'Applied 137docs auth solution to nautBrain',
        'Connected database patterns between projects',
        'Shared error handling approaches across codebases'
      ],
      icon: Network
    },
    {
      name: 'Context Understanding',
      current: 82,
      potential: 88,
      trend: 'stable',
      description: 'Comprehending project context, requirements, and appropriate solution selection',
      examples: [
        'Understands project-specific constraints',
        'Adapts solutions to current technology stack',
        'Considers team preferences and coding standards'
      ],
      icon: Brain
    },
    {
      name: 'Solution Prediction',
      current: 74,
      potential: 85,
      trend: 'improving',
      description: 'Predicting which solutions will work based on context and historical success',
      examples: [
        '89% accuracy in predicting authentication approach success',
        'Correctly identified database scaling needs',
        'Predicted performance bottlenecks before they occurred'
      ],
      icon: Zap
    },
    {
      name: 'Knowledge Synthesis',
      current: 69,
      potential: 92,
      trend: 'improving',
      description: 'Combining multiple knowledge sources to create novel solutions',
      examples: [
        'Combined React patterns with database optimization',
        'Merged security practices from different projects',
        'Created hybrid solutions from multiple sources'
      ],
      icon: BookOpen
    },
    {
      name: 'Learning Acceleration',
      current: 91,
      potential: 96,
      trend: 'improving',
      description: 'Speed and effectiveness of acquiring and applying new knowledge',
      examples: [
        'Learned Docker patterns from single example',
        'Quickly adapted to new project conventions',
        'Rapid understanding of unfamiliar technologies'
      ],
      icon: TrendingUp
    }
  ]

  // Mock insights data
  const defaultInsights: IntelligenceInsight[] = insights.length > 0 ? insights : [
    {
      id: '1',
      category: 'Pattern Discovery',
      title: 'Emerging API Rate Limiting Pattern',
      description: 'BETTY has identified a new pattern for API rate limiting that appears in 3 recent implementations with 95% success rate.',
      confidence: 0.92,
      evidenceCount: 7,
      impact: 'high',
      timeframe: '2 weeks'
    },
    {
      id: '2',
      category: 'Technology Trends',
      title: 'TypeScript Adoption Accelerating',
      description: 'Detected increased use of TypeScript patterns across projects, suggesting team preference shift.',
      confidence: 0.87,
      evidenceCount: 12,
      impact: 'medium',
      timeframe: '1 month'
    },
    {
      id: '3',
      category: 'Performance Optimization',
      title: 'Database Query Patterns Optimizing',
      description: 'Multiple projects showing similar database optimization patterns that reduce query times by 60%.',
      confidence: 0.94,
      evidenceCount: 5,
      impact: 'high',
      timeframe: '3 weeks'
    },
    {
      id: '4',
      category: 'Security Evolution',
      title: 'Enhanced Input Validation Standards',
      description: 'BETTY observed evolution in input validation approaches, now recommending Zod over manual validation.',
      confidence: 0.89,
      evidenceCount: 8,
      impact: 'medium',
      timeframe: '1 month'
    }
  ]

  // Prepare radar chart data
  const radarData = defaultCapabilities.map(cap => ({
    capability: cap.name.split(' ').slice(0, 2).join(' '),
    current: cap.current,
    potential: cap.potential
  }))

  // Mock timeline data for intelligence growth
  const timelineData = [
    { date: 'Week 1', intelligence: 45, patterns: 12, connections: 3 },
    { date: 'Week 2', intelligence: 52, patterns: 18, connections: 7 },
    { date: 'Week 3', intelligence: 61, patterns: 24, connections: 12 },
    { date: 'Week 4', intelligence: 67, patterns: 31, connections: 18 },
    { date: 'Week 5', intelligence: 74, patterns: 38, connections: 24 },
    { date: 'Week 6', intelligence: 79, patterns: 44, connections: 29 },
    { date: 'Week 7', intelligence: 83, patterns: 51, connections: 35 },
    { date: 'Week 8', intelligence: 87, patterns: 58, connections: 42 }
  ]

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-600 bg-red-100 border-red-200'
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200'
      case 'low': return 'text-green-600 bg-green-100 border-green-200'
      default: return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="w-3 h-3 text-green-500" />
      case 'stable': return <Target className="w-3 h-3 text-blue-500" />
      case 'declining': return <TrendingUp className="w-3 h-3 text-red-500 rotate-180" />
      default: return <Target className="w-3 h-3 text-gray-500" />
    }
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
          <div className="p-2 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Intelligence Capabilities
            </h3>
            <p className="text-sm text-gray-500">
              What BETTY can do and how it's growing smarter
            </p>
          </div>
        </div>
        
        {/* View Mode Selector */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {(['radar', 'timeline', 'insights'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === mode
                  ? 'bg-white text-purple-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {mode === 'radar' && <Target className="w-4 h-4 inline mr-1" />}
              {mode === 'timeline' && <Clock className="w-4 h-4 inline mr-1" />}
              {mode === 'insights' && <Eye className="w-4 h-4 inline mr-1" />}
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Content based on view mode */}
      <AnimatePresence mode="wait">
        {viewMode === 'radar' && (
          <motion.div
            key="radar"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-6"
          >
            {/* Radar Chart */}
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#E5E7EB" />
                  <PolarAngleAxis 
                    dataKey="capability" 
                    tick={{ fontSize: 12, fill: '#6B7280' }}
                  />
                  <PolarRadiusAxis 
                    domain={[0, 100]} 
                    tick={{ fontSize: 10, fill: '#6B7280' }}
                    tickCount={5}
                  />
                  <Radar
                    name="Current"
                    dataKey="current"
                    stroke="#8B5CF6"
                    fill="#8B5CF6"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Radar
                    name="Potential"
                    dataKey="potential"
                    stroke="#06B6D4"
                    fill="transparent"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="flex justify-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-0.5 bg-purple-500"></div>
                <span className="text-gray-600">Current Level</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-0.5 border-b-2 border-cyan-500 border-dashed"></div>
                <span className="text-gray-600">Growth Potential</span>
              </div>
            </div>

            {/* Capability Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {defaultCapabilities.map((capability, index) => {
                const Icon = capability.icon
                const progress = (capability.current / capability.potential) * 100
                
                return (
                  <motion.div
                    key={capability.name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-sm transition-all cursor-pointer"
                    onClick={() => setSelectedCapability(capability)}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-purple-100 rounded-lg">
                          <Icon className="w-4 h-4 text-purple-600" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-700">
                            {capability.name}
                          </h4>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-500">
                              {capability.current}%
                            </span>
                            {getTrendIcon(capability.trend)}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-purple-600">
                          {capability.current}%
                        </div>
                        <div className="text-xs text-gray-500">
                          of {capability.potential}%
                        </div>
                      </div>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ delay: 0.3 + index * 0.1, duration: 0.8 }}
                        className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500"
                      />
                    </div>
                    
                    <p className="text-xs text-gray-500 line-clamp-2">
                      {capability.description}
                    </p>
                  </motion.div>
                )
              })}
            </div>
          </motion.div>
        )}

        {viewMode === 'timeline' && (
          <motion.div
            key="timeline"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-6"
          >
            {/* Intelligence Growth Chart */}
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineData}>
                  <defs>
                    <linearGradient id="intelligenceGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12, fill: '#6B7280' }}
                    axisLine={{ stroke: '#E5E7EB' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12, fill: '#6B7280' }}
                    axisLine={{ stroke: '#E5E7EB' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="intelligence"
                    stroke="#8B5CF6"
                    strokeWidth={3}
                    fill="url(#intelligenceGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Growth Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">87%</div>
                <div className="text-sm text-gray-500">Current Intelligence</div>
                <div className="text-xs text-green-600 mt-1">+42% growth</div>
              </div>
              <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
                <div className="text-2xl font-bold text-blue-600 mb-1">58</div>
                <div className="text-sm text-gray-500">Patterns Learned</div>
                <div className="text-xs text-green-600 mt-1">+46 new patterns</div>
              </div>
              <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
                <div className="text-2xl font-bold text-green-600 mb-1">42</div>
                <div className="text-sm text-gray-500">Cross-Project Links</div>
                <div className="text-xs text-green-600 mt-1">+39 connections</div>
              </div>
            </div>

            {/* Learning Milestones */}
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <h4 className="font-semibold text-gray-700 mb-4 flex items-center">
                <Award className="w-4 h-4 mr-2 text-yellow-500" />
                Recent Learning Milestones
              </h4>
              <div className="space-y-3">
                {[
                  { week: 'Week 8', achievement: 'Mastered Docker containerization patterns', confidence: '94%' },
                  { week: 'Week 7', achievement: 'Connected authentication patterns across all projects', confidence: '91%' },
                  { week: 'Week 6', achievement: 'Learned advanced React optimization techniques', confidence: '87%' },
                  { week: 'Week 5', achievement: 'Identified database performance patterns', confidence: '89%' }
                ].map((milestone, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg"
                  >
                    <div>
                      <div className="font-medium text-gray-700">{milestone.achievement}</div>
                      <div className="text-sm text-gray-500">{milestone.week}</div>
                    </div>
                    <div className="text-sm font-medium text-purple-600">
                      {milestone.confidence}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {viewMode === 'insights' && (
          <motion.div
            key="insights"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-4"
          >
            {defaultInsights.map((insight, index) => (
              <motion.div
                key={insight.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h4 className="font-semibold text-gray-700">{insight.title}</h4>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getImpactColor(insight.impact)}`}>
                        {insight.impact} impact
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{insight.description}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="flex items-center">
                        <Database className="w-3 h-3 mr-1" />
                        {insight.evidenceCount} evidence points
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {insight.timeframe}
                      </span>
                      <span className="flex items-center">
                        <Target className="w-3 h-3 mr-1" />
                        {Math.round(insight.confidence * 100)}% confidence
                      </span>
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-lg font-bold text-purple-600">
                      {Math.round(insight.confidence * 100)}%
                    </div>
                    <div className="text-xs text-gray-500">confidence</div>
                  </div>
                </div>
                
                <div className="bg-purple-50 border border-purple-200 p-3 rounded-lg">
                  <div className="text-sm text-purple-800">
                    <strong>Category:</strong> {insight.category}
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Capability Detail Modal */}
      <AnimatePresence>
        {selectedCapability && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setSelectedCapability(null)}
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
                  {selectedCapability.name}
                </h3>
                <button
                  onClick={() => setSelectedCapability(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <p className="text-gray-600">{selectedCapability.description}</p>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-purple-50 p-3 rounded-lg">
                    <div className="text-sm text-gray-500">Current Level</div>
                    <div className="text-2xl font-bold text-purple-600">
                      {selectedCapability.current}%
                    </div>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-sm text-gray-500">Growth Potential</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {selectedCapability.potential}%
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold text-gray-700 mb-2">Recent Examples</h4>
                  <ul className="space-y-2">
                    {selectedCapability.examples.map((example, index) => (
                      <li key={index} className="flex items-start space-x-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{example}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default IntelligenceCapabilities