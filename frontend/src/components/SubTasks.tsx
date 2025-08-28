// ABOUTME: Sub-tasks management component for issue parent-child relationships
// ABOUTME: Handles creation, display, and management of sub-tasks with progress tracking

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { Issue, API_URL } from '../App'
import MarkdownRenderer from './MarkdownRenderer'
import { getMarkdownPreview } from '../utils/markdown'

interface SubTask extends Issue {
  parent_issue_id: string
  issue_type: string
  assignee?: string
}

interface Props {
  parentIssue: Issue
  onUpdate: () => void
}

const SubTasks: React.FC<Props> = ({ parentIssue, onUpdate }) => {
  const [subtasks, setSubtasks] = useState<SubTask[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewSubtaskForm, setShowNewSubtaskForm] = useState(false)
  const [newSubtask, setNewSubtask] = useState({
    title: '',
    description: '',
    priority: 3,
    estimated_hours: 0,
    assignee: ''
  })
  const [expandedSubtasks, setExpandedSubtasks] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchSubtasks()
  }, [parentIssue.id])

  const fetchSubtasks = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/issues/${parentIssue.id}/subtasks`)
      setSubtasks(response.data || [])
    } catch (error) {
      console.error('Error fetching subtasks:', error)
      toast.error('Failed to load subtasks')
    } finally {
      setLoading(false)
    }
  }

  const createSubtask = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!newSubtask.title.trim()) {
      toast.error('Title is required')
      return
    }

    try {
      await axios.post(`${API_URL}/issues/${parentIssue.id}/subtasks`, newSubtask)
      toast.success('Subtask created successfully')
      setNewSubtask({
        title: '',
        description: '',
        priority: 3,
        estimated_hours: 0,
        assignee: ''
      })
      setShowNewSubtaskForm(false)
      fetchSubtasks()
      onUpdate()
    } catch (error) {
      console.error('Error creating subtask:', error)
      toast.error('Failed to create subtask')
    }
  }

  const updateSubtaskStatus = async (subtaskId: string, newStatus: string) => {
    try {
      await axios.patch(`${API_URL}/issues/${subtaskId}`, { status: newStatus })
      toast.success('Status updated')
      fetchSubtasks()
      onUpdate()
    } catch (error) {
      console.error('Error updating subtask status:', error)
      toast.error('Failed to update status')
    }
  }

  const promoteToIssue = async (subtaskId: string) => {
    try {
      await axios.post(`${API_URL}/issues/${subtaskId}/promote-to-issue`)
      toast.success('Subtask promoted to issue')
      fetchSubtasks()
      onUpdate()
    } catch (error) {
      console.error('Error promoting subtask:', error)
      toast.error('Failed to promote subtask')
    }
  }

  const deleteSubtask = async (subtaskId: string) => {
    if (!confirm('Are you sure you want to delete this subtask?')) return
    
    try {
      await axios.delete(`${API_URL}/issues/${subtaskId}`)
      toast.success('Subtask deleted')
      fetchSubtasks()
      onUpdate()
    } catch (error) {
      console.error('Error deleting subtask:', error)
      toast.error('Failed to delete subtask')
    }
  }

  const toggleExpanded = (subtaskId: string) => {
    const newExpanded = new Set(expandedSubtasks)
    if (newExpanded.has(subtaskId)) {
      newExpanded.delete(subtaskId)
    } else {
      newExpanded.add(subtaskId)
    }
    setExpandedSubtasks(newExpanded)
  }

  // Calculate overall progress
  const calculateProgress = () => {
    if (subtasks.length === 0) return 0
    const completedCount = subtasks.filter(s => s.status === 'done').length
    return Math.round((completedCount / subtasks.length) * 100)
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      backlog: 'bg-gray-500',
      todo: 'bg-blue-500',
      in_progress: 'bg-yellow-500',
      in_review: 'bg-purple-500',
      done: 'bg-green-500',
      cancelled: 'bg-red-500'
    }
    return colors[status] || 'bg-gray-500'
  }

  const getPriorityColor = (priority: number) => {
    const colors: Record<number, string> = {
      1: 'text-red-500',
      2: 'text-orange-500',
      3: 'text-yellow-500',
      4: 'text-blue-500',
      5: 'text-gray-500'
    }
    return colors[priority] || 'text-gray-500'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header with progress */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-white">
            Subtasks ({subtasks.length})
          </h3>
          {subtasks.length > 0 && (
            <div className="flex items-center space-x-2">
              <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-purple-500 transition-all duration-300"
                  style={{ width: `${calculateProgress()}%` }}
                />
              </div>
              <span className="text-sm text-gray-400">{calculateProgress()}%</span>
            </div>
          )}
        </div>
        
        <button
          onClick={() => setShowNewSubtaskForm(!showNewSubtaskForm)}
          className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          {showNewSubtaskForm ? 'Cancel' : '+ Add Subtask'}
        </button>
      </div>

      {/* New subtask form */}
      {showNewSubtaskForm && (
        <form onSubmit={createSubtask} className="bg-gray-800 rounded-lg p-4 space-y-3">
          <input
            type="text"
            placeholder="Subtask title"
            value={newSubtask.title}
            onChange={(e) => setNewSubtask({ ...newSubtask, title: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
            autoFocus
          />
          
          <textarea
            placeholder="Description (optional)"
            value={newSubtask.description}
            onChange={(e) => setNewSubtask({ ...newSubtask, description: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
            rows={2}
          />
          
          <div className="flex items-center space-x-3">
            <select
              value={newSubtask.priority}
              onChange={(e) => setNewSubtask({ ...newSubtask, priority: parseInt(e.target.value) })}
              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500"
            >
              <option value={1}>Critical</option>
              <option value={2}>High</option>
              <option value={3}>Medium</option>
              <option value={4}>Low</option>
              <option value={5}>Very Low</option>
            </select>
            
            <input
              type="number"
              placeholder="Est. hours"
              value={newSubtask.estimated_hours || ''}
              onChange={(e) => setNewSubtask({ ...newSubtask, estimated_hours: parseFloat(e.target.value) || 0 })}
              className="w-24 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
              min="0"
              step="0.5"
            />
            
            <input
              type="text"
              placeholder="Assignee (optional)"
              value={newSubtask.assignee}
              onChange={(e) => setNewSubtask({ ...newSubtask, assignee: e.target.value })}
              className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
            />
            
            <button
              type="submit"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              Create
            </button>
          </div>
        </form>
      )}

      {/* Subtasks list */}
      {subtasks.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No subtasks yet</p>
          <p className="text-sm mt-2">Break down this issue into smaller tasks</p>
        </div>
      ) : (
        <div className="space-y-2">
          {subtasks.map((subtask) => (
            <div
              key={subtask.id}
              className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden hover:border-gray-600 transition-colors"
            >
              {/* Subtask header */}
              <div className="p-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {/* Status checkbox/indicator */}
                    <button
                      onClick={() => updateSubtaskStatus(
                        subtask.id,
                        subtask.status === 'done' ? 'todo' : 'done'
                      )}
                      className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                        subtask.status === 'done'
                          ? 'bg-green-500 border-green-500'
                          : 'border-gray-600 hover:border-purple-500'
                      }`}
                    >
                      {subtask.status === 'done' && (
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                    
                    <div className="flex-1">
                      <button
                        onClick={() => toggleExpanded(subtask.id)}
                        className={`text-left w-full ${
                          subtask.status === 'done' ? 'line-through text-gray-500' : 'text-white'
                        }`}
                      >
                        <h4 className="font-medium hover:text-purple-400 transition-colors">
                          {subtask.title}
                        </h4>
                      </button>
                      
                      {subtask.description && !expandedSubtasks.has(subtask.id) && (
                        <p className="text-gray-400 text-sm mt-1 line-clamp-1">
                          {getMarkdownPreview(subtask.description, 100)}
                        </p>
                      )}
                      
                      <div className="flex items-center space-x-4 mt-2 text-xs">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full ${getStatusColor(subtask.status)} bg-opacity-20 text-white`}>
                          {subtask.status.replace('_', ' ')}
                        </span>
                        
                        <span className={`${getPriorityColor(subtask.priority)}`}>
                          P{subtask.priority}
                        </span>
                        
                        {subtask.estimated_hours && (
                          <span className="text-gray-500">
                            {subtask.estimated_hours}h estimated
                          </span>
                        )}
                        
                        {subtask.assignee && (
                          <span className="text-gray-500">
                            @{subtask.assignee}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Actions dropdown */}
                  <div className="relative group">
                    <button className="p-1 hover:bg-gray-700 rounded transition-colors">
                      <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                      </svg>
                    </button>
                    
                    <div className="absolute right-0 mt-1 w-48 bg-gray-900 border border-gray-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                      <button
                        onClick={() => promoteToIssue(subtask.id)}
                        className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
                      >
                        Promote to Issue
                      </button>
                      <button
                        onClick={() => deleteSubtask(subtask.id)}
                        className="w-full px-3 py-2 text-left text-sm text-red-400 hover:bg-gray-800 hover:text-red-300 transition-colors"
                      >
                        Delete Subtask
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Expanded content */}
                {expandedSubtasks.has(subtask.id) && subtask.description && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <MarkdownRenderer content={subtask.description} className="text-sm" />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SubTasks