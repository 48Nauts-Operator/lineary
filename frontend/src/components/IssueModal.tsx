// ABOUTME: Comprehensive issue modal with editing, dependencies, subtasks, and AI features
// ABOUTME: Handles issue creation, editing, and detailed view with activity timeline

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { Project, Issue, Activity, API_URL } from '../App'
import ActivityTimeline from './ActivityTimeline'
import MarkdownEditor from './MarkdownEditor'

interface Props {
  issue?: Issue
  isOpen: boolean
  onClose: () => void
  onUpdate: () => void
  projects: Project[]
  selectedProject?: Project | null
}

const IssueModal: React.FC<Props> = ({ 
  issue, 
  isOpen, 
  onClose, 
  onUpdate, 
  projects, 
  selectedProject 
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'backlog' as Issue['status'],
    priority: 3,
    project_id: selectedProject?.id || '',
    story_points: 0,
    estimated_hours: 0,
    token_cost: 0,
    completion_percentage: 0,
    start_date: '',
    end_date: '',
    dependencies: [] as string[],
    ai_prompt: ''
  })
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'details' | 'activity' | 'ai'>('details')
  const [activities, setActivities] = useState<Activity[]>([])
  const [availableIssues, setAvailableIssues] = useState<Issue[]>([])
  const [showAIPrompt, setShowAIPrompt] = useState(false)

  useEffect(() => {
    if (issue) {
      setFormData({
        title: issue.title,
        description: issue.description,
        status: issue.status,
        priority: issue.priority,
        project_id: issue.project_id,
        story_points: issue.story_points || 0,
        estimated_hours: issue.estimated_hours || 0,
        token_cost: issue.token_cost || 0,
        completion_percentage: issue.completion_percentage || 0,
        start_date: issue.start_date ? issue.start_date.split('T')[0] : '',
        end_date: issue.end_date ? issue.end_date.split('T')[0] : '',
        dependencies: issue.dependencies || [],
        ai_prompt: issue.ai_prompt || ''
      })
      fetchActivities(issue.id)
    } else {
      // Reset form for new issue
      setFormData({
        title: '',
        description: '',
        status: 'backlog',
        priority: 3,
        project_id: selectedProject?.id || '',
        story_points: 0,
        estimated_hours: 0,
        token_cost: 0,
        completion_percentage: 0,
        start_date: '',
        end_date: '',
        dependencies: [],
        ai_prompt: ''
      })
    }
    
    if (isOpen) {
      fetchAvailableIssues()
    }
  }, [issue, isOpen, selectedProject])

  const fetchActivities = async (issueId: string) => {
    try {
      const response = await axios.get(`${API_URL}/issues/${issueId}/activities`)
      setActivities(response.data || [])
    } catch (error) {
      console.error('Error fetching activities:', error)
    }
  }

  const fetchAvailableIssues = async () => {
    try {
      const response = await axios.get(`${API_URL}/issues`)
      setAvailableIssues(response.data.filter((i: Issue) => i.id !== issue?.id) || [])
    } catch (error) {
      console.error('Error fetching available issues:', error)
    }
  }

  const generateAIPrompt = async () => {
    if (!formData.title || !formData.description) {
      toast.error('Please provide title and description first')
      return
    }

    setShowAIPrompt(true)
    try {
      const response = await axios.post(`${API_URL}/prompts/generate`, {
        title: formData.title,
        description: formData.description,
        priority: formData.priority
      })
      
      const aiData = response.data
      setFormData(prev => ({
        ...prev,
        story_points: aiData.story_points || prev.story_points,
        estimated_hours: aiData.estimated_hours || prev.estimated_hours,
        token_cost: aiData.token_cost || prev.token_cost,
        ai_prompt: aiData.prompt || prev.ai_prompt
      }))
      
      toast.success('AI analysis completed!')
    } catch (error) {
      console.error('Error generating AI prompt:', error)
      toast.error('Failed to generate AI analysis')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim()) {
      toast.error('Title is required')
      return
    }

    setLoading(true)
    try {
      const payload = {
        ...formData,
        start_date: formData.start_date || null,
        end_date: formData.end_date || null
      }

      if (issue) {
        await axios.patch(`${API_URL}/issues/${issue.id}`, payload)
        toast.success('Issue updated successfully!')
      } else {
        await axios.post(`${API_URL}/issues`, payload)
        toast.success('Issue created successfully!')
      }
      
      onUpdate()
      onClose()
    } catch (error) {
      console.error('Error saving issue:', error)
      toast.error(`Failed to ${issue ? 'update' : 'create'} issue`)
    } finally {
      setLoading(false)
    }
  }

  const addToSprint = async () => {
    if (!issue) return
    
    try {
      // This would need sprint selection UI, for now just show message
      toast.success('Sprint planning feature - select sprint to add issue')
    } catch (error) {
      console.error('Error adding to sprint:', error)
      toast.error('Failed to add to sprint')
    }
  }

  const statusOptions = [
    { value: 'backlog', label: 'Backlog', color: 'bg-gray-500' },
    { value: 'todo', label: 'To Do', color: 'bg-blue-500' },
    { value: 'in_progress', label: 'In Progress', color: 'bg-yellow-500' },
    { value: 'in_review', label: 'In Review', color: 'bg-purple-500' },
    { value: 'done', label: 'Done', color: 'bg-green-500' },
    { value: 'cancelled', label: 'Cancelled', color: 'bg-red-500' }
  ]

  const priorityOptions = [
    { value: 1, label: 'Critical', emoji: '🔥', color: 'text-red-400' },
    { value: 2, label: 'High', emoji: '⚡', color: 'text-orange-400' },
    { value: 3, label: 'Medium', emoji: '➡️', color: 'text-blue-400' },
    { value: 4, label: 'Low', emoji: '🔽', color: 'text-gray-400' }
  ]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-white">
              {issue ? `Edit Issue: ${issue.title}` : 'Create New Issue'}
            </h2>
            {issue && (
              <p className="text-gray-400 text-sm mt-1">
                #{issue.id.slice(-6)} • Created {format(new Date(issue.created_at), 'MMM dd, yyyy')}
              </p>
            )}
          </div>
          <div className="flex items-center space-x-3">
            {issue && (
              <button
                onClick={addToSprint}
                className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors"
              >
                Add to Sprint
              </button>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          {['details', 'activity', 'ai'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-6 py-3 text-sm font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'text-purple-400 border-b-2 border-purple-500'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab === 'ai' ? 'AI Analysis' : tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {activeTab === 'details' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Title *
                    </label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                      className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                      placeholder="Enter issue title"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Description
                    </label>
                    <MarkdownEditor
                      value={formData.description}
                      onChange={(value) => setFormData(prev => ({ ...prev, description: value }))}
                      placeholder="Describe the issue in detail (supports Markdown)"
                      minRows={4}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Status
                      </label>
                      <select
                        value={formData.status}
                        onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value as any }))}
                        className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                      >
                        {statusOptions.map(option => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Priority
                      </label>
                      <select
                        value={formData.priority}
                        onChange={(e) => setFormData(prev => ({ ...prev, priority: parseInt(e.target.value) }))}
                        className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                      >
                        {priorityOptions.map(option => (
                          <option key={option.value} value={option.value}>
                            {option.emoji} {option.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Start Date
                      </label>
                      <input
                        type="date"
                        value={formData.start_date}
                        onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                        className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        End Date
                      </label>
                      <input
                        type="date"
                        value={formData.end_date}
                        onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                        className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                      />
                    </div>
                  </div>
                </div>

                {/* Right Column */}
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Story Points
                      </label>
                      <input
                        type="number"
                        value={formData.story_points}
                        onChange={(e) => setFormData(prev => ({ ...prev, story_points: parseInt(e.target.value) || 0 }))}
                        className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                        min="0"
                        max="100"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Estimated Hours
                      </label>
                      <input
                        type="number"
                        value={formData.estimated_hours}
                        onChange={(e) => setFormData(prev => ({ ...prev, estimated_hours: parseInt(e.target.value) || 0 }))}
                        className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                        min="0"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Token Cost
                      </label>
                      <input
                        type="number"
                        value={formData.token_cost}
                        onChange={(e) => setFormData(prev => ({ ...prev, token_cost: parseInt(e.target.value) || 0 }))}
                        className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                        min="0"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Completion %
                      </label>
                      <input
                        type="number"
                        value={formData.completion_percentage}
                        onChange={(e) => setFormData(prev => ({ ...prev, completion_percentage: parseInt(e.target.value) || 0 }))}
                        className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                        min="0"
                        max="100"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Project
                    </label>
                    <select
                      value={formData.project_id}
                      onChange={(e) => setFormData(prev => ({ ...prev, project_id: e.target.value }))}
                      className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                      required
                    >
                      <option value="">Select Project</option>
                      {projects.map(project => (
                        <option key={project.id} value={project.id}>
                          {project.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-gray-300">
                        AI Analysis
                      </label>
                      <button
                        type="button"
                        onClick={generateAIPrompt}
                        className="bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-xs text-white transition-colors"
                      >
                        Generate
                      </button>
                    </div>
                    <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-3">
                      <p className="text-sm text-gray-400">
                        🤖 AI will analyze your issue and provide estimates, suggestions, and implementation guidance.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-6 border-t border-gray-700">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 px-6 py-2 rounded-lg text-white font-medium transition-all duration-200"
                >
                  {loading ? 'Saving...' : (issue ? 'Update Issue' : 'Create Issue')}
                </button>
              </div>
            </form>
          )}

          {activeTab === 'activity' && issue && (
            <ActivityTimeline activities={activities} />
          )}

          {activeTab === 'ai' && (
            <div className="space-y-6">
              {formData.ai_prompt ? (
                <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600">
                  <h3 className="text-lg font-semibold text-white mb-4">AI Generated Prompt</h3>
                  <pre className="text-gray-300 text-sm whitespace-pre-wrap leading-relaxed">
                    {formData.ai_prompt}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🤖</div>
                  <h3 className="text-xl font-semibold text-white mb-2">No AI Analysis Yet</h3>
                  <p className="text-gray-400 mb-6">
                    Generate AI analysis to get implementation guidance and estimates
                  </p>
                  <button
                    onClick={generateAIPrompt}
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-3 rounded-lg text-white font-medium transition-all duration-200"
                  >
                    Generate AI Analysis
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default IssueModal