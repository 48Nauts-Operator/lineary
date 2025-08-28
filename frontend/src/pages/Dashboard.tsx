import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useDashboardData } from '../hooks/useAnalytics'
import HeroMetrics from '../components/dashboard/HeroMetrics'
import KnowledgeGrowthChart from '../components/dashboard/KnowledgeGrowthChart'
import CrossProjectNetwork from '../components/dashboard/CrossProjectNetwork'
import PatternUsageChart from '../components/dashboard/PatternUsageChart'
import RealTimeActivity from '../components/dashboard/RealTimeActivity'
import IntelligenceMetrics from '../components/dashboard/IntelligenceMetrics'
import SystemPerformance from '../components/dashboard/SystemPerformance'
import LoadingDashboard from '../components/dashboard/LoadingDashboard'
import ErrorState from '../components/dashboard/ErrorState'
import DetailedErrorState from '../components/dashboard/DetailedErrorState'
import ErrorMonitor from '../components/dashboard/ErrorMonitor'

// Enhanced Intelligence Visualizations
import PatternLearningJourney from '../components/dashboard/PatternLearningJourney'
import KnowledgeEnhancementPanel from '../components/dashboard/KnowledgeEnhancementPanel'
import IntelligentReminders from '../components/dashboard/IntelligentReminders'
import IntelligenceCapabilities from '../components/dashboard/IntelligenceCapabilities'
import InteractivePatternExplorer from '../components/dashboard/InteractivePatternExplorer'

// Memory Correctness System
import MemoryCorrectnessMonitor from '../components/dashboard/MemoryCorrectnessMonitor'

// Knowledge Flow Dashboard
import KnowledgeFlowDashboard from './KnowledgeFlowDashboard'

const Dashboard: React.FC = () => {
  const [viewMode, setViewMode] = useState<'overview' | 'enhanced' | 'knowledge-flow'>('overview')
  
  const {
    summary,
    knowledgeGrowth,
    crossProject,
    patterns,
    activity,
    intelligence,
    performance,
    isLoading,
    isError,
    error,
    refetch
  } = useDashboardData()

  if (isLoading) {
    return <LoadingDashboard />
  }

  if (isError) {
    return (
      <>
        <DetailedErrorState 
          error={error} 
          onRetry={refetch}
          showDiagnostics={true}
          serviceName="BETTY Memory API"
        />
        <ErrorMonitor />
      </>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Title */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <h1 className="text-4xl font-bold text-white mb-4">
          Intelligence Dashboard
        </h1>
        <p className="text-xl text-white/80 max-w-3xl mx-auto">
          Visualizing Claude's growing intelligence across projects with real-time insights 
          into knowledge capture, pattern recognition, and cross-project connections.
        </p>
        
        {/* View Mode Toggle */}
        <div className="flex justify-center mt-6">
          <div className="flex space-x-1 bg-white/10 backdrop-blur-lg rounded-lg p-1">
            <button
              onClick={() => setViewMode('overview')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'overview'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-white/80 hover:text-white hover:bg-white/10'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setViewMode('enhanced')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'enhanced'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-white/80 hover:text-white hover:bg-white/10'
              }`}
            >
              Enhanced Intelligence
            </button>
            <button
              onClick={() => setViewMode('knowledge-flow')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'knowledge-flow'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-white/80 hover:text-white hover:bg-white/10'
              }`}
            >
              Knowledge Flow
            </button>
          </div>
        </div>
      </motion.div>

      {/* Hero Metrics Row */}
      <HeroMetrics data={summary} />

      {viewMode === 'overview' ? (
        /* Standard Dashboard View */
        <>
          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Charts */}
            <div className="lg:col-span-2 space-y-8">
              {/* Knowledge Growth */}
              <KnowledgeGrowthChart data={knowledgeGrowth} />

              {/* Cross-Project Network */}
              <CrossProjectNetwork data={crossProject} />

              {/* Pattern Usage */}
              <PatternUsageChart data={patterns} />
            </div>

            {/* Right Column - Activity & Metrics */}
            <div className="space-y-8">
              {/* Real-Time Activity Feed */}
              <RealTimeActivity data={activity} />

              {/* Intelligence Quality Metrics */}
              <IntelligenceMetrics data={intelligence} />

              {/* System Performance */}
              <SystemPerformance data={performance} />
            </div>
          </div>

          {/* Memory Correctness Monitor - Full Width */}
          <MemoryCorrectnessMonitor 
            projectId="betty"
            autoRefresh={true}
            refreshInterval={30000}
          />
        </>
      ) : viewMode === 'enhanced' ? (
        /* Enhanced Intelligence View */
        <>
          {/* Enhanced Intelligence Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            {/* Pattern Learning Journey */}
            <PatternLearningJourney />
            
            {/* Knowledge Enhancement Panel */}
            <KnowledgeEnhancementPanel />
          </div>

          {/* Intelligence Capabilities Full Width */}
          <IntelligenceCapabilities />
          
          {/* Intelligent Reminders and Pattern Explorer */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <IntelligentReminders 
              currentContext={{
                project: 'Betty',
                currentTask: 'Enhanced Intelligence Visualization',
                recentFiles: ['Dashboard.tsx', 'PatternLearningJourney.tsx'],
                keywords: ['visualization', 'intelligence', 'patterns', 'dashboard']
              }}
            />
            
            <InteractivePatternExplorer />
          </div>
        </>
      ) : (
        /* Knowledge Flow View */
        <KnowledgeFlowDashboard />
      )}

      {/* Technology Trends Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass-card rounded-2xl p-6"
      >
        <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center">
          <span className="mr-2">🚀</span>
          Recent Achievements
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {summary?.recent_achievements?.map((achievement, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 * index }}
              className="bg-gradient-to-r from-success-50 to-betty-50 p-4 rounded-lg border border-success-200"
            >
              <p className="text-sm text-gray-700 font-medium">
                {achievement}
              </p>
            </motion.div>
          )) || []}
        </div>
      </motion.div>

      {/* Footer Stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="glass-card rounded-2xl p-6 text-center"
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <div className="text-2xl font-bold text-betty-600">
              {summary?.total_knowledge_items?.toLocaleString() || '0'}
            </div>
            <div className="text-sm text-gray-500">Total Knowledge Items</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-success-600">
              {Math.round((summary?.intelligence_score || 0) * 10) / 10}
            </div>
            <div className="text-sm text-gray-500">Intelligence Score</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600">
              {summary?.cross_project_connections || 0}
            </div>
            <div className="text-sm text-gray-500">Project Connections</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-warning-600">
              {Math.round(summary?.avg_response_time_ms || 0)}ms
            </div>
            <div className="text-sm text-gray-500">Avg Response Time</div>
          </div>
        </div>
      </motion.div>

      {/* Error Monitor - Always present for debugging */}
      <ErrorMonitor position="bottom-right" />
    </div>
  )
}

export default Dashboard