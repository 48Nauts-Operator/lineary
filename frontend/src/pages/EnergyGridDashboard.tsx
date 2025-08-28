// ABOUTME: Energy Grid Management Dashboard - Real-time grid monitoring and predictive analytics
// ABOUTME: Shows critical energy metrics, anomaly detection, and pattern-based failure predictions

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Zap, AlertTriangle, Activity, TrendingUp, 
  ThermometerSun, Wind, Sun, Battery,
  AlertCircle, CheckCircle, Clock, BarChart3,
  Gauge, Cpu, Shield, Waves, Brain
} from 'lucide-react'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface GridMetrics {
  frequency: number
  voltage: number
  loadPercentage: number
  powerFactor: number
  totalGeneration: number
  totalDemand: number
  transmissionLoss: number
  renewablePercentage: number
}

interface AnomalyAlert {
  id: string
  severity: 'critical' | 'warning' | 'info'
  type: string
  location: string
  description: string
  timestamp: string
  similarity: number // % similarity to past events
  predictedOutcome?: string
  recommendedAction?: string
}

interface PredictiveInsight {
  equipmentId: string
  equipmentType: string
  failureProbability: number
  timeToFailure: string
  lastMaintenance: string
  historicalFailures: number
  recommendedAction: string
}

const EnergyGridDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<GridMetrics>({
    frequency: 50.02,
    voltage: 230.5,
    loadPercentage: 67,
    powerFactor: 0.95,
    totalGeneration: 2450,
    totalDemand: 2380,
    transmissionLoss: 2.8,
    renewablePercentage: 34
  })

  const [alerts, setAlerts] = useState<AnomalyAlert[]>([
    {
      id: '1',
      severity: 'critical',
      type: 'Demand Response Pattern',
      location: 'Downtown Business District',
      description: '🔥 Load surge pattern matches July 2023 blackout event (95% similarity)',
      timestamp: '1 min ago',
      similarity: 95,
      predictedOutcome: '⚡ Grid instability likely in 45-60 minutes during evening peak',
      recommendedAction: '📢 Activate emergency demand response - Reduce industrial load by 400MW'
    },
    {
      id: '2', 
      severity: 'warning',
      type: 'Weather Correlation Alert',
      location: 'Solar Farm District',
      description: '☁️ Cloud formation reducing solar output, wind generation down 15%',
      timestamp: '3 min ago',
      similarity: 78,
      predictedOutcome: '📉 Renewable shortfall of 800MW predicted for next 2 hours',
      recommendedAction: '🏭 Bring online backup natural gas peaker plants'
    },
    {
      id: '3',
      severity: 'warning', 
      type: 'Equipment Degradation',
      location: 'Transmission Line T-447',
      description: '🌡️ Conductor temperature 15°C above normal for current load',
      timestamp: '8 min ago',
      similarity: 89,
      predictedOutcome: '⚡ Thermal limit breach if temperature exceeds 85°C',
      recommendedAction: '🔄 Reroute 200MW through parallel transmission paths'
    },
    {
      id: '4',
      severity: 'info',
      type: 'Load Balancing Optimization',
      location: 'Regional Grid Controller',
      description: '📊 Off-peak charging pattern detected - EV fleet synchronized',
      timestamp: '12 min ago', 
      similarity: 71,
      predictedOutcome: '💡 Optimal window for scheduled maintenance tasks',
      recommendedAction: '🔧 Deploy maintenance crews to non-critical substations'
    }
  ])

  // Simulated real-time frequency data
  const [frequencyHistory, setFrequencyHistory] = useState<any[]>([])
  
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        frequency: 49.95 + Math.random() * 0.1,
        voltage: 229 + Math.random() * 3,
        loadPercentage: Math.min(95, prev.loadPercentage + (Math.random() - 0.3) * 2)
      }))

      setFrequencyHistory(prev => {
        const newData = [...prev, {
          time: new Date().toLocaleTimeString(),
          frequency: 49.95 + Math.random() * 0.1,
          target: 50
        }].slice(-20)
        return newData
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  // Peak/Off-peak Load Patterns (MW)
  const loadForecast = [
    { hour: '00:00', actual: 1800, predicted: 1820, bettyPredicted: 1810, pattern: 'Overnight Base Load', temperature: 22 },
    { hour: '04:00', actual: 1650, predicted: 1700, bettyPredicted: 1660, pattern: 'Pre-Dawn Minimum', temperature: 19 },
    { hour: '06:00', actual: 2100, predicted: 2050, bettyPredicted: 2090, pattern: 'Morning Ramp Start', temperature: 20 },
    { hour: '08:00', actual: 2800, predicted: 2750, bettyPredicted: 2790, pattern: 'Morning Peak (Industrial)', temperature: 24 },
    { hour: '12:00', actual: 3200, predicted: 3150, bettyPredicted: 3190, pattern: 'Midday Commercial Peak', temperature: 32 },
    { hour: '16:00', actual: 3400, predicted: 3350, bettyPredicted: 3395, pattern: 'Afternoon Industrial', temperature: 35 },
    { hour: '18:00', actual: 3800, predicted: 3750, bettyPredicted: 3785, pattern: 'Evening Residential Peak', temperature: 33 },
    { hour: '20:00', actual: 3200, predicted: 3250, bettyPredicted: 3195, pattern: 'Evening Wind Down', temperature: 29 },
    { hour: '22:00', actual: 2400, predicted: 2450, bettyPredicted: 2395, pattern: 'Night Base Transition', temperature: 26 },
    { hour: '24:00', actual: null, predicted: 1900, bettyPredicted: 1895, pattern: 'Predicted Base Load', temperature: 23 }
  ]

  // Equipment health data
  const equipmentHealth = [
    { equipment: 'Transformers', health: 89, issues: 3 },
    { equipment: 'Breakers', health: 94, issues: 1 },
    { equipment: 'Capacitor Banks', health: 78, issues: 5 },
    { equipment: 'Transmission Lines', health: 92, issues: 2 },
    { equipment: 'Generators', health: 96, issues: 0 }
  ]

  // Betty's Pattern-Based Predictions
  const predictions: PredictiveInsight[] = [
    {
      equipmentId: 'TR-045',
      equipmentType: 'Transformer (Downtown Substation)',
      failureProbability: 78,
      timeToFailure: '3-5 days',
      lastMaintenance: '45 days ago',
      historicalFailures: 2,
      recommendedAction: '⚡ CRITICAL: Oil temperature pattern matches 2019 failure - Schedule immediate inspection'
    },
    {
      equipmentId: 'CB-112', 
      equipmentType: 'Circuit Breaker (Industrial District)',
      failureProbability: 45,
      timeToFailure: '2-3 weeks',
      lastMaintenance: '120 days ago',
      historicalFailures: 0,
      recommendedAction: '🔧 Contact arcing pattern detected - Add to next maintenance cycle'
    },
    {
      equipmentId: 'GEN-08',
      equipmentType: 'Natural Gas Turbine',
      failureProbability: 67,
      timeToFailure: '1-2 weeks',
      lastMaintenance: '30 days ago',
      historicalFailures: 1,
      recommendedAction: '🌡️ Bearing temperature trend matches summer 2022 failure pattern'
    }
  ]

  // Energy source mix with real-time generation
  const energyMix = [
    { name: 'Solar', value: 15, color: '#FDB462', status: 'Reduced (Cloud Cover)', capacity: '2.1 GW' },
    { name: 'Wind', value: 19, color: '#80B1D3', status: 'Low Wind Speeds', capacity: '1.8 GW' },
    { name: 'Natural Gas', value: 35, color: '#B3DE69', status: 'Peak Load Response', capacity: '4.2 GW' },
    { name: 'Nuclear', value: 20, color: '#BEBADA', status: 'Base Load Stable', capacity: '2.4 GW' },
    { name: 'Coal', value: 11, color: '#FB8072', status: 'Being Phased Down', capacity: '1.3 GW' }
  ]

  // Betty's Discovered Energy Patterns
  const discoveredPatterns = [
    {
      id: 'P001',
      name: '📊 Monday Morning Audit System Spike',
      description: 'Auditing systems restart after weekend, causing 15% load spike between 6:30-8:00 AM',
      occurrence: '94% of Mondays',
      impact: '+450 MW peak demand',
      mitigation: 'Pre-staged additional generation capacity',
      discovered: '2024-03-15',
      accuracy: '98.2%'
    },
    {
      id: 'P002', 
      name: '🌡️ Heat Dome Cascade Pattern',
      description: 'When temperature exceeds 95°F for 3+ consecutive days, AC load grows exponentially not linearly',
      occurrence: 'Summer heat waves',
      impact: '40% higher than linear projections',
      mitigation: 'Emergency demand response protocols activated at day 2',
      discovered: '2023-07-08',
      accuracy: '96.7%'
    },
    {
      id: 'P003',
      name: '⚡ Evening Peak Shift',
      description: 'Remote work has shifted residential peak from 8 PM to 6 PM, coinciding with commercial peak',
      occurrence: 'Daily pattern change',
      impact: '+800 MW coincident peak',
      mitigation: 'Time-of-use pricing and smart appliance scheduling',
      discovered: '2024-01-22',
      accuracy: '94.1%'
    },
    {
      id: 'P004',
      name: '🌪️ Wind Generation Cliff Effect',
      description: 'Wind farms show synchronized drop-off when speeds fall below 12 mph - not gradual decline',
      occurrence: 'Weather transition periods',
      impact: '-1.2 GW in 15 minutes',
      mitigation: 'Fast-ramping gas turbines on standby during wind transitions',
      discovered: '2023-09-14',
      accuracy: '97.8%'
    }
  ]

  const getStatusColor = (value: number, min: number, max: number) => {
    if (value < min || value > max) return 'text-red-500'
    if (value < min + 0.1 || value > max - 0.1) return 'text-yellow-500'
    return 'text-green-500'
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50'
      case 'warning': return 'border-yellow-500 bg-yellow-50'
      default: return 'border-blue-500 bg-blue-50'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-8xl mx-auto space-y-6">
        
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-800/50 backdrop-blur-lg rounded-2xl p-6 border border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-xl">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">Energy Grid Command Center</h1>
                <p className="text-slate-400">Powered by Betty Pattern Recognition • 6,128 Historical Events Analyzed</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-green-400 font-medium">Grid Stable</span>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-white">{metrics.totalGeneration} MW</div>
                <div className="text-xs text-slate-400">Total Generation</div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Critical Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-4 border border-slate-700"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Grid Frequency</span>
              <Waves className="w-4 h-4 text-slate-500" />
            </div>
            <div className={`text-3xl font-bold ${getStatusColor(metrics.frequency, 49.8, 50.2)}`}>
              {metrics.frequency.toFixed(2)} Hz
            </div>
            <div className="text-xs text-slate-500 mt-1">Target: 50.00 Hz ±0.2</div>
            <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
                style={{ width: `${((metrics.frequency - 49.5) / 1) * 100}%` }}
              />
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.15 }}
            className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-4 border border-slate-700"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">System Load</span>
              <Gauge className="w-4 h-4 text-slate-500" />
            </div>
            <div className={`text-3xl font-bold ${metrics.loadPercentage > 85 ? 'text-red-500' : metrics.loadPercentage > 70 ? 'text-yellow-500' : 'text-green-500'}`}>
              {metrics.loadPercentage}%
            </div>
            <div className="text-xs text-slate-500 mt-1">{metrics.totalDemand} / {metrics.totalGeneration} MW</div>
            <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${
                  metrics.loadPercentage > 85 ? 'bg-red-500' : 
                  metrics.loadPercentage > 70 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${metrics.loadPercentage}%` }}
              />
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-4 border border-slate-700"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Power Factor</span>
              <Cpu className="w-4 h-4 text-slate-500" />
            </div>
            <div className={`text-3xl font-bold ${metrics.powerFactor < 0.9 ? 'text-yellow-500' : 'text-green-500'}`}>
              {metrics.powerFactor.toFixed(2)}
            </div>
            <div className="text-xs text-slate-500 mt-1">Target: &gt;0.95</div>
            <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500"
                style={{ width: `${metrics.powerFactor * 100}%` }}
              />
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.25 }}
            className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-4 border border-slate-700"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Renewable Mix</span>
              <Sun className="w-4 h-4 text-slate-500" />
            </div>
            <div className="text-3xl font-bold text-green-500">
              {metrics.renewablePercentage}%
            </div>
            <div className="text-xs text-slate-500 mt-1">↑ 2.3% from yesterday</div>
            <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-green-500 to-emerald-600 transition-all duration-500"
                style={{ width: `${metrics.renewablePercentage}%` }}
              />
            </div>
          </motion.div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Real-time Frequency Chart */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-2 bg-slate-800/50 backdrop-blur-lg rounded-xl p-6 border border-slate-700"
          >
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-yellow-500" />
              Real-time Grid Frequency
            </h2>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={frequencyHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#94a3b8" />
                <YAxis domain={[49.8, 50.2]} stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Line type="monotone" dataKey="frequency" stroke="#facc15" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="target" stroke="#ef4444" strokeWidth={1} strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Energy Source Mix */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.35 }}
            className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-6 border border-slate-700"
          >
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <Battery className="w-5 h-5 mr-2 text-green-500" />
              Generation Mix
            </h2>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={energyMix}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {energyMix.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Anomaly Detection & Pattern Recognition */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-6 border border-slate-700"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2 text-orange-500" />
              Betty Pattern Recognition Alerts
            </h2>
            <span className="text-sm text-slate-400">Analyzing against 6,128 historical events</span>
          </div>
          
          <div className="space-y-3">
            <AnimatePresence>
              {alerts.map((alert, index) => (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.1 }}
                  className={`border-l-4 ${getSeverityColor(alert.severity)} p-4 rounded-lg`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        {alert.severity === 'critical' ? 
                          <AlertCircle className="w-5 h-5 text-red-500" /> :
                          <AlertTriangle className="w-5 h-5 text-yellow-500" />
                        }
                        <span className="font-semibold text-white">{alert.type}</span>
                        <span className="text-sm text-slate-400">• {alert.location}</span>
                        <span className="text-xs text-slate-500">{alert.timestamp}</span>
                      </div>
                      <p className="text-sm text-slate-300 mb-2">{alert.description}</p>
                      
                      <div className="grid grid-cols-3 gap-4 mt-3 p-3 bg-slate-900/50 rounded-lg">
                        <div>
                          <div className="text-xs text-slate-500">Pattern Match</div>
                          <div className="text-lg font-semibold text-orange-400">{alert.similarity}%</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500">Predicted Outcome</div>
                          <div className="text-sm text-slate-300">{alert.predictedOutcome}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500">Recommended Action</div>
                          <div className="text-sm text-green-400">{alert.recommendedAction}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Bottom Grid - Load Forecast & Equipment Health */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Load Forecast with Betty Predictions */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-6 border border-slate-700"
          >
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-blue-500" />
              24h Load Forecast
            </h2>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={loadForecast}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="hour" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(value, name, props) => {
                    if (name === 'Betty AI Forecast') {
                      return [`${value} MW`, `🧠 Betty AI (Pattern: ${props.payload.pattern})`]
                    }
                    return [`${value} MW`, name]
                  }}
                  labelFormatter={(hour) => `${hour} | Temp: ${loadForecast.find(d => d.hour === hour)?.temperature}°C`}
                />
                <Legend />
                <Area type="monotone" dataKey="actual" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} name="Actual" />
                <Area type="monotone" dataKey="predicted" stackId="2" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.3} name="Standard Forecast" />
                <Area type="monotone" dataKey="bettyPredicted" stackId="3" stroke="#10b981" fill="#10b981" fillOpacity={0.5} name="Betty AI Forecast" />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-3 text-xs text-slate-400">
              Betty's forecast accuracy: 98.2% (based on pattern matching with 1,247 similar days)
            </div>
          </motion.div>

          {/* Equipment Health Matrix */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.55 }}
            className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-6 border border-slate-700"
          >
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <Shield className="w-5 h-5 mr-2 text-purple-500" />
              Equipment Health Matrix
            </h2>
            <div className="space-y-3">
              {equipmentHealth.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      item.health > 90 ? 'bg-green-500' : 
                      item.health > 80 ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <span className="text-slate-300">{item.equipment}</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-500 ${
                          item.health > 90 ? 'bg-green-500' : 
                          item.health > 80 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${item.health}%` }}
                      />
                    </div>
                    <span className="text-sm text-slate-400 w-12">{item.health}%</span>
                    {item.issues > 0 && (
                      <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">
                        {item.issues} issues
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Predictive Maintenance */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-6 border border-slate-700"
        >
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-indigo-500" />
            Predictive Maintenance Intelligence
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {predictions.map((pred, index) => (
              <div key={index} className="bg-slate-900/50 rounded-lg p-4 border border-slate-600">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="text-white font-semibold">{pred.equipmentId}</span>
                    <span className="text-slate-400 text-sm ml-2">• {pred.equipmentType}</span>
                  </div>
                  <div className={`text-lg font-bold ${
                    pred.failureProbability > 70 ? 'text-red-500' : 
                    pred.failureProbability > 40 ? 'text-yellow-500' : 'text-green-500'
                  }`}>
                    {pred.failureProbability}% risk
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-500">Time to Failure:</span>
                    <div className="text-slate-300">{pred.timeToFailure}</div>
                  </div>
                  <div>
                    <span className="text-slate-500">Last Maintenance:</span>
                    <div className="text-slate-300">{pred.lastMaintenance}</div>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-700">
                  <span className="text-xs text-slate-500">Action Required:</span>
                  <div className="text-sm text-cyan-400">{pred.recommendedAction}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Bottom Status Bar */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-4 border border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm text-slate-300">Betty AI: Active</span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-slate-300">Pattern Analysis: Real-time</span>
              </div>
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-purple-500" />
                <span className="text-sm text-slate-300">Historical Events: 6,128</span>
              </div>
            </div>
            <div className="text-sm text-slate-400">
              Last Grid Event: 2 minutes ago • Next Maintenance Window: 03:00 - 05:00
            </div>
          </div>
        </motion.div>

        {/* Betty's Pattern Intelligence Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="mt-8 bg-gradient-to-r from-blue-900/30 to-purple-900/30 backdrop-blur-lg rounded-xl p-6 border border-blue-500/30"
        >
          <div className="flex items-center mb-6">
            <Brain className="w-6 h-6 mr-3 text-blue-400" />
            <h2 className="text-2xl font-semibold text-white">Betty's Discovered Energy Patterns</h2>
            <div className="ml-auto text-sm text-blue-300 bg-blue-500/20 px-3 py-1 rounded-full">
              🧠 {discoveredPatterns.length} Active Patterns
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {discoveredPatterns.map((pattern) => (
              <div key={pattern.id} className="bg-slate-800/70 rounded-lg p-4 border border-slate-600/50 hover:border-blue-500/50 transition-all">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-medium text-white">{pattern.name}</h3>
                  <div className="text-xs bg-green-500/20 text-green-300 px-2 py-1 rounded-full">
                    {pattern.accuracy} accurate
                  </div>
                </div>
                
                <p className="text-slate-300 text-sm mb-3">{pattern.description}</p>
                
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400">Occurs:</span>
                    <div className="text-yellow-300 font-medium">{pattern.occurrence}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Impact:</span>
                    <div className="text-orange-300 font-medium">{pattern.impact}</div>
                  </div>
                </div>
                
                <div className="mt-3 pt-3 border-t border-slate-700">
                  <div className="text-slate-400 text-xs mb-1">Betty's Mitigation:</div>
                  <div className="text-green-300 text-sm">{pattern.mitigation}</div>
                </div>
                
                <div className="mt-2 text-xs text-slate-500">
                  Pattern discovered: {pattern.discovered} • ID: {pattern.id}
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 p-4 bg-slate-900/50 rounded-lg border-l-4 border-blue-500">
            <div className="flex items-center mb-2">
              <Zap className="w-5 h-5 mr-2 text-yellow-400" />
              <span className="text-white font-medium">Pattern Recognition Impact</span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">847</div>
                <div className="text-slate-400">Blackouts Prevented</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">$23.8M</div>
                <div className="text-slate-400">Cost Savings (Annual)</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">94.2%</div>
                <div className="text-slate-400">Load Forecast Accuracy</div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default EnergyGridDashboard