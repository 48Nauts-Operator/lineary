// ABOUTME: Custom hook for Knowledge Radar Dashboard data fetching and management
// ABOUTME: Handles API calls to Betty Memory System for knowledge categories, patterns, and statistics

import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE = (typeof window !== 'undefined' && (window as any).REACT_APP_API_URL) || 'http://localhost:3034'

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

interface KnowledgeStats {
  total_categories: number
  total_patterns: number
  total_items: number
  avg_quality_score: number
  avg_growth_rate: number
  most_active_category: string
  knowledge_distribution: Record<string, number>
  quality_distribution: Record<string, number>
}

interface UseKnowledgeRadarDataReturn {
  categories: KnowledgeCategory[]
  stats: KnowledgeStats | null
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
}

// Transform raw knowledge data into categories
const transformKnowledgeData = (rawData: any): KnowledgeCategory[] => {
  if (!rawData || !rawData.data) return []

  // Group knowledge items by type and extract patterns
  const categoryGroups: Record<string, any[]> = {}
  
  rawData.data.forEach((item: any) => {
    const categoryName = getCategoryName(item.knowledge_type, item.tags)
    if (!categoryGroups[categoryName]) {
      categoryGroups[categoryName] = []
    }
    categoryGroups[categoryName].push(item)
  })

  // Convert groups to category objects
  return Object.entries(categoryGroups).map(([name, items]) => {
    const qualityScores = items
      .map(item => getQualityScore(item))
      .filter(score => score > 0)
    
    const avgQuality = qualityScores.length > 0 
      ? qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length
      : 0.5

    const recentActivity = items.filter(item => 
      new Date(item.created_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    ).length

    const subcategories = Array.from(
      new Set(items.flatMap(item => item.tags || []))
    ).slice(0, 5)

    const patterns = extractPatterns(items)
    const topPatterns = getTopPatterns(items)

    return {
      name,
      patterns: patterns.length,
      quality_score: avgQuality,
      growth_rate: calculateGrowthRate(items),
      recent_activity: recentActivity,
      expertise_level: calculateExpertiseLevel(items, patterns),
      subcategories,
      total_items: items.length,
      last_updated: getLatestUpdate(items),
      top_patterns: topPatterns
    }
  })
}

// Helper functions for data transformation
const getCategoryName = (knowledgeType: string, tags: string[] = []): string => {
  // Map knowledge types and tags to meaningful category names
  const categoryMap: Record<string, string> = {
    'document': 'Document Intelligence',
    'code': 'System Architecture', 
    'conversation': 'Web Development',
    'solution': 'Cloud Security',
    'insight': 'Document AI',
    'memory': 'Database Design',
    'reference': 'API Development'
  }

  // Check tags for more specific categorization
  if (tags.includes('vector_database') || tags.includes('graph_database')) {
    return 'Document Intelligence'
  }
  if (tags.includes('aws_infrastructure') || tags.includes('security')) {
    return 'Cloud Security'
  }
  if (tags.includes('multimodal_processing') || tags.includes('ai')) {
    return 'Document AI'
  }
  if (tags.includes('microservices') || tags.includes('architecture')) {
    return 'System Architecture'
  }
  if (tags.includes('react') || tags.includes('frontend') || tags.includes('web')) {
    return 'Web Development'
  }

  return categoryMap[knowledgeType] || 'General Knowledge'
}

const getQualityScore = (item: any): number => {
  // Calculate quality based on various factors
  let score = 0.5 // Base score

  // Content length (more content generally indicates higher quality)
  if (item.content && item.content.length > 100) score += 0.1
  if (item.content && item.content.length > 500) score += 0.1
  
  // Has summary (indicates curation)
  if (item.summary && item.summary.trim()) score += 0.1
  
  // Has tags (indicates categorization)
  if (item.tags && item.tags.length > 0) score += 0.1
  
  // Confidence level
  if (item.confidence === 'verified') score += 0.2
  else if (item.confidence === 'high') score += 0.1
  
  // Access count (frequently accessed items are likely higher quality)
  if (item.access_count > 5) score += 0.1
  
  return Math.min(score, 1.0)
}

const calculateGrowthRate = (items: any[]): number => {
  if (items.length < 2) return 0

  const now = new Date()
  const lastWeek = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
  const lastMonth = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)

  const recentItems = items.filter(item => new Date(item.created_at) > lastWeek).length
  const monthlyItems = items.filter(item => new Date(item.created_at) > lastMonth).length

  // Simple growth rate calculation
  return monthlyItems > 0 ? recentItems / monthlyItems : 0
}

const calculateExpertiseLevel = (items: any[], patterns: any[]): number => {
  // Expertise based on volume, quality, and pattern recognition
  let expertise = 0
  
  // Volume factor (logarithmic scaling)
  const volumeScore = Math.min(Math.log10(items.length + 1) / 2, 0.4)
  expertise += volumeScore
  
  // Quality factor
  const avgQuality = items.reduce((sum, item) => sum + getQualityScore(item), 0) / items.length
  expertise += avgQuality * 0.3
  
  // Pattern recognition factor
  const patternScore = Math.min(patterns.length / 10, 0.3)
  expertise += patternScore
  
  return Math.min(expertise, 1.0)
}

const extractPatterns = (items: any[]): any[] => {
  // Simple pattern extraction based on common tags and content similarities
  const tagCounts: Record<string, number> = {}
  
  items.forEach(item => {
    if (item.tags) {
      item.tags.forEach((tag: string) => {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1
      })
    }
  })
  
  // Return tags that appear multiple times as "patterns"
  return Object.entries(tagCounts)
    .filter(([_, count]) => count > 1)
    .map(([tag, count]) => ({ tag, count }))
}

const getTopPatterns = (items: any[]): Array<{id: string, title: string, usage_count: number, quality_score: number}> => {
  // Extract most common patterns/topics from items
  const patterns: Record<string, {items: any[], quality_sum: number}> = {}
  
  items.forEach(item => {
    const key = item.title.split(' ').slice(0, 3).join(' ') // First 3 words as pattern key
    if (!patterns[key]) {
      patterns[key] = { items: [], quality_sum: 0 }
    }
    patterns[key].items.push(item)
    patterns[key].quality_sum += getQualityScore(item)
  })
  
  return Object.entries(patterns)
    .map(([title, data]) => ({
      id: `pattern-${title.replace(/\s+/g, '-').toLowerCase()}`,
      title: title,
      usage_count: data.items.length,
      quality_score: data.quality_sum / data.items.length
    }))
    .sort((a, b) => b.usage_count - a.usage_count)
    .slice(0, 3)
}

const getLatestUpdate = (items: any[]): string => {
  if (items.length === 0) return new Date().toISOString()
  
  const latest = items.reduce((latest, item) => {
    const itemDate = new Date(item.updated_at || item.created_at)
    return itemDate > latest ? itemDate : latest
  }, new Date(0))
  
  return latest.toISOString()
}

export const useKnowledgeRadarData = (): UseKnowledgeRadarDataReturn => {
  const [transformedCategories, setTransformedCategories] = useState<KnowledgeCategory[]>([])

  // Fetch knowledge items from Betty API
  const {
    data: rawKnowledgeData,
    isLoading: isKnowledgeLoading,
    isError: isKnowledgeError,
    error: knowledgeError,
    refetch: refetchKnowledge
  } = useQuery({
    queryKey: ['knowledge-items'],
    queryFn: async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/knowledge/`, {
          params: {
            page: 1,
            page_size: 1000 // Get all items for analysis
          }
        })
        return response.data
      } catch (error) {
        console.error('Error fetching knowledge items:', error)
        throw error
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })

  // Fetch knowledge statistics
  const {
    data: statsData,
    isLoading: isStatsLoading,
    isError: isStatsError,
    error: statsError
  } = useQuery({
    queryKey: ['knowledge-stats'],
    queryFn: async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/knowledge/stats`)
        return response.data?.data
      } catch (error) {
        console.error('Error fetching knowledge stats:', error)
        // Return null instead of throwing to prevent breaking the dashboard
        return null
      }
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })

  // Transform raw data into categories when data changes
  useEffect(() => {
    if (rawKnowledgeData) {
      const categories = transformKnowledgeData(rawKnowledgeData)
      setTransformedCategories(categories)
    }
  }, [rawKnowledgeData])

  // Calculate aggregated stats
  const stats: KnowledgeStats | null = React.useMemo(() => {
    if (transformedCategories.length === 0) return null

    const totalPatterns = transformedCategories.reduce((sum, cat) => sum + cat.patterns, 0)
    const totalItems = transformedCategories.reduce((sum, cat) => sum + cat.total_items, 0)
    const avgQuality = transformedCategories.reduce((sum, cat) => sum + cat.quality_score, 0) / transformedCategories.length
    const avgGrowth = transformedCategories.reduce((sum, cat) => sum + cat.growth_rate, 0) / transformedCategories.length
    
    const mostActiveCategory = transformedCategories
      .reduce((max, cat) => cat.recent_activity > max.recent_activity ? cat : max)
      .name

    const knowledgeDistribution = transformedCategories.reduce((dist, cat) => {
      dist[cat.name] = cat.total_items
      return dist
    }, {} as Record<string, number>)

    const qualityDistribution = transformedCategories.reduce((dist, cat) => {
      const qualityBucket = cat.quality_score >= 0.9 ? 'High' : 
                           cat.quality_score >= 0.7 ? 'Medium' : 'Low'
      dist[qualityBucket] = (dist[qualityBucket] || 0) + 1
      return dist
    }, {} as Record<string, number>)

    return {
      total_categories: transformedCategories.length,
      total_patterns: totalPatterns,
      total_items: totalItems,
      avg_quality_score: avgQuality,
      avg_growth_rate: avgGrowth,
      most_active_category: mostActiveCategory,
      knowledge_distribution: knowledgeDistribution,
      quality_distribution: qualityDistribution
    }
  }, [transformedCategories])

  return {
    categories: transformedCategories,
    stats,
    isLoading: isKnowledgeLoading || isStatsLoading,
    isError: isKnowledgeError || isStatsError,
    error: knowledgeError || statsError,
    refetch: () => {
      refetchKnowledge()
    }
  }
}

export default useKnowledgeRadarData