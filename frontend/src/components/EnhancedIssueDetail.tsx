// ABOUTME: Enhanced issue detail component with comprehensive features and AI integration
// ABOUTME: Includes test cases, tags, activity monitoring, documentation links, and AI activity tracking

import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { Project, Issue, Activity, API_URL } from '../App'
import MarkdownRenderer from './MarkdownRenderer'
import MarkdownEditor from './MarkdownEditor'
import SubTasks from './SubTasks'

// Extended types for enhanced features
interface TestCase {
  id: string
  title: string
  description?: string
  given?: string[]
  when?: string[]
  then?: string[]
  given_steps?: string[]
  when_steps?: string[]
  then_steps?: string[]
  gherkin_scenario?: string
  test_type?: string
  status: 'pending' | 'passed' | 'failed'
  type?: 'unit' | 'integration' | 'e2e' | 'manual' | 'security' | 'performance'
  created_at: string
  updated_at: string
}

interface Tag {
  id: string
  name: string
  color: string
  description: string
}

interface DocumentationLink {
  id: string
  title: string
  url: string
  type: 'spec' | 'design' | 'api' | 'wiki' | 'external'
  created_at: string
}

interface GitLink {
  id: string
  type: 'branch' | 'commit' | 'pr' | 'issue'
  url: string
  title: string
  status?: string
  created_at: string
}

interface AIActivity extends Activity {
  token_cost?: number
  execution_time?: number
  model_used?: string
  prompt?: string
  response?: string
  input_tokens?: number
  output_tokens?: number
  cost_usd?: number
}

interface Comment {
  id: string
  content: string
  author: string
  created_at: string
  converted_to_ticket?: string
}

interface TokenSummary {
  total_cost: number
  total_tokens: number
  input_tokens: number
  output_tokens: number
  cost_usd: number
  activities_count: number
}

interface Props {
  issue: Issue
  isOpen: boolean
  onClose: () => void
  onUpdate: () => void
  projects: Project[]
}

const EnhancedIssueDetail: React.FC<Props> = ({ 
  issue, 
  isOpen, 
  onClose, 
  onUpdate, 
  projects 
}) => {
  // State management
  const [loading, setLoading] = useState(false)
  const [activeSection, setActiveSection] = useState<'overview' | 'subtasks' | 'test-cases' | 'activity'>('overview')
  const [showDropdown, setShowDropdown] = useState(false)
  const [showTagSelector, setShowTagSelector] = useState(false)
  const [showDocPanel, setShowDocPanel] = useState(false)
  const [showGitPanel, setShowGitPanel] = useState(false)
  
  // Data states
  const [testCases, setTestCases] = useState<TestCase[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [issueTags, setIssueTags] = useState<string[]>([])
  const [availableTags, setAvailableTags] = useState<Tag[]>([])
  const [docLinks, setDocLinks] = useState<DocumentationLink[]>([])
  const [gitLinks, setGitLinks] = useState<GitLink[]>([])
  const [activities, setActivities] = useState<AIActivity[]>([])
  const [comments, setComments] = useState<Comment[]>([])
  const [tokenSummary, setTokenSummary] = useState<TokenSummary | null>(null)
  
  // Form states
  const [isEditingDescription, setIsEditingDescription] = useState(false)
  const [editedDescription, setEditedDescription] = useState('')
  
  // Resize states
  const [modalSize, setModalSize] = useState({ width: 1152, height: 720 }) // Default: max-w-6xl ~= 1152px, 90vh ~= 720px
  const [isResizing, setIsResizing] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)
  const [previousSize, setPreviousSize] = useState({ width: 1152, height: 720 })
  const modalRef = useRef<HTMLDivElement>(null)
  const [newComment, setNewComment] = useState('')
  const [newTestCase, setNewTestCase] = useState({
    title: '',
    description: '',
    given: [''],
    when: [''],
    then: [''],
    type: 'unit' as TestCase['type']
  })
  const [newDocLink, setNewDocLink] = useState({
    title: '',
    url: '',
    type: 'spec' as DocumentationLink['type']
  })
  const [tagSearch, setTagSearch] = useState('')
  const [showNewTagForm, setShowNewTagForm] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const [newTagColor, setNewTagColor] = useState('#8B5CF6')
  
  // Refs
  const dropdownRef = useRef<HTMLDivElement>(null)
  const activityRef = useRef<HTMLDivElement>(null)

  // Load all data when component opens
  useEffect(() => {
    if (isOpen && issue) {
      loadIssueData()
    }
  }, [isOpen, issue])

  // Handle outside clicks for dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const loadIssueData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadTestCases(),
        loadTags(),
        loadDocLinks(),
        loadGitLinks(),
        loadActivities(),
        loadComments(),
        loadTokenSummary(),
        loadAvailableTags()
      ])
    } catch (error) {
      console.error('Error loading issue data:', error)
      toast.error('Failed to load issue data')
    } finally {
      setLoading(false)
    }
  }

  const loadTestCases = async () => {
    try {
      const response = await axios.get(`${API_URL}/issues/${issue.id}/test-cases`)
      // Map database fields to component fields
      const mappedTestCases = (response.data || []).map((tc: any) => ({
        ...tc,
        given: tc.given_steps || tc.given || [],
        when: tc.when_steps || tc.when || [],
        then: tc.then_steps || tc.then || [],
        type: tc.test_type || tc.type || 'functional',
        description: tc.description || tc.gherkin_scenario || ''
      }))
      setTestCases(mappedTestCases)
    } catch (error) {
      console.error('Error loading test cases:', error)
    }
  }

  const loadTags = async () => {
    try {
      const response = await axios.get(`${API_URL}/issues/${issue.id}/tags`)
      setIssueTags(response.data?.tags || [])
    } catch (error) {
      console.error('Error loading tags:', error)
    }
  }

  const loadAvailableTags = async () => {
    try {
      const response = await axios.get(`${API_URL}/tags`)
      setAvailableTags(response.data || [])
    } catch (error) {
      console.error('Error loading available tags:', error)
    }
  }

  const loadDocLinks = async () => {
    try {
      const response = await axios.get(`${API_URL}/issues/${issue.id}/doc-links`)
      setDocLinks(response.data || [])
    } catch (error) {
      console.error('Error loading doc links:', error)
    }
  }

  const loadGitLinks = async () => {
    try {
      const response = await axios.get(`${API_URL}/issues/${issue.id}/git-links`)
      setGitLinks(response.data || [])
    } catch (error) {
      console.error('Error loading git links:', error)
    }
  }

  const loadActivities = async () => {
    try {
      const response = await axios.get(`${API_URL}/issues/${issue.id}/activities/detailed`)
      setActivities(response.data || [])
    } catch (error) {
      console.error('Error loading activities:', error)
    }
  }

  const loadComments = async () => {
    try {
      const response = await axios.get(`${API_URL}/issues/${issue.id}/comments`)
      setComments(response.data || [])
    } catch (error) {
      console.error('Error loading comments:', error)
    }
  }

  const loadTokenSummary = async () => {
    try {
      const response = await axios.get(`${API_URL}/issues/${issue.id}/token-summary`)
      setTokenSummary(response.data)
    } catch (error) {
      console.error('Error loading token summary:', error)
    }
  }

  // Menu actions
  const scrollToActivity = () => {
    setActiveSection('activity')
    setTimeout(() => {
      activityRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, 100)
    setShowDropdown(false)
  }

  const exportIssueData = async () => {
    try {
      const data = {
        issue,
        testCases,
        tags: issueTags,
        docLinks,
        gitLinks,
        activities,
        comments,
        tokenSummary
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `issue-${issue.id.slice(-6)}-export.json`
      a.click()
      URL.revokeObjectURL(url)
      
      toast.success('Issue data exported')
    } catch (error) {
      console.error('Error exporting data:', error)
      toast.error('Failed to export data')
    }
    setShowDropdown(false)
  }

  // Tag management
  const addTag = async (tagName: string) => {
    try {
      await axios.post(`${API_URL}/issues/${issue.id}/tags`, { tag: tagName })
      setIssueTags(prev => [...prev, tagName])
      toast.success('Tag added')
    } catch (error) {
      console.error('Error adding tag:', error)
      toast.error('Failed to add tag')
    }
  }

  const removeTag = async (tagName: string) => {
    try {
      await axios.delete(`${API_URL}/issues/${issue.id}/tags/${tagName}`)
      setIssueTags(prev => prev.filter(t => t !== tagName))
      toast.success('Tag removed')
    } catch (error) {
      console.error('Error removing tag:', error)
      toast.error('Failed to remove tag')
    }
  }

  // Test case management
  const autoGenerateTests = async () => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_URL}/issues/${issue.id}/test-cases/auto-generate`)
      setTestCases(prev => [...prev, ...response.data])
      toast.success(`Generated ${response.data.length} test cases`)
    } catch (error) {
      console.error('Error generating tests:', error)
      toast.error('Failed to generate test cases')
    } finally {
      setLoading(false)
    }
  }

  const addTestCase = async () => {
    if (!newTestCase.title.trim()) {
      toast.error('Test case title is required')
      return
    }

    try {
      const response = await axios.post(`${API_URL}/issues/${issue.id}/test-cases`, newTestCase)
      setTestCases(prev => [...prev, response.data])
      setNewTestCase({
        title: '',
        description: '',
        given: [''],
        when: [''],
        then: [''],
        type: 'unit'
      })
      toast.success('Test case added')
    } catch (error) {
      console.error('Error adding test case:', error)
      toast.error('Failed to add test case')
    }
  }

  // Comment management
  const addComment = async () => {
    if (!newComment.trim()) return

    try {
      const response = await axios.post(`${API_URL}/issues/${issue.id}/comments`, {
        content: newComment
      })
      setComments(prev => [...prev, response.data])
      setNewComment('')
      toast.success('Comment added')
    } catch (error) {
      console.error('Error adding comment:', error)
      toast.error('Failed to add comment')
    }
  }

  const createRequestFromComment = async (commentId: string) => {
    try {
      const response = await axios.post(`${API_URL}/comments/${commentId}/convert-to-ticket`)
      toast.success('Sub-ticket created successfully')
      loadComments() // Reload to show conversion status
    } catch (error) {
      console.error('Error creating request:', error)
      toast.error('Failed to create sub-ticket')
    }
  }

  // Add documentation link
  const addDocLink = async () => {
    if (!newDocLink.title.trim() || !newDocLink.url.trim()) {
      toast.error('Title and URL are required')
      return
    }

    try {
      const response = await axios.post(`${API_URL}/issues/${issue.id}/doc-links`, newDocLink)
      setDocLinks(prev => [...prev, response.data])
      setNewDocLink({ title: '', url: '', type: 'spec' })
      toast.success('Documentation link added')
    } catch (error) {
      console.error('Error adding doc link:', error)
      toast.error('Failed to add documentation link')
    }
  }

  // Utility functions
  const getTagColor = (tagName: string) => {
    const colors: Record<string, string> = {
      bug: 'bg-red-500/20 text-red-400 border-red-500/30',
      feature: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      documentation: 'bg-green-500/20 text-green-400 border-green-500/30',
      performance: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      security: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      ux: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
      api: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
      database: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      testing: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
      deployment: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
      ai: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
      urgent: 'bg-red-600/20 text-red-300 border-red-600/30',
      blocked: 'bg-red-700/20 text-red-200 border-red-700/30',
      ready: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    }
    return colors[tagName] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  }

  const getTestStatusColor = (status: TestCase['status']) => {
    switch (status) {
      case 'passed': return 'text-green-400 bg-green-500/20'
      case 'failed': return 'text-red-400 bg-red-500/20'
      default: return 'text-yellow-400 bg-yellow-500/20'
    }
  }

  const getDocTypeIcon = (type: DocumentationLink['type']) => {
    switch (type) {
      case 'spec': return '📋'
      case 'design': return '🎨'
      case 'api': return '🔌'
      case 'wiki': return '📚'
      default: return '🔗'
    }
  }

  const getGitTypeIcon = (type: GitLink['type']) => {
    switch (type) {
      case 'branch': return '🌿'
      case 'commit': return '📝'
      case 'pr': return '🔀'
      default: return '📋'
    }
  }

  const filteredTags = availableTags.filter(tag => 
    tag.name.toLowerCase().includes(tagSearch.toLowerCase()) &&
    !issueTags.includes(tag.name)
  )

  const testPassRate = testCases.length > 0 
    ? Math.round((testCases.filter(t => t.status === 'passed').length / testCases.length) * 100)
    : 0

  if (!isOpen) return null

  // Handle resize
  const handleMouseDown = (e: React.MouseEvent, direction: string) => {
    e.preventDefault()
    setIsResizing(true)
    
    const startX = e.clientX
    const startY = e.clientY
    const startWidth = modalSize.width
    const startHeight = modalSize.height
    
    const handleMouseMove = (e: MouseEvent) => {
      if (direction.includes('right')) {
        const newWidth = Math.max(600, Math.min(window.innerWidth - 32, startWidth + (e.clientX - startX)))
        setModalSize(prev => ({ ...prev, width: newWidth }))
      }
      if (direction.includes('left')) {
        const newWidth = Math.max(600, Math.min(window.innerWidth - 32, startWidth - (e.clientX - startX)))
        setModalSize(prev => ({ ...prev, width: newWidth }))
      }
      if (direction.includes('bottom')) {
        const newHeight = Math.max(400, Math.min(window.innerHeight - 32, startHeight + (e.clientY - startY)))
        setModalSize(prev => ({ ...prev, height: newHeight }))
      }
      if (direction.includes('top')) {
        const newHeight = Math.max(400, Math.min(window.innerHeight - 32, startHeight - (e.clientY - startY)))
        setModalSize(prev => ({ ...prev, height: newHeight }))
      }
    }
    
    const handleMouseUp = () => {
      setIsResizing(false)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  return (
    <div className={`fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 ${isResizing ? 'select-none' : ''}`}>
      <div 
        ref={modalRef}
        className="bg-gray-800/95 backdrop-blur-xl rounded-xl overflow-hidden border border-gray-700/50 shadow-2xl relative"
        style={{ 
          width: `${modalSize.width}px`, 
          height: `${modalSize.height}px`,
          maxWidth: '95vw',
          maxHeight: '95vh'
        }}
      >
        {/* Resize Handles */}
        {/* Top */}
        <div 
          className="absolute top-0 left-2 right-2 h-2 cursor-n-resize hover:bg-purple-500/20 transition-colors"
          onMouseDown={(e) => handleMouseDown(e, 'top')}
        />
        {/* Bottom */}
        <div 
          className="absolute bottom-0 left-2 right-2 h-2 cursor-s-resize hover:bg-purple-500/20 transition-colors"
          onMouseDown={(e) => handleMouseDown(e, 'bottom')}
        />
        {/* Left */}
        <div 
          className="absolute left-0 top-2 bottom-2 w-2 cursor-w-resize hover:bg-purple-500/20 transition-colors"
          onMouseDown={(e) => handleMouseDown(e, 'left')}
        />
        {/* Right */}
        <div 
          className="absolute right-0 top-2 bottom-2 w-2 cursor-e-resize hover:bg-purple-500/20 transition-colors"
          onMouseDown={(e) => handleMouseDown(e, 'right')}
        />
        {/* Corners */}
        <div 
          className="absolute top-0 left-0 w-4 h-4 cursor-nw-resize hover:bg-purple-500/30 transition-colors rounded-tl-xl"
          onMouseDown={(e) => handleMouseDown(e, 'top-left')}
        />
        <div 
          className="absolute top-0 right-0 w-4 h-4 cursor-ne-resize hover:bg-purple-500/30 transition-colors rounded-tr-xl"
          onMouseDown={(e) => handleMouseDown(e, 'top-right')}
        />
        <div 
          className="absolute bottom-0 left-0 w-4 h-4 cursor-sw-resize hover:bg-purple-500/30 transition-colors rounded-bl-xl"
          onMouseDown={(e) => handleMouseDown(e, 'bottom-left')}
        />
        <div 
          className="absolute bottom-0 right-0 w-6 h-6 cursor-se-resize hover:bg-purple-500/30 transition-colors rounded-br-xl flex items-center justify-center group"
          onMouseDown={(e) => handleMouseDown(e, 'bottom-right')}
        >
          <svg className="w-4 h-4 text-gray-600 group-hover:text-purple-400 transition-colors" fill="none" viewBox="0 0 24 24">
            <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 20h16M4 20v-4M4 20l8-8m8 8v-4m0 4l-8-8" />
          </svg>
        </div>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700/50 bg-gray-800/50">
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-white pr-4">{issue.title}</h1>
              
              {/* Top Right Menu */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setShowDropdown(!showDropdown)}
                  className="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-700/50"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </button>
                
                {showDropdown && (
                  <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-xl border border-gray-700 z-50">
                    <button
                      onClick={scrollToActivity}
                      className="w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors flex items-center space-x-2"
                    >
                      <span>📊</span><span>Activity</span>
                    </button>
                    <button
                      onClick={() => { setShowDocPanel(true); setShowDropdown(false) }}
                      className="w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors flex items-center space-x-2"
                    >
                      <span>📚</span><span>Doc Links</span>
                    </button>
                    <button
                      onClick={() => { setShowGitPanel(true); setShowDropdown(false) }}
                      className="w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors flex items-center space-x-2"
                    >
                      <span>🔗</span><span>Git Links</span>
                    </button>
                    <button
                      onClick={exportIssueData}
                      className="w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors flex items-center space-x-2"
                    >
                      <span>💾</span><span>Export</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-4 mt-2">
              <span className="text-gray-400 text-sm">#{issue.id.slice(-6)}</span>
              <span className="text-gray-400 text-sm">
                Created {format(new Date(issue.created_at), 'MMM dd, yyyy')}
              </span>
              {tokenSummary && tokenSummary.cost_usd != null && (
                <span className="text-purple-400 text-sm font-medium">
                  💰 ${(tokenSummary.cost_usd || 0).toFixed(4)} total cost
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            <button
              onClick={() => {
                if (isMaximized) {
                  setModalSize(previousSize)
                  setIsMaximized(false)
                } else {
                  setPreviousSize(modalSize)
                  setModalSize({ 
                    width: window.innerWidth - 32, 
                    height: window.innerHeight - 32 
                  })
                  setIsMaximized(true)
                }
              }}
              className="text-gray-400 hover:text-white transition-colors p-1"
              title={isMaximized ? "Restore" : "Maximize"}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMaximized ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                )}
              </svg>
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tags Section */}
        <div className="px-6 py-4 border-b border-gray-700/50 bg-gray-800/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 flex-wrap">
              <span className="text-sm text-gray-400 mr-2">Tags:</span>
              {issueTags.map(tagName => (
                <span
                  key={tagName}
                  className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium border ${getTagColor(tagName)}`}
                >
                  <span>{tagName}</span>
                  <button
                    onClick={() => removeTag(tagName)}
                    className="hover:text-red-400 transition-colors"
                  >
                    ✕
                  </button>
                </span>
              ))}
              <button
                onClick={() => setShowTagSelector(!showTagSelector)}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-700/50 text-gray-300 hover:bg-gray-600/50 border border-gray-600 transition-colors"
              >
                + Add Tag
              </button>
            </div>
          </div>
          
          {/* Tag Selector */}
          {showTagSelector && (
            <div className="mt-3 p-3 bg-gray-700/50 rounded-lg border border-gray-600">
              <input
                type="text"
                placeholder="Search or create tags..."
                value={tagSearch}
                onChange={(e) => setTagSearch(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm mb-2"
              />
              
              {/* Existing Tags */}
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto mb-3">
                {filteredTags.map(tag => (
                  <button
                    key={tag.id}
                    onClick={() => {
                      addTag(tag.name)
                      setShowTagSelector(false)
                      setTagSearch('')
                    }}
                    className={`px-3 py-1 rounded-full text-xs font-medium border hover:bg-opacity-80 transition-colors ${getTagColor(tag.name)}`}
                  >
                    {tag.name}
                  </button>
                ))}
              </div>
              
              {/* Create New Tag Option */}
              {tagSearch && !availableTags.some(tag => tag.name.toLowerCase() === tagSearch.toLowerCase()) && (
                <div className="border-t border-gray-600 pt-3">
                  {!showNewTagForm ? (
                    <button
                      onClick={() => {
                        setNewTagName(tagSearch)
                        setShowNewTagForm(true)
                      }}
                      className="flex items-center space-x-2 text-purple-400 hover:text-purple-300 text-sm transition-colors"
                    >
                      <span className="text-lg">+</span>
                      <span>Create new tag "{tagSearch}"</span>
                    </button>
                  ) : (
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs text-gray-400 block mb-1">Tag Name</label>
                        <input
                          type="text"
                          value={newTagName}
                          onChange={(e) => setNewTagName(e.target.value)}
                          className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                        />
                      </div>
                      
                      <div>
                        <label className="text-xs text-gray-400 block mb-1">Choose Color</label>
                        <div className="grid grid-cols-8 gap-2">
                          {[
                            '#EF4444', // Red
                            '#F97316', // Orange
                            '#F59E0B', // Amber
                            '#84CC16', // Lime
                            '#10B981', // Emerald
                            '#06B6D4', // Cyan
                            '#3B82F6', // Blue
                            '#8B5CF6', // Purple
                            '#EC4899', // Pink
                            '#F43F5E', // Rose
                            '#6366F1', // Indigo
                            '#9333EA', // Violet
                            '#64748B', // Slate
                            '#71717A', // Zinc
                            '#737373', // Neutral
                            '#525252'  // Gray
                          ].map(color => (
                            <button
                              key={color}
                              onClick={() => setNewTagColor(color)}
                              className={`w-8 h-8 rounded-full border-2 transition-all ${
                                newTagColor === color ? 'border-white scale-110' : 'border-gray-600 hover:border-gray-400'
                              }`}
                              style={{ backgroundColor: color }}
                            />
                          ))}
                        </div>
                      </div>
                      
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => {
                            setShowNewTagForm(false)
                            setNewTagName('')
                            setNewTagColor('#8B5CF6')
                          }}
                          className="px-3 py-1 text-gray-400 hover:text-white text-sm transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={async () => {
                            if (newTagName.trim()) {
                              try {
                                // Create the new tag
                                await axios.post(`${API_URL}/tags`, {
                                  name: newTagName.trim().toLowerCase(),
                                  color: newTagColor,
                                  description: `Custom tag created for ${issue.title}`
                                })
                                
                                // Add the tag to the issue
                                await addTag(newTagName.trim().toLowerCase())
                                
                                // Reload available tags
                                await loadAvailableTags()
                                
                                // Reset form
                                setShowNewTagForm(false)
                                setNewTagName('')
                                setNewTagColor('#8B5CF6')
                                setTagSearch('')
                                setShowTagSelector(false)
                                
                                toast.success('Tag created and added!')
                              } catch (error) {
                                console.error('Error creating tag:', error)
                                toast.error('Failed to create tag')
                              }
                            }
                          }}
                          className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm font-medium transition-colors"
                        >
                          Create & Add
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-gray-700/50 bg-gray-800/30">
          {[
            { key: 'overview', label: 'Overview', icon: '📋' },
            { key: 'subtasks', label: 'Subtasks', icon: '🔗', badge: undefined },
            { key: 'test-cases', label: 'Test Cases', icon: '🧪', badge: testCases.length },
            { key: 'activity', label: 'Activity', icon: '📊', badge: activities.length }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveSection(tab.key as any)}
              className={`px-6 py-3 text-sm font-medium transition-colors flex items-center space-x-2 ${
                activeSection === tab.key
                  ? 'text-purple-400 border-b-2 border-purple-500 bg-purple-500/10'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/30'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span className="bg-gray-600 text-white text-xs px-2 py-0.5 rounded-full">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div 
          className="p-6 overflow-y-auto"
          style={{ maxHeight: 'calc(100% - 200px)' }}
        >
          {activeSection === 'overview' && (
            <div className="space-y-6">
              {/* Description */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">Description</h3>
                  {!isEditingDescription ? (
                    <button
                      onClick={() => {
                        setIsEditingDescription(true)
                        setEditedDescription(issue.description || '')
                      }}
                      className="px-3 py-1 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-md transition-colors"
                    >
                      Edit
                    </button>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={async () => {
                          try {
                            await axios.patch(`${API_URL}/issues/${issue.id}`, {
                              description: editedDescription
                            })
                            issue.description = editedDescription
                            setIsEditingDescription(false)
                            toast.success('Description updated')
                            onUpdate()
                          } catch (error) {
                            console.error('Error updating description:', error)
                            toast.error('Failed to update description')
                          }
                        }}
                        className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setIsEditingDescription(false)
                          setEditedDescription('')
                        }}
                        className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
                <div className={`bg-gray-700/50 rounded-lg p-4 border border-gray-600 transition-all duration-300 ${
                  isEditingDescription ? 'min-h-[400px]' : ''
                }`}>
                  {!isEditingDescription ? (
                    <MarkdownRenderer 
                      content={issue.description || 'No description provided'}
                      className="prose prose-invert max-w-none"
                    />
                  ) : (
                    <div className="h-full">
                      <MarkdownEditor
                        value={editedDescription}
                        onChange={setEditedDescription}
                        placeholder="Enter issue description..."
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Issue Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-400 mb-2">Status</h4>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-500/20 text-blue-400">
                    {issue.status.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-400 mb-2">Priority</h4>
                  <span className="text-white">{issue.priority}</span>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-400 mb-2">Story Points</h4>
                  <span className="text-white">{issue.story_points || 0}</span>
                </div>
              </div>

              {/* Token Summary - Subtle design */}
              {tokenSummary && tokenSummary.total_tokens > 0 && (
                <div className="bg-gray-700/30 rounded-lg p-3 border border-gray-600">
                  <h4 className="text-sm font-medium text-gray-400 mb-2">AI Usage Metrics</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="text-gray-500">Tokens:</span>
                      <span className="ml-2 text-gray-300">{tokenSummary.total_tokens.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Cost:</span>
                      <span className="ml-2 text-gray-300">${(tokenSummary.cost_usd || 0).toFixed(4)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Input:</span>
                      <span className="ml-2 text-gray-300">{tokenSummary.input_tokens.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Output:</span>
                      <span className="ml-2 text-gray-300">{tokenSummary.output_tokens.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeSection === 'subtasks' && (
            <div className="space-y-4">
              <SubTasks 
                parentIssue={issue} 
                onUpdate={onUpdate}
              />
            </div>
          )}

          {activeSection === 'test-cases' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Test Cases</h3>
                <div className="flex items-center space-x-3">
                  <div className="text-sm text-gray-400">
                    Pass Rate: <span className={testPassRate >= 80 ? 'text-green-400' : testPassRate >= 60 ? 'text-yellow-400' : 'text-red-400'}>
                      {testPassRate}%
                    </span>
                  </div>
                  <button
                    onClick={autoGenerateTests}
                    disabled={loading}
                    className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors"
                  >
                    🤖 Auto-Generate Tests
                  </button>
                </div>
              </div>

              {/* Test Cases List */}
              <div className="space-y-4">
                {testCases.map(testCase => (
                  <div key={testCase.id} className="bg-gray-700/50 rounded-lg p-4 border border-gray-600">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <h4 className="font-medium text-white">{testCase.title}</h4>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getTestStatusColor(testCase.status)}`}>
                          {testCase.status}
                        </span>
                        <span className="px-2 py-1 rounded text-xs font-medium bg-gray-600 text-gray-300">
                          {testCase.type}
                        </span>
                      </div>
                    </div>
                    
                    {testCase.description && (
                      <div className="mb-3">
                        <MarkdownRenderer 
                          content={testCase.description}
                          className="text-sm"
                        />
                      </div>
                    )}
                    
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-green-400 font-medium">Given:</span>
                        <ul className="ml-4 text-gray-300">
                          {(testCase.given || testCase.given_steps || []).map((step, i) => (
                            <li key={i}>• {step}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="text-blue-400 font-medium">When:</span>
                        <ul className="ml-4 text-gray-300">
                          {(testCase.when || testCase.when_steps || []).map((step, i) => (
                            <li key={i}>• {step}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="text-purple-400 font-medium">Then:</span>
                        <ul className="ml-4 text-gray-300">
                          {(testCase.then || testCase.then_steps || []).map((step, i) => (
                            <li key={i}>• {step}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Add New Test Case Form */}
              <div className="bg-gray-700/30 rounded-lg p-4 border border-gray-600">
                <h4 className="font-medium text-white mb-3">Add Manual Test Case</h4>
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Test case title"
                    value={newTestCase.title}
                    onChange={(e) => setNewTestCase(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                  />
                  <textarea
                    placeholder="Description (optional)"
                    value={newTestCase.description}
                    onChange={(e) => setNewTestCase(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                    rows={2}
                  />
                  <select
                    value={newTestCase.type}
                    onChange={(e) => setNewTestCase(prev => ({ ...prev, type: e.target.value as TestCase['type'] }))}
                    className="px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                  >
                    <option value="unit">Unit</option>
                    <option value="integration">Integration</option>
                    <option value="e2e">End-to-End</option>
                    <option value="manual">Manual</option>
                    <option value="security">Security</option>
                    <option value="performance">Performance</option>
                  </select>
                  <button
                    onClick={addTestCase}
                    className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white text-sm font-medium transition-colors"
                  >
                    Add Test Case
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'activity' && (
            <div ref={activityRef} className="space-y-6">
              <h3 className="text-lg font-semibold text-white">Enhanced Activity Timeline</h3>
              
              {activities.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📊</div>
                  <h4 className="text-xl font-semibold text-white mb-2">No Activity Yet</h4>
                  <p className="text-gray-400">Activity will appear here as AI and humans interact with this issue</p>
                </div>
              ) : (
                <div className="relative">
                  <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-700"></div>
                  
                  <div className="space-y-6">
                    {activities.map((activity) => (
                      <div key={activity.id} className="relative flex items-start space-x-4">
                        <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full bg-gray-800 border-2 ${
                          (activity as any).user_type === 'ai' ? 'border-purple-500 text-purple-400' : 'border-blue-500 text-blue-400'
                        }`}>
                          <span className="text-lg">
                            {(activity as any).user_type === 'ai' ? '🤖' : '👤'}
                          </span>
                        </div>
                        
                        <div className="flex-1 min-w-0 pb-6">
                          <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-3">
                                <h4 className={`font-medium capitalize ${
                                  (activity as any).user_type === 'ai' ? 'text-purple-400' : 'text-blue-400'
                                }`}>
                                  {(activity.type || 'activity').replace('_', ' ')}
                                </h4>
                                {activity.model_used && (
                                  <span className="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded">
                                    {activity.model_used}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center space-x-3 text-xs text-gray-400">
                                {activity.execution_time && (
                                  <span>⏱️ {activity.execution_time}ms</span>
                                )}
                                {activity.cost_usd && (
                                  <span className="text-green-400">💰 ${(activity.cost_usd || 0).toFixed(4)}</span>
                                )}
                                <time>{format(new Date(activity.created_at), 'MMM dd, HH:mm')}</time>
                              </div>
                            </div>
                            
                            <div className="mb-3">
                              <MarkdownRenderer 
                                content={activity.description}
                                className="text-sm"
                              />
                            </div>
                            
                            {/* Token breakdown for AI activities */}
                            {activity.input_tokens && activity.output_tokens && (
                              <div className="grid grid-cols-3 gap-3 mb-3">
                                <div className="bg-gray-800/50 rounded p-2 text-center">
                                  <div className="text-blue-400 font-medium">{activity.input_tokens.toLocaleString()}</div>
                                  <div className="text-xs text-gray-400">Input Tokens</div>
                                </div>
                                <div className="bg-gray-800/50 rounded p-2 text-center">
                                  <div className="text-green-400 font-medium">{activity.output_tokens.toLocaleString()}</div>
                                  <div className="text-xs text-gray-400">Output Tokens</div>
                                </div>
                                <div className="bg-gray-800/50 rounded p-2 text-center">
                                  <div className="text-purple-400 font-medium">{(activity.input_tokens + activity.output_tokens).toLocaleString()}</div>
                                  <div className="text-xs text-gray-400">Total Tokens</div>
                                </div>
                              </div>
                            )}
                            
                            {/* Expandable sections for AI prompts and responses */}
                            {(activity.prompt || activity.response) && (
                              <div className="space-y-2">
                                {activity.prompt && (
                                  <details className="group">
                                    <summary className="cursor-pointer text-sm text-purple-400 hover:text-purple-300 select-none">
                                      📝 View Full Prompt
                                    </summary>
                                    <div className="mt-2 p-3 bg-gray-800/50 rounded border border-gray-600">
                                      <pre className="text-xs text-gray-300 whitespace-pre-wrap overflow-x-auto">
                                        {activity.prompt}
                                      </pre>
                                    </div>
                                  </details>
                                )}
                                
                                {activity.response && (
                                  <details className="group">
                                    <summary className="cursor-pointer text-sm text-green-400 hover:text-green-300 select-none">
                                      🤖 View AI Response
                                    </summary>
                                    <div className="mt-2 p-3 bg-gray-800/50 rounded border border-gray-600">
                                      <pre className="text-xs text-gray-300 whitespace-pre-wrap overflow-x-auto">
                                        {activity.response}
                                      </pre>
                                    </div>
                                  </details>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Comments & Requests Section - Only in Activity Tab */}
              <div className="mt-8 pt-6 border-t border-gray-700/50">
                <h4 className="font-medium text-white mb-4">Comments & Requests</h4>
                
                {/* Recent Comments */}
                {comments.length > 0 && (
                  <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
                    {comments.slice(-5).map(comment => (
                      <div key={comment.id} className="bg-gray-700/30 rounded p-3 text-sm">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-gray-400">{comment.author}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-500 text-xs">
                              {format(new Date(comment.created_at), 'MMM dd, HH:mm')}
                            </span>
                            {!comment.converted_to_ticket && (
                              <button
                                onClick={() => createRequestFromComment(comment.id)}
                                className="text-purple-400 hover:text-purple-300 text-xs"
                              >
                                Create Ticket
                              </button>
                            )}
                            {comment.converted_to_ticket && (
                              <span className="text-green-400 text-xs">→ Ticket #{comment.converted_to_ticket.slice(-6)}</span>
                            )}
                          </div>
                        </div>
                        <p className="text-gray-300">{comment.content}</p>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Comment Input */}
                <div className="flex space-x-3">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment or describe a new request..."
                    className="flex-1 px-3 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white text-sm resize-none"
                    rows={2}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                        addComment()
                      }
                    }}
                  />
                  <div className="flex flex-col space-y-2">
                    <button
                      onClick={addComment}
                      disabled={!newComment.trim()}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors"
                    >
                      Add Comment
                    </button>
                    <button
                      onClick={() => {
                        if (newComment.trim()) {
                          createRequestFromComment('new')
                        }
                      }}
                      disabled={!newComment.trim()}
                      className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors"
                    >
                      Create Request
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Documentation Links Panel */}
        {showDocPanel && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-60">
            <div className="bg-gray-800 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden border border-gray-700 m-4">
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-white">Documentation Links</h3>
                <button onClick={() => setShowDocPanel(false)} className="text-gray-400 hover:text-white">✕</button>
              </div>
              <div className="p-4 max-h-96 overflow-y-auto">
                <div className="space-y-3">
                  {docLinks.map(link => (
                    <div key={link.id} className="flex items-center justify-between bg-gray-700/50 rounded-lg p-3 border border-gray-600">
                      <div className="flex items-center space-x-3">
                        <span className="text-xl">{getDocTypeIcon(link.type)}</span>
                        <div>
                          <h4 className="font-medium text-white">{link.title}</h4>
                          <p className="text-gray-400 text-sm">{link.type}</p>
                        </div>
                      </div>
                      <a
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        Open →
                      </a>
                    </div>
                  ))}
                </div>
                
                {/* Add Doc Link Form */}
                <div className="mt-4 p-3 bg-gray-700/30 rounded-lg border border-gray-600">
                  <h4 className="font-medium text-white mb-3">Add Documentation Link</h4>
                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder="Title"
                      value={newDocLink.title}
                      onChange={(e) => setNewDocLink(prev => ({ ...prev, title: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                    />
                    <input
                      type="url"
                      placeholder="URL"
                      value={newDocLink.url}
                      onChange={(e) => setNewDocLink(prev => ({ ...prev, url: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                    />
                    <select
                      value={newDocLink.type}
                      onChange={(e) => setNewDocLink(prev => ({ ...prev, type: e.target.value as DocumentationLink['type'] }))}
                      className="px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                    >
                      <option value="spec">Specification</option>
                      <option value="design">Design</option>
                      <option value="api">API Documentation</option>
                      <option value="wiki">Wiki</option>
                      <option value="external">External</option>
                    </select>
                    <button
                      onClick={addDocLink}
                      className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white text-sm font-medium transition-colors"
                    >
                      Add Link
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Git Links Panel */}
        {showGitPanel && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-60">
            <div className="bg-gray-800 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden border border-gray-700 m-4">
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-white">Git Integration</h3>
                <button onClick={() => setShowGitPanel(false)} className="text-gray-400 hover:text-white">✕</button>
              </div>
              <div className="p-4 max-h-96 overflow-y-auto">
                <div className="space-y-3">
                  {gitLinks.map(link => (
                    <div key={link.id} className="flex items-center justify-between bg-gray-700/50 rounded-lg p-3 border border-gray-600">
                      <div className="flex items-center space-x-3">
                        <span className="text-xl">{getGitTypeIcon(link.type)}</span>
                        <div>
                          <h4 className="font-medium text-white">{link.title}</h4>
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-400 text-sm capitalize">{link.type}</span>
                            {link.status && (
                              <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">
                                {link.status}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <a
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        Open →
                      </a>
                    </div>
                  ))}
                </div>
                
                {gitLinks.length === 0 && (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-2">🔗</div>
                    <p className="text-gray-400">No git links yet</p>
                    <p className="text-gray-500 text-sm">Links will appear automatically when code is committed</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default EnhancedIssueDetail