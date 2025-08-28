// ABOUTME: Enhanced error state component with detailed error information and diagnostics
// ABOUTME: Provides comprehensive error details, troubleshooting steps, and service status

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  AlertTriangle, 
  RefreshCw, 
  Wifi, 
  Server,
  Database,
  Activity,
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { healthApi } from '../../services/api'

interface DetailedErrorStateProps {
  error?: any
  onRetry?: () => void
  showDiagnostics?: boolean
  serviceName?: string
}

interface ServiceStatus {
  name: string
  status: 'healthy' | 'unhealthy' | 'unknown'
  endpoint: string
  responseTime?: number
  lastChecked: Date
  error?: string
}

const DetailedErrorState: React.FC<DetailedErrorStateProps> = ({ 
  error, 
  onRetry, 
  showDiagnostics = true,
  serviceName = "BETTY Memory API"
}) => {
  const [expanded, setExpanded] = useState(false)
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus[]>([])
  const [checking, setChecking] = useState(false)

  // Auto-check service status on mount
  useEffect(() => {
    if (showDiagnostics) {
      checkServiceStatus()
    }
  }, [showDiagnostics])

  const checkServiceStatus = async () => {
    setChecking(true)
    const services: ServiceStatus[] = []
    
    // Use relative paths for nginx proxy compatibility
    
    try {
      const start = Date.now()
      await healthApi.checkHealth()
      const responseTime = Date.now() - start
      
      services.push({
        name: 'BETTY Memory API',
        status: 'healthy',
        endpoint: '/api/health',
        responseTime,
        lastChecked: new Date()
      })
    } catch (err: any) {
      services.push({
        name: 'BETTY Memory API',
        status: 'unhealthy',
        endpoint: '/api/health',
        lastChecked: new Date(),
        error: err.message || 'Service unavailable'
      })
    }

    // Check additional services using the correct base URL
    const additionalChecks = [
      { name: 'Analytics Service', endpoint: '/api/analytics/dashboard-summary' },
      { name: 'Knowledge Service', endpoint: '/api/knowledge/search' },
      { name: 'Sessions Service', endpoint: '/api/sessions' }
    ]

    for (const service of additionalChecks) {
      try {
        const start = Date.now()
        const response = await fetch(service.endpoint)
        const responseTime = Date.now() - start
        
        services.push({
          name: service.name,
          status: response.ok ? 'healthy' : 'unhealthy',
          endpoint: service.endpoint,
          responseTime,
          lastChecked: new Date(),
          error: !response.ok ? `HTTP ${response.status}` : undefined
        })
      } catch (err: any) {
        services.push({
          name: service.name,
          status: 'unhealthy',
          endpoint: service.endpoint,
          lastChecked: new Date(),
          error: err.message || 'Connection failed'
        })
      }
    }

    setServiceStatus(services)
    setChecking(false)
  }

  const getErrorCategory = () => {
    if (error?.response?.status === 404) return 'Service Not Found'
    if (error?.response?.status >= 500) return 'Server Error'
    if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network')) return 'Network Error'
    if (error?.message?.includes('timeout')) return 'Timeout Error'
    if (error?.message?.includes('Database')) return 'Database Error'
    return 'Application Error'
  }

  const getDetailedErrorMessage = () => {
    const category = getErrorCategory()
    
    switch (category) {
      case 'Service Not Found':
        return `${serviceName} endpoint not found. The service may not be running or the URL may be incorrect.`
      case 'Server Error':
        return `${serviceName} is experiencing internal issues. This is typically a backend problem.`
      case 'Network Error':
        return `Cannot connect to ${serviceName}. Check your network connection and service availability.`
      case 'Timeout Error':
        return `Request to ${serviceName} timed out. The service may be overloaded or unresponsive.`
      case 'Database Error':
        return `Database connectivity issues detected. Backend services may be degraded.`
      default:
        return error?.message || `${serviceName} encountered an unexpected error.`
    }
  }

  const getErrorIcon = () => {
    const category = getErrorCategory()
    switch (category) {
      case 'Network Error': return Wifi
      case 'Server Error': return Server
      case 'Database Error': return Database
      default: return AlertTriangle
    }
  }

  const copyErrorDetails = () => {
    const errorDetails = {
      timestamp: new Date().toISOString(),
      service: serviceName,
      category: getErrorCategory(),
      message: error?.message,
      status: error?.response?.status,
      statusText: error?.response?.statusText,
      url: error?.config?.url,
      serviceStatus: serviceStatus
    }
    
    navigator.clipboard.writeText(JSON.stringify(errorDetails, null, 2))
  }

  const ErrorIcon = getErrorIcon()

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-2xl p-8 max-w-2xl mx-auto"
      >
        {/* Error Header */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="text-center mb-6"
        >
          <div className="w-16 h-16 mx-auto bg-error-100 rounded-full flex items-center justify-center mb-4">
            <ErrorIcon className="w-8 h-8 text-error-600" />
          </div>
          
          <h2 className="text-xl font-semibold text-gray-700 mb-2">
            {serviceName} Unavailable
          </h2>
          
          <div className="inline-flex items-center px-3 py-1 bg-error-100 text-error-700 rounded-full text-sm font-medium mb-4">
            <AlertCircle className="w-4 h-4 mr-2" />
            {getErrorCategory()}
          </div>
          
          <p className="text-gray-600 text-sm leading-relaxed max-w-md mx-auto">
            {getDetailedErrorMessage()}
          </p>
        </motion.div>

        {/* Error Details Panel */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mb-6"
          >
            <div className="bg-error-50 border border-error-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-error-800">Error Details</h3>
                <button
                  onClick={copyErrorDetails}
                  className="flex items-center space-x-1 text-xs text-error-600 hover:text-error-700 transition-colors"
                >
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </button>
              </div>
              
              <div className="space-y-2 text-xs text-error-700 font-mono">
                {error.response?.status && (
                  <div>Status: {error.response.status} {error.response.statusText}</div>
                )}
                {error.config?.url && (
                  <div>Endpoint: {error.config.url}</div>
                )}
                {error.code && (
                  <div>Error Code: {error.code}</div>
                )}
                <div>Timestamp: {new Date().toISOString()}</div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Service Status Dashboard */}
        {showDiagnostics && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="mb-6"
          >
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center justify-between w-full p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Service Diagnostics</span>
              </div>
              {expanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>

            <AnimatePresence>
              {expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-3 space-y-2"
                >
                  {checking ? (
                    <div className="flex items-center justify-center p-4">
                      <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                      <span className="text-sm text-gray-600">Checking services...</span>
                    </div>
                  ) : (
                    serviceStatus.map((service, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-white rounded border">
                        <div className="flex items-center space-x-3">
                          {service.status === 'healthy' ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <XCircle className="w-4 h-4 text-error-500" />
                          )}
                          <div>
                            <div className="text-sm font-medium text-gray-700">{service.name}</div>
                            <div className="text-xs text-gray-500">{service.endpoint}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          {service.responseTime && (
                            <div className="text-xs text-gray-600">{service.responseTime}ms</div>
                          )}
                          {service.error && (
                            <div className="text-xs text-error-600">{service.error}</div>
                          )}
                          <div className="text-xs text-gray-500">
                            <Clock className="w-3 h-3 inline mr-1" />
                            {service.lastChecked.toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                  
                  <button
                    onClick={checkServiceStatus}
                    className="w-full flex items-center justify-center space-x-2 p-2 text-sm text-gray-600 hover:text-gray-700 hover:bg-gray-50 rounded transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Refresh Status</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="flex flex-col space-y-3"
        >
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-betty-500 to-purple-600 hover:from-betty-600 hover:to-purple-700 text-white rounded-lg transition-all duration-200 hover:shadow-lg"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry Loading</span>
            </button>
          )}

          <div className="flex space-x-3">
            <button
              onClick={() => window.location.reload()}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-600 hover:text-gray-700 hover:border-gray-400 rounded-lg transition-colors"
            >
              Refresh Page
            </button>
            
            <button
              onClick={() => window.open('http://localhost:8001/docs', '_blank')}
              className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 border border-gray-300 text-gray-600 hover:text-gray-700 hover:border-gray-400 rounded-lg transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              <span>API Docs</span>
            </button>
          </div>
        </motion.div>

        {/* Troubleshooting Tips */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-8 pt-6 border-t border-gray-200"
        >
          <h3 className="text-sm font-medium text-gray-600 mb-3">
            Troubleshooting Steps:
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-gray-500">
            <div className="space-y-1">
              <div>• Check if Docker containers are running:</div>
              <code className="block bg-gray-100 p-1 rounded">docker-compose ps</code>
            </div>
            <div className="space-y-1">
              <div>• Verify API endpoint:</div>
              <code className="block bg-gray-100 p-1 rounded">curl http://localhost:8001/health</code>
            </div>
            <div className="space-y-1">
              <div>• Check container logs:</div>
              <code className="block bg-gray-100 p-1 rounded">docker logs betty_memory_api</code>
            </div>
            <div className="space-y-1">
              <div>• Restart services:</div>
              <code className="block bg-gray-100 p-1 rounded">docker-compose restart</code>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default DetailedErrorState