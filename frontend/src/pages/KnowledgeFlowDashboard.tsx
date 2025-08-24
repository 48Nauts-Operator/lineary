// ABOUTME: Knowledge Flow Dashboard - Real-time visualization of Betty's knowledge ingestion and processing
// ABOUTME: Shows transparent audit trail of how documentation, code, and conversations become structured knowledge

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Database,
  FileText,
  Code,
  MessageSquare,
  Globe,
  Activity,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  ArrowRight,
  Search,
  Filter,
  Play,
  Pause,
  BarChart3,
  Network,
  Zap,
  Eye,
  Archive,
  TrendingUp,
  Layers,
  GitBranch
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, PieChart, Pie, Cell, Tooltip, AreaChart, Area } from 'recharts'

// Types for Knowledge Flow
interface KnowledgeFlowEvent {
  event_id: string
  source_id: string
  source_type: 'document' | 'code' | 'conversation' | 'web_scrape' | 'api_response'
  source_name: string
  stage: string
  timestamp: string
  processing_time_ms?: number
  data_size_bytes?: number
  patterns_extracted?: number
  quality_score?: number
  storage_locations: string[]
  metadata: Record<string, any>
  error_message?: string
}

interface KnowledgeFlowSession {
  session_id: string
  source_type: string
  source_name: string
  started_at: string
  completed_at?: string
  total_items_processed: number
  patterns_generated: number
  avg_quality_score?: number
  storage_distribution: Record<string, number>
  status: 'active' | 'completed' | 'failed'
}

interface RealtimeStats {
  active_sessions: number
  events_last_hour: number
  events_last_24h: number
  patterns_generated_last_hour: number
  patterns_generated_last_24h: number
  avg_processing_time_ms: number
  avg_quality_score: number
  storage_distribution: Record<string, number>
  source_type_breakdown: Record<string, number>
}

// Source type icons and colors
const SOURCE_TYPE_CONFIG = {
  document: { icon: FileText, color: '#3B82F6', label: 'Document' },
  code: { icon: Code, color: '#10B981', label: 'Code' },
  conversation: { icon: MessageSquare, color: '#8B5CF6', label: 'Conversation' },
  web_scrape: { icon: Globe, color: '#F59E0B', label: 'Web Scrape' },
  api_response: { icon: Database, color: '#EF4444', label: 'API Response' }
}

// Processing stage configuration
const STAGE_CONFIG = {
  ingested: { label: 'Ingested', color: '#6B7280', icon: Archive },
  parsing: { label: 'Parsing', color: '#3B82F6', icon: FileText },
  pattern_extraction: { label: 'Pattern Extraction', color: '#8B5CF6', icon: GitBranch },
  quality_scoring: { label: 'Quality Scoring', color: '#F59E0B', icon: BarChart3 },
  relationship_mapping: { label: 'Relationship Mapping', color: '#10B981', icon: Network },
  storage_postgres: { label: 'PostgreSQL Storage', color: '#1F2937', icon: Database },
  storage_neo4j: { label: 'Neo4j Storage', color: '#059669', icon: Network },
  storage_qdrant: { label: 'Qdrant Storage', color: '#7C3AED', icon: Layers },
  storage_redis: { label: 'Redis Cache', color: '#DC2626', icon: Zap },
  completed: { label: 'Completed', color: '#10B981', icon: CheckCircle },
  failed: { label: 'Failed', color: '#EF4444', icon: XCircle }
}

// Mock API functions (replace with real API calls)
const mockApi = {
  getRealtimeStats: async (): Promise<{ realtime_stats: RealtimeStats }> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))
    return {
      realtime_stats: {
        active_sessions: 3,
        events_last_hour: 24,
        events_last_24h: 187,
        patterns_generated_last_hour: 12,
        patterns_generated_last_24h: 89,
        avg_processing_time_ms: 1250.5,
        avg_quality_score: 0.87,
        storage_distribution: {
          postgres: 45,
          neo4j: 38,
          qdrant: 42,
          redis: 89
        },
        source_type_breakdown: {
          document: 12,
          code: 8,
          conversation: 15,
          web_scrape: 6,
          api_response: 4
        }
      }
    }
  },
  
  getRecentEvents: async (limit: number = 20): Promise<{ events: KnowledgeFlowEvent[] }> => {
    await new Promise(resolve => setTimeout(resolve, 300))
    return {
      events: [
        {
          event_id: '1',
          source_id: 'session-123',
          source_type: 'web_scrape',
          source_name: 'FastAPI Documentation',
          stage: 'pattern_extraction',
          timestamp: new Date(Date.now() - 30000).toISOString(),
          processing_time_ms: 1200,
          patterns_extracted: 5,
          storage_locations: [],
          metadata: { description: 'Extracting authentication patterns' }
        },
        {
          event_id: '2', 
          source_id: 'session-124',
          source_type: 'code',
          source_name: 'auth.py',
          stage: 'quality_scoring',
          timestamp: new Date(Date.now() - 45000).toISOString(),
          processing_time_ms: 800,
          quality_score: 0.92,
          storage_locations: [],
          metadata: { description: 'Analyzing code quality metrics' }
        },
        {
          event_id: '3',
          source_id: 'session-123',
          source_type: 'web_scrape', 
          source_name: 'FastAPI Documentation',
          stage: 'storage_qdrant',
          timestamp: new Date(Date.now() - 60000).toISOString(),
          processing_time_ms: 450,
          storage_locations: ['qdrant'],
          metadata: { description: 'Storing vector embeddings' }
        },
        {
          event_id: '4',
          source_id: 'session-125',
          source_type: 'conversation',
          source_name: 'Claude Code Session #47',
          stage: 'completed',
          timestamp: new Date(Date.now() - 120000).toISOString(),
          processing_time_ms: 3500,
          patterns_extracted: 8,
          quality_score: 0.89,
          storage_locations: ['postgres', 'neo4j', 'qdrant'],
          metadata: { description: 'Debugging session analysis complete' }
        }
      ]
    }
  },
  
  getActiveSessions: async (): Promise<{ active_sessions: KnowledgeFlowSession[] }> => {
    await new Promise(resolve => setTimeout(resolve, 400))
    return {
      active_sessions: [
        {
          session_id: 'session-123',
          source_type: 'web_scrape',
          source_name: 'FastAPI Documentation',
          started_at: new Date(Date.now() - 300000).toISOString(),
          total_items_processed: 12,
          patterns_generated: 8,
          avg_quality_score: 0.91,
          storage_distribution: { postgres: 8, neo4j: 6, qdrant: 8, redis: 12 },
          status: 'active'
        },
        {
          session_id: 'session-124',
          source_type: 'code',
          source_name: 'Authentication System',
          started_at: new Date(Date.now() - 180000).toISOString(),
          total_items_processed: 6,
          patterns_generated: 4,
          avg_quality_score: 0.94,
          storage_distribution: { postgres: 4, neo4j: 3, qdrant: 4, redis: 6 },
          status: 'active'
        }
      ]
    }
  },
  
  startDemoIngestion: async (url: string): Promise<{ session_id: string }> => {
    await new Promise(resolve => setTimeout(resolve, 200))
    return { session_id: 'demo-' + Date.now() }
  }
}

const KnowledgeFlowDashboard: React.FC = () => {
  const [realtimeStats, setRealtimeStats] = useState<RealtimeStats | null>(null)
  const [recentEvents, setRecentEvents] = useState<KnowledgeFlowEvent[]>([])
  const [activeSessions, setActiveSessions] = useState<KnowledgeFlowSession[]>([])
  const [isLiveMode, setIsLiveMode] = useState(true)
  const [selectedEvent, setSelectedEvent] = useState<KnowledgeFlowEvent | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, eventsRes, sessionsRes] = await Promise.all([
          mockApi.getRealtimeStats(),
          mockApi.getRecentEvents(20),
          mockApi.getActiveSessions()
        ])
        
        setRealtimeStats(statsRes.realtime_stats)
        setRecentEvents(eventsRes.events)
        setActiveSessions(sessionsRes.active_sessions)
      } catch (error) {
        console.error('Failed to fetch knowledge flow data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
    
    // Auto-refresh in live mode
    const interval = setInterval(() => {
      if (isLiveMode) {
        fetchData()
      }
    }, 5000)
    
    return () => clearInterval(interval)
  }, [isLiveMode])

  const handleStartDemo = async () => {
    try {
      await mockApi.startDemoIngestion('https://fastapi.tiangolo.com/tutorial/')
      // Refresh data to show new session
      setTimeout(() => window.location.reload(), 1000)
    } catch (error) {
      console.error('Failed to start demo:', error)
    }
  }

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
            Loading Knowledge Flow
          </h2>
          <p className="text-gray-500">
            Analyzing Betty's learning processes...
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
          <Activity className="w-8 h-8 text-betty-500 mr-3" />
          <h1 className="text-4xl font-bold text-white">Knowledge Flow</h1>
        </div>
        <p className="text-xl text-white/80 max-w-3xl mx-auto">
          Real-time visualization of Betty's knowledge ingestion, pattern generation, and storage processes.
          Watch as documentation, code, and conversations become structured intelligence.
        </p>
        
        {/* Live Mode Toggle */}
        <div className="flex items-center justify-center mt-6 space-x-4">
          <button
            onClick={() => setIsLiveMode(!isLiveMode)}
            className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
              isLiveMode
                ? 'bg-green-500 text-white'
                : 'bg-gray-500 text-white/70'
            }`}
          >
            {isLiveMode ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
            {isLiveMode ? 'Live Mode' : 'Paused'}
          </button>
          
          <button
            onClick={handleStartDemo}
            className="flex items-center px-4 py-2 bg-betty-500 text-white rounded-lg hover:bg-betty-600 transition-colors"
          >
            <Globe className="w-4 h-4 mr-2" />
            Demo: Ingest Documentation
          </button>
        </div>
      </motion.div>

      {/* Real-time Stats */}
      {realtimeStats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8"
        >
          <div className="glass-card rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-green-500">{realtimeStats.active_sessions}</div>
            <div className="text-sm text-gray-600">Active Sessions</div>
          </div>
          <div className="glass-card rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-blue-500">{realtimeStats.events_last_hour}</div>
            <div className="text-sm text-gray-600">Events (1h)</div>
          </div>
          <div className="glass-card rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-purple-500">{realtimeStats.patterns_generated_last_hour}</div>
            <div className="text-sm text-gray-600">Patterns (1h)</div>
          </div>
          <div className="glass-card rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-yellow-500">{Math.round(realtimeStats.avg_processing_time_ms)}ms</div>
            <div className="text-sm text-gray-600">Avg Processing</div>
          </div>
          <div className="glass-card rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-green-500">{Math.round(realtimeStats.avg_quality_score * 100)}%</div>
            <div className="text-sm text-gray-600">Quality Score</div>
          </div>
          <div className="glass-card rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-red-500">{realtimeStats.events_last_24h}</div>
            <div className="text-sm text-gray-600">Events (24h)</div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Recent Events Stream */}
        <div className="xl:col-span-2">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card rounded-2xl p-6 h-96 overflow-hidden"
          >
            <h3 className="text-xl font-semibold text-gray-700 mb-4 flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Live Event Stream
            </h3>
            
            <div className="space-y-3 overflow-y-auto h-full">
              {recentEvents.map((event, index) => {
                const sourceConfig = SOURCE_TYPE_CONFIG[event.source_type as keyof typeof SOURCE_TYPE_CONFIG]
                const stageConfig = STAGE_CONFIG[event.stage as keyof typeof STAGE_CONFIG]
                const SourceIcon = sourceConfig?.icon || Database
                const StageIcon = stageConfig?.icon || Activity
                
                return (
                  <motion.div
                    key={event.event_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => setSelectedEvent(event)}
                    className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg`} style={{ backgroundColor: `${sourceConfig?.color}20`, border: `1px solid ${sourceConfig?.color}` }}>
                          <SourceIcon className="w-4 h-4" style={{ color: sourceConfig?.color }} />
                        </div>
                        <div>
                          <div className="font-medium text-sm text-gray-800">{event.source_name}</div>
                          <div className="flex items-center text-xs text-gray-500 mt-1">
                            <StageIcon className="w-3 h-3 mr-1" style={{ color: stageConfig?.color }} />
                            {stageConfig?.label}
                            {event.processing_time_ms && (
                              <span className="ml-2">• {event.processing_time_ms}ms</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                    
                    {event.metadata?.description && (
                      <div className="mt-2 text-xs text-gray-600">
                        {event.metadata.description}
                      </div>
                    )}
                    
                    {event.storage_locations.length > 0 && (
                      <div className="mt-2 flex space-x-1">
                        {event.storage_locations.map(location => (
                          <span key={location} className="px-2 py-1 bg-gray-100 text-xs rounded">
                            {location}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    {event.patterns_extracted && (
                      <div className="mt-2 text-xs text-purple-600">
                        🎯 {event.patterns_extracted} patterns extracted
                      </div>
                    )}
                    
                    {event.quality_score && (
                      <div className="mt-2 text-xs text-green-600">
                        ⭐ Quality: {Math.round(event.quality_score * 100)}%
                      </div>
                    )}
                  </motion.div>
                )
              })}
            </div>
          </motion.div>
        </div>

        {/* Active Sessions */}
        <div>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card rounded-2xl p-6 mb-6"
          >
            <h3 className="text-xl font-semibold text-gray-700 mb-4 flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              Active Sessions
            </h3>
            
            <div className="space-y-4">
              {activeSessions.map(session => {
                const sourceConfig = SOURCE_TYPE_CONFIG[session.source_type as keyof typeof SOURCE_TYPE_CONFIG]
                const SourceIcon = sourceConfig?.icon || Database
                
                return (
                  <div key={session.session_id} className="bg-white p-4 rounded-lg border border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div className={`p-1 rounded`} style={{ backgroundColor: `${sourceConfig?.color}20`, border: `1px solid ${sourceConfig?.color}` }}>
                          <SourceIcon className="w-3 h-3" style={{ color: sourceConfig?.color }} />
                        </div>
                        <span className="font-medium text-sm">{session.source_name}</span>
                      </div>
                      <div className={`px-2 py-1 rounded-full text-xs ${
                        session.status === 'active' ? 'bg-green-100 text-green-800' :
                        session.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {session.status}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                      <div>Items: {session.total_items_processed}</div>
                      <div>Patterns: {session.patterns_generated}</div>
                      {session.avg_quality_score && (
                        <div className="col-span-2">
                          Quality: {Math.round(session.avg_quality_score * 100)}%
                        </div>
                      )}
                    </div>
                    
                    <div className="mt-2 text-xs text-gray-500">
                      Started: {new Date(session.started_at).toLocaleTimeString()}
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>

          {/* Storage Distribution */}
          {realtimeStats && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="glass-card rounded-2xl p-6"
            >
              <h3 className="text-xl font-semibold text-gray-700 mb-4 flex items-center">
                <Database className="w-5 h-5 mr-2" />
                Storage Distribution
              </h3>
              
              <div className="space-y-3">
                {Object.entries(realtimeStats.storage_distribution).map(([db, count]) => {
                  const colors = {
                    postgres: '#1F2937',
                    neo4j: '#059669', 
                    qdrant: '#7C3AED',
                    redis: '#DC2626'
                  }
                  
                  const total = Object.values(realtimeStats.storage_distribution).reduce((a, b) => a + b, 0)
                  const percentage = Math.round((count / total) * 100)
                  
                  return (
                    <div key={db} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: colors[db as keyof typeof colors] }}
                        ></div>
                        <span className="text-sm font-medium capitalize">{db}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-600">{count}</span>
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all duration-500"
                            style={{ 
                              backgroundColor: colors[db as keyof typeof colors],
                              width: `${percentage}%`
                            }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500 w-10">{percentage}%</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Event Detail Modal */}
      <AnimatePresence>
        {selectedEvent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setSelectedEvent(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold">Event Details</h3>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Source</label>
                  <div className="text-lg">{selectedEvent.source_name}</div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Stage</label>
                  <div className="text-lg">{STAGE_CONFIG[selectedEvent.stage as keyof typeof STAGE_CONFIG]?.label || selectedEvent.stage}</div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Timestamp</label>
                  <div>{new Date(selectedEvent.timestamp).toLocaleString()}</div>
                </div>
                
                {selectedEvent.processing_time_ms && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Processing Time</label>
                    <div>{selectedEvent.processing_time_ms}ms</div>
                  </div>
                )}
                
                {selectedEvent.patterns_extracted && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Patterns Extracted</label>
                    <div>{selectedEvent.patterns_extracted}</div>
                  </div>
                )}
                
                {selectedEvent.quality_score && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Quality Score</label>
                    <div>{Math.round(selectedEvent.quality_score * 100)}%</div>
                  </div>
                )}
                
                {selectedEvent.storage_locations.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Storage Locations</label>
                    <div className="flex space-x-2 mt-1">
                      {selectedEvent.storage_locations.map(location => (
                        <span key={location} className="px-2 py-1 bg-gray-100 rounded text-sm">
                          {location}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {selectedEvent.metadata && Object.keys(selectedEvent.metadata).length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Metadata</label>
                    <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto mt-1">
                      {JSON.stringify(selectedEvent.metadata, null, 2)}
                    </pre>
                  </div>
                )}
                
                {selectedEvent.error_message && (
                  <div>
                    <label className="text-sm font-medium text-red-600">Error</label>
                    <div className="text-red-700 bg-red-50 p-3 rounded">{selectedEvent.error_message}</div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default KnowledgeFlowDashboard