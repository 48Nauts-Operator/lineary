// ABOUTME: Project settings component for repository configuration
// ABOUTME: Manages GitHub/GitLab integration and project preferences

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { Project, API_URL } from '../App'
import GitIntegrationCards from './GitIntegrationCards'

interface Props {
  project: Project
  isOpen: boolean
  onClose: () => void
  onUpdate: () => void
}

interface ProjectSettingsData {
  github_repo?: string
  gitlab_repo?: string
  repo_type: 'github' | 'gitlab' | 'both'
  auto_create_issues: boolean
  auto_sync_enabled: boolean
  webhook_secret?: string
}

const ProjectSettings: React.FC<Props> = ({ project, isOpen, onClose, onUpdate }) => {
  const [settings, setSettings] = useState<ProjectSettingsData>({
    github_repo: '',
    gitlab_repo: '',
    repo_type: 'github',
    auto_create_issues: false,
    auto_sync_enabled: false
  })
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'repository' | 'automation' | 'team'>('repository')

  useEffect(() => {
    if (isOpen && project) {
      loadProjectSettings()
    }
  }, [isOpen, project])

  const loadProjectSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/projects/${project.id}/settings`)
      setSettings(response.data)
    } catch (error) {
      console.error('Error loading project settings:', error)
    }
  }

  const saveSettings = async () => {
    setLoading(true)
    try {
      await axios.put(`${API_URL}/projects/${project.id}/settings`, settings)
      toast.success('Settings saved successfully')
      onUpdate()
    } catch (error) {
      console.error('Error saving settings:', error)
      toast.error('Failed to save settings')
    } finally {
      setLoading(false)
    }
  }

  const testGitHubConnection = async () => {
    if (!settings.github_repo) {
      toast.error('Please enter a GitHub repository URL')
      return
    }
    
    setLoading(true)
    try {
      const response = await axios.post(`${API_URL}/projects/${project.id}/test-repo-connection`, {
        repo_url: settings.github_repo,
        repo_type: 'github'
      })
      
      if (response.data.success) {
        toast.success('GitHub connection successful!')
      } else {
        toast.error('Failed to connect to GitHub repository')
      }
    } catch (error) {
      toast.error('Connection test failed')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800/95 backdrop-blur-xl rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden border border-gray-700/50 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700/50 bg-gray-800/50">
          <div>
            <h2 className="text-xl font-bold text-white">Project Settings</h2>
            <p className="text-sm text-gray-400 mt-1">{project.name}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700/50 bg-gray-800/30">
          {[
            { key: 'repository', label: 'Repository', icon: '🔗' },
            { key: 'automation', label: 'Automation', icon: '⚙️' },
            { key: 'team', label: 'Team', icon: '👥' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`px-6 py-3 text-sm font-medium transition-colors flex items-center space-x-2 ${
                activeTab === tab.key
                  ? 'text-purple-400 border-b-2 border-purple-500 bg-purple-500/10'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/30'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 max-h-[50vh] overflow-y-auto">
          {activeTab === 'repository' && (
            <div className="space-y-6">
              <GitIntegrationCards 
                projectId={project.id} 
                onConnectionChange={() => {
                  loadProjectSettings()
                  onUpdate()
                }}
              />
            </div>
          )}

          {activeTab === 'automation' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Automation Settings</h3>
              
              <div className="space-y-4">
                {/* Auto Create Issues */}
                <div className="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg border border-gray-600">
                  <div className="flex-1">
                    <h4 className="font-medium text-white">Auto-create Issues from PRs</h4>
                    <p className="text-sm text-gray-400 mt-1">
                      Automatically create issues when pull requests are opened
                    </p>
                  </div>
                  <button
                    onClick={() => setSettings({ ...settings, auto_create_issues: !settings.auto_create_issues })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.auto_create_issues ? 'bg-purple-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.auto_create_issues ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Auto Sync */}
                <div className="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg border border-gray-600">
                  <div className="flex-1">
                    <h4 className="font-medium text-white">Auto-sync with Repository</h4>
                    <p className="text-sm text-gray-400 mt-1">
                      Keep issues synchronized with repository issues/tickets
                    </p>
                  </div>
                  <button
                    onClick={() => setSettings({ ...settings, auto_sync_enabled: !settings.auto_sync_enabled })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.auto_sync_enabled ? 'bg-purple-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.auto_sync_enabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>

              <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <div className="flex items-start space-x-2">
                  <span className="text-blue-400">ℹ️</span>
                  <div>
                    <h4 className="text-sm font-medium text-blue-400">MCP Integration Available</h4>
                    <p className="text-xs text-gray-400 mt-1">
                      Use the Lineary MCP server with Claude Code to automate issue management directly from your IDE
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'team' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Team Settings</h3>
              <div className="text-center py-8">
                <div className="text-4xl mb-2">👥</div>
                <p className="text-gray-400">Team management features coming soon</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-700/50 bg-gray-800/30">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={saveSettings}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg font-medium transition-colors"
          >
            {loading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ProjectSettings