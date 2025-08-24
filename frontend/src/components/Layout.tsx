import React from 'react'
import { motion } from 'framer-motion'
import { useLocation, Link } from 'react-router-dom'
import { Brain, Activity, Zap, RefreshCw, BarChart3, Target, GitBranch, Settings, ClipboardList } from 'lucide-react'
import { useRefreshCache } from '../hooks/useAnalytics'

interface LayoutProps {
  children: React.ReactNode
  systemHealth?: any
}

const Layout: React.FC<LayoutProps> = ({ children, systemHealth }) => {
  const refreshCache = useRefreshCache()
  const location = useLocation()

  const handleRefresh = () => {
    refreshCache.mutate()
  }

  return (
    <div className="min-h-screen bg-neural-network">
      {/* Header */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="bg-black/40 backdrop-blur-xl border-b border-white/5 sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Title */}
            <div className="flex items-center space-x-4">
              <motion.div
                whileHover={{ rotate: 360 }}
                transition={{ duration: 0.8 }}
                className="p-2 bg-gradient-to-r from-betty-500 to-purple-600 rounded-lg"
              >
                <Brain className="w-6 h-6 text-white" />
              </motion.div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  BETTY Analytics
                </h1>
                <p className="text-xs text-white/70">
                  Claude's Extended Brain
                </p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              <NavigationLink to="/" icon={BarChart3} label="Dashboard" />
              <NavigationLink to="/real-data" icon={Activity} label="Live Data" />
              <NavigationLink to="/energy" icon={Zap} label="Energy Grid" />
              <NavigationLink to="/real-radar" icon={Target} label="Knowledge Radar" />
              <NavigationLink to="/knowledge-visualization" icon={Brain} label="Knowledge Viz" />
              <NavigationLink to="/patterns" icon={GitBranch} label="Patterns" />
              <NavigationLink to="/tasks" icon={ClipboardList} label="Tasks" />
              <NavigationLink to="/admin" icon={Settings} label="Admin" />
            </nav>

            {/* Status and Actions */}
            <div className="flex items-center space-x-4">
              {/* System Health Indicator */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  systemHealth?.status === 'healthy' 
                    ? 'bg-success-500 animate-pulse' 
                    : 'bg-warning-500'
                }`} />
                <span className="text-sm text-white/80">
                  {systemHealth?.status === 'healthy' ? 'Operational' : 'Checking...'}
                </span>
              </div>

              {/* Refresh Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleRefresh}
                disabled={refreshCache.isPending}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 text-white ${
                  refreshCache.isPending ? 'animate-spin' : ''
                }`} />
              </motion.button>

              {/* Activity Indicator */}
              <div className="flex items-center space-x-1">
                <Activity className="w-4 h-4 text-white/60" />
                <div className="flex space-x-1">
                  <div className="w-1 h-4 bg-betty-400 rounded-full animate-pulse" />
                  <div className="w-1 h-3 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                  <div className="w-1 h-2 bg-pink-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="glass-morphism border-t border-white/10 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Zap className="w-4 h-4 text-betty-400" />
              <span className="text-sm text-white/70">
                Powered by Claude's temporal knowledge graphs
              </span>
            </div>
            <div className="flex items-center space-x-6 text-xs text-white/50">
              <span>Neo4j + Graphiti</span>
              <span>•</span>
              <span>Qdrant Vector DB</span>
              <span>•</span>
              <span>Real-time Intelligence</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Navigation Link Component
interface NavigationLinkProps {
  to: string
  icon: React.ComponentType<any>
  label: string
}

const NavigationLink: React.FC<NavigationLinkProps> = ({ to, icon: Icon, label }) => {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link to={to}>
      <motion.div
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
          isActive
            ? 'bg-white/20 text-white'
            : 'text-white/70 hover:text-white hover:bg-white/10'
        }`}
      >
        <Icon className="w-4 h-4" />
        <span className="text-sm font-medium">{label}</span>
      </motion.div>
    </Link>
  )
}

export default Layout