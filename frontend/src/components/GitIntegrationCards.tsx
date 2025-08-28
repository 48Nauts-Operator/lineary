// ABOUTME: Git integration cards component for OAuth authentication
// ABOUTME: Handles GitHub and GitLab repository connections with OAuth flow

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

interface GitIntegrationCardsProps {
  projectId: string
  onConnectionChange?: () => void
}

interface GitConnection {
  provider: 'github' | 'gitlab'
  connected: boolean
  username?: string
  email?: string
  repositories?: Repository[]
  selectedRepo?: string
  accessToken?: string
  refreshToken?: string
  expiresAt?: string
}

interface Repository {
  id: string
  name: string
  fullName: string
  url: string
  defaultBranch: string
  private: boolean
}

const GitIntegrationCards: React.FC<GitIntegrationCardsProps> = ({ projectId, onConnectionChange }) => {
  const [githubConnection, setGithubConnection] = useState<GitConnection>({
    provider: 'github',
    connected: false
  })
  const [gitlabConnection, setGitlabConnection] = useState<GitConnection>({
    provider: 'gitlab',
    connected: false
  })
  const [loading, setLoading] = useState(false)
  const [showRepoSelector, setShowRepoSelector] = useState<'github' | 'gitlab' | null>(null)

  useEffect(() => {
    loadConnections()
    checkOAuthCallback()
  }, [projectId])

  const loadConnections = async () => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/git-connections`)
      const { github, gitlab } = response.data
      
      if (github) setGithubConnection(github)
      if (gitlab) setGitlabConnection(gitlab)
    } catch (error) {
      console.error('Error loading Git connections:', error)
    }
  }

  const checkOAuthCallback = () => {
    // Check if we're returning from OAuth flow
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const state = urlParams.get('state')
    const provider = urlParams.get('provider')

    if (code && state) {
      handleOAuthCallback(provider as 'github' | 'gitlab', code, state)
    }
  }

  const handleOAuthCallback = async (provider: 'github' | 'gitlab', code: string, state: string) => {
    setLoading(true)
    try {
      const response = await axios.post(`/api/auth/oauth/callback`, {
        provider,
        code,
        state,
        projectId
      })

      if (response.data.success) {
        toast.success(`Successfully connected to ${provider === 'github' ? 'GitHub' : 'GitLab'}`)
        loadConnections()
        onConnectionChange?.()
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)
      }
    } catch (error) {
      toast.error(`Failed to complete ${provider} authentication`)
    } finally {
      setLoading(false)
    }
  }

  const initiateOAuth = async (provider: 'github' | 'gitlab') => {
    setLoading(true)
    try {
      const response = await axios.post(`/api/auth/oauth/initiate`, {
        provider,
        projectId,
        redirectUri: `${window.location.origin}/projects/${projectId}/settings`
      })

      if (response.data.authUrl) {
        // Redirect to OAuth provider
        window.location.href = response.data.authUrl
      }
    } catch (error) {
      toast.error(`Failed to initiate ${provider} authentication`)
      setLoading(false)
    }
  }

  const disconnectProvider = async (provider: 'github' | 'gitlab') => {
    setLoading(true)
    try {
      await axios.delete(`/api/projects/${projectId}/git-connections/${provider}`)
      
      if (provider === 'github') {
        setGithubConnection({ provider: 'github', connected: false })
      } else {
        setGitlabConnection({ provider: 'gitlab', connected: false })
      }
      
      toast.success(`Disconnected from ${provider === 'github' ? 'GitHub' : 'GitLab'}`)
      onConnectionChange?.()
    } catch (error) {
      toast.error(`Failed to disconnect from ${provider}`)
    } finally {
      setLoading(false)
    }
  }

  const selectRepository = async (provider: 'github' | 'gitlab', repoId: string) => {
    setLoading(true)
    try {
      await axios.post(`/api/projects/${projectId}/git-connections/${provider}/select-repo`, {
        repositoryId: repoId
      })
      
      toast.success('Repository selected successfully')
      loadConnections()
      setShowRepoSelector(null)
      onConnectionChange?.()
    } catch (error) {
      toast.error('Failed to select repository')
    } finally {
      setLoading(false)
    }
  }

  const refreshRepositories = async (provider: 'github' | 'gitlab') => {
    setLoading(true)
    try {
      const response = await axios.post(`/api/projects/${projectId}/git-connections/${provider}/refresh-repos`)
      
      if (provider === 'github') {
        setGithubConnection(prev => ({ ...prev, repositories: response.data.repositories }))
      } else {
        setGitlabConnection(prev => ({ ...prev, repositories: response.data.repositories }))
      }
      
      toast.success('Repository list refreshed')
    } catch (error) {
      toast.error('Failed to refresh repositories')
    } finally {
      setLoading(false)
    }
  }

  const renderConnectionCard = (
    connection: GitConnection,
    icon: string,
    title: string,
    bgColor: string,
    hoverColor: string
  ) => {
    const isGithub = connection.provider === 'github'
    
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden">
        {/* Header */}
        <div className={`p-6 ${bgColor} bg-opacity-10 border-b border-gray-700/50`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`text-3xl ${isGithub ? 'text-gray-100' : 'text-orange-500'}`}>
                {icon}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="text-sm text-gray-400">
                  {connection.connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
            </div>
            {connection.connected && (
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-sm text-green-400">Active</span>
              </div>
            )}
          </div>
        </div>

        {/* Body */}
        <div className="p-6">
          {connection.connected ? (
            <div className="space-y-4">
              {/* User Info */}
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center">
                  <span className="text-gray-400">👤</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-white">
                    {connection.username || 'Unknown User'}
                  </p>
                  <p className="text-xs text-gray-400">{connection.email || 'No email'}</p>
                </div>
              </div>

              {/* Selected Repository */}
              {connection.selectedRepo ? (
                <div className="bg-gray-700/30 rounded-lg p-3">
                  <p className="text-xs text-gray-400 mb-1">Selected Repository</p>
                  <p className="text-sm font-medium text-white">
                    {connection.repositories?.find(r => r.id === connection.selectedRepo)?.fullName}
                  </p>
                </div>
              ) : (
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                  <p className="text-sm text-yellow-400">No repository selected</p>
                </div>
              )}

              {/* Actions */}
              <div className="flex space-x-2">
                <button
                  onClick={() => setShowRepoSelector(connection.provider)}
                  disabled={loading}
                  className={`flex-1 px-3 py-2 ${bgColor} bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg transition-colors text-sm font-medium disabled:opacity-50`}
                >
                  {connection.selectedRepo ? 'Change Repository' : 'Select Repository'}
                </button>
                <button
                  onClick={() => refreshRepositories(connection.provider)}
                  disabled={loading}
                  className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
                  title="Refresh repositories"
                >
                  🔄
                </button>
                <button
                  onClick={() => disconnectProvider(connection.provider)}
                  disabled={loading}
                  className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors disabled:opacity-50"
                >
                  Disconnect
                </button>
              </div>

              {/* Repository Selector Modal */}
              {showRepoSelector === connection.provider && (
                <div className="mt-4 border-t border-gray-700/50 pt-4">
                  <h4 className="text-sm font-medium text-white mb-3">Select Repository</h4>
                  <div className="max-h-60 overflow-y-auto space-y-2">
                    {connection.repositories?.map(repo => (
                      <button
                        key={repo.id}
                        onClick={() => selectRepository(connection.provider, repo.id)}
                        className={`w-full text-left p-3 rounded-lg border transition-all ${
                          connection.selectedRepo === repo.id
                            ? 'bg-purple-500/20 border-purple-500'
                            : 'bg-gray-700/30 border-gray-600 hover:bg-gray-700/50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-white">{repo.name}</p>
                            <p className="text-xs text-gray-400">{repo.fullName}</p>
                          </div>
                          {repo.private && (
                            <span className="text-xs bg-gray-600 text-gray-300 px-2 py-1 rounded">
                              Private
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setShowRepoSelector(null)}
                    className="mt-3 w-full px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-400">
                Connect your {title} account to enable repository integration, automatic issue sync, and commit tracking.
              </p>
              
              <div className="space-y-2 text-sm">
                <div className="flex items-start space-x-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span className="text-gray-300">Automatic issue synchronization</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span className="text-gray-300">Pull request tracking</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span className="text-gray-300">Commit linking to issues</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span className="text-gray-300">Real-time webhook updates</span>
                </div>
              </div>

              <button
                onClick={() => initiateOAuth(connection.provider)}
                disabled={loading}
                className={`w-full px-4 py-3 ${bgColor} ${hoverColor} text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2`}
              >
                {loading ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    <span>Connecting...</span>
                  </>
                ) : (
                  <>
                    <span>{icon}</span>
                    <span>Connect with {title}</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Footer Status */}
        {connection.connected && connection.expiresAt && (
          <div className="px-6 py-3 bg-gray-700/20 border-t border-gray-700/50">
            <p className="text-xs text-gray-400">
              Token expires: {new Date(connection.expiresAt).toLocaleDateString()}
            </p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">Repository Integration</h3>
        <p className="text-sm text-gray-400 mb-6">
          Connect your Git repositories to enable automatic synchronization and tracking
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {renderConnectionCard(
          githubConnection,
          '🐙',
          'GitHub',
          'bg-gray-900',
          'hover:bg-gray-800'
        )}
        
        {renderConnectionCard(
          gitlabConnection,
          '🦊',
          'GitLab',
          'bg-orange-900',
          'hover:bg-orange-800'
        )}
      </div>

      {/* Integration Status Summary */}
      {(githubConnection.connected || gitlabConnection.connected) && (
        <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <div className="flex items-start space-x-2">
            <span className="text-blue-400">ℹ️</span>
            <div>
              <h4 className="text-sm font-medium text-blue-400">Integration Active</h4>
              <p className="text-xs text-gray-400 mt-1">
                Your repository is now connected. Commits, pull requests, and issues will be automatically synchronized.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GitIntegrationCards