// ABOUTME: Enhanced issues management page with dependencies, subtasks, and AI features
// ABOUTME: Comprehensive issue tracking with progress, dates, and activity timeline

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { Project, Issue, Activity, API_URL } from '../App'
import EnhancedIssueDetail from '../components/EnhancedIssueDetail'
import IssueModal from '../components/IssueModal'
import { getMarkdownPreview } from '../utils/markdown'

interface Props {
  selectedProject: Project | null
  projects: Project[]
  statusFilter?: string
  filteredIssues?: Issue[]
}

const IssuesPage: React.FC<Props> = ({ selectedProject, projects, statusFilter, filteredIssues }) => {
  const [issues, setIssues] = useState<Issue[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewIssueForm, setShowNewIssueForm] = useState(false)
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [showAllProjects, setShowAllProjects] = useState(false)
  const [showFilterDropdown, setShowFilterDropdown] = useState(false)

  useEffect(() => {
    fetchIssues()
  }, [selectedProject, showAllProjects])

  const fetchIssues = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/issues`)
      let issuesData = response.data || []
      
      // Filter by selected project if one is selected and not showing all
      if (selectedProject && !showAllProjects) {
        issuesData = issuesData.filter((issue: Issue) => issue.project_id === selectedProject.id)
      }
      
      setIssues(issuesData)
    } catch (error) {
      console.error('Error fetching issues:', error)
      toast.error('Failed to load issues')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    // More meaningful status-based icons
    const icons: Record<string, string> = {
      backlog: '📋',      // Clipboard for backlog items
      todo: '⭕',         // Circle/ready to start
      in_progress: '🔄',  // In progress/working
      in_review: '👁️',    // Review/checking
      done: '✅',         // Checkmark for done
      cancelled: '⛔',    // Stop/cancelled
      blocked: '🚧',      // Roadblock/blocked
      testing: '🧪'       // Testing
    }
    return icons[status] || '📋'
  }

  const getPriorityIcon = (priority: number) => {
    // Cleaner priority indicators
    const icons = {
      1: '🔴',  // Urgent/Critical (red)
      2: '🟠',  // High (orange)
      3: '🟡',  // Medium (yellow)
      4: '🟢',  // Low (green)
      5: '⚪'   // None/Minimal (white)
    }
    return icons[priority as keyof typeof icons] || '⚪'
  }

  // Use passed filteredIssues if available, otherwise filter locally
  const displayIssues = filteredIssues || issues.filter(issue => {
    if (filterStatus === 'active') {
      return !['done', 'cancelled'].includes(issue.status)
    } else if (filterStatus === 'completed') {
      return issue.status === 'done'
    }
    return true
  })

  const groupedIssues = displayIssues.reduce((acc, issue) => {
    const status = issue.status
    if (!acc[status]) {
      acc[status] = []
    }
    acc[status].push(issue)
    return acc
  }, {} as Record<string, Issue[]>)

  const statusOrder = ['backlog', 'todo', 'in_progress', 'in_review', 'done', 'cancelled']
  const orderedStatuses = statusOrder.filter(status => groupedIssues[status])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500/30 rounded-full animate-spin border-t-purple-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading issues...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold">
            Issues - {selectedProject ? selectedProject.name : 'All Projects'}
          </h2>
          
          {/* Filter Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowFilterDropdown(!showFilterDropdown)}
              className="flex items-center space-x-2 px-3 py-1 text-sm rounded hover:bg-gray-800 transition-colors"
            >
              <span className={filterStatus === 'all' ? 'text-gray-400' : 'text-purple-400'}>
                {filterStatus === 'all' ? 'All Issues' : 
                 filterStatus === 'active' ? 'Active' :
                 filterStatus === 'completed' ? 'Done' :
                 filterStatus === 'backlog' ? 'Backlog' :
                 filterStatus === 'sprint' ? 'Sprint' :
                 filterStatus === 'processing' ? 'Processing' :
                 filterStatus === 'testing' ? 'Testing' : filterStatus}
              </span>
              <svg className="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showFilterDropdown && (
              <div className="absolute top-full left-0 mt-1 w-40 bg-gray-900 border border-gray-700 rounded-lg shadow-lg py-1 z-50">
                {[
                  { value: 'all', label: 'All Issues' },
                  { value: 'backlog', label: 'Backlog' },
                  { value: 'sprint', label: 'Sprint' },
                  { value: 'active', label: 'In Progress' },
                  { value: 'testing', label: 'Testing' },
                  { value: 'completed', label: 'Done' }
                ].map(option => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setFilterStatus(option.value)
                      setShowFilterDropdown(false)
                    }}
                    className={`w-full text-left px-3 py-1.5 text-sm hover:bg-gray-800 transition-colors flex items-center justify-between ${
                      filterStatus === option.value ? 'text-purple-400' : 'text-gray-300'
                    }`}
                  >
                    <span>{option.label}</span>
                    {filterStatus === option.value && (
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <span className="text-sm text-gray-500">
            {displayIssues.length} issues
          </span>
        </div>
        
        <button 
          onClick={() => setShowNewIssueForm(true)}
          className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-white font-medium transition-all duration-200"
        >
          + New Issue
        </button>
      </div>

      {/* Issues List - Linear Style */}
      <div className="flex-1 overflow-y-auto">
        {displayIssues.length > 0 ? (
          <div className="space-y-1">
            {orderedStatuses.map(status => (
              <div key={status}>
                {/* Status Group Header */}
                <div className="flex items-center px-3 py-2 text-xs font-medium text-gray-500 uppercase">
                  <span className="mr-2">{getStatusIcon(status)}</span>
                  <span>{status.replace('_', ' ')}</span>
                  <span className="ml-2 text-gray-600">
                    {groupedIssues[status].length}
                  </span>
                </div>
                
                {/* Issues in this status */}
                {groupedIssues[status].map(issue => {
                  const project = projects.find(p => p.id === issue.project_id)
                  
                  return (
                    <div
                      key={issue.id}
                      onClick={() => setSelectedIssue(issue)}
                      className="flex items-center px-4 py-2 hover:bg-gray-800/30 cursor-pointer transition-colors group"
                    >
                      {/* Issue ID */}
                      <div className="w-20 flex-shrink-0">
                        <span className="text-xs text-gray-500 font-mono">
                          {issue.id.slice(-6).toUpperCase()}
                        </span>
                      </div>

                      {/* Priority Icon */}
                      <div className="w-8 flex-shrink-0 text-center">
                        <span className="text-sm">{getPriorityIcon(issue.priority)}</span>
                      </div>

                      {/* Issue Title */}
                      <div className="flex-1 min-w-0 mr-4">
                        <p className="text-sm text-white truncate group-hover:text-purple-400 transition-colors">
                          {issue.title}
                        </p>
                      </div>

                      {/* Story Points */}
                      {issue.story_points && (
                        <div className="w-12 flex-shrink-0 text-center">
                          <span className="text-xs text-gray-500">{issue.story_points} pts</span>
                        </div>
                      )}

                      {/* Due Date */}
                      {issue.end_date && (
                        <div className="w-20 flex-shrink-0 text-right">
                          <span className="text-xs text-gray-500">
                            {format(new Date(issue.end_date), 'MMM dd')}
                          </span>
                        </div>
                      )}

                      {/* Created Date */}
                      <div className="w-20 flex-shrink-0 text-right">
                        <span className="text-xs text-gray-600">
                          {format(new Date(issue.created_at), 'MMM dd')}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-4xl mb-2">📋</div>
              <h3 className="text-sm font-medium text-white mb-1">No issues found</h3>
              <p className="text-xs text-gray-400">
                {!selectedProject
                  ? 'Select a project to view issues'
                  : 'Create your first issue to get started'
                }
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showNewIssueForm && (
        <IssueModal
          isOpen={showNewIssueForm}
          onClose={() => setShowNewIssueForm(false)}
          onUpdate={fetchIssues}
          projects={projects}
          selectedProject={selectedProject}
        />
      )}
      
      {selectedIssue && (
        <EnhancedIssueDetail
          issue={selectedIssue}
          isOpen={!!selectedIssue}
          onClose={() => setSelectedIssue(null)}
          onUpdate={fetchIssues}
          projects={projects}
        />
      )}
    </div>
  )
}

export default IssuesPage