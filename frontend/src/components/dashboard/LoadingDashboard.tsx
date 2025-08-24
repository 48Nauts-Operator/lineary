import React from 'react'
import { motion } from 'framer-motion'
import { Brain, Loader2 } from 'lucide-react'

const LoadingDashboard: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Loading Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <div className="flex items-center justify-center mb-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="p-3 bg-gradient-to-r from-betty-500 to-purple-600 rounded-xl mr-4"
          >
            <Brain className="w-8 h-8 text-white" />
          </motion.div>
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">
              Loading Intelligence Dashboard
            </h1>
            <p className="text-xl text-white/80">
              Gathering Claude's extended brain data...
            </p>
          </div>
        </div>
        
        <div className="flex items-center justify-center space-x-2">
          <Loader2 className="w-5 h-5 text-white/60 animate-spin" />
          <span className="text-white/60">Analyzing knowledge patterns</span>
        </div>
      </motion.div>

      {/* Hero Metrics Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card rounded-2xl p-6"
          >
            <div className="animate-pulse">
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 bg-gray-300 rounded-lg"></div>
                <div className="w-4 h-4 bg-gray-300 rounded"></div>
              </div>
              <div className="w-20 h-8 bg-gray-300 rounded mb-2"></div>
              <div className="w-24 h-4 bg-gray-300 rounded mb-4"></div>
              <div className="flex items-center justify-between">
                <div className="w-16 h-4 bg-gray-300 rounded"></div>
                <div className="flex space-x-1">
                  {[...Array(7)].map((_, j) => (
                    <div key={j} className="w-1 h-4 bg-gray-300 rounded"></div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main Content Grid Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Knowledge Growth Chart Skeleton */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="glass-card rounded-2xl p-6"
          >
            <div className="animate-pulse">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-lg"></div>
                  <div>
                    <div className="w-40 h-5 bg-gray-300 rounded mb-2"></div>
                    <div className="w-60 h-3 bg-gray-300 rounded"></div>
                  </div>
                </div>
                <div className="w-20 h-6 bg-gray-300 rounded-full"></div>
              </div>
              <div className="w-full h-64 bg-gray-300 rounded mb-6"></div>
              <div className="grid grid-cols-5 gap-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="w-full h-16 bg-gray-300 rounded"></div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Network Skeleton */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="glass-card rounded-2xl p-6"
          >
            <div className="animate-pulse">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-lg"></div>
                  <div>
                    <div className="w-48 h-5 bg-gray-300 rounded mb-2"></div>
                    <div className="w-64 h-3 bg-gray-300 rounded"></div>
                  </div>
                </div>
              </div>
              <div className="w-full h-64 bg-gray-300 rounded mb-6"></div>
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="w-full h-16 bg-gray-300 rounded"></div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Column */}
        <div className="space-y-8">
          {/* Activity Feed Skeleton */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="glass-card rounded-2xl p-6"
          >
            <div className="animate-pulse">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-lg"></div>
                  <div>
                    <div className="w-32 h-5 bg-gray-300 rounded mb-2"></div>
                    <div className="w-40 h-3 bg-gray-300 rounded"></div>
                  </div>
                </div>
                <div className="w-16 h-6 bg-gray-300 rounded-full"></div>
              </div>
              <div className="space-y-3">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="w-full h-16 bg-gray-300 rounded"></div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Intelligence Metrics Skeleton */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="glass-card rounded-2xl p-6"
          >
            <div className="animate-pulse">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-lg"></div>
                  <div>
                    <div className="w-36 h-5 bg-gray-300 rounded mb-2"></div>
                    <div className="w-44 h-3 bg-gray-300 rounded"></div>
                  </div>
                </div>
                <div className="w-12 h-8 bg-gray-300 rounded"></div>
              </div>
              <div className="w-full h-24 bg-gray-300 rounded mb-6"></div>
              <div className="space-y-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="w-full h-16 bg-gray-300 rounded"></div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Loading Messages */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="text-center"
      >
        <div className="glass-card rounded-2xl p-6 max-w-md mx-auto">
          <div className="flex items-center justify-center space-x-3">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="w-2 h-2 bg-betty-400 rounded-full"
            />
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
              className="w-2 h-2 bg-purple-400 rounded-full"
            />
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
              className="w-2 h-2 bg-pink-400 rounded-full"
            />
          </div>
          <p className="text-sm text-gray-600 mt-3">
            Preparing stunning visualizations...
          </p>
        </div>
      </motion.div>
    </div>
  )
}

export default LoadingDashboard