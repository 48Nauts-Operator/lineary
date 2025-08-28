// ABOUTME: Centralized error monitoring and reporting component for BETTY dashboard
// ABOUTME: Tracks API errors, service health, and provides debugging information

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { errorApi } from '../../services/api'
import { 
  AlertTriangle, 
  X, 
  Eye, 
  Download, 
  Trash2, 
  RefreshCw,
  Clock,
  Activity,
  Database,
  Server
} from 'lucide-react'

interface ErrorLog {
  timestamp: string
  url: string
  method: string
  status?: number
  statusText?: string
  message: string
  code?: string
  data?: any
}

interface ErrorMonitorProps {
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
}

const ErrorMonitor: React.FC<ErrorMonitorProps> = ({ 
  position = 'bottom-right' 
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [errors, setErrors] = useState<ErrorLog[]>([])
  const [errorCount, setErrorCount] = useState(0)
  const [lastErrorTime, setLastErrorTime] = useState<Date | null>(null)
  const [backendErrors, setBackendErrors] = useState<any[]>([])
  const [showBackendErrors, setShowBackendErrors] = useState(false)

  useEffect(() => {
    // Load stored errors
    loadStoredErrors()
    loadBackendErrors()

    // Set up global error handler
    window.bettyErrorHandler = (errorInfo: ErrorLog) => {
      setErrors(prev => [errorInfo, ...prev.slice(0, 19)]) // Keep max 20 errors
      setErrorCount(prev => prev + 1)
      setLastErrorTime(new Date())
    }

    // Clean up on unmount
    return () => {
      delete window.bettyErrorHandler
    }
  }, [])

  const loadBackendErrors = async () => {
    try {
      const response = await errorApi.getErrorLogs({ limit: 20, since_hours: 24 })
      setBackendErrors(response.data?.logs || [])
    } catch (e) {
      console.debug('Could not load backend errors:', e)
    }
  }

  const loadStoredErrors = () => {
    try {
      const stored = localStorage.getItem('betty_api_errors')
      if (stored) {
        const parsedErrors = JSON.parse(stored)
        setErrors(parsedErrors)
        setErrorCount(parsedErrors.length)
        if (parsedErrors.length > 0) {
          setLastErrorTime(new Date(parsedErrors[0].timestamp))
        }
      }
    } catch (e) {
      console.warn('Could not load stored errors:', e)
    }
  }

  const clearErrors = () => {
    setErrors([])
    setErrorCount(0)
    setLastErrorTime(null)
    localStorage.removeItem('betty_api_errors')
  }

  const downloadErrorLog = () => {
    const data = {
      generated: new Date().toISOString(),
      totalErrors: errors.length,
      errors: errors
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `betty-errors-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getErrorIcon = (error: ErrorLog) => {
    if (error.message?.includes('Database') || error.url?.includes('database')) return Database
    if (error.status && error.status >= 500) return Server
    return AlertTriangle
  }

  const getErrorSeverity = (error: ErrorLog) => {
    if (error.status && error.status >= 500) return 'high'
    if (error.status === 404) return 'medium'
    if (error.code === 'NETWORK_ERROR') return 'high'
    return 'low'
  }

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4'
  }

  return (
    <div className={`fixed ${positionClasses[position]} z-50`}>
      {/* Error Counter Badge */}
      <AnimatePresence>
        {errorCount > 0 && !isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            onClick={() => setIsOpen(true)}
            className="mb-4 bg-error-500 hover:bg-error-600 text-white rounded-full p-3 shadow-lg transition-colors relative"
          >
            <AlertTriangle className="w-5 h-5" />
            <span className="absolute -top-2 -right-2 bg-error-600 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">
              {errorCount}
            </span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Error Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            className="bg-white rounded-xl shadow-2xl border border-gray-200 w-96 max-h-[600px] overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b bg-gray-50">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-error-500" />
                <h3 className="font-semibold text-gray-800">Error Monitor</h3>
                {errorCount > 0 && (
                  <span className="bg-error-100 text-error-700 px-2 py-1 rounded-full text-xs">
                    {errorCount} errors
                  </span>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={downloadErrorLog}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                  title="Download error log"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button
                  onClick={clearErrors}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                  title="Clear errors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Error List */}
            <div className="max-h-96 overflow-y-auto">
              {errors.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Eye className="w-8 h-8 mx-auto mb-3 text-gray-400" />
                  <p className="text-sm">No errors detected</p>
                  <p className="text-xs text-gray-400 mt-1">BETTY services are running smoothly</p>
                </div>
              ) : (
                <div className="space-y-1 p-2">
                  {errors.map((error, index) => {
                    const ErrorIcon = getErrorIcon(error)
                    const severity = getErrorSeverity(error)
                    
                    return (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={`p-3 rounded-lg border-l-4 ${
                          severity === 'high' ? 'border-error-500 bg-error-50' :
                          severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                          'border-gray-400 bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <ErrorIcon className={`w-4 h-4 mt-0.5 ${
                            severity === 'high' ? 'text-error-600' :
                            severity === 'medium' ? 'text-yellow-600' :
                            'text-gray-600'
                          }`} />
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="text-xs font-medium text-gray-800 uppercase">
                                {error.method}
                              </span>
                              {error.status && (
                                <span className={`text-xs px-2 py-0.5 rounded ${
                                  error.status >= 500 ? 'bg-error-100 text-error-700' :
                                  error.status === 404 ? 'bg-yellow-100 text-yellow-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {error.status}
                                </span>
                              )}
                            </div>
                            
                            <p className="text-sm text-gray-900 mb-1 truncate" title={error.message}>
                              {error.message}
                            </p>
                            
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <span className="truncate" title={error.url}>
                                {error.url.split('/').slice(-2).join('/')}
                              </span>
                              <div className="flex items-center space-x-1">
                                <Clock className="w-3 h-3" />
                                <span>
                                  {new Date(error.timestamp).toLocaleTimeString()}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Footer */}
            {lastErrorTime && (
              <div className="p-3 border-t bg-gray-50 text-xs text-gray-600">
                <div className="flex items-center justify-between">
                  <span>Last error: {lastErrorTime.toLocaleString()}</span>
                  <button
                    onClick={loadStoredErrors}
                    className="flex items-center space-x-1 text-betty-600 hover:text-betty-700 transition-colors"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Refresh</span>
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ErrorMonitor