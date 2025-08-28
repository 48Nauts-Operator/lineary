import React from 'react'
import { motion } from 'framer-motion'
import {
  Target,
  TrendingUp,
  Star,
  Brain,
  Award,
  Activity,
  BarChart3
} from 'lucide-react'
import { useExpertiseLevels } from '../../hooks/useKnowledgeVisualization'

interface ExpertiseRadarChartProps {
  confidenceThreshold: number
}

const ExpertiseRadarChart: React.FC<ExpertiseRadarChartProps> = ({
  confidenceThreshold
}) => {
  const {
    data: expertiseLevels,
    isLoading,
    error
  } = useExpertiseLevels(confidenceThreshold)

  const getProficiencyColor = (level: string): string => {
    const colors: Record<string, string> = {
      'Expert': 'text-green-400 bg-green-400/10 border-green-400/30',
      'Advanced': 'text-betty-400 bg-betty-400/10 border-betty-400/30',
      'Intermediate': 'text-purple-400 bg-purple-400/10 border-purple-400/30',
      'Beginner': 'text-pink-400 bg-pink-400/10 border-pink-400/30',
      'Basic': 'text-gray-400 bg-gray-400/10 border-gray-400/30'
    }
    return colors[level] || colors['Basic']
  }

  const getConfidenceDescription = (score: number): string => {
    if (score >= 0.9) return 'Exceptional mastery'
    if (score >= 0.8) return 'Strong expertise'
    if (score >= 0.7) return 'Good proficiency'
    if (score >= 0.6) return 'Adequate knowledge'
    if (score >= 0.5) return 'Basic understanding'
    return 'Limited familiarity'
  }

  // Create radar chart data points
  const radarPoints = expertiseLevels?.slice(0, 8).map((expertise, index) => {
    const angle = (index / 8) * 2 * Math.PI - Math.PI / 2 // Start from top
    const radius = expertise.confidence_score * 120 // Max radius of 120
    const x = 150 + radius * Math.cos(angle) // Center at 150,150
    const y = 150 + radius * Math.sin(angle)
    return { x, y, ...expertise }
  }) || []

  // Create background grid circles
  const gridCircles = [0.2, 0.4, 0.6, 0.8, 1.0].map(level => level * 120)

  if (isLoading) {
    return (
      <div className="glass-morphism border border-white/10 rounded-lg p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Target className="w-12 h-12 text-betty-400 mx-auto mb-4 animate-pulse" />
            <div className="text-white font-semibold mb-2">Analyzing Expertise</div>
            <div className="text-white/60">Calculating confidence scores...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-morphism border border-red-500/20 rounded-lg p-8 text-center">
        <Target className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-red-400 text-lg font-semibold mb-2">Failed to Load Expertise Data</h3>
        <p className="text-white/60">{error.message || 'An unexpected error occurred'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Expertise Radar</h2>
          <p className="text-white/70">
            {expertiseLevels?.length || 0} expertise domains • Min confidence: {Math.round(confidenceThreshold * 100)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Radar Chart */}
        <div className="glass-morphism border border-white/10 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center">
            <Target className="w-5 h-5 mr-2 text-betty-400" />
            Expertise Radar Chart
          </h3>

          <div className="flex justify-center">
            <svg width="300" height="300" className="overflow-visible">
              {/* Background grid */}
              <g opacity="0.2">
                {gridCircles.map((radius, index) => (
                  <circle
                    key={index}
                    cx="150"
                    cy="150"
                    r={radius}
                    fill="none"
                    stroke="white"
                    strokeWidth="1"
                    strokeDasharray="2,2"
                  />
                ))}
                {/* Grid lines */}
                {Array.from({ length: 8 }, (_, i) => {
                  const angle = (i / 8) * 2 * Math.PI - Math.PI / 2
                  const x2 = 150 + 120 * Math.cos(angle)
                  const y2 = 150 + 120 * Math.sin(angle)
                  return (
                    <line
                      key={i}
                      x1="150"
                      y1="150"
                      x2={x2}
                      y2={y2}
                      stroke="white"
                      strokeWidth="1"
                      strokeDasharray="2,2"
                    />
                  )
                })}
              </g>

              {/* Radar polygon */}
              {radarPoints.length >= 3 && (
                <motion.polygon
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 0.3, scale: 1 }}
                  transition={{ duration: 0.8 }}
                  points={radarPoints.map(p => `${p.x},${p.y}`).join(' ')}
                  fill="url(#radarGradient)"
                  stroke="rgba(139, 92, 246, 0.6)"
                  strokeWidth="2"
                />
              )}

              {/* Data points */}
              {radarPoints.map((point, index) => (
                <motion.g
                  key={point.domain}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                >
                  {/* Point circle */}
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="6"
                    fill="rgba(139, 92, 246, 0.8)"
                    stroke="white"
                    strokeWidth="2"
                    className="cursor-pointer hover:r-8 transition-all"
                  />
                  
                  {/* Domain label */}
                  <text
                    x={point.x + (point.x > 150 ? 12 : -12)}
                    y={point.y}
                    textAnchor={point.x > 150 ? 'start' : 'end'}
                    className="text-xs fill-white/80 font-medium pointer-events-none"
                    dominantBaseline="middle"
                  >
                    {point.domain.replace(/([A-Z])/g, ' $1').trim()}
                  </text>
                </motion.g>
              ))}

              {/* Gradient definition */}
              <defs>
                <radialGradient id="radarGradient" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="rgba(139, 92, 246, 0.4)" />
                  <stop offset="100%" stopColor="rgba(139, 92, 246, 0.1)" />
                </radialGradient>
              </defs>
            </svg>
          </div>

          {/* Legend */}
          <div className="mt-4 text-center">
            <div className="text-white/60 text-sm mb-2">Confidence Scale</div>
            <div className="flex justify-center space-x-4 text-xs">
              <span className="text-white/40">20%</span>
              <span className="text-white/40">40%</span>
              <span className="text-white/40">60%</span>
              <span className="text-white/40">80%</span>
              <span className="text-white/40">100%</span>
            </div>
          </div>
        </div>

        {/* Expertise List */}
        <div className="glass-morphism border border-white/10 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center">
            <Brain className="w-5 h-5 mr-2 text-betty-400" />
            Domain Expertise
          </h3>

          <div className="space-y-3 max-h-80 overflow-y-auto">
            {expertiseLevels?.map((expertise, index) => (
              <motion.div
                key={expertise.domain}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`border rounded-lg p-4 transition-all hover:scale-102 ${getProficiencyColor(expertise.proficiency_level)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{expertise.domain}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full border ${getProficiencyColor(expertise.proficiency_level)}`}>
                    {expertise.proficiency_level}
                  </span>
                </div>

                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="opacity-80">Confidence Score</span>
                  <span className="font-semibold">{Math.round(expertise.confidence_score * 100)}%</span>
                </div>

                <div className="w-full bg-black/20 rounded-full h-2 mb-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${expertise.confidence_score * 100}%` }}
                    transition={{ delay: index * 0.05 + 0.2, duration: 0.5 }}
                    className="h-2 rounded-full bg-current opacity-60"
                  />
                </div>

                <div className="flex items-center justify-between text-xs opacity-70">
                  <span>{expertise.knowledge_items_count} items</span>
                  <span>{getConfidenceDescription(expertise.confidence_score)}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Expertise Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Award className="w-6 h-6 text-green-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {expertiseLevels?.filter(e => e.proficiency_level === 'Expert').length || 0}
          </div>
          <div className="text-sm text-white/60">Expert</div>
        </div>

        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Star className="w-6 h-6 text-betty-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {expertiseLevels?.filter(e => e.proficiency_level === 'Advanced').length || 0}
          </div>
          <div className="text-sm text-white/60">Advanced</div>
        </div>

        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <TrendingUp className="w-6 h-6 text-purple-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {expertiseLevels?.filter(e => e.proficiency_level === 'Intermediate').length || 0}
          </div>
          <div className="text-sm text-white/60">Intermediate</div>
        </div>

        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Activity className="w-6 h-6 text-pink-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {expertiseLevels ? 
              (expertiseLevels.reduce((sum, e) => sum + e.confidence_score, 0) / expertiseLevels.length * 100).toFixed(0) 
              : '0'}%
          </div>
          <div className="text-sm text-white/60">Avg Confidence</div>
        </div>

        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <BarChart3 className="w-6 h-6 text-orange-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {expertiseLevels?.reduce((sum, e) => sum + e.knowledge_items_count, 0) || 0}
          </div>
          <div className="text-sm text-white/60">Total Items</div>
        </div>
      </div>

      {expertiseLevels?.length === 0 && (
        <div className="text-center py-12">
          <Target className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <h3 className="text-white/60 text-lg font-medium mb-2">No expertise data</h3>
          <p className="text-white/40">
            Expertise levels will be calculated as Betty learns and processes knowledge
          </p>
        </div>
      )}
    </div>
  )
}

export default ExpertiseRadarChart