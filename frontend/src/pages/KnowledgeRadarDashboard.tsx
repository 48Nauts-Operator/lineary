// ABOUTME: Knowledge Category Radar Dashboard - Interactive visualization of Betty's knowledge patterns
// ABOUTME: Multi-dimensional knowledge visualization with radar charts, category breakdowns, and drill-down capabilities

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  RadarChart, 
  Radar, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts'
import { 
  Brain, 
  Target, 
  TrendingUp, 
  Filter, 
  Search, 
  Grid3X3, 
  Calendar, 
  Zap,
  Eye,
  BookOpen,
  Code,
  MessageSquare,
  Lightbulb,
  FileText,
  Database,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Activity,
  Star,
  Clock,
  Tag
} from 'lucide-react'
import { useKnowledgeRadarData } from '../hooks/useKnowledgeRadar'

// Knowledge Category Colors - Consistent across visualizations
const CATEGORY_COLORS = {
  'Document Intelligence': '#3B82F6',
  'Cloud Security': '#10B981', 
  'Document AI': '#8B5CF6',
  'System Architecture': '#F59E0B',
  'Web Development': '#EF4444',
  'Database Design': '#06B6D4',
  'API Development': '#84CC16',
  'Machine Learning': '#EC4899',
  'DevOps': '#6366F1',
  'UI/UX Design': '#F97316'
}

const VIEW_MODES = [
  { id: 'radar', label: 'Radar View', icon: Target },
  { id: 'grid', label: 'Grid View', icon: Grid3X3 },
  { id: 'timeline', label: 'Timeline', icon: Calendar }
] as const

type ViewMode = typeof VIEW_MODES[number]['id']

interface KnowledgeCategory {
  name: string
  patterns: number
  quality_score: number
  growth_rate: number
  recent_activity: number
  expertise_level: number
  subcategories: string[]
  total_items: number
  last_updated: string
  top_patterns: Array<{
    id: string
    title: string
    usage_count: number
    quality_score: number
  }>
}

interface RadarDataPoint {
  category: string
  expertise: number
  quality: number
  activity: number
  growth: number
  fullMark: number
}

// Mock knowledge data based on current Betty patterns
const MOCK_KNOWLEDGE_CATEGORIES: KnowledgeCategory[] = [
  {
    name: 'Document Intelligence',
    patterns: 2,
    quality_score: 0.93,
    growth_rate: 0.15,
    recent_activity: 8,
    expertise_level: 0.85,
    subcategories: ['vector_database', 'graph_database'],
    total_items: 8,
    last_updated: '2024-01-15T10:30:00Z',
    top_patterns: [
      { id: '1', title: 'Vector Search Optimization', usage_count: 12, quality_score: 0.95 },
      { id: '2', title: 'Graph Relationship Modeling', usage_count: 8, quality_score: 0.91 }
    ]
  },
  {
    name: 'Cloud Security',
    patterns: 1,
    quality_score: 0.98,
    growth_rate: 0.08,
    recent_activity: 3,
    expertise_level: 0.92,
    subcategories: ['aws_infrastructure'],
    total_items: 5,
    last_updated: '2024-01-14T16:45:00Z',
    top_patterns: [
      { id: '3', title: 'AWS Security Best Practices', usage_count: 15, quality_score: 0.98 }
    ]
  },
  {
    name: 'Document AI',
    patterns: 1,
    quality_score: 0.94,
    growth_rate: 0.12,
    recent_activity: 6,
    expertise_level: 0.88,
    subcategories: ['multimodal_processing'],
    total_items: 4,
    last_updated: '2024-01-13T14:20:00Z',
    top_patterns: [
      { id: '4', title: 'Multimodal Document Processing', usage_count: 10, quality_score: 0.94 }
    ]
  },
  {
    name: 'System Architecture',
    patterns: 1,
    quality_score: 0.96,
    growth_rate: 0.10,
    recent_activity: 4,
    expertise_level: 0.90,
    subcategories: ['microservices'],
    total_items: 6,
    last_updated: '2024-01-12T09:15:00Z',
    top_patterns: [
      { id: '5', title: 'Microservices Design Patterns', usage_count: 18, quality_score: 0.96 }
    ]
  },
  {
    name: 'Web Development',
    patterns: 3,
    quality_score: 0.87,
    growth_rate: 0.20,
    recent_activity: 12,
    expertise_level: 0.82,
    subcategories: ['react_patterns', 'api_design', 'frontend_architecture'],
    total_items: 12,
    last_updated: '2024-01-15T11:00:00Z',
    top_patterns: [
      { id: '6', title: 'React Component Patterns', usage_count: 22, quality_score: 0.89 },
      { id: '7', title: 'API Design Principles', usage_count: 16, quality_score: 0.85 }
    ]
  }
]

const KnowledgeRadarDashboard: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('radar')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterQuality, setFilterQuality] = useState<number>(0)
  const [expandedCard, setExpandedCard] = useState<string | null>(null)

  // Mock data hook - in real implementation this would fetch from Betty API
  const { 
    categories = MOCK_KNOWLEDGE_CATEGORIES, 
    isLoading = false, 
    stats 
  } = useKnowledgeRadarData()

  // Transform data for radar chart
  const radarData: RadarDataPoint[] = categories.map(category => ({
    category: category.name,
    expertise: Math.round(category.expertise_level * 10),
    quality: Math.round(category.quality_score * 10), 
    activity: Math.min(category.recent_activity, 10),
    growth: Math.round(category.growth_rate * 50), // Scale for visibility
    fullMark: 10
  }))

  // Filter categories based on search and quality
  const filteredCategories = categories.filter(category => {
    const matchesSearch = category.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         category.subcategories.some(sub => sub.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesQuality = category.quality_score >= filterQuality / 10
    return matchesSearch && matchesQuality
  })

  // Calculate aggregate stats
  const totalPatterns = categories.reduce((sum, cat) => sum + cat.patterns, 0)
  const avgQuality = categories.reduce((sum, cat) => sum + cat.quality_score, 0) / categories.length
  const totalItems = categories.reduce((sum, cat) => sum + cat.total_items, 0)
  const avgGrowth = categories.reduce((sum, cat) => sum + cat.growth_rate, 0) / categories.length

  if (isLoading) {
    return (
      <div className="min-h-screen bg-neural-network flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card rounded-2xl p-8 text-center"
        >
          <div className="animate-spin w-8 h-8 border-2 border-betty-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">
            Analyzing Knowledge Patterns
          </h2>
          <p className="text-gray-500">
            Mapping Andre's expertise across domains...
          </p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neural-network p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="flex items-center justify-center mb-4">
          <Brain className="w-8 h-8 text-betty-500 mr-3" />
          <h1 className="text-4xl font-bold text-white">
            Knowledge Category Radar
          </h1>
        </div>
        <p className="text-xl text-white/80 max-w-3xl mx-auto">
          Interactive visualization of Andre's knowledge patterns and expertise across different domains.
          Based on {totalItems} knowledge items across {categories.length} categories.
        </p>
      </motion.div>

      {/* Stats Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
      >
        <div className="glass-card rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-betty-500">{totalPatterns}</div>
          <div className="text-sm text-gray-600">Knowledge Patterns</div>
        </div>
        <div className="glass-card rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-success-500">
            {Math.round(avgQuality * 100)}%
          </div>
          <div className="text-sm text-gray-600">Avg Quality Score</div>
        </div>
        <div className="glass-card rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-purple-500">{totalItems}</div>
          <div className="text-sm text-gray-600">Total Items</div>
        </div>
        <div className="glass-card rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-warning-500">
            +{Math.round(avgGrowth * 100)}%
          </div>
          <div className="text-sm text-gray-600">Avg Growth Rate</div>
        </div>
      </motion.div>

      {/* Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-card rounded-xl p-6 mb-8"
      >
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* View Mode Toggle */}
          <div className="flex space-x-1 bg-white/10 backdrop-blur-lg rounded-lg p-1">
            {VIEW_MODES.map(mode => {
              const Icon = mode.icon
              return (
                <button
                  key={mode.id}
                  onClick={() => setViewMode(mode.id)}
                  className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    viewMode === mode.id
                      ? 'bg-white text-gray-800 shadow-sm'
                      : 'text-white/80 hover:text-white hover:bg-white/10'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {mode.label}
                </button>
              )
            })}
          </div>

          {/* Search and Filters */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search categories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-betty-500/50 focus:border-transparent"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <input
                type="range"
                min="0"
                max="10"
                value={filterQuality}
                onChange={(e) => setFilterQuality(Number(e.target.value))}
                className="w-20"
              />
              <span className="text-sm text-white/70">
                Quality ≥ {filterQuality}/10
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <AnimatePresence mode="wait">
        {viewMode === 'radar' && (
          <motion.div
            key="radar"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="grid grid-cols-1 xl:grid-cols-2 gap-8"
          >
            {/* Radar Chart */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-gray-700 mb-6 flex items-center">
                <Target className="w-5 h-5 mr-2" />
                Knowledge Expertise Radar
              </h3>
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="category" />
                    <PolarRadiusAxis 
                      angle={90} 
                      domain={[0, 10]}
                      tick={false}
                    />
                    <Radar
                      name="Expertise Level"
                      dataKey="expertise"
                      stroke="#3B82F6"
                      fill="#3B82F6"
                      fillOpacity={0.1}
                      strokeWidth={2}
                    />
                    <Radar
                      name="Quality Score"
                      dataKey="quality"
                      stroke="#10B981"
                      fill="#10B981"
                      fillOpacity={0.1}
                      strokeWidth={2}
                    />
                    <Radar
                      name="Recent Activity"
                      dataKey="activity"
                      stroke="#F59E0B"
                      fill="#F59E0B"
                      fillOpacity={0.1}
                      strokeWidth={2}
                    />
                    <Tooltip 
                      formatter={(value, name) => [value, name]}
                      labelFormatter={(label) => `Category: ${label}`}
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        border: 'none',
                        borderRadius: '12px',
                        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)'
                      }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                  Expertise Level
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  Quality Score
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                  Recent Activity
                </div>
              </div>
            </div>

            {/* Quality vs Activity Scatter */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-gray-700 mb-6 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2" />
                Quality vs Activity Analysis
              </h3>
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={filteredCategories}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip 
                      formatter={(value, name, props) => [
                        typeof value === 'number' ? value.toFixed(2) : value, 
                        name
                      ]}
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        border: 'none',
                        borderRadius: '12px'
                      }}
                    />
                    <Bar dataKey="quality_score" fill="#10B981" name="Quality Score" />
                    <Bar dataKey="recent_activity" fill="#3B82F6" name="Recent Activity" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </motion.div>
        )}

        {viewMode === 'grid' && (
          <motion.div
            key="grid"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
          >
            {filteredCategories.map((category, index) => (
              <motion.div
                key={category.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`glass-card rounded-xl p-6 cursor-pointer transition-all duration-300 ${
                  expandedCard === category.name 
                    ? 'ring-2 ring-betty-500 shadow-xl' 
                    : 'hover:shadow-lg hover:scale-105'
                }`}
                onClick={() => setExpandedCard(
                  expandedCard === category.name ? null : category.name
                )}
              >
                {/* Category Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700 mb-1">
                      {category.name}
                    </h3>
                    <div className="flex items-center text-sm text-gray-500">
                      <BookOpen className="w-4 h-4 mr-1" />
                      {category.total_items} items
                    </div>
                  </div>
                  <div className="flex items-center">
                    <Star className="w-4 h-4 text-yellow-500 mr-1" />
                    <span className="text-sm font-medium">
                      {Math.round(category.quality_score * 100)}%
                    </span>
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-xl font-bold text-betty-500">
                      {category.patterns}
                    </div>
                    <div className="text-xs text-gray-500">Patterns</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-green-500">
                      {Math.round(category.expertise_level * 100)}%
                    </div>
                    <div className="text-xs text-gray-500">Expertise</div>
                  </div>
                </div>

                {/* Activity Indicator */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Recent Activity</span>
                    <span>{category.recent_activity}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-betty-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(category.recent_activity * 10, 100)}%` }}
                    ></div>
                  </div>
                </div>

                {/* Expandable Content */}
                <AnimatePresence>
                  {expandedCard === category.name && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="border-t border-gray-200 pt-4 mt-4"
                    >
                      {/* Subcategories */}
                      <div className="mb-4">
                        <div className="text-sm font-medium text-gray-600 mb-2">
                          Subcategories
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {category.subcategories.map(sub => (
                            <span
                              key={sub}
                              className="px-2 py-1 bg-betty-100 text-betty-700 rounded-md text-xs"
                            >
                              {sub}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Top Patterns */}
                      <div className="mb-4">
                        <div className="text-sm font-medium text-gray-600 mb-2">
                          Top Patterns
                        </div>
                        {category.top_patterns.map(pattern => (
                          <div
                            key={pattern.id}
                            className="flex items-center justify-between py-1"
                          >
                            <span className="text-xs text-gray-600 truncate">
                              {pattern.title}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500">
                                {pattern.usage_count}x
                              </span>
                              <div className="flex items-center">
                                <Star className="w-3 h-3 text-yellow-500 mr-1" />
                                <span className="text-xs">
                                  {Math.round(pattern.quality_score * 100)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Last Updated */}
                      <div className="flex items-center text-xs text-gray-500">
                        <Clock className="w-3 h-3 mr-1" />
                        Updated {new Date(category.last_updated).toLocaleDateString()}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Expand/Collapse Icon */}
                <div className="flex justify-center mt-2">
                  {expandedCard === category.name ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}

        {viewMode === 'timeline' && (
          <motion.div
            key="timeline"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-8"
          >
            {/* Growth Trend Chart */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-gray-700 mb-6 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                Knowledge Growth Timeline
              </h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={categories}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        border: 'none',
                        borderRadius: '12px'
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="total_items"
                      stroke="#3B82F6"
                      fill="#3B82F6"
                      fillOpacity={0.3}
                      name="Total Items"
                    />
                    <Area
                      type="monotone"
                      dataKey="patterns"
                      stroke="#10B981"
                      fill="#10B981"
                      fillOpacity={0.3}
                      name="Patterns"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Category Distribution Pie Chart */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              <div className="glass-card rounded-2xl p-6">
                <h3 className="text-xl font-semibold text-gray-700 mb-6 flex items-center">
                  <Activity className="w-5 h-5 mr-2" />
                  Knowledge Distribution
                </h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categories}
                        dataKey="total_items"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label={(entry) => `${entry.name} (${entry.total_items})`}
                      >
                        {categories.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={Object.values(CATEGORY_COLORS)[index % Object.values(CATEGORY_COLORS).length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Quality Trends */}
              <div className="glass-card rounded-2xl p-6">
                <h3 className="text-xl font-semibold text-gray-700 mb-6 flex items-center">
                  <Star className="w-5 h-5 mr-2" />
                  Quality Trends
                </h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={categories}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 1]} />
                      <Tooltip 
                        formatter={(value) => [
                          `${Math.round(Number(value) * 100)}%`,
                          'Quality Score'
                        ]}
                        contentStyle={{
                          backgroundColor: 'rgba(255, 255, 255, 0.9)',
                          border: 'none',
                          borderRadius: '12px'
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="quality_score"
                        stroke="#10B981"
                        strokeWidth={3}
                        dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Knowledge Gap Analysis */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="mt-8 glass-card rounded-2xl p-6"
      >
        <h3 className="text-xl font-semibold text-gray-700 mb-6 flex items-center">
          <Lightbulb className="w-5 h-5 mr-2" />
          Knowledge Enhancement Opportunities
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <h4 className="font-semibold text-blue-800 mb-2">Expand Coverage</h4>
            <p className="text-blue-700 text-sm mb-3">
              Categories with high quality but low volume could benefit from more examples.
            </p>
            <div className="space-y-1">
              {categories
                .filter(cat => cat.quality_score > 0.9 && cat.total_items < 5)
                .map(cat => (
                  <div key={cat.name} className="text-xs text-blue-600">
                    • {cat.name}
                  </div>
                ))}
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <h4 className="font-semibold text-green-800 mb-2">Quality Improvement</h4>
            <p className="text-green-700 text-sm mb-3">
              Focus on improving quality scores in these high-volume categories.
            </p>
            <div className="space-y-1">
              {categories
                .filter(cat => cat.quality_score < 0.9 && cat.total_items > 8)
                .map(cat => (
                  <div key={cat.name} className="text-xs text-green-600">
                    • {cat.name} ({Math.round(cat.quality_score * 100)}%)
                  </div>
                ))}
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <h4 className="font-semibold text-purple-800 mb-2">New Domains</h4>
            <p className="text-purple-700 text-sm mb-3">
              Suggested knowledge areas to explore based on current patterns.
            </p>
            <div className="space-y-1 text-xs text-purple-600">
              <div>• Testing & Quality Assurance</div>
              <div>• Performance Optimization</div>
              <div>• Data Analytics</div>
              <div>• Mobile Development</div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default KnowledgeRadarDashboard