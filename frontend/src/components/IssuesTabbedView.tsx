// ABOUTME: Tabbed view for issues with status-based categories and auto-refresh
// ABOUTME: Displays issues organized by status with drag-and-drop support and real-time updates

import React, { useState, useEffect } from 'react'
import { Issue, Project } from '../App'
import { format } from 'date-fns'
import MarkdownRenderer from './MarkdownRenderer'
import { getMarkdownPreview } from '../utils/markdown'

interface Props {
  issues: Issue[]
  projects: Project[]
  onStatusUpdate: (issueId: string, newStatus: Issue['status']) => void
  onIssueClick: (issue: Issue) => void
  onNewIssue: () => void
  autoRefresh?: boolean
  refreshInterval?: number
  onRefresh?: () => void
}

// Define the tabs with their corresponding statuses
const ISSUE_TABS = [
  { id: 'backlog', label: 'Backlog', status: 'backlog', color: 'bg-gray-500', icon: '📋' },
  { id: 'in_progress', label: 'In Progress', status: 'in_progress', color: 'bg-yellow-500', icon: '🚀' },
  { id: 'in_testing', label: 'In Testing', status: 'in_review', color: 'bg-purple-500', icon: '🧪' },
  { id: 'completed', label: 'Completed', status: 'done', color: 'bg-green-500', icon: '✅' },
  { id: 'failed', label: 'Failed', status: 'cancelled', color: 'bg-red-500', icon: '❌' },
  { id: 'bug', label: 'Bugs', status: 'bug', color: 'bg-orange-500', icon: '🐛' },
]

const IssuesTabbedView: React.FC<Props> = ({
  issues,
  projects,
  onStatusUpdate,
  onIssueClick,
  onNewIssue,
  autoRefresh = true,
  refreshInterval = 10000, // 10 seconds
  onRefresh
}) => {
  const [activeTab, setActiveTab] = useState('backlog')
  const [lastRefresh, setLastRefresh] = useState(new Date())
  const [countdown, setCountdown] = useState(refreshInterval / 1000)

  // Auto-refresh logic
  useEffect(() => {
    if (!autoRefresh || !onRefresh) return

    const interval = setInterval(() => {
      onRefresh()
      setLastRefresh(new Date())
      setCountdown(refreshInterval / 1000)
    }, refreshInterval)

    // Countdown timer
    const countdownInterval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) return refreshInterval / 1000
        return prev - 1
      })
    }, 1000)

    return () => {
      clearInterval(interval)
      clearInterval(countdownInterval)
    }
  }, [autoRefresh, refreshInterval, onRefresh])

  // Filter issues by tab
  const getIssuesByTab = (tabId: string) => {
    if (tabId === 'bug') {
      // Special handling for bugs - filter by title or label
      return issues.filter(issue => 
        issue.title.toLowerCase().includes('bug') ||
        issue.description.toLowerCase().includes('bug') ||
        issue.priority === 1 // Critical priority often indicates bugs
      )
    }
    
    const tab = ISSUE_TABS.find(t => t.id === tabId)
    if (!tab) return []
    
    return issues.filter(issue => issue.status === tab.status)
  }

  // Get count for each tab
  const getTabCount = (tabId: string) => {
    return getIssuesByTab(tabId).length
  }

  // Priority badge
  const getPriorityBadge = (priority: number) => {
    const priorities = {
      1: { label: 'Critical', color: 'bg-red-600 text-white' },
      2: { label: 'High', color: 'bg-orange-600 text-white' },
      3: { label: 'Medium', color: 'bg-yellow-600 text-white' },
      4: { label: 'Low', color: 'bg-gray-600 text-white' },
      5: { label: 'Very Low', color: 'bg-gray-500 text-gray-200' }
    }
    const p = priorities[priority as keyof typeof priorities] || priorities[3]
    return (
      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${p.color}`}>
        {p.label}
      </span>
    )
  }

  // Handle drag and drop
  const handleDragStart = (e: React.DragEvent, issueId: string) => {
    e.dataTransfer.setData('issueId', issueId)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent, targetStatus: string) => {
    e.preventDefault()
    const issueId = e.dataTransfer.getData('issueId')
    if (issueId && targetStatus !== 'bug') {
      onStatusUpdate(issueId, targetStatus as Issue['status'])
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header with tabs and auto-refresh indicator */}
      <div className="border-b border-gray-700 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-white">Issues Dashboard</h1>
          
          <div className="flex items-center space-x-4">
            {/* Auto-refresh indicator */}
            {autoRefresh && (
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refreshing in {countdown}s</span>
                <span className="text-gray-500">|</span>
                <span>Last: {format(lastRefresh, 'HH:mm:ss')}</span>
              </div>
            )}
            
            {/* New Issue button */}
            <button
              onClick={onNewIssue}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>New Issue</span>
            </button>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="flex space-x-1">
          {ISSUE_TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 font-medium text-sm rounded-t-lg transition-colors flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'bg-gray-800 text-white border-b-2 border-purple-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {getTabCount(tab.id) > 0 && (
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  activeTab === tab.id ? 'bg-purple-600' : 'bg-gray-700'
                }`}>
                  {getTabCount(tab.id)}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
      
      {/* Tab content */}
      <div 
        className="flex-1 overflow-y-auto"
        onDragOver={handleDragOver}
        onDrop={(e) => {
          const tab = ISSUE_TABS.find(t => t.id === activeTab)
          if (tab) handleDrop(e, tab.status)
        }}
      >
        {ISSUE_TABS.map(tab => {
          if (tab.id !== activeTab) return null
          
          const tabIssues = getIssuesByTab(tab.id)
          
          if (tabIssues.length === 0) {
            return (
              <div key={tab.id} className="flex flex-col items-center justify-center h-64 text-gray-500">
                <span className="text-4xl mb-4">{tab.icon}</span>
                <p className="text-lg">No issues in {tab.label}</p>
                <p className="text-sm mt-2">Drag issues here or create a new one</p>
              </div>
            )
          }
          
          return (
            <div key={tab.id} className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {tabIssues.map(issue => {
                const project = projects.find(p => p.id === issue.project_id)
                
                return (
                  <div
                    key={issue.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, issue.id)}
                    onClick={() => onIssueClick(issue)}
                    className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-purple-500 transition-all cursor-pointer group"
                  >
                    {/* Issue header */}
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium text-white flex-1 line-clamp-2 group-hover:text-purple-400 transition-colors">
                        {issue.title}
                      </h3>
                      {getPriorityBadge(issue.priority)}
                    </div>
                    
                    {/* Description preview */}
                    <p className="text-gray-400 text-sm mb-3 line-clamp-2">
                      {getMarkdownPreview(issue.description, 80)}
                    </p>
                    
                    {/* Meta info */}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      {project && (
                        <span 
                          className="px-2 py-1 rounded"
                          style={{ 
                            backgroundColor: `${project.color}20`,
                            color: project.color
                          }}
                        >
                          {project.name}
                        </span>
                      )}
                      
                      <div className="flex items-center space-x-2">
                        {issue.story_points > 0 && (
                          <span className="flex items-center">
                            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                            {issue.story_points}
                          </span>
                        )}
                        
                        {issue.completion_percentage && issue.completion_percentage > 0 && (
                          <span className="flex items-center">
                            <div className="w-8 h-1 bg-gray-700 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-purple-500"
                                style={{ width: `${issue.completion_percentage}%` }}
                              />
                            </div>
                            <span className="ml-1">{issue.completion_percentage}%</span>
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Dates if available */}
                    {(issue.start_date || issue.end_date) && (
                      <div className="mt-2 pt-2 border-t border-gray-700 text-xs text-gray-500">
                        {issue.start_date && (
                          <span>Start: {format(new Date(issue.start_date), 'MMM dd')}</span>
                        )}
                        {issue.start_date && issue.end_date && <span className="mx-2">•</span>}
                        {issue.end_date && (
                          <span>Due: {format(new Date(issue.end_date), 'MMM dd')}</span>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default IssuesTabbedView