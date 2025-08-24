// ABOUTME: Projects overview page with project management features
// ABOUTME: Handles project creation, editing, and selection

import React, { useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { Project, API_URL } from '../App'

interface Props {
  projects: Project[]
  setProjects: (projects: Project[]) => void
  selectedProject: Project | null
  setSelectedProject: (project: Project | null) => void
}

const ProjectsPage: React.FC<Props> = ({ 
  projects, 
  setProjects, 
  selectedProject, 
  setSelectedProject 
}) => {
  const [showNewProjectForm, setShowNewProjectForm] = useState(false)
  const [newProject, setNewProject] = useState({ 
    name: '', 
    description: '', 
    color: '#8B5CF6' 
  })
  const [submitting, setSubmitting] = useState(false)

  const createProject = async () => {
    if (!newProject.name.trim()) {
      toast.error('Project name is required')
      return
    }
    
    setSubmitting(true)
    try {
      const response = await axios.post(`${API_URL}/projects`, {
        name: newProject.name,
        description: newProject.description,
        color: newProject.color,
        icon: 'folder'
      })
      
      const createdProject = response.data
      setProjects([createdProject, ...projects])
      setSelectedProject(createdProject)
      setShowNewProjectForm(false)
      setNewProject({ name: '', description: '', color: '#8B5CF6' })
      toast.success('Project created successfully!')
    } catch (error) {
      console.error('Error creating project:', error)
      toast.error('Failed to create project')
    } finally {
      setSubmitting(false)
    }
  }

  const colors = [
    '#8B5CF6', '#EF4444', '#10B981', '#F59E0B', 
    '#3B82F6', '#EC4899', '#06B6D4', '#84CC16'
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Projects</h1>
          <p className="text-gray-400 mt-1">
            Manage your development projects with AI-powered insights
          </p>
        </div>
        <button 
          onClick={() => setShowNewProjectForm(true)}
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-3 rounded-lg text-white font-medium transition-all duration-200 shadow-lg hover:shadow-purple-500/25"
        >
          + New Project
        </button>
      </div>

      {/* New Project Form */}
      {showNewProjectForm && (
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-purple-500/30 shadow-2xl">
          <h3 className="text-xl font-semibold mb-6 text-white">Create New Project</h3>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Project Name *
              </label>
              <input
                type="text"
                value={newProject.name}
                onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 text-white placeholder-gray-400"
                placeholder="Enter project name"
                autoFocus
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={newProject.description}
                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 text-white placeholder-gray-400"
                placeholder="Describe your project"
                rows={3}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Project Color
              </label>
              <div className="flex items-center space-x-3">
                {colors.map(color => (
                  <button
                    key={color}
                    onClick={() => setNewProject({ ...newProject, color })}
                    className={`w-8 h-8 rounded-lg transition-all duration-200 ${
                      newProject.color === color 
                        ? 'ring-2 ring-white ring-offset-2 ring-offset-gray-800' 
                        : 'hover:scale-110'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
                <input
                  type="color"
                  value={newProject.color}
                  onChange={(e) => setNewProject({ ...newProject, color: e.target.value })}
                  className="w-8 h-8 rounded-lg border-2 border-gray-600 cursor-pointer"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 pt-4">
              <button
                onClick={() => setShowNewProjectForm(false)}
                className="px-6 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={createProject}
                disabled={submitting || !newProject.name.trim()}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 px-6 py-2 rounded-lg text-white font-medium transition-all duration-200"
              >
                {submitting ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Projects Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {projects.map(project => (
          <div
            key={project.id}
            onClick={() => setSelectedProject(project)}
            className={`group bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border cursor-pointer transition-all duration-300 hover:shadow-2xl hover:scale-105 ${
              selectedProject?.id === project.id 
                ? 'border-purple-500 shadow-purple-500/20 bg-purple-900/20' 
                : 'border-gray-700/50 hover:border-purple-500/50'
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shadow-lg"
                  style={{ 
                    backgroundColor: project.color + '20',
                    border: `2px solid ${project.color}40`
                  }}
                >
                  {project.icon === 'rocket' ? '🚀' : '📁'}
                </div>
                <div>
                  <h3 className="font-semibold text-lg text-white group-hover:text-purple-300 transition-colors">
                    {project.name}
                  </h3>
                  <p className="text-xs text-gray-400">/{project.slug}</p>
                </div>
              </div>
              
              {selectedProject?.id === project.id && (
                <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse"></div>
              )}
            </div>
            
            <p className="text-gray-400 text-sm mb-6 leading-relaxed">
              {project.description || 'No description'}
            </p>
            
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span className="flex items-center space-x-1">
                <span>📅</span>
                <span>{new Date(project.created_at).toLocaleDateString()}</span>
              </span>
              <div 
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: project.color }}
              />
            </div>
          </div>
        ))}
        
        {projects.length === 0 && !showNewProjectForm && (
          <div className="col-span-full bg-gray-800/30 rounded-xl p-12 text-center border border-dashed border-gray-600">
            <div className="text-6xl mb-4">🚀</div>
            <h3 className="text-xl font-semibold text-white mb-2">No projects yet</h3>
            <p className="text-gray-400 mb-6">
              Create your first project to start building with AI-powered development tools
            </p>
            <button
              onClick={() => setShowNewProjectForm(true)}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-3 rounded-lg text-white font-medium transition-all duration-200"
            >
              Create Your First Project
            </button>
          </div>
        )}
      </div>

      {/* Stats */}
      {projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                📊
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{projects.length}</p>
                <p className="text-gray-400 text-sm">Total Projects</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                ✅
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {projects.filter(p => p.created_at).length}
                </p>
                <p className="text-gray-400 text-sm">Active Projects</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                🤖
              </div>
              <div>
                <p className="text-2xl font-bold text-white">AI-Powered</p>
                <p className="text-gray-400 text-sm">Development</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectsPage