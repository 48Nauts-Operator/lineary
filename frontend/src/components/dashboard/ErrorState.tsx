import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, Wifi, Server } from 'lucide-react'

interface ErrorStateProps {
  error?: any
  onRetry?: () => void
}

const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry }) => {
  const getErrorMessage = () => {
    if (error?.response?.status === 404) {
      return "Analytics service not found. Please check if BETTY Memory API is running."
    }
    if (error?.response?.status === 500) {
      return "Internal server error. The analytics service is experiencing issues."
    }
    if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network')) {
      return "Network connection error. Please check your connection and try again."
    }
    if (error?.message) {
      return error.message
    }
    return "Unable to load dashboard data. Please try again."
  }

  const getErrorIcon = () => {
    if (error?.code === 'NETWORK_ERROR') return Wifi
    if (error?.response?.status >= 500) return Server
    return AlertTriangle
  }

  const ErrorIcon = getErrorIcon()

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-2xl p-8 max-w-md mx-auto text-center"
      >
        {/* Error Icon */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="mb-6"
        >
          <div className="w-16 h-16 mx-auto bg-error-100 rounded-full flex items-center justify-center">
            <ErrorIcon className="w-8 h-8 text-error-600" />
          </div>
        </motion.div>

        {/* Error Message */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-700 mb-2">
            Dashboard Unavailable
          </h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            {getErrorMessage()}
          </p>
        </motion.div>

        {/* Error Details (if available) */}
        {error?.response?.status && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mb-6 p-3 bg-error-50 border border-error-200 rounded-lg"
          >
            <p className="text-xs text-error-600 font-mono">
              HTTP {error.response.status}: {error.response.statusText || 'Server Error'}
            </p>
          </motion.div>
        )}

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
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

          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 border border-gray-300 text-gray-600 hover:text-gray-700 hover:border-gray-400 rounded-lg transition-colors"
          >
            Refresh Page
          </button>
        </motion.div>

        {/* Troubleshooting Tips */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-8 pt-6 border-t border-gray-200"
        >
          <h3 className="text-sm font-medium text-gray-600 mb-3">
            Troubleshooting Tips:
          </h3>
          <ul className="text-xs text-gray-500 space-y-1 text-left">
            <li>• Ensure BETTY Memory API is running on port 8001</li>
            <li>• Check if all Docker services are healthy</li>
            <li>• Verify network connectivity to the backend</li>
            <li>• Try refreshing the page in a few moments</li>
          </ul>
        </motion.div>

        {/* Service Status Indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-6 p-3 bg-gray-50 rounded-lg"
        >
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-error-500 rounded-full animate-pulse" />
            <span className="text-xs text-gray-600">
              BETTY Analytics Service: Unavailable
            </span>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default ErrorState