import api from './api'

const BASE_URL = '/api/knowledge-visualization'

export interface KnowledgeVisualizationStats {
  total_code_lines: number
  total_repositories: number
  total_documentation_sources: number
  programming_languages: Record<string, number>
  knowledge_domains: Record<string, number>
  learning_velocity: number
  expertise_areas: ExpertiseLevel[]
  recent_learning: LearningTimelineEntry[]
  total_knowledge_items: number
  knowledge_growth_rate: number
  confidence_score: number
}

export interface CodeRepository {
  repository_name: string
  total_files: number
  total_lines: number
  programming_languages: Record<string, number>
  file_types: Record<string, number>
  complexity_metrics: Record<string, any>
  architecture_patterns: string[]
  dependencies: string[]
  last_analyzed: string
}

export interface CodeFileDetails {
  file_path: string
  file_name: string
  programming_language: string
  lines_of_code: number
  functions: Array<Record<string, any>>
  classes: Array<Record<string, any>>
  imports: string[]
  complexity_score: number
  documentation_coverage: number
}

export interface DocumentationSource {
  source_id: string
  source_name: string
  source_type: string
  document_count: number
  total_words: number
  categories: string[]
  knowledge_depth: number
  last_updated: string
}

export interface KnowledgeGraphNode {
  id: string
  label: string
  type: string
  properties: Record<string, any>
  connections: number
}

export interface KnowledgeGraphEdge {
  source: string
  target: string
  relationship_type: string
  weight: number
}

export interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[]
  edges: KnowledgeGraphEdge[]
  stats: Record<string, any>
}

export interface LearningTimelineEntry {
  timestamp: string
  event_type: string
  description: string
  knowledge_area: string
  impact_score: number
}

export interface ExpertiseLevel {
  domain: string
  confidence_score: number
  knowledge_items_count: number
  last_updated: string
  proficiency_level: string
}

export interface FileContentWithHighlighting {
  file_id: string
  file_path: string
  programming_language: string
  content: string
  functions: Array<Record<string, any>>
  classes: Array<Record<string, any>>
  line_annotations: Record<string, any>
}

export interface DocumentationSearchResult {
  id: string
  title: string
  content_preview: string
  source_name: string
  source_type: string
  categories: string[]
  relevance_score: number
}

export const knowledgeVisualizationApi = {
  // Dashboard stats
  async getDashboardStats(): Promise<KnowledgeVisualizationStats> {
    const response = await api.get(`${BASE_URL}/dashboard/stats`)
    return response.data
  },

  // Code repositories
  async getCodeRepositories(
    programmingLanguage?: string,
    minLines?: number
  ): Promise<CodeRepository[]> {
    const params = new URLSearchParams()
    if (programmingLanguage) params.append('programming_language', programmingLanguage)
    if (minLines) params.append('min_lines', minLines.toString())
    
    const response = await api.get(`${BASE_URL}/code/repositories?${params}`)
    return response.data
  },

  // Repository files
  async getRepositoryFiles(
    repositoryName: string,
    fileType?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<CodeFileDetails[]> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    })
    if (fileType) params.append('file_type', fileType)
    
    const response = await api.get(`${BASE_URL}/code/files/${encodeURIComponent(repositoryName)}?${params}`)
    return response.data
  },

  // File content with highlighting
  async getFileContentWithHighlighting(fileId: string): Promise<FileContentWithHighlighting> {
    const response = await api.get(`${BASE_URL}/code/file-content/${fileId}`)
    return response.data
  },

  // Documentation sources
  async getDocumentationSources(
    sourceType?: string,
    category?: string
  ): Promise<DocumentationSource[]> {
    const params = new URLSearchParams()
    if (sourceType) params.append('source_type', sourceType)
    if (category) params.append('category', category)
    
    const response = await api.get(`${BASE_URL}/documentation/sources?${params}`)
    return response.data
  },

  // Documentation search
  async searchDocumentation(
    query: string,
    sourceType?: string,
    category?: string,
    limit: number = 20
  ): Promise<DocumentationSearchResult[]> {
    const params = new URLSearchParams({
      query,
      limit: limit.toString()
    })
    if (sourceType) params.append('source_type', sourceType)
    if (category) params.append('category', category)
    
    const response = await api.get(`${BASE_URL}/documentation/search?${params}`)
    return response.data
  },

  // Knowledge graph
  async getKnowledgeGraph(
    focusArea?: string,
    depth: number = 3,
    maxNodes: number = 100
  ): Promise<KnowledgeGraph> {
    const params = new URLSearchParams({
      depth: depth.toString(),
      max_nodes: maxNodes.toString()
    })
    if (focusArea) params.append('focus_area', focusArea)
    
    const response = await api.get(`${BASE_URL}/knowledge-graph?${params}`)
    return response.data
  },

  // Learning timeline
  async getLearningTimeline(
    startDate?: string,
    endDate?: string,
    knowledgeArea?: string,
    limit: number = 50
  ): Promise<LearningTimelineEntry[]> {
    const params = new URLSearchParams({
      limit: limit.toString()
    })
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    if (knowledgeArea) params.append('knowledge_area', knowledgeArea)
    
    const response = await api.get(`${BASE_URL}/learning-timeline?${params}`)
    return response.data
  },

  // Expertise levels
  async getExpertiseLevels(
    minConfidence?: number,
    domain?: string
  ): Promise<ExpertiseLevel[]> {
    const params = new URLSearchParams()
    if (minConfidence !== undefined) params.append('min_confidence', minConfidence.toString())
    if (domain) params.append('domain', domain)
    
    const response = await api.get(`${BASE_URL}/expertise-levels?${params}`)
    return response.data
  },

  // Cross-references
  async getCrossReferences(
    knowledgeId: string,
    maxDepth: number = 2,
    relationshipTypes?: string[]
  ): Promise<any[]> {
    const params = new URLSearchParams({
      max_depth: maxDepth.toString()
    })
    if (relationshipTypes) {
      relationshipTypes.forEach(type => params.append('relationship_types', type))
    }
    
    const response = await api.get(`${BASE_URL}/cross-references/${knowledgeId}?${params}`)
    return response.data
  },

  // Analyze code patterns
  async analyzeCodePatterns(
    repositoryNames?: string[],
    programmingLanguages?: string[]
  ): Promise<any> {
    const response = await api.post(`${BASE_URL}/analyze/code-patterns`, {
      repository_names: repositoryNames,
      programming_languages: programmingLanguages
    })
    return response.data
  },

  // Confidence metrics
  async getConfidenceMetrics(knowledgeType?: string): Promise<any> {
    const params = new URLSearchParams()
    if (knowledgeType) params.append('knowledge_type', knowledgeType)
    
    const response = await api.get(`${BASE_URL}/confidence-metrics?${params}`)
    return response.data
  }
}

export default knowledgeVisualizationApi