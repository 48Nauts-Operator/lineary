// ABOUTME: Simplified working Lineary app
// ABOUTME: Basic structure with navigation and pages

import React, { useState, useEffect } from 'react'
import axios from 'axios'
// EnhancedIssueDetail is the legacy kitchen-sink modal; kept in src/ for now
// (unused) until the IssueStream replacement is fully proven in prod.
import IssueStream from './components/IssueStream'
import IssuesPage from './pages/IssuesPage'
import SprintsPage from './pages/SprintsPage'
import DocsPage from './pages/DocsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import { AccountPage } from './pages/Settings/Account'
import { ProjectModeDialog } from './components/ProjectModeDialog'
import { GitHubSyncBadge } from './components/GitHubSyncBadge'
import { ProjectPulse } from './components/ProjectPulse'
import { ReviewPage } from './pages/ReviewPage'
import { ProjectDashboard } from './pages/ProjectDashboard'
import { AgentsPage } from './pages/AgentsPage'
import { OperationsPage } from './pages/OperationsPage'
import { WelcomePage } from './pages/WelcomePage'
import IntegrationCards from './components/IntegrationCards'
import AutopilotDashboard from './components/AutopilotDashboard'
import BugReportForm from './components/BugReportForm'
import FileUpload from './components/FileUpload'
import VersionManager from './components/VersionManager'
import DevelopmentTimeline from './components/DevelopmentTimeline'
import ProjectColorPicker from './components/ProjectColorPicker'

// Relative: nginx inside the frontend container proxies /api/ to the backend.
export const API_URL = '/api'

export interface Project {
  id: string
  name: string
  description: string
  slug: string
  color: string
  icon: string
  created_at: string
  mode?: 'mcp_only' | 'github'
}

export interface Issue {
  id: string
  project_id: string
  title: string
  description: string
  status: string
  priority: number
  story_points: number
  estimated_hours: number
  created_at: string
  dependencies?: string[]
  start_date?: string
  end_date?: string
  token_cost?: number
  completion_scope?: number
  completion_percentage?: number
  parent_issue_id?: string
  sprint_id?: string
  ai_prompt?: string
  tags?: string[]
}

export interface Sprint {
  id: string
  name: string
  project_id: string
  start_date: string
  end_date: string
  status: string
  created_at: string
  issues?: Issue[]
  planned_story_points?: number
  completed_story_points?: number
  issue_count?: number
  completed_count?: number
  completed_points?: number
}

export interface Activity {
  id: string
  type: string
  description: string
  created_at: string
  metadata?: any
}

const App: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const [issues, setIssues] = useState<Issue[]>([])
  const [activeTab, setActiveTab] = useState<'review' | 'projects' | 'docs' | 'agents' | 'operations' | 'account'>('review')
  const [loading, setLoading] = useState(true)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [showNewProjectForm, setShowNewProjectForm] = useState(false)
  const [newProject, setNewProject] = useState({ name: '', description: '', color: '#8B5CF6' })
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)
  const [showIssueDetail, setShowIssueDetail] = useState(false)
  const [modeDialogFor, setModeDialogFor] = useState<Project | null>(null)
  const [welcomeKit, setWelcomeKit] = useState<{
    user: { name: string; email: string }
    project: { id: string; name: string; slug: string }
    api_key: { raw: string; name: string; prefix: string }
  } | null>(null)
  const [bootstrapChecked, setBootstrapChecked] = useState(false)

  useEffect(() => {
    // First-login onboarding. Bootstrap is idempotent; new users get the
    // welcome kit, returning users get a quick { is_new_user: false }.
    axios
      .post(`${API_URL}/auth/bootstrap`)
      .then((r) => {
        if (r.data?.is_new_user) setWelcomeKit(r.data)
      })
      .catch(() => {})
      .finally(() => setBootstrapChecked(true))

    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [projectsRes, issuesRes] = await Promise.all([
        axios.get(`${API_URL}/projects`),
        axios.get(`${API_URL}/issues`)
      ])
      setProjects(projectsRes.data.projects || [])
      setIssues(issuesRes.data || [])
      
      if (projectsRes.data.projects && projectsRes.data.projects.length > 0) {
        setSelectedProject(projectsRes.data.projects[0])
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const createProject = async () => {
    if (!newProject.name.trim()) return
    
    try {
      const response = await axios.post(`${API_URL}/projects`, {
        name: newProject.name,
        description: newProject.description,
        color: newProject.color,
        icon: 'folder'
      })
      
      setProjects([response.data, ...projects])
      setSelectedProject(response.data)
      setShowNewProjectForm(false)
      setNewProject({ name: '', description: '', color: '#8B5CF6' })
      // Prompt the user to pick project mode immediately after creation.
      setModeDialogFor(response.data)
    } catch (error) {
      console.error('Error creating project:', error)
    }
  }

  const deleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project? All associated issues will also be deleted.')) {
      return
    }
    
    try {
      await axios.delete(`${API_URL}/projects/${projectId}`)
      setProjects(projects.filter(p => p.id !== projectId))
      if (selectedProject?.id === projectId) {
        setSelectedProject(null)
      }
    } catch (error) {
      console.error('Error deleting project:', error)
      alert('Failed to delete project')
    }
  }

  const deleteIssue = async (issueId: string) => {
    if (!confirm('Are you sure you want to delete this issue?')) {
      return
    }
    
    try {
      await axios.delete(`${API_URL}/issues/${issueId}`)
      setIssues(issues.filter(i => i.id !== issueId))
    } catch (error) {
      console.error('Error deleting issue:', error)
      alert('Failed to delete issue')
    }
  }

  const filteredIssues = selectedProject 
    ? issues.filter(issue => issue.project_id === selectedProject.id)
    : issues

  if (loading || !bootstrapChecked) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500 mx-auto"></div>
          <h2 className="text-xl font-semibold text-white mt-4">Loading Lineary...</h2>
        </div>
      </div>
    )
  }

  // First-login welcome — the user hasn't onboarded yet. Show starter project,
  // API key, and Claude Desktop config, then let them "Open Lineary".
  if (welcomeKit) {
    return (
      <WelcomePage
        kit={welcomeKit}
        onDone={() => {
          setWelcomeKit(null)
          fetchData()
        }}
      />
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                Lineary
              </h1>
              <span className="text-sm text-gray-400">Project management, rebuilt for AI</span>
            </div>
            <div className="flex items-center space-x-4">
              {selectedProject && (
                <div className="flex items-center space-x-2 bg-gray-700 px-3 py-1 rounded-lg">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: selectedProject.color }}></div>
                  <span className="text-sm font-medium">{selectedProject.name}</span>
                </div>
              )}
              {selectedProject && selectedProject.mode === 'github' && (
                <GitHubSyncBadge projectId={selectedProject.id} />
              )}
              <span className="text-sm text-gray-400">
                {projects.length} Projects • {filteredIssues.length} Issues
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4">
          <nav className="flex space-x-8">
            {(['review', 'projects', 'docs', 'agents', 'operations', 'account'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors capitalize ${
                  activeTab === tab
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'review' && <ReviewPage />}

        {activeTab === 'agents' && <AgentsPage />}

        {activeTab === 'projects' && selectedProject && (
          <ProjectDashboard
            project={selectedProject}
            issues={filteredIssues}
            onOpenIssue={(issue) => {
              setSelectedIssue(issue)
              setShowIssueDetail(true)
            }}
            onBack={() => setSelectedProject(null)}
          />
        )}

        {activeTab === 'projects' && !selectedProject && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">Projects</h2>
              <button
                onClick={() => setShowNewProjectForm(true)}
                className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                + New Project
              </button>
            </div>
            
            {showNewProjectForm && (
              <div className="bg-gray-800 rounded-lg p-6 border border-purple-500 mb-6">
                <h3 className="text-lg font-semibold mb-4">Create New Project</h3>
                <div className="space-y-4">
                  <input
                    type="text"
                    value={newProject.name}
                    onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500"
                    placeholder="Project name"
                  />
                  <textarea
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500"
                    placeholder="Description"
                    rows={3}
                  />
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={() => setShowNewProjectForm(false)}
                      className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={createProject}
                      className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      Create Project
                    </button>
                  </div>
                </div>
              </div>
            )}
            
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {projects.map(project => (
                <div
                  key={project.id}
                  onClick={() => {
                    setSelectedProject(project)
                    setActiveTab('projects')
                  }}
                  className={`bg-gray-800 rounded-lg p-6 border transition-all hover:shadow-lg relative group border-gray-700 hover:border-purple-500`}
                >
                  {/* Delete button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteProject(project.id)
                    }}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-red-600/20 rounded-lg"
                    title="Delete project"
                  >
                    <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                  
                  {/* Settings button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedProject(project)
                      setActiveTab('projects')
                    }}
                    className="absolute top-2 right-10 opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-purple-600/20 rounded-lg"
                    title="Project settings"
                  >
                    <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </button>
                  
                  <div
                    onClick={() => {
                      setSelectedProject(project)
                      setActiveTab('projects')
                    }}
                    className="cursor-pointer"
                  >
                    <h3 className="font-semibold text-lg mb-2">{project.name}</h3>
                    <p className="text-gray-400 text-sm mb-4">{project.description || 'No description'}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>/{project.slug}</span>
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: project.color }}></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'docs' && (
          <DocsPage selectedProject={selectedProject} projects={projects} />
        )}

        {activeTab === 'operations' && <OperationsPage />}

        {activeTab === 'account' && (
          <AccountPage />
        )}
      </main>
      
      {/* New Feature: Bug Report Form (floating button) */}
      {selectedProject && (
        <BugReportForm projectId={selectedProject.id} />
      )}
      
      {/* Issue detail — Linear-style stream (replaces EnhancedIssueDetail as the default). */}
      {selectedIssue && (
        <IssueStream
          issue={selectedIssue}
          isOpen={showIssueDetail}
          onClose={() => {
            setShowIssueDetail(false)
            setSelectedIssue(null)
          }}
          onUpdate={() => {
            fetchData()
          }}
          projects={projects}
        />
      )}

      {modeDialogFor && (
        <ProjectModeDialog
          projectId={modeDialogFor.id}
          projectName={modeDialogFor.name}
          onClose={() => setModeDialogFor(null)}
          onSelected={(mode) => {
            // Reflect chosen mode in local state without a full refetch.
            setProjects((prev) =>
              prev.map((p) => (p.id === modeDialogFor.id ? { ...p, mode } : p))
            )
            setSelectedProject((prev) =>
              prev && prev.id === modeDialogFor.id ? { ...prev, mode } : prev
            )
          }}
        />
      )}
    </div>
  )
}

export default App