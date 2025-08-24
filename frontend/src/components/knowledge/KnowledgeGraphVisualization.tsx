import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  Network,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Settings,
  Filter,
  Eye,
  Target,
  Layers,
  Activity
} from 'lucide-react'
import { useKnowledgeGraph } from '../../hooks/useKnowledgeVisualization'

interface KnowledgeGraphVisualizationProps {
  focusArea?: string
}

const KnowledgeGraphVisualization: React.FC<KnowledgeGraphVisualizationProps> = ({
  focusArea
}) => {
  const [zoom, setZoom] = useState(1)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [filterType, setFilterType] = useState<string>('')
  const [minConnections, setMinConnections] = useState(0)
  const svgRef = useRef<SVGSVGElement>(null)

  const {
    data: graphData,
    isLoading,
    error,
    refetch
  } = useKnowledgeGraph(focusArea, 3, 100)

  const handleZoomIn = () => setZoom(prev => Math.min(prev * 1.2, 3))
  const handleZoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.3))
  const handleReset = () => {
    setZoom(1)
    setSelectedNode(null)
    refetch()
  }

  // Filter nodes and edges based on current filters
  const filteredNodes = graphData?.nodes.filter(node => {
    if (filterType && node.type !== filterType) return false
    if (minConnections && node.connections < minConnections) return false
    return true
  }) || []

  const filteredEdges = graphData?.edges.filter(edge =>
    filteredNodes.some(n => n.id === edge.source) &&
    filteredNodes.some(n => n.id === edge.target)
  ) || []

  const nodeTypeColors: Record<string, string> = {
    'code_repository': '#10B981',
    'code_file': '#3B82F6', 
    'documentation': '#8B5CF6',
    'pattern': '#F59E0B',
    'concept': '#EF4444',
    'dependency': '#6B7280'
  }

  const getNodeColor = (type: string): string => {
    return nodeTypeColors[type] || '#64748B'
  }

  // Calculate node positions (simplified force-directed layout)
  const calculatePositions = (nodes: any[], edges: any[], width: number, height: number) => {
    const positions = new Map()
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(width, height) * 0.3

    nodes.forEach((node, index) => {
      const angle = (index / nodes.length) * 2 * Math.PI
      const x = centerX + Math.cos(angle) * radius + (Math.random() - 0.5) * 100
      const y = centerY + Math.sin(angle) * radius + (Math.random() - 0.5) * 100
      
      positions.set(node.id, { x, y })
    })

    return positions
  }

  if (isLoading) {
    return (
      <div className="glass-morphism border border-white/10 rounded-lg p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Network className="w-12 h-12 text-betty-400 mx-auto mb-4 animate-pulse" />
            <div className="text-white font-semibold mb-2">Building Knowledge Graph</div>
            <div className="text-white/60">Analyzing relationships...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-morphism border border-red-500/20 rounded-lg p-8 text-center">
        <Network className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-red-400 text-lg font-semibold mb-2">Failed to Load Knowledge Graph</h3>
        <p className="text-white/60 mb-4">{error.message || 'An unexpected error occurred'}</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-betty-500 hover:bg-betty-600 text-white rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  const positions = calculatePositions(filteredNodes, filteredEdges, 800, 600)

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Knowledge Graph</h2>
          <p className="text-white/70">
            {filteredNodes.length} nodes • {filteredEdges.length} connections
            {focusArea && ` • Focused on: ${focusArea}`}
          </p>
        </div>

        {/* Graph Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 bg-white/5 rounded-lg p-1">
            <button
              onClick={handleZoomOut}
              className="p-2 hover:bg-white/10 rounded transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4 text-white/70" />
            </button>
            <span className="px-2 text-sm text-white/70 min-w-12 text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-2 hover:bg-white/10 rounded transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4 text-white/70" />
            </button>
          </div>

          <button
            onClick={handleReset}
            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4 text-white/70" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-morphism border border-white/10 rounded-lg p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-white/70" />
            <span className="text-sm text-white/70">Filters:</span>
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:border-betty-400"
          >
            <option value="">All Types</option>
            <option value="code_repository">Repositories</option>
            <option value="code_file">Code Files</option>
            <option value="documentation">Documentation</option>
            <option value="pattern">Patterns</option>
            <option value="concept">Concepts</option>
          </select>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-white/70">Min connections:</span>
            <input
              type="range"
              min="0"
              max="10"
              value={minConnections}
              onChange={(e) => setMinConnections(Number(e.target.value))}
              className="w-20"
            />
            <span className="text-sm text-white/70 w-8">{minConnections}</span>
          </div>
        </div>
      </div>

      {/* Main Graph Visualization */}
      <div className="glass-morphism border border-white/10 rounded-lg overflow-hidden">
        <svg
          ref={svgRef}
          width="100%"
          height="600"
          viewBox="0 0 800 600"
          className="bg-gradient-to-br from-gray-900/50 to-gray-800/50"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
        >
          {/* Define gradients and patterns */}
          <defs>
            <radialGradient id="nodeGradient" cx="30%" cy="30%">
              <stop offset="0%" stopColor="rgba(255,255,255,0.2)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0.05)" />
            </radialGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Render edges */}
          <g id="edges">
            {filteredEdges.map((edge, index) => {
              const sourcePos = positions.get(edge.source)
              const targetPos = positions.get(edge.target)
              if (!sourcePos || !targetPos) return null

              return (
                <motion.line
                  key={`edge-${index}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.3 }}
                  transition={{ delay: index * 0.01 }}
                  x1={sourcePos.x}
                  y1={sourcePos.y}
                  x2={targetPos.x}
                  y2={targetPos.y}
                  stroke={`url(#gradient-${edge.relationship_type})`}
                  strokeWidth={Math.max(1, edge.weight * 2)}
                  strokeDasharray={edge.relationship_type === 'dependency' ? '4,4' : ''}
                  className="transition-opacity duration-200"
                />
              )
            })}
          </g>

          {/* Render nodes */}
          <g id="nodes">
            {filteredNodes.map((node, index) => {
              const pos = positions.get(node.id)
              if (!pos) return null

              const isSelected = selectedNode === node.id
              const nodeRadius = Math.max(8, Math.min(20, 5 + node.connections * 2))

              return (
                <motion.g
                  key={node.id}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.02 }}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={() => setSelectedNode(isSelected ? null : node.id)}
                  className="cursor-pointer"
                >
                  {/* Node glow effect */}
                  {isSelected && (
                    <circle
                      r={nodeRadius + 8}
                      fill="none"
                      stroke={getNodeColor(node.type)}
                      strokeWidth="2"
                      opacity="0.4"
                      filter="url(#glow)"
                    />
                  )}

                  {/* Main node circle */}
                  <circle
                    r={nodeRadius}
                    fill={getNodeColor(node.type)}
                    stroke="rgba(255,255,255,0.2)"
                    strokeWidth="2"
                    opacity={isSelected ? 0.9 : 0.7}
                    className="transition-all duration-200 hover:opacity-100"
                  />

                  {/* Node label */}
                  <text
                    y={nodeRadius + 16}
                    textAnchor="middle"
                    className="text-xs fill-white/70 pointer-events-none"
                    fontSize="10"
                  >
                    {node.label.length > 12 ? node.label.slice(0, 12) + '...' : node.label}
                  </text>

                  {/* Connection count */}
                  <text
                    y="3"
                    textAnchor="middle"
                    className="text-xs fill-white font-semibold pointer-events-none"
                    fontSize="8"
                  >
                    {node.connections}
                  </text>
                </motion.g>
              )
            })}
          </g>
        </svg>
      </div>

      {/* Graph Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Network className="w-6 h-6 text-betty-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">{filteredNodes.length}</div>
          <div className="text-sm text-white/60">Nodes</div>
        </div>
        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Activity className="w-6 h-6 text-purple-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">{filteredEdges.length}</div>
          <div className="text-sm text-white/60">Connections</div>
        </div>
        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Layers className="w-6 h-6 text-pink-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {new Set(filteredNodes.map(n => n.type)).size}
          </div>
          <div className="text-sm text-white/60">Types</div>
        </div>
        <div className="glass-morphism border border-white/10 rounded-lg p-4 text-center">
          <Target className="w-6 h-6 text-green-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-white">
            {graphData?.stats?.average_connections?.toFixed(1) || '0.0'}
          </div>
          <div className="text-sm text-white/60">Avg Connections</div>
        </div>
      </div>

      {/* Selected Node Details */}
      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-morphism border border-betty-400/30 rounded-lg p-6"
        >
          {(() => {
            const node = filteredNodes.find(n => n.id === selectedNode)
            if (!node) return null

            return (
              <div>
                <h3 className="text-white font-semibold text-lg mb-3 flex items-center">
                  <div 
                    className="w-4 h-4 rounded-full mr-2"
                    style={{ backgroundColor: getNodeColor(node.type) }}
                  />
                  {node.label}
                </h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <span className="text-white/60 text-sm">Type:</span>
                    <div className="text-white capitalize">{node.type.replace('_', ' ')}</div>
                  </div>
                  <div>
                    <span className="text-white/60 text-sm">Connections:</span>
                    <div className="text-white">{node.connections}</div>
                  </div>
                </div>
                {Object.keys(node.properties).length > 0 && (
                  <div>
                    <span className="text-white/60 text-sm mb-2 block">Properties:</span>
                    <div className="bg-white/5 rounded-lg p-3">
                      <pre className="text-white/80 text-xs overflow-x-auto">
                        {JSON.stringify(node.properties, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )
          })()}
        </motion.div>
      )}
    </div>
  )
}

export default KnowledgeGraphVisualization