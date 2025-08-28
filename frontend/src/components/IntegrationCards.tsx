// ABOUTME: Integration cards component for OAuth connections
// ABOUTME: Visual cards for GitHub, GitLab, BitBucket, and Slack integrations

import React, { useState } from 'react'
import axios from 'axios'
import { API_URL } from '../App'

interface Props {
  projectId: string
  currentIntegrations?: {
    github?: boolean
    gitlab?: boolean
    bitbucket?: boolean
    slack?: boolean
  }
}

const IntegrationCards: React.FC<Props> = ({ projectId, currentIntegrations = {} }) => {
  const [connecting, setConnecting] = useState<string | null>(null)
  const [integrations, setIntegrations] = useState(currentIntegrations)

  const handleConnect = async (provider: 'github' | 'gitlab' | 'bitbucket' | 'slack') => {
    setConnecting(provider)
    
    try {
      // Initiate OAuth flow
      const response = await axios.post(`${API_URL}/projects/${projectId}/integrations/connect`, {
        provider
      })
      
      if (response.data.authUrl) {
        // Redirect to OAuth provider
        window.location.href = response.data.authUrl
      } else if (response.data.requiresSetup) {
        // OAuth not configured yet
        alert(response.data.message || `${provider} integration requires OAuth setup. Please contact your administrator.`)
      }
    } catch (error: any) {
      console.error(`Error connecting to ${provider}:`, error)
      const errorMessage = error.response?.data?.error || `Failed to connect to ${provider}. Please try again.`
      alert(errorMessage)
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnect = async (provider: string) => {
    if (!confirm(`Are you sure you want to disconnect ${provider}?`)) {
      return
    }
    
    try {
      await axios.delete(`${API_URL}/projects/${projectId}/integrations/${provider}`)
      setIntegrations({ ...integrations, [provider]: false })
    } catch (error) {
      console.error(`Error disconnecting ${provider}:`, error)
      alert(`Failed to disconnect ${provider}`)
    }
  }

  const integrationConfigs = [
    {
      id: 'github',
      name: 'GitHub',
      description: 'Connect your GitHub repositories for seamless issue tracking and PR management',
      icon: (
        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
        </svg>
      ),
      color: 'from-gray-700 to-gray-900',
      features: ['Repository sync', 'Issue tracking', 'PR status updates', 'Webhook notifications']
    },
    {
      id: 'gitlab',
      name: 'GitLab',
      description: 'Integrate with GitLab for comprehensive DevOps workflows and issue management',
      icon: (
        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
          <path d="M4.845.904c-.435 0-.82.28-.955.692C2.639 5.449 1.246 9.728 1.246 12c0 2.272 1.393 6.551 2.644 10.404.135.412.52.692.955.692.435 0 .82-.28.955-.692 1.251-3.853 2.644-8.132 2.644-10.404 0-2.272-1.393-6.551-2.644-10.404C5.665 1.184 5.28.904 4.845.904zM22.755 12c0 2.272-1.393 6.551-2.644 10.404-.135.412-.52.692-.955.692-.435 0-.82-.28-.955-.692-1.251-3.853-2.644-8.132-2.644-10.404 0-2.272 1.393-6.551 2.644-10.404.135-.412.52-.692.955-.692.435 0 .82.28.955.692C21.362 5.449 22.755 9.728 22.755 12zM12 .904c-.435 0-.82.28-.955.692-1.251 3.853-2.644 8.132-2.644 10.404 0 2.272 1.393 6.551 2.644 10.404.135.412.52.692.955.692.435 0 .82-.28.955-.692 1.251-3.853 2.644-8.132 2.644-10.404 0-2.272-1.393-6.551-2.644-10.404C12.82 1.184 12.435.904 12 .904z"/>
        </svg>
      ),
      color: 'from-orange-500 to-orange-700',
      features: ['Merge request tracking', 'Pipeline status', 'Issue sync', 'GitLab CI/CD integration']
    },
    {
      id: 'bitbucket',
      name: 'Bitbucket',
      description: 'Connect Bitbucket repositories for Atlassian ecosystem integration',
      icon: (
        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3.429 5.214c-.188 0-.365.071-.498.2a.68.68 0 00-.204.481c0 .025.002.051.007.076l3.258 14.457c.07.299.338.518.645.528h10.686c.237 0 .453-.137.552-.35l3.263-14.443a.678.678 0 00-.666-.758.68.68 0 00-.142.015L3.571 5.229a.686.686 0 00-.142-.015zm8.571 9.429H8.571l-.857-4.286h5.143l-.857 4.286z"/>
        </svg>
      ),
      color: 'from-blue-600 to-blue-800',
      features: ['Repository linking', 'Pull request tracking', 'Commit status', 'Jira integration']
    },
    {
      id: 'slack',
      name: 'Slack',
      description: 'Get real-time notifications and updates in your Slack workspace',
      icon: (
        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
          <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
        </svg>
      ),
      color: 'from-purple-600 to-pink-600',
      features: ['Channel notifications', 'Issue updates', 'Sprint reminders', 'Custom slash commands']
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {integrationConfigs.map((integration) => {
        const isConnected = integrations[integration.id as keyof typeof integrations]
        
        return (
          <div
            key={integration.id}
            className={`relative overflow-hidden rounded-xl border ${
              isConnected ? 'border-green-500/50 bg-green-900/10' : 'border-gray-700 bg-gray-800/50'
            } hover:shadow-xl transition-all duration-300`}
          >
            {/* Background Gradient */}
            <div className={`absolute inset-0 bg-gradient-to-br ${integration.color} opacity-10`} />
            
            {/* Content */}
            <div className="relative p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className={`p-3 rounded-lg bg-gradient-to-br ${integration.color} text-white`}>
                    {integration.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                      <span>{integration.name}</span>
                      {isConnected && (
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
                          Connected
                        </span>
                      )}
                    </h3>
                    <p className="text-sm text-gray-400 mt-1">
                      {integration.description}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Features */}
              <div className="mb-6">
                <div className="flex flex-wrap gap-2">
                  {integration.features.map((feature, index) => (
                    <span
                      key={index}
                      className="text-xs px-2 py-1 bg-gray-700/50 text-gray-300 rounded-full"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
              
              {/* Action Button */}
              <div className="flex justify-end">
                {isConnected ? (
                  <button
                    onClick={() => handleDisconnect(integration.id)}
                    className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg font-medium transition-colors border border-red-600/30"
                  >
                    Disconnect
                  </button>
                ) : (
                  <button
                    onClick={() => handleConnect(integration.id as any)}
                    disabled={connecting === integration.id}
                    className={`px-4 py-2 bg-gradient-to-r ${integration.color} hover:opacity-90 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {connecting === integration.id ? (
                      <span className="flex items-center space-x-2">
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span>Connecting...</span>
                      </span>
                    ) : (
                      'Connect'
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default IntegrationCards