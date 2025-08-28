import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { knowledgeVisualizationApi } from '../services/knowledgeVisualizationApi'

// Dashboard stats hook
export const useKnowledgeVisualization = () => {
  const {
    data: dashboardStats,
    isLoading: isLoadingStats,
    error,
    refetch: refetchStats
  } = useQuery({
    queryKey: ['knowledge-visualization', 'stats'],
    queryFn: () => knowledgeVisualizationApi.getDashboardStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  })

  return {
    dashboardStats,
    isLoadingStats,
    error,
    refetchStats
  }
}

// Code repositories hook
export const useCodeRepositories = (programmingLanguage?: string, minLines?: number) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'code-repositories', programmingLanguage, minLines],
    queryFn: () => knowledgeVisualizationApi.getCodeRepositories(programmingLanguage, minLines),
    staleTime: 10 * 60 * 1000, // 10 minutes
    enabled: true
  })
}

// Repository files hook
export const useRepositoryFiles = (repositoryName: string, fileType?: string, page: number = 1, pageSize: number = 20) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'repository-files', repositoryName, fileType, page, pageSize],
    queryFn: () => knowledgeVisualizationApi.getRepositoryFiles(repositoryName, fileType, page, pageSize),
    staleTime: 10 * 60 * 1000,
    enabled: !!repositoryName
  })
}

// File content with highlighting hook
export const useFileContent = (fileId: string) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'file-content', fileId],
    queryFn: () => knowledgeVisualizationApi.getFileContentWithHighlighting(fileId),
    staleTime: 15 * 60 * 1000, // 15 minutes
    enabled: !!fileId
  })
}

// Documentation sources hook
export const useDocumentationSources = (sourceType?: string, category?: string) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'documentation-sources', sourceType, category],
    queryFn: () => knowledgeVisualizationApi.getDocumentationSources(sourceType, category),
    staleTime: 10 * 60 * 1000
  })
}

// Documentation search hook
export const useDocumentationSearch = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      query,
      sourceType,
      category,
      limit
    }: {
      query: string
      sourceType?: string
      category?: string
      limit?: number
    }) => knowledgeVisualizationApi.searchDocumentation(query, sourceType, category, limit),
    onSuccess: (data, variables) => {
      // Cache the search results
      queryClient.setQueryData(
        ['knowledge-visualization', 'documentation-search', variables.query],
        data
      )
    }
  })
}

// Knowledge graph hook
export const useKnowledgeGraph = (focusArea?: string, depth: number = 3, maxNodes: number = 100) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'knowledge-graph', focusArea, depth, maxNodes],
    queryFn: () => knowledgeVisualizationApi.getKnowledgeGraph(focusArea, depth, maxNodes),
    staleTime: 15 * 60 * 1000,
    enabled: true
  })
}

// Learning timeline hook
export const useLearningTimeline = (
  startDate?: string,
  endDate?: string,
  knowledgeArea?: string,
  limit: number = 50
) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'learning-timeline', startDate, endDate, knowledgeArea, limit],
    queryFn: () => knowledgeVisualizationApi.getLearningTimeline(startDate, endDate, knowledgeArea, limit),
    staleTime: 5 * 60 * 1000
  })
}

// Expertise levels hook
export const useExpertiseLevels = (minConfidence?: number, domain?: string) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'expertise-levels', minConfidence, domain],
    queryFn: () => knowledgeVisualizationApi.getExpertiseLevels(minConfidence, domain),
    staleTime: 30 * 60 * 1000 // 30 minutes
  })
}

// Cross-references hook
export const useCrossReferences = (
  knowledgeId: string,
  maxDepth: number = 2,
  relationshipTypes?: string[]
) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'cross-references', knowledgeId, maxDepth, relationshipTypes],
    queryFn: () => knowledgeVisualizationApi.getCrossReferences(knowledgeId, maxDepth, relationshipTypes),
    staleTime: 10 * 60 * 1000,
    enabled: !!knowledgeId
  })
}

// Code pattern analysis hook
export const useCodePatternAnalysis = () => {
  return useMutation({
    mutationFn: ({
      repositoryNames,
      programmingLanguages
    }: {
      repositoryNames?: string[]
      programmingLanguages?: string[]
    }) => knowledgeVisualizationApi.analyzeCodePatterns(repositoryNames, programmingLanguages)
  })
}

// Confidence metrics hook
export const useConfidenceMetrics = (knowledgeType?: string) => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'confidence-metrics', knowledgeType],
    queryFn: () => knowledgeVisualizationApi.getConfidenceMetrics(knowledgeType),
    staleTime: 10 * 60 * 1000
  })
}

// Combined search hook for all knowledge types
export const useUniversalSearch = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      query,
      filters
    }: {
      query: string
      filters: {
        programmingLanguage?: string
        documentationType?: string
        knowledgeDomain?: string
        confidenceThreshold?: number
      }
    }) => {
      // Search across multiple knowledge types in parallel
      const [codeResults, docResults] = await Promise.all([
        // Search code repositories
        knowledgeVisualizationApi.getCodeRepositories(filters.programmingLanguage),
        // Search documentation
        knowledgeVisualizationApi.searchDocumentation(
          query,
          filters.documentationType,
          filters.knowledgeDomain,
          10
        )
      ])

      return {
        code: codeResults,
        documentation: docResults,
        query,
        totalResults: codeResults.length + docResults.length
      }
    },
    onSuccess: (data, variables) => {
      // Cache the universal search results
      queryClient.setQueryData(
        ['knowledge-visualization', 'universal-search', variables.query],
        data
      )
    }
  })
}

// Hook for real-time knowledge updates
export const useKnowledgeUpdates = () => {
  const queryClient = useQueryClient()

  // This would typically connect to a WebSocket for real-time updates
  // For now, we'll provide a manual refresh mechanism
  const refreshAllKnowledgeData = () => {
    queryClient.invalidateQueries({
      queryKey: ['knowledge-visualization']
    })
  }

  return {
    refreshAllKnowledgeData
  }
}

// Analytics and insights hook
export const useKnowledgeInsights = () => {
  return useQuery({
    queryKey: ['knowledge-visualization', 'insights'],
    queryFn: async () => {
      // Combine multiple endpoints to generate insights
      const [stats, expertise, timeline] = await Promise.all([
        knowledgeVisualizationApi.getDashboardStats(),
        knowledgeVisualizationApi.getExpertiseLevels(),
        knowledgeVisualizationApi.getLearningTimeline()
      ])

      // Generate insights from the combined data
      const insights = {
        topExpertiseDomains: expertise.slice(0, 5),
        recentLearningTrends: timeline.slice(0, 10),
        knowledgeGrowthRate: stats.learning_velocity,
        strengthAreas: expertise.filter((e: any) => e.confidence_score > 0.8),
        improvementAreas: expertise.filter((e: any) => e.confidence_score < 0.6),
        totalKnowledgeValue: {
          codeLines: stats.total_code_lines,
          documentSources: stats.total_documentation_sources,
          repositories: stats.total_repositories
        }
      }

      return insights
    },
    staleTime: 30 * 60 * 1000 // 30 minutes
  })
}