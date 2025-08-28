import React, { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Network, Share2, Zap, ArrowRight } from 'lucide-react'
import { CrossProjectIntelligenceData } from '../../services/api'

interface CrossProjectNetworkProps {
  data?: CrossProjectIntelligenceData
}

const CrossProjectNetwork: React.FC<CrossProjectNetworkProps> = ({ data }) => {
  const networkRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!data || !networkRef.current) return

    // Simple network visualization using CSS and DOM manipulation
    // In a real implementation, you'd use vis.js or d3.js
    const container = networkRef.current
    container.innerHTML = '' // Clear previous render

    // Create SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    svg.setAttribute('width', '100%')
    svg.setAttribute('height', '300')
    svg.setAttribute('viewBox', '0 0 600 300')
    
    // Position nodes in a circle
    const centerX = 300
    const centerY = 150
    const radius = 80
    
    data.project_nodes.forEach((node, index) => {
      const angle = (index * 2 * Math.PI) / data.project_nodes.length
      const x = centerX + radius * Math.cos(angle)
      const y = centerY + radius * Math.sin(angle)
      
      // Create node circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
      circle.setAttribute('cx', x.toString())
      circle.setAttribute('cy', y.toString())
      circle.setAttribute('r', (node.size / 2).toString())
      circle.setAttribute('fill', node.color)
      circle.setAttribute('stroke', '#ffffff')
      circle.setAttribute('stroke-width', '3')
      circle.setAttribute('opacity', '0.9')
      circle.classList.add('animate-pulse')
      
      // Create node label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
      text.setAttribute('x', x.toString())
      text.setAttribute('y', (y + 5).toString())
      text.setAttribute('text-anchor', 'middle')
      text.setAttribute('fill', '#ffffff')
      text.setAttribute('font-size', '12')
      text.setAttribute('font-weight', 'bold')
      text.textContent = node.project_name
      
      svg.appendChild(circle)
      svg.appendChild(text)
    })
    
    // Draw connections
    data.connections.forEach(connection => {
      const sourceNode = data.project_nodes.find(n => n.project_id === connection.source_project_id)
      const targetNode = data.project_nodes.find(n => n.project_id === connection.target_project_id)
      
      if (sourceNode && targetNode) {
        const sourceIndex = data.project_nodes.indexOf(sourceNode)
        const targetIndex = data.project_nodes.indexOf(targetNode)
        
        const sourceAngle = (sourceIndex * 2 * Math.PI) / data.project_nodes.length
        const targetAngle = (targetIndex * 2 * Math.PI) / data.project_nodes.length
        
        const sourceX = centerX + radius * Math.cos(sourceAngle)
        const sourceY = centerY + radius * Math.sin(sourceAngle)
        const targetX = centerX + radius * Math.cos(targetAngle)
        const targetY = centerY + radius * Math.sin(targetAngle)
        
        // Create connection line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
        line.setAttribute('x1', sourceX.toString())
        line.setAttribute('y1', sourceY.toString())
        line.setAttribute('x2', targetX.toString())
        line.setAttribute('y2', targetY.toString())
        line.setAttribute('stroke', '#60A5FA')
        line.setAttribute('stroke-width', (connection.strength * 4).toString())
        line.setAttribute('opacity', (connection.strength * 0.8).toString())
        line.setAttribute('stroke-dasharray', '5,5')
        line.classList.add('animate-pulse')
        
        svg.insertBefore(line, svg.firstChild) // Insert lines behind nodes
      }
    })
    
    container.appendChild(svg)
  }, [data])

  if (!data) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass-card rounded-2xl p-6"
      >
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg">
            <Network className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-700">
              Cross-Project Intelligence Network
            </h3>
            <p className="text-sm text-gray-500">
              {Math.round(data.network_density * 100)}% network density • 
              {data.most_connected_project} is most connected
            </p>
          </div>
        </div>
        
        {/* Connection Strength Indicator */}
        <div className="flex items-center space-x-2 bg-purple-50 px-3 py-1 rounded-full border border-purple-200">
          <Share2 className="w-3 h-3 text-purple-600" />
          <span className="text-sm font-medium text-purple-700">
            {Math.round(data.cross_project_reuse_rate * 100)}% reuse rate
          </span>
        </div>
      </div>

      {/* Network Visualization */}
      <div 
        ref={networkRef} 
        className="network-container h-64 mb-6 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100"
      >
        <div className="text-gray-500">Loading network visualization...</div>
      </div>

      {/* Hot Connection Paths */}
      <div className="space-y-3 mb-6">
        <h4 className="text-sm font-medium text-gray-600 flex items-center">
          <Zap className="w-4 h-4 mr-1 text-warning-500" />
          Hot Connection Paths
        </h4>
        {data.hot_connection_paths.map((path, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className="flex items-center justify-between p-3 bg-gradient-to-r from-warning-50 to-orange-50 rounded-lg border border-warning-200"
          >
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {path.pattern}
                </span>
                <span className="text-xs bg-warning-100 text-warning-700 px-2 py-0.5 rounded-full">
                  {path.reuse_count}x used
                </span>
              </div>
              <div className="text-xs text-gray-500 flex items-center">
                {path.path.split(' → ').map((project, i, arr) => (
                  <React.Fragment key={i}>
                    <span className="font-medium">{project}</span>
                    {i < arr.length - 1 && (
                      <ArrowRight className="w-3 h-3 mx-1 text-gray-400" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold text-success-600">
                {Math.round(path.success_rate * 100)}%
              </div>
              <div className="text-xs text-gray-500">success</div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Project Nodes Summary */}
      <div className="border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium text-gray-600 mb-3">Project Nodes</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {data.project_nodes.map((node, index) => (
            <motion.div
              key={node.project_id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 + index * 0.1 }}
              className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200"
            >
              <div 
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: node.color }}
              />
              <div className="flex-1 text-left">
                <div className="text-sm font-medium text-gray-700">
                  {node.project_name}
                </div>
                <div className="text-xs text-gray-500">
                  {node.knowledge_count} items • {Math.round(node.connection_strength * 100)}% connected
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default CrossProjectNetwork