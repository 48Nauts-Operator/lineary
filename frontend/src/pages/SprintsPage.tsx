// ABOUTME: Sprint planning and management page with burndown charts
// ABOUTME: Handles sprint creation, issue assignment, and sprint analytics

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { format, differenceInDays } from 'date-fns'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { Project, Issue, Sprint, API_URL } from '../App'

interface Props {
  selectedProject: Project | null
  projects: Project[]
}

const SprintsPage: React.FC<Props> = ({ selectedProject, projects }) => {
  const [sprints, setSprints] = useState<Sprint[]>([])
  const [issues, setIssues] = useState<Issue[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewSprintForm, setShowNewSprintForm] = useState(false)
  const [selectedSprint, setSelectedSprint] = useState<Sprint | null>(null)
  const [showSprintPlanning, setShowSprintPlanning] = useState(false)
  const [burndownData, setBurndownData] = useState<any[]>([])
  const [newSprint, setNewSprint] = useState({
    name: '',
    start_date: '',
    end_date: '',
    project_id: selectedProject?.id || ''
  })

  useEffect(() => {
    fetchSprints()
    fetchAvailableIssues()
  }, [selectedProject])

  useEffect(() => {
    if (selectedSprint) {
      fetchBurndownData(selectedSprint.id)
    }
  }, [selectedSprint])

  const fetchSprints = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/sprints`)
      let sprintsData = response.data || []
      
      if (selectedProject) {
        sprintsData = sprintsData.filter((sprint: Sprint) => sprint.project_id === selectedProject.id)
      }
      
      setSprints(sprintsData)
      if (sprintsData.length > 0 && !selectedSprint) {
        setSelectedSprint(sprintsData[0])
      }
    } catch (error) {
      console.error('Error fetching sprints:', error)
      toast.error('Failed to load sprints')
    } finally {
      setLoading(false)
    }
  }

  const fetchAvailableIssues = async () => {
    try {
      const response = await axios.get(`${API_URL}/sprints/planning/issues`)
      setIssues(response.data || [])
    } catch (error) {
      console.error('Error fetching available issues:', error)
    }
  }

  const fetchBurndownData = async (sprintId: string) => {
    try {
      const response = await axios.get(`${API_URL}/sprints/${sprintId}/burndown`)
      setBurndownData(response.data || [])
    } catch (error) {
      console.error('Error fetching burndown data:', error)
    }
  }

  const createSprint = async () => {
    if (!newSprint.name.trim() || !newSprint.start_date || !newSprint.end_date) {
      toast.error('Please fill in all required fields')
      return
    }

    try {
      const response = await axios.post(`${API_URL}/sprints`, {
        ...newSprint,
        project_id: selectedProject?.id || newSprint.project_id
      })
      
      const createdSprint = response.data
      setSprints([createdSprint, ...sprints])
      setSelectedSprint(createdSprint)
      setShowNewSprintForm(false)
      setNewSprint({
        name: '',
        start_date: '',
        end_date: '',
        project_id: selectedProject?.id || ''
      })
      toast.success('Sprint created successfully!')
    } catch (error) {
      console.error('Error creating sprint:', error)
      toast.error('Failed to create sprint')
    }
  }

  const addIssuesToSprint = async (sprintId: string, issueIds: string[]) => {
    try {
      await axios.post(`${API_URL}/sprints/${sprintId}/issues`, { issueIds })
      toast.success(`Added ${issueIds.length} issues to sprint`)
      fetchSprints()
      setShowSprintPlanning(false)
    } catch (error) {
      console.error('Error adding issues to sprint:', error)
      toast.error('Failed to add issues to sprint')
    }
  }

  const getSprintStatus = (sprint: Sprint) => {
    const now = new Date()
    const startDate = new Date(sprint.start_date)
    const endDate = new Date(sprint.end_date)

    if (now < startDate) return { label: 'Not Started', color: 'bg-gray-500' }
    if (now > endDate) return { label: 'Completed', color: 'bg-green-500' }
    return { label: 'Active', color: 'bg-blue-500' }
  }

  const getSprintProgress = (sprint: Sprint) => {
    const completedIssues = sprint.issues?.filter(issue => issue.status === 'done').length || 0
    const totalIssues = sprint.issues?.length || 0
    return totalIssues > 0 ? Math.round((completedIssues / totalIssues) * 100) : 0
  }

  const getSprintVelocity = (sprint: Sprint) => {
    const completedPoints = sprint.issues
      ?.filter(issue => issue.status === 'done')
      .reduce((sum, issue) => sum + (issue.story_points || 0), 0) || 0
    return completedPoints
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500/30 rounded-full animate-spin border-t-purple-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading sprints...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Sprint Planning</h1>
          <p className="text-gray-400 mt-1">
            {selectedProject ? `${selectedProject.name} Sprints` : 'All Sprints'}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button 
            onClick={() => setShowSprintPlanning(true)}
            disabled={!selectedSprint}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded-lg text-white font-medium transition-colors"
          >
            Plan Sprint
          </button>
          <button 
            onClick={() => setShowNewSprintForm(true)}
            disabled={!selectedProject}
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 px-6 py-3 rounded-lg text-white font-medium transition-all duration-200 shadow-lg hover:shadow-purple-500/25"
          >
            + New Sprint
          </button>
        </div>
      </div>

      {/* New Sprint Form */}
      {showNewSprintForm && (
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-purple-500/30 shadow-2xl">
          <h3 className="text-xl font-semibold mb-6 text-white">Create New Sprint</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Sprint Name *
              </label>
              <input
                type="text"
                value={newSprint.name}
                onChange={(e) => setNewSprint({ ...newSprint, name: e.target.value })}
                className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                placeholder="Sprint 1, Feature Sprint, etc."
                autoFocus
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Project
              </label>
              <select
                value={newSprint.project_id}
                onChange={(e) => setNewSprint({ ...newSprint, project_id: e.target.value })}
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
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Start Date *
              </label>
              <input
                type="date"
                value={newSprint.start_date}
                onChange={(e) => setNewSprint({ ...newSprint, start_date: e.target.value })}
                className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                End Date *
              </label>
              <input
                type="date"
                value={newSprint.end_date}
                onChange={(e) => setNewSprint({ ...newSprint, end_date: e.target.value })}
                className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white"
              />
            </div>
          </div>
          
          <div className="flex justify-end space-x-3 pt-6">
            <button
              onClick={() => setShowNewSprintForm(false)}
              className="px-6 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={createSprint}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-2 rounded-lg text-white font-medium transition-all duration-200"
            >
              Create Sprint
            </button>
          </div>
        </div>
      )}

      {/* Sprint Planning Modal */}
      {showSprintPlanning && selectedSprint && (
        <SprintPlanningModal
          sprint={selectedSprint}
          availableIssues={issues}
          onClose={() => setShowSprintPlanning(false)}
          onAddIssues={addIssuesToSprint}
        />
      )}

      {/* Sprints Overview */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {sprints.map(sprint => {
          const status = getSprintStatus(sprint)
          const progress = getSprintProgress(sprint)
          const velocity = getSprintVelocity(sprint)
          const duration = differenceInDays(new Date(sprint.end_date), new Date(sprint.start_date))
          
          return (
            <div
              key={sprint.id}
              onClick={() => setSelectedSprint(sprint)}
              className={`bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border cursor-pointer transition-all duration-300 hover:shadow-lg ${
                selectedSprint?.id === sprint.id 
                  ? 'border-purple-500 shadow-purple-500/20' 
                  : 'border-gray-700/50 hover:border-purple-500/50'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-lg text-white">{sprint.name}</h3>
                  <p className="text-xs text-gray-400">
                    {format(new Date(sprint.start_date), 'MMM dd')} - {format(new Date(sprint.end_date), 'MMM dd')}
                  </p>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color} bg-opacity-20 text-white`}>
                  {status.label}
                </span>
              </div>
              
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-sm font-medium text-white">{sprint.issues?.length || 0}</p>
                    <p className="text-xs text-gray-400">Issues</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{velocity}</p>
                    <p className="text-xs text-gray-400">Points</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{duration}</p>
                    <p className="text-xs text-gray-400">Days</p>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
        
        {sprints.length === 0 && !showNewSprintForm && (
          <div className="col-span-full bg-gray-800/30 rounded-xl p-12 text-center border border-dashed border-gray-600">
            <div className="text-6xl mb-4">🏃</div>
            <h3 className="text-xl font-semibold text-white mb-2">No sprints yet</h3>
            <p className="text-gray-400 mb-6">
              Create your first sprint to start organizing your development work
            </p>
            <button
              onClick={() => setShowNewSprintForm(true)}
              disabled={!selectedProject}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 px-6 py-3 rounded-lg text-white font-medium transition-all duration-200"
            >
              Create Your First Sprint
            </button>
          </div>
        )}
      </div>

      {/* Sprint Details */}
      {selectedSprint && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Burndown Chart */}
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Burndown Chart</h3>
            {burndownData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={burndownData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1F2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="remaining" 
                    stroke="#8B5CF6" 
                    strokeWidth={2}
                    name="Remaining Points"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="ideal" 
                    stroke="#6B7280" 
                    strokeDasharray="5 5"
                    name="Ideal Burndown"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <p>No burndown data available</p>
              </div>
            )}
          </div>

          {/* Sprint Statistics */}
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Sprint Statistics</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <p className="text-2xl font-bold text-white">{getSprintVelocity(selectedSprint)}</p>
                  <p className="text-gray-400 text-sm">Velocity (Points)</p>
                </div>
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <p className="text-2xl font-bold text-white">{getSprintProgress(selectedSprint)}%</p>
                  <p className="text-gray-400 text-sm">Completion</p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Total Issues:</span>
                  <span className="text-white">{selectedSprint.issues?.length || 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Completed:</span>
                  <span className="text-green-400">
                    {selectedSprint.issues?.filter(i => i.status === 'done').length || 0}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">In Progress:</span>
                  <span className="text-yellow-400">
                    {selectedSprint.issues?.filter(i => i.status === 'in_progress').length || 0}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Remaining:</span>
                  <span className="text-blue-400">
                    {selectedSprint.issues?.filter(i => ['backlog', 'todo'].includes(i.status)).length || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Sprint Planning Modal Component
const SprintPlanningModal: React.FC<{
  sprint: Sprint
  availableIssues: Issue[]
  onClose: () => void
  onAddIssues: (sprintId: string, issueIds: string[]) => void
}> = ({ sprint, availableIssues, onClose, onAddIssues }) => {
  const [selectedIssues, setSelectedIssues] = useState<string[]>([])

  const toggleIssue = (issueId: string) => {
    setSelectedIssues(prev => 
      prev.includes(issueId) 
        ? prev.filter(id => id !== issueId)
        : [...prev, issueId]
    )
  }

  const handleAddIssues = () => {
    if (selectedIssues.length > 0) {
      onAddIssues(sprint.id, selectedIssues)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden border border-gray-700">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">Plan Sprint: {sprint.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          <div className="space-y-4">
            {availableIssues.map(issue => (
              <div
                key={issue.id}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedIssues.includes(issue.id)
                    ? 'border-purple-500 bg-purple-900/20'
                    : 'border-gray-600 bg-gray-700/50 hover:border-purple-500/50'
                }`}
                onClick={() => toggleIssue(issue.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-white">{issue.title}</h4>
                    <p className="text-gray-400 text-sm mt-1">{issue.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-400">
                      <span>Priority: {issue.priority}</span>
                      {issue.story_points && <span>Points: {issue.story_points}</span>}
                      {issue.estimated_hours && <span>Hours: {issue.estimated_hours}h</span>}
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={selectedIssues.includes(issue.id)}
                    onChange={() => toggleIssue(issue.id)}
                    className="ml-4 w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex items-center justify-between p-6 border-t border-gray-700">
          <p className="text-gray-400">
            {selectedIssues.length} issue{selectedIssues.length !== 1 ? 's' : ''} selected
          </p>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleAddIssues}
              disabled={selectedIssues.length === 0}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-6 py-2 rounded-lg text-white font-medium"
            >
              Add to Sprint
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SprintsPage