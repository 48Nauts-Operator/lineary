// ABOUTME: Compact Linear-style issues view showing all issues across projects
// ABOUTME: Provides streamlined list view with project tags and efficient density

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { Project, Issue, API_URL } from '../App'
import IssueModal from './IssueModal'

// Extend Issue type to include additional fields
interface ExtendedIssue extends Issue {
  assignee_id?: string
  updated_at?: string
}

interface Props {
  selectedProject: Project | null
  projects: Project[]
}

type ViewMode = 'project' | 'all'

const CompactIssuesView: React.FC<Props> = ({ selectedProject, projects }) => {
  const [issues, setIssues] = useState<ExtendedIssue[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedIssue, setSelectedIssue] = useState<ExtendedIssue | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('project')
  const [filterStatus, setFilterStatus] = useState<string>('active')
  const [showNewIssueForm, setShowNewIssueForm] = useState(false)

  useEffect(() => {
    fetchIssues()
  }, [selectedProject, viewMode])

  const fetchIssues = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/issues`)
      let issuesData = response.data || []
      
      // Filter by view mode
      if (viewMode === 'project' && selectedProject) {
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
    const icons: Record<string, string> = {
      backlog: '⚪',
      todo: '🔵',
      in_progress: '🟡',
      in_review: '🟣',
      done: '🟢',
      cancelled: '🔴'
    }
    return icons[status] || '⚪'
  }

  const getPriorityIcon = (priority: number) => {
    const icons = {
      1: '🔺',  // Critical - up triangle
      2: '🔸',  // High - diamond
      3: '➖',  // Medium - dash
      4: '🔻',  // Low - down triangle
      5: '⏸️'   // Lowest - pause
    }
    return icons[priority as keyof typeof icons] || '➖'
  }

  const getProjectColor = (projectId: string) => {
    const project = projects.find(p => p.id === projectId)
    return project?.color || '#6B7280'
  }

  const getProjectName = (projectId: string) => {
    const project = projects.find(p => p.id === projectId)
    return project?.name || 'Unknown'
  }

  const getProjectAbbreviation = (projectId: string) => {
    const project = projects.find(p => p.id === projectId)
    if (!project) return 'UN'
    
    // Create abbreviation from project name
    const words = project.name.split(' ')
    if (words.length > 1) {
      return words.map(w => w[0]).join('').toUpperCase().slice(0, 3)
    }
    return project.name.slice(0, 3).toUpperCase()
  }

  const filteredIssues = issues.filter(issue => {
    if (filterStatus === 'active') {
      return !['done', 'cancelled'].includes(issue.status)
    } else if (filterStatus === 'completed') {
      return ['done', 'cancelled'].includes(issue.status)
    }
    return true
  })

  const groupedIssues = filteredIssues.reduce((acc, issue) => {
    const status = issue.status
    if (!acc[status]) {
      acc[status] = []
    }
    acc[status].push(issue)
    return acc
  }, {} as Record<string, ExtendedIssue[]>)

  const statusOrder = ['backlog', 'todo', 'in_progress', 'in_review', 'done', 'cancelled']
  const orderedStatuses = statusOrder.filter(status => groupedIssues[status])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-purple-500/30 rounded-full animate-spin border-t-purple-500 mx-auto"></div>
          <p className="text-gray-400 mt-2 text-sm">Loading issues...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Compact Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-800">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-white">Issues</h2>
          
          {/* View Toggle */}
          <div className="flex items-center bg-gray-800 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('project')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'project'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Current Project
            </button>
            <button
              onClick={() => setViewMode('all')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'all'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              All Issues
            </button>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filterStatus === 'all'
                  ? 'bg-purple-600/20 text-purple-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterStatus('active')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filterStatus === 'active'
                  ? 'bg-purple-600/20 text-purple-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setFilterStatus('completed')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filterStatus === 'completed'
                  ? 'bg-purple-600/20 text-purple-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              Completed
            </button>
          </div>

          <span className="text-xs text-gray-500">
            {filteredIssues.length} {filteredIssues.length === 1 ? 'issue' : 'issues'}
          </span>
        </div>

        <button
          onClick={() => setShowNewIssueForm(true)}
          disabled={viewMode === 'project' && !selectedProject}
          className="flex items-center space-x-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-md text-white text-xs font-medium transition-colors"
        >
          <span>+</span>
          <span>New Issue</span>
        </button>
      </div>

      {/* Compact Issues List */}
      <div className="flex-1 overflow-y-auto">
        {filteredIssues.length > 0 ? (
          <div className="divide-y divide-gray-800/50">
            {orderedStatuses.map(status => (
              <div key={status}>
                {/* Status Group Header */}
                <div className="px-6 py-2 bg-gray-900/30 border-b border-gray-800/50">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs">{getStatusIcon(status)}</span>
                    <span className="text-xs font-medium text-gray-400 uppercase">
                      {status.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-gray-600">
                      {groupedIssues[status].length}
                    </span>
                  </div>
                </div>
                
                {/* Issues in this status */}
                {groupedIssues[status].map(issue => (
                  <div
                    key={issue.id}
                    onClick={() => setSelectedIssue(issue)}
                    className="flex items-center px-6 py-2 hover:bg-gray-800/30 cursor-pointer transition-colors group"
                  >
                    {/* Issue ID */}
                    <div className="w-20 flex-shrink-0">
                      <span className="text-xs text-gray-500 font-mono">
                        {issue.id.slice(-6).toUpperCase()}
                      </span>
                    </div>

                    {/* Priority */}
                    <div className="w-8 flex-shrink-0 text-center">
                      <span className="text-xs">{getPriorityIcon(issue.priority)}</span>
                    </div>

                    {/* Project Badge (only in All Issues view) */}
                    {viewMode === 'all' && (
                      <div className="w-24 flex-shrink-0 mr-3">
                        <div 
                          className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-medium"
                          style={{ 
                            backgroundColor: `${getProjectColor(issue.project_id)}20`,
                            color: getProjectColor(issue.project_id)
                          }}
                        >
                          <div 
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ backgroundColor: getProjectColor(issue.project_id) }}
                          />
                          <span>{getProjectAbbreviation(issue.project_id)}</span>
                        </div>
                      </div>
                    )}

                    {/* Issue Title */}
                    <div className="flex-1 min-w-0 mr-4">
                      <p className="text-sm text-white truncate group-hover:text-purple-400 transition-colors">
                        {issue.title}
                      </p>
                    </div>

                    {/* Assignee */}
                    <div className="w-8 flex-shrink-0">
                      {issue.assignee_id ? (
                        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                          <span className="text-xs text-white font-medium">
                            {issue.assignee_id.slice(0, 1).toUpperCase()}
                          </span>
                        </div>
                      ) : (
                        <div className="w-6 h-6 rounded-full border border-gray-700 border-dashed" />
                      )}
                    </div>

                    {/* Story Points */}
                    {issue.story_points && (
                      <div className="w-12 flex-shrink-0 text-right">
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

                    {/* Updated */}
                    {issue.updated_at && (
                      <div className="w-16 flex-shrink-0 text-right">
                        <span className="text-xs text-gray-600">
                          {format(new Date(issue.updated_at), 'HH:mm')}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-4xl mb-2">📋</div>
              <h3 className="text-sm font-medium text-white mb-1">No issues found</h3>
              <p className="text-xs text-gray-400">
                {viewMode === 'project' && !selectedProject
                  ? 'Select a project to view issues'
                  : 'Create your first issue to get started'
                }
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Issue Modal */}
      {selectedIssue && (
        <IssueModal
          issue={selectedIssue}
          isOpen={!!selectedIssue}
          onClose={() => setSelectedIssue(null)}
          onUpdate={fetchIssues}
          projects={projects}
        />
      )}

      {/* New Issue Modal */}
      {showNewIssueForm && (
        <IssueModal
          isOpen={showNewIssueForm}
          onClose={() => setShowNewIssueForm(false)}
          onUpdate={fetchIssues}
          projects={projects}
          selectedProject={viewMode === 'project' ? selectedProject : null}
        />
      )}
    </div>
  )
}

export default CompactIssuesView