// ABOUTME: Project documentation page with rich text editor
// ABOUTME: Manages project documentation with sections for overview, architecture, requirements, and API

import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import toast from 'react-hot-toast'
import { Project, API_URL } from '../App'
import RichTextEditor from '../components/RichTextEditor'

interface Props {
  projects: Project[]
}

interface Documentation {
  id: string
  project_id: string
  section: 'overview' | 'architecture' | 'requirements' | 'api'
  title: string
  content: string
  updated_at: string
}

const ProjectDocumentationPage: React.FC<Props> = ({ projects }) => {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)
  const [documentation, setDocumentation] = useState<Documentation[]>([])
  const [activeSection, setActiveSection] = useState<'overview' | 'architecture' | 'requirements' | 'api'>('overview')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [content, setContent] = useState('')

  const sections = [
    { key: 'overview', label: 'Overview', icon: '📋', description: 'Project overview and goals' },
    { key: 'architecture', label: 'Architecture', icon: '🏗️', description: 'System architecture and design' },
    { key: 'requirements', label: 'Requirements', icon: '📝', description: 'Functional and technical requirements' },
    { key: 'api', label: 'API', icon: '🔌', description: 'API documentation and endpoints' }
  ]

  useEffect(() => {
    if (projectId) {
      const foundProject = projects.find(p => p.id === projectId)
      if (foundProject) {
        setProject(foundProject)
        fetchDocumentation()
      } else {
        toast.error('Project not found')
        navigate('/')
      }
    }
  }, [projectId, projects])

  useEffect(() => {
    // Load content for active section
    const sectionDoc = documentation.find(doc => doc.section === activeSection)
    setContent(sectionDoc?.content || '')
  }, [activeSection, documentation])

  const fetchDocumentation = async () => {
    if (!projectId) return
    
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/projects/${projectId}/documentation`)
      setDocumentation(response.data || [])
    } catch (error) {
      console.error('Error fetching documentation:', error)
      toast.error('Failed to load documentation')
    } finally {
      setLoading(false)
    }
  }

  const saveDocumentation = async () => {
    if (!projectId || !content.trim()) {
      toast.error('Content cannot be empty')
      return
    }

    setSaving(true)
    try {
      const existingDoc = documentation.find(doc => doc.section === activeSection)
      const section = sections.find(s => s.key === activeSection)
      
      const payload = {
        section: activeSection,
        title: section?.label || activeSection,
        content: content
      }

      if (existingDoc) {
        await axios.patch(`${API_URL}/projects/${projectId}/documentation/${existingDoc.id}`, payload)
      } else {
        await axios.post(`${API_URL}/projects/${projectId}/documentation`, payload)
      }
      
      toast.success('Documentation saved successfully!')
      fetchDocumentation()
    } catch (error) {
      console.error('Error saving documentation:', error)
      toast.error('Failed to save documentation')
    } finally {
      setSaving(false)
    }
  }

  const getLastUpdated = (section: string) => {
    const doc = documentation.find(d => d.section === section)
    return doc ? new Date(doc.updated_at).toLocaleDateString() : 'Never'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500/30 rounded-full animate-spin border-t-purple-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading documentation...</p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">❓</div>
        <h2 className="text-xl font-semibold text-white mb-2">Project Not Found</h2>
        <p className="text-gray-400">The requested project could not be found.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/')}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ← Back to Projects
          </button>
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center space-x-3">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: project.color + '40' }}
              >
                📚
              </div>
              <span>{project.name} Documentation</span>
            </h1>
            <p className="text-gray-400 mt-1">{project.description}</p>
          </div>
        </div>
        
        <button
          onClick={saveDocumentation}
          disabled={saving}
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 px-6 py-3 rounded-lg text-white font-medium transition-all duration-200 shadow-lg hover:shadow-purple-500/25"
        >
          {saving ? 'Saving...' : 'Save Documentation'}
        </button>
      </div>

      {/* Section Navigation */}
      <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl border border-gray-700/50 overflow-hidden">
        <div className="flex border-b border-gray-700/50">
          {sections.map(section => (
            <button
              key={section.key}
              onClick={() => setActiveSection(section.key as any)}
              className={`flex-1 px-6 py-4 text-left transition-all duration-200 ${
                activeSection === section.key
                  ? 'bg-purple-600/20 text-purple-400 border-b-2 border-purple-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/30'
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-xl">{section.icon}</span>
                <div>
                  <div className="font-medium">{section.label}</div>
                  <div className="text-xs text-gray-500">
                    Updated: {getLastUpdated(section.key)}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
        
        {/* Section Description */}
        <div className="px-6 py-3 bg-gray-700/30">
          <p className="text-sm text-gray-400">
            {sections.find(s => s.key === activeSection)?.description}
          </p>
        </div>
      </div>

      {/* Content Editor */}
      <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl border border-gray-700/50 overflow-hidden">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">
              {sections.find(s => s.key === activeSection)?.label} Documentation
            </h2>
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <span>Auto-save: Off</span>
              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
            </div>
          </div>
          
          {/* Rich Text Editor */}
          <div className="min-h-[500px]">
            <RichTextEditor
              content={content}
              onChange={setContent}
              placeholder={`Start writing the ${activeSection} documentation...`}
            />
          </div>
        </div>
      </div>

      {/* Documentation Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-2xl mb-2">📄</div>
          <p className="text-lg font-bold text-white">{documentation.length}</p>
          <p className="text-gray-400 text-sm">Sections</p>
        </div>
        
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-2xl mb-2">📝</div>
          <p className="text-lg font-bold text-white">
            {documentation.reduce((sum, doc) => sum + doc.content.length, 0)}
          </p>
          <p className="text-gray-400 text-sm">Characters</p>
        </div>
        
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-2xl mb-2">🕒</div>
          <p className="text-lg font-bold text-white">
            {documentation.length > 0 ? 
              new Date(Math.max(...documentation.map(d => new Date(d.updated_at).getTime()))).toLocaleDateString()
              : 'Never'
            }
          </p>
          <p className="text-gray-400 text-sm">Last Updated</p>
        </div>
        
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-2xl mb-2">✅</div>
          <p className="text-lg font-bold text-white">
            {Math.round((documentation.length / sections.length) * 100)}%
          </p>
          <p className="text-gray-400 text-sm">Complete</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button className="flex items-center space-x-3 p-4 bg-gray-700/50 rounded-lg hover:bg-gray-600/50 transition-colors">
            <span className="text-xl">📤</span>
            <div className="text-left">
              <div className="font-medium text-white">Export PDF</div>
              <div className="text-xs text-gray-400">Download documentation</div>
            </div>
          </button>
          
          <button className="flex items-center space-x-3 p-4 bg-gray-700/50 rounded-lg hover:bg-gray-600/50 transition-colors">
            <span className="text-xl">🔗</span>
            <div className="text-left">
              <div className="font-medium text-white">Share Link</div>
              <div className="text-xs text-gray-400">Get shareable URL</div>
            </div>
          </button>
          
          <button className="flex items-center space-x-3 p-4 bg-gray-700/50 rounded-lg hover:bg-gray-600/50 transition-colors">
            <span className="text-xl">📋</span>
            <div className="text-left">
              <div className="font-medium text-white">Copy Template</div>
              <div className="text-xs text-gray-400">Use as template</div>
            </div>
          </button>
          
          <button className="flex items-center space-x-3 p-4 bg-gray-700/50 rounded-lg hover:bg-gray-600/50 transition-colors">
            <span className="text-xl">🤖</span>
            <div className="text-left">
              <div className="font-medium text-white">AI Assist</div>
              <div className="text-xs text-gray-400">Generate content</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  )
}

export default ProjectDocumentationPage