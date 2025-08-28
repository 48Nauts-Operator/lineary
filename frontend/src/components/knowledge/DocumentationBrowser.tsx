import React, { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookOpen,
  Search,
  Filter,
  Clock,
  Hash,
  Tag,
  ExternalLink,
  Zap,
  TrendingUp,
  Eye,
  Star,
  ChevronRight
} from 'lucide-react'
import { 
  useDocumentationSources, 
  useDocumentationSearch 
} from '../../hooks/useKnowledgeVisualization'
import { DocumentationSource, DocumentationSearchResult } from '../../services/knowledgeVisualizationApi'

interface DocumentationBrowserProps {
  searchQuery: string
  typeFilter?: string
}

const DocumentationBrowser: React.FC<DocumentationBrowserProps> = ({
  searchQuery,
  typeFilter
}) => {
  const [selectedSource, setSelectedSource] = useState<DocumentationSource | null>(null)
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery)
  const [searchResults, setSearchResults] = useState<DocumentationSearchResult[]>([])
  const [activeTab, setActiveTab] = useState<'sources' | 'search'>('sources')

  const {
    data: documentationSources,
    isLoading: isLoadingSources,
    error: sourcesError
  } = useDocumentationSources(typeFilter)

  const searchMutation = useDocumentationSearch()

  // Perform search when query changes
  useEffect(() => {
    if (localSearchQuery.length > 2) {
      setActiveTab('search')
      searchMutation.mutate({
        query: localSearchQuery,
        sourceType: typeFilter,
        limit: 25
      }, {
        onSuccess: (results) => {
          setSearchResults(results)
        }
      })
    } else {
      setActiveTab('sources')
      setSearchResults([])
    }
  }, [localSearchQuery, typeFilter])

  // Update local search when prop changes
  useEffect(() => {
    setLocalSearchQuery(searchQuery)
  }, [searchQuery])

  const sortedSources = useMemo(() => {
    if (!documentationSources) return []
    return [...documentationSources].sort((a, b) => b.knowledge_depth - a.knowledge_depth)
  }, [documentationSources])

  const getSourceTypeColor = (sourceType: string): string => {
    const colors: Record<string, string> = {
      'api': 'betty-400',
      'tutorial': 'purple-400',
      'reference': 'pink-400',
      'examples': 'green-400',
      'guide': 'blue-400',
      'specification': 'orange-400'
    }
    return colors[sourceType] || 'white'
  }

  const getKnowledgeDepthLabel = (depth: number): string => {
    if (depth >= 0.8) return 'Comprehensive'
    if (depth >= 0.6) return 'Detailed'
    if (depth >= 0.4) return 'Moderate'
    if (depth >= 0.2) return 'Basic'
    return 'Limited'
  }

  if (sourcesError) {
    return (
      <div className="glass-morphism border border-red-500/20 rounded-lg p-8 text-center">
        <BookOpen className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-red-400 text-lg font-semibold mb-2">Failed to Load Documentation</h3>
        <p className="text-white/60">{sourcesError.message || 'An unexpected error occurred'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header and Search */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Documentation Browser</h2>
          <p className="text-white/70">
            {documentationSources?.length || 0} sources • {documentationSources?.reduce((sum, source) => sum + source.document_count, 0) || 0} documents
          </p>
        </div>

        {/* Advanced Search */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
            <input
              type="text"
              placeholder="Search documentation content..."
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-betty-400 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-4 border-b border-white/10">
        <button
          onClick={() => setActiveTab('sources')}
          className={`pb-3 px-1 font-medium transition-colors ${
            activeTab === 'sources'
              ? 'text-betty-400 border-b-2 border-betty-400'
              : 'text-white/60 hover:text-white'
          }`}
        >
          Documentation Sources
        </button>
        <button
          onClick={() => setActiveTab('search')}
          className={`pb-3 px-1 font-medium transition-colors flex items-center ${
            activeTab === 'search'
              ? 'text-betty-400 border-b-2 border-betty-400'
              : 'text-white/60 hover:text-white'
          }`}
        >
          Search Results
          {searchResults.length > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-betty-500/20 text-betty-300 text-xs rounded-full">
              {searchResults.length}
            </span>
          )}
        </button>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'sources' && (
          <motion.div
            key="sources"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            <SourcesView 
              sources={sortedSources}
              isLoading={isLoadingSources}
              onSourceSelect={setSelectedSource}
              selectedSource={selectedSource}
              getSourceTypeColor={getSourceTypeColor}
              getKnowledgeDepthLabel={getKnowledgeDepthLabel}
            />
          </motion.div>
        )}

        {activeTab === 'search' && (
          <motion.div
            key="search"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <SearchResultsView 
              results={searchResults}
              isLoading={searchMutation.isPending}
              searchQuery={localSearchQuery}
              getSourceTypeColor={getSourceTypeColor}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Sources View Component
interface SourcesViewProps {
  sources: DocumentationSource[]
  isLoading: boolean
  onSourceSelect: (source: DocumentationSource) => void
  selectedSource: DocumentationSource | null
  getSourceTypeColor: (type: string) => string
  getKnowledgeDepthLabel: (depth: number) => string
}

const SourcesView: React.FC<SourcesViewProps> = ({
  sources,
  isLoading,
  onSourceSelect,
  selectedSource,
  getSourceTypeColor,
  getKnowledgeDepthLabel
}) => {
  if (isLoading) {
    return <LoadingSourcesView />
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {sources.map((source, index) => (
        <motion.div
          key={source.source_id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          onClick={() => onSourceSelect(source)}
          className={`glass-morphism border rounded-lg p-6 cursor-pointer transition-all hover:scale-105 ${
            selectedSource?.source_id === source.source_id
              ? 'border-betty-400 bg-betty-500/5'
              : 'border-white/10 hover:border-white/20'
          }`}
        >
          {/* Source Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className={`p-2 bg-${getSourceTypeColor(source.source_type)}/10 rounded-lg`}>
                <BookOpen className={`w-5 h-5 text-${getSourceTypeColor(source.source_type)}`} />
              </div>
              <div>
                <h3 className="text-white font-semibold text-lg">{source.source_name}</h3>
                <span className={`text-${getSourceTypeColor(source.source_type)} text-sm font-medium capitalize`}>
                  {source.source_type}
                </span>
              </div>
            </div>
            <ExternalLink className="w-4 h-4 text-white/40" />
          </div>

          {/* Knowledge Depth Indicator */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white/70 text-sm">Knowledge Depth</span>
              <span className="text-betty-400 text-sm font-medium">
                {getKnowledgeDepthLabel(source.knowledge_depth)}
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-betty-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${source.knowledge_depth * 100}%` }}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="text-center bg-white/5 rounded-lg p-3">
              <div className="text-lg font-bold text-white">{source.document_count}</div>
              <div className="text-xs text-white/60">Documents</div>
            </div>
            <div className="text-center bg-white/5 rounded-lg p-3">
              <div className="text-lg font-bold text-white">
                {Math.round(source.total_words / 1000)}K
              </div>
              <div className="text-xs text-white/60">Words</div>
            </div>
          </div>

          {/* Categories */}
          <div className="mb-4">
            <div className="flex flex-wrap gap-1">
              {source.categories.slice(0, 3).map((category, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-white/10 text-white/70 text-xs rounded-full border border-white/20"
                >
                  {category}
                </span>
              ))}
              {source.categories.length > 3 && (
                <span className="px-2 py-1 bg-white/5 text-white/50 text-xs rounded-full border border-white/10">
                  +{source.categories.length - 3}
                </span>
              )}
            </div>
          </div>

          {/* Last Updated */}
          <div className="flex items-center text-white/50 text-xs">
            <Clock className="w-3 h-3 mr-1" />
            Updated {new Date(source.last_updated).toLocaleDateString()}
          </div>
        </motion.div>
      ))}
    </div>
  )
}

// Search Results View Component
interface SearchResultsViewProps {
  results: DocumentationSearchResult[]
  isLoading: boolean
  searchQuery: string
  getSourceTypeColor: (type: string) => string
}

const SearchResultsView: React.FC<SearchResultsViewProps> = ({
  results,
  isLoading,
  searchQuery,
  getSourceTypeColor
}) => {
  if (isLoading) {
    return <LoadingSearchView />
  }

  if (results.length === 0 && searchQuery.length > 2) {
    return (
      <div className="text-center py-12">
        <Search className="w-16 h-16 text-white/20 mx-auto mb-4" />
        <h3 className="text-white/60 text-lg font-medium mb-2">No results found</h3>
        <p className="text-white/40">
          Try adjusting your search query or removing filters
        </p>
      </div>
    )
  }

  if (searchQuery.length <= 2) {
    return (
      <div className="text-center py-12">
        <Search className="w-16 h-16 text-white/20 mx-auto mb-4" />
        <h3 className="text-white/60 text-lg font-medium mb-2">Start searching</h3>
        <p className="text-white/40">
          Enter at least 3 characters to search documentation
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold">
          {results.length} results for "{searchQuery}"
        </h3>
      </div>

      <div className="space-y-4">
        {results.map((result, index) => (
          <motion.div
            key={result.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="glass-morphism border border-white/10 rounded-lg p-6 hover:border-white/20 transition-colors cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h4 className="text-white font-semibold text-lg mb-1">{result.title}</h4>
                <div className="flex items-center space-x-3 text-sm text-white/60 mb-3">
                  <span className={`text-${getSourceTypeColor(result.source_type)} font-medium capitalize`}>
                    {result.source_type}
                  </span>
                  <span>•</span>
                  <span>{result.source_name}</span>
                  <span>•</span>
                  <span className="flex items-center">
                    <Star className="w-3 h-3 mr-1" />
                    {result.relevance_score.toFixed(2)}
                  </span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-white/40 mt-1" />
            </div>

            <div 
              className="text-white/80 text-sm leading-relaxed mb-3"
              dangerouslySetInnerHTML={{ __html: result.content_preview }}
            />

            <div className="flex items-center justify-between">
              <div className="flex flex-wrap gap-1">
                {result.categories.slice(0, 3).map((category, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-white/10 text-white/60 text-xs rounded-full"
                  >
                    <Tag className="w-2 h-2 mr-1 inline" />
                    {category}
                  </span>
                ))}
              </div>
              <div className="text-white/40 text-xs flex items-center">
                <Eye className="w-3 h-3 mr-1" />
                View full document
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

const LoadingSourcesView: React.FC = () => (
  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
    {[...Array(6)].map((_, i) => (
      <div key={i} className="glass-morphism border border-white/10 rounded-lg p-6 animate-pulse">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-9 h-9 bg-white/10 rounded-lg"></div>
          <div>
            <div className="w-32 h-4 bg-white/10 rounded mb-2"></div>
            <div className="w-16 h-3 bg-white/10 rounded"></div>
          </div>
        </div>
        <div className="w-full h-2 bg-white/10 rounded-full mb-4"></div>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="h-12 bg-white/10 rounded-lg"></div>
          <div className="h-12 bg-white/10 rounded-lg"></div>
        </div>
      </div>
    ))}
  </div>
)

const LoadingSearchView: React.FC = () => (
  <div className="space-y-4">
    {[...Array(4)].map((_, i) => (
      <div key={i} className="glass-morphism border border-white/10 rounded-lg p-6 animate-pulse">
        <div className="w-64 h-5 bg-white/10 rounded mb-3"></div>
        <div className="w-48 h-3 bg-white/10 rounded mb-3"></div>
        <div className="space-y-2 mb-4">
          <div className="w-full h-3 bg-white/10 rounded"></div>
          <div className="w-full h-3 bg-white/10 rounded"></div>
          <div className="w-3/4 h-3 bg-white/10 rounded"></div>
        </div>
        <div className="flex space-x-2">
          <div className="w-16 h-5 bg-white/10 rounded-full"></div>
          <div className="w-20 h-5 bg-white/10 rounded-full"></div>
        </div>
      </div>
    ))}
  </div>
)

export default DocumentationBrowser