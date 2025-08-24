// ABOUTME: Main App component with comprehensive Lineary frontend
// ABOUTME: Includes navigation, issue management, sprint planning, and analytics

import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import axios from 'axios'
import toast, { Toaster } from 'react-hot-toast'

// Pages
import ProjectsPage from './pages/ProjectsPage'
import IssuesPage from './pages/IssuesPage'
import SprintsPage from './pages/SprintsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import ProjectDocumentationPage from './pages/ProjectDocumentationPage'

const API_URL = 'https://ai-linear.blockonauts.io/api'

// Types
export interface Project {
  id: string
  name: string
  description: string
  slug: string
  color: string
  icon: string
  created_at: string
}

export interface Issue {
  id: string
  project_id: string
  title: string
  description: string
  status: 'backlog' | 'todo' | 'in_progress' | 'in_review' | 'done' | 'cancelled'
  priority: number
  story_points: number
  estimated_hours: number
  token_cost?: number
  completion_percentage?: number
  start_date?: string
  end_date?: string
  dependencies?: string[]
  parent_id?: string
  subtasks?: Issue[]
  ai_prompt?: string
  created_at: string
  updated_at?: string
}

export interface Sprint {
  id: string
  name: string
  project_id: string
  start_date: string
  end_date: string
  status: 'planning' | 'active' | 'completed'
  issues: Issue[]
  velocity?: number
  created_at: string
}

export interface Activity {
  id: string
  issue_id: string
  type: 'created' | 'updated' | 'status_changed' | 'comment'
  description: string
  metadata?: any
  created_at: string
}

// Main App Component
const AppContent: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)

  // Navigation Component (moved inside AppContent to access Router context)
  const Navigation: React.FC = () => {
    const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Projects', icon: '📁' },
    { path: '/issues', label: 'Issues', icon: '📋' },
    { path: '/sprints', label: 'Sprints', icon: '🏃' },
    { path: '/analytics', label: 'Analytics', icon: '📊' },
  ]

  return (
    <nav className="bg-gray-800/80 backdrop-blur-xl border-b border-gray-700/50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AL</span>
              </div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                Lineary
              </h1>
            </Link>
          </div>

          {/* Navigation Items */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  location.pathname === item.path
                    ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                }`}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>

          {/* Project Selector */}
          <div className="flex items-center space-x-4">
            {projects.length > 0 && (
              <select
                value={selectedProject?.id || ''}
                onChange={(e) => {
                  const project = projects.find(p => p.id === e.target.value)
                  setSelectedProject(project || null)
                }}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-1 text-sm focus:outline-none focus:border-purple-500"
              >
                <option value="">All Projects</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            )}
            
            {selectedProject && (
              <div className="flex items-center space-x-2 bg-gray-700/50 px-3 py-1 rounded-lg border border-gray-600">
                <div 
                  className="w-2 h-2 rounded-full" 
                  style={{ backgroundColor: selectedProject.color }}
                />
                <span className="text-sm font-medium text-white">{selectedProject.name}</span>
                <Link
                  to={`/projects/${selectedProject.id}/docs`}
                  className="text-gray-400 hover:text-purple-400 transition-colors"
                  title="Documentation"
                >
                  📚
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API_URL}/projects`)
      const projectsData = response.data.projects || []
      setProjects(projectsData)
      
      // Auto-select first project if available and none selected
      if (projectsData.length > 0 && !selectedProject) {
        setSelectedProject(projectsData[0])
      }
    } catch (error) {
      console.error('Error fetching projects:', error)
      toast.error('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-purple-500/30 rounded-full animate-spin border-t-purple-500 mx-auto"></div>
            <div className="w-12 h-12 border-4 border-blue-500/30 rounded-full animate-spin border-t-blue-500 absolute top-2 left-2 animate-pulse"></div>
          </div>
          <h2 className="text-xl font-semibold text-white mt-6">Loading Lineary...</h2>
          <p className="text-gray-400 mt-2">Initializing self-driving development platform</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-purple-900/20">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route 
            path="/" 
            element={
              <ProjectsPage 
                projects={projects} 
                setProjects={setProjects}
                selectedProject={selectedProject}
                setSelectedProject={setSelectedProject}
              />
            } 
          />
          <Route 
            path="/issues" 
            element={
              <IssuesPage 
                selectedProject={selectedProject}
                projects={projects}
              />
            } 
          />
          <Route 
            path="/sprints" 
            element={
              <SprintsPage 
                selectedProject={selectedProject}
                projects={projects}
              />
            } 
          />
          <Route 
            path="/analytics" 
            element={
              <AnalyticsPage 
                selectedProject={selectedProject}
                projects={projects}
              />
            } 
          />
          <Route 
            path="/projects/:projectId/docs" 
            element={
              <ProjectDocumentationPage 
                projects={projects}
              />
            } 
          />
        </Routes>
      </main>

      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#1f2937',
            color: '#fff',
            border: '1px solid #374151'
          }
        }}
      />
    </div>
  )
}

const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
export { API_URL }