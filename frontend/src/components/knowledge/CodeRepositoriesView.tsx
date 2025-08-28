import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Code,
  GitBranch,
  FileText,
  BarChart3,
  TrendingUp,
  Calendar,
  Hash,
  Layers,
  Package,
  ChevronDown,
  ChevronRight,
  ExternalLink
} from 'lucide-react'
import { useCodeRepositories } from '../../hooks/useKnowledgeVisualization'
import { CodeRepository } from '../../services/knowledgeVisualizationApi'

interface CodeRepositoriesViewProps {
  searchQuery: string
  languageFilter?: string
}

const CodeRepositoriesView: React.FC<CodeRepositoriesViewProps> = ({
  searchQuery,
  languageFilter
}) => {
  const [selectedRepository, setSelectedRepository] = useState<CodeRepository | null>(null)
  const [sortBy, setSortBy] = useState<'lines' | 'files' | 'complexity' | 'recent'>('lines')
  const [expandedRepos, setExpandedRepos] = useState<Set<string>>(new Set())

  const {
    data: repositories,
    isLoading,
    error
  } = useCodeRepositories(languageFilter, undefined)

  const toggleExpanded = (repoName: string) => {
    const newExpanded = new Set(expandedRepos)
    if (newExpanded.has(repoName)) {
      newExpanded.delete(repoName)
    } else {
      newExpanded.add(repoName)
    }
    setExpandedRepos(newExpanded)
  }

  const filteredRepositories = repositories?.filter(repo =>
    repo.repository_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    Object.keys(repo.programming_languages).some(lang =>
      lang.toLowerCase().includes(searchQuery.toLowerCase())
    )
  ) || []

  const sortedRepositories = [...filteredRepositories].sort((a, b) => {
    switch (sortBy) {
      case 'lines':
        return b.total_lines - a.total_lines
      case 'files':
        return b.total_files - a.total_files
      case 'complexity':
        return (b.complexity_metrics?.average_complexity || 0) - (a.complexity_metrics?.average_complexity || 0)
      case 'recent':
        return new Date(b.last_analyzed).getTime() - new Date(a.last_analyzed).getTime()
      default:
        return 0
    }
  })

  if (isLoading) {
    return <LoadingRepositoriesView />
  }

  if (error) {
    return (
      <div className="glass-morphism border border-red-500/20 rounded-lg p-8 text-center">
        <Code className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-red-400 text-lg font-semibold mb-2">Failed to Load Repositories</h3>
        <p className="text-white/60">{error.message || 'An unexpected error occurred'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Code Repositories</h2>
          <p className="text-white/70">
            {filteredRepositories.length} repositories • {filteredRepositories.reduce((sum, repo) => sum + repo.total_lines, 0).toLocaleString()} total lines
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-betty-400 transition-colors"
          >
            <option value="lines">Sort by Lines</option>
            <option value="files">Sort by Files</option>
            <option value="complexity">Sort by Complexity</option>
            <option value="recent">Sort by Recent</option>
          </select>
        </div>
      </div>

      {/* Repositories Grid */}
      <div className="space-y-4">
        <AnimatePresence>
          {sortedRepositories.map((repository, index) => {
            const isExpanded = expandedRepos.has(repository.repository_name)
            return (
              <motion.div
                key={repository.repository_name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
                className="glass-morphism border border-white/10 rounded-lg overflow-hidden hover:border-white/20 transition-all"
              >
                {/* Repository Header */}
                <div 
                  className="p-6 cursor-pointer"
                  onClick={() => toggleExpanded(repository.repository_name)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="p-2 bg-betty-500/10 rounded-lg">
                        <GitBranch className="w-5 h-5 text-betty-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-white mb-1 flex items-center">
                          {repository.repository_name}
                          <ExternalLink className="w-4 h-4 text-white/40 ml-2" />
                        </h3>
                        <div className="flex items-center space-x-4 text-sm text-white/60">
                          <span className="flex items-center">
                            <FileText className="w-3 h-3 mr-1" />
                            {repository.total_files} files
                          </span>
                          <span className="flex items-center">
                            <Hash className="w-3 h-3 mr-1" />
                            {repository.total_lines.toLocaleString()} lines
                          </span>
                          <span className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {new Date(repository.last_analyzed).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="flex items-center space-x-6 mr-4">
                      <div className="text-center">
                        <div className="text-lg font-bold text-betty-400">
                          {Object.keys(repository.programming_languages).length}
                        </div>
                        <div className="text-xs text-white/50">Languages</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-purple-400">
                          {repository.architecture_patterns.length}
                        </div>
                        <div className="text-xs text-white/50">Patterns</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-pink-400">
                          {repository.dependencies.length}
                        </div>
                        <div className="text-xs text-white/50">Dependencies</div>
                      </div>
                    </div>

                    <div className="flex items-center">
                      {isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-white/60" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-white/60" />
                      )}
                    </div>
                  </div>

                  {/* Language Pills */}
                  <div className="flex flex-wrap gap-2 mt-4">
                    {Object.entries(repository.programming_languages).map(([lang, count]) => (
                      <span
                        key={lang}
                        className="px-2 py-1 bg-white/5 text-white/80 text-xs rounded-full border border-white/10 flex items-center"
                      >
                        <Code className="w-3 h-3 mr-1" />
                        {lang} ({count})
                      </span>
                    ))}
                  </div>
                </div>

                {/* Expanded Content */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="border-t border-white/10"
                    >
                      <div className="p-6 space-y-6">
                        {/* Complexity Metrics */}
                        {repository.complexity_metrics && (
                          <div>
                            <h4 className="text-white font-semibold mb-3 flex items-center">
                              <BarChart3 className="w-4 h-4 mr-2 text-betty-400" />
                              Complexity Metrics
                            </h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              {Object.entries(repository.complexity_metrics).map(([metric, value]) => (
                                <div key={metric} className="bg-white/5 rounded-lg p-3">
                                  <div className="text-sm text-white/60 capitalize">{metric.replace('_', ' ')}</div>
                                  <div className="text-lg font-semibold text-white">{value}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Architecture Patterns */}
                        {repository.architecture_patterns.length > 0 && (
                          <div>
                            <h4 className="text-white font-semibold mb-3 flex items-center">
                              <Layers className="w-4 h-4 mr-2 text-betty-400" />
                              Architecture Patterns
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {repository.architecture_patterns.map((pattern, index) => (
                                <span
                                  key={index}
                                  className="px-3 py-1 bg-purple-500/10 text-purple-300 text-sm rounded-lg border border-purple-500/20"
                                >
                                  {pattern}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Dependencies */}
                        {repository.dependencies.length > 0 && (
                          <div>
                            <h4 className="text-white font-semibold mb-3 flex items-center">
                              <Package className="w-4 h-4 mr-2 text-betty-400" />
                              Key Dependencies
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {repository.dependencies.slice(0, 10).map((dependency, index) => (
                                <span
                                  key={index}
                                  className="px-3 py-1 bg-pink-500/10 text-pink-300 text-sm rounded-lg border border-pink-500/20"
                                >
                                  {dependency}
                                </span>
                              ))}
                              {repository.dependencies.length > 10 && (
                                <span className="px-3 py-1 bg-white/5 text-white/60 text-sm rounded-lg border border-white/10">
                                  +{repository.dependencies.length - 10} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {/* File Types Distribution */}
                        {repository.file_types && Object.keys(repository.file_types).length > 0 && (
                          <div>
                            <h4 className="text-white font-semibold mb-3 flex items-center">
                              <FileText className="w-4 h-4 mr-2 text-betty-400" />
                              File Types
                            </h4>
                            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                              {Object.entries(repository.file_types).map(([type, count]) => (
                                <div key={type} className="text-center bg-white/5 rounded-lg p-2">
                                  <div className="text-sm font-semibold text-white">{count}</div>
                                  <div className="text-xs text-white/60">.{type}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>

      {filteredRepositories.length === 0 && (
        <div className="text-center py-12">
          <Code className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <h3 className="text-white/60 text-lg font-medium mb-2">No repositories found</h3>
          <p className="text-white/40">
            {searchQuery ? 'Try adjusting your search query' : 'No code repositories have been analyzed yet'}
          </p>
        </div>
      )}
    </div>
  )
}

const LoadingRepositoriesView: React.FC = () => (
  <div className="space-y-4">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="glass-morphism border border-white/10 rounded-lg p-6 animate-pulse">
        <div className="flex items-center space-x-4 mb-4">
          <div className="w-10 h-10 bg-white/10 rounded-lg"></div>
          <div className="flex-1">
            <div className="w-48 h-5 bg-white/10 rounded mb-2"></div>
            <div className="w-64 h-3 bg-white/10 rounded"></div>
          </div>
          <div className="w-20 h-4 bg-white/10 rounded"></div>
        </div>
        <div className="flex space-x-2">
          <div className="w-16 h-6 bg-white/10 rounded-full"></div>
          <div className="w-20 h-6 bg-white/10 rounded-full"></div>
          <div className="w-18 h-6 bg-white/10 rounded-full"></div>
        </div>
      </div>
    ))}
  </div>
)

export default CodeRepositoriesView