import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Code, 
  BookOpen, 
  GitBranch, 
  TrendingUp, 
  Search, 
  Filter,
  Eye,
  BarChart3,
  Network,
  Clock,
  Brain,
  Target,
  Layers,
  Activity
} from 'lucide-react'
import Layout from '../components/Layout'
import { useKnowledgeVisualization } from '../hooks/useKnowledgeVisualization'
import CodeRepositoriesView from '../components/knowledge/CodeRepositoriesView'
import DocumentationBrowser from '../components/knowledge/DocumentationBrowser'
import KnowledgeGraphVisualization from '../components/knowledge/KnowledgeGraphVisualization'
import LearningTimelineView from '../components/knowledge/LearningTimelineView'
import ExpertiseRadarChart from '../components/knowledge/ExpertiseRadarChart'
import InteractiveCodeBrowser from '../components/knowledge/InteractiveCodeBrowser'

type ViewMode = 'overview' | 'code' | 'documentation' | 'graph' | 'timeline' | 'expertise' | 'browser'

const KnowledgeVisualizationDashboard: React.FC = () => {
  const [activeView, setActiveView] = useState<ViewMode>('overview')
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    programmingLanguage: '',
    documentationType: '',
    knowledgeDomain: '',
    confidenceThreshold: 0.5
  })

  const {
    dashboardStats,
    isLoadingStats,
    error
  } = useKnowledgeVisualization()

  const viewOptions = [
    { id: 'overview', label: 'Overview', icon: BarChart3, description: 'Knowledge statistics and metrics' },
    { id: 'code', label: 'Code Analysis', icon: Code, description: 'Repository and code pattern analysis' },
    { id: 'documentation', label: 'Documentation', icon: BookOpen, description: 'Documentation sources and content' },
    { id: 'graph', label: 'Knowledge Graph', icon: Network, description: 'Knowledge relationships and connections' },
    { id: 'timeline', label: 'Learning Timeline', icon: Clock, description: 'Knowledge acquisition over time' },
    { id: 'expertise', label: 'Expertise Map', icon: Target, description: 'Domain expertise and confidence levels' },
    { id: 'browser', label: 'Code Browser', icon: Eye, description: 'Interactive code and file explorer' }
  ]

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="text-red-400 text-lg font-semibold mb-2">
              Failed to load knowledge visualization
            </div>
            <div className="text-white/60">
              {error.message || 'An unexpected error occurred'}
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header with Stats */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4"
        >
          <div>
            <p className="text-white/70 text-lg">
              Explore Betty's extensive learned knowledge across code, documentation, and patterns
            </p>
          </div>

          {/* Quick Stats */}
          {!isLoadingStats && dashboardStats && (
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex items-center space-x-6 bg-white/5 rounded-lg px-6 py-4"
            >
              <div className="text-center">
                <div className="text-2xl font-bold text-betty-400">
                  {dashboardStats.total_code_lines.toLocaleString()}
                </div>
                <div className="text-xs text-white/60">Lines of Code</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {dashboardStats.total_repositories}
                </div>
                <div className="text-xs text-white/60">Repositories</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-pink-400">
                  {dashboardStats.total_documentation_sources}
                </div>
                <div className="text-xs text-white/60">Doc Sources</div>
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* Search and Filters */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="glass-morphism border border-white/10 rounded-lg p-4"
        >
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="text"
                  placeholder="Search across all knowledge..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-betty-400 transition-colors"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
              <select
                value={filters.programmingLanguage}
                onChange={(e) => setFilters(prev => ({ ...prev, programmingLanguage: e.target.value }))}
                className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-betty-400 transition-colors"
              >
                <option value="">All Languages</option>
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="sql">SQL</option>
              </select>

              <select
                value={filters.documentationType}
                onChange={(e) => setFilters(prev => ({ ...prev, documentationType: e.target.value }))}
                className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-betty-400 transition-colors"
              >
                <option value="">All Docs</option>
                <option value="api">API Documentation</option>
                <option value="tutorial">Tutorials</option>
                <option value="reference">Reference Guides</option>
                <option value="examples">Code Examples</option>
              </select>

              <button className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors">
                <Filter className="w-4 h-4 text-white/60" />
              </button>
            </div>
          </div>
        </motion.div>

        {/* View Navigation */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex flex-wrap gap-2"
        >
          {viewOptions.map((option) => {
            const Icon = option.icon
            return (
              <motion.button
                key={option.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveView(option.id as ViewMode)}
                className={`flex items-center space-x-2 px-4 py-3 rounded-lg transition-all ${
                  activeView === option.id
                    ? 'bg-betty-500/20 border-betty-400 text-betty-200 border'
                    : 'bg-white/5 border-white/10 text-white/70 hover:text-white hover:bg-white/10 border'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{option.label}</span>
              </motion.button>
            )
          })}
        </motion.div>

        {/* Main Content Area */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeView}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="min-h-[500px]"
          >
            {activeView === 'overview' && (
              <OverviewDashboard 
                stats={dashboardStats}
                isLoading={isLoadingStats}
              />
            )}

            {activeView === 'code' && (
              <CodeRepositoriesView 
                searchQuery={searchQuery}
                languageFilter={filters.programmingLanguage}
              />
            )}

            {activeView === 'documentation' && (
              <DocumentationBrowser 
                searchQuery={searchQuery}
                typeFilter={filters.documentationType}
              />
            )}

            {activeView === 'graph' && (
              <KnowledgeGraphVisualization 
                focusArea={filters.knowledgeDomain}
              />
            )}

            {activeView === 'timeline' && (
              <LearningTimelineView />
            )}

            {activeView === 'expertise' && (
              <ExpertiseRadarChart 
                confidenceThreshold={filters.confidenceThreshold}
              />
            )}

            {activeView === 'browser' && (
              <InteractiveCodeBrowser 
                searchQuery={searchQuery}
                languageFilter={filters.programmingLanguage}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </Layout>
  )
}

// Overview Dashboard Component
interface OverviewDashboardProps {
  stats: any
  isLoading: boolean
}

const OverviewDashboard: React.FC<OverviewDashboardProps> = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="glass-morphism border border-white/10 rounded-lg p-6 animate-pulse">
            <div className="w-8 h-8 bg-white/10 rounded-lg mb-4"></div>
            <div className="w-24 h-4 bg-white/10 rounded mb-2"></div>
            <div className="w-16 h-6 bg-white/10 rounded"></div>
          </div>
        ))}
      </div>
    )
  }

  const overviewCards = [
    {
      title: 'Total Code Lines',
      value: stats?.total_code_lines?.toLocaleString() || '0',
      icon: Code,
      color: 'betty-400',
      bgColor: 'betty-500/10'
    },
    {
      title: 'Knowledge Items',
      value: stats?.total_knowledge_items?.toLocaleString() || '0',
      icon: Brain,
      color: 'purple-400',
      bgColor: 'purple-500/10'
    },
    {
      title: 'Documentation Sources',
      value: stats?.total_documentation_sources || '0',
      icon: BookOpen,
      color: 'pink-400',
      bgColor: 'pink-500/10'
    },
    {
      title: 'Learning Velocity',
      value: `${stats?.learning_velocity?.toFixed(1) || '0'}/day`,
      icon: TrendingUp,
      color: 'green-400',
      bgColor: 'green-500/10'
    },
    {
      title: 'Confidence Score',
      value: `${Math.round((stats?.confidence_score || 0) * 100)}%`,
      icon: Target,
      color: 'blue-400',
      bgColor: 'blue-500/10'
    },
    {
      title: 'Active Repositories',
      value: stats?.total_repositories || '0',
      icon: GitBranch,
      color: 'orange-400',
      bgColor: 'orange-500/10'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {overviewCards.map((card, index) => {
          const Icon = card.icon
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="glass-morphism border border-white/10 rounded-lg p-6 hover:border-white/20 transition-colors"
            >
              <div className={`w-12 h-12 bg-${card.bgColor} rounded-lg flex items-center justify-center mb-4`}>
                <Icon className={`w-6 h-6 text-${card.color}`} />
              </div>
              <h3 className="text-white/80 text-sm font-medium mb-2">{card.title}</h3>
              <div className={`text-2xl font-bold text-${card.color}`}>
                {card.value}
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Programming Languages Breakdown */}
      {stats?.programming_languages && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="glass-morphism border border-white/10 rounded-lg p-6"
        >
          <h3 className="text-white text-lg font-semibold mb-4 flex items-center">
            <Layers className="w-5 h-5 mr-2 text-betty-400" />
            Programming Languages
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.programming_languages).map(([lang, count]: [string, any]) => (
              <div key={lang} className="text-center">
                <div className="text-xl font-bold text-white">{count}</div>
                <div className="text-sm text-white/60 capitalize">{lang}</div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recent Learning Activity */}
      {stats?.recent_learning && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="glass-morphism border border-white/10 rounded-lg p-6"
        >
          <h3 className="text-white text-lg font-semibold mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-betty-400" />
            Recent Learning Activity
          </h3>
          <div className="space-y-2">
            {stats.recent_learning.slice(0, 5).map((event: any, index: number) => (
              <div key={index} className="flex items-center justify-between py-2 border-b border-white/5 last:border-b-0">
                <div>
                  <div className="text-white text-sm">{event.description}</div>
                  <div className="text-white/50 text-xs">{event.knowledge_area}</div>
                </div>
                <div className="text-betty-400 text-xs">{event.impact_score}/5</div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default KnowledgeVisualizationDashboard