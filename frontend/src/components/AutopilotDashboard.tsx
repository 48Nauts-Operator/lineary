// ABOUTME: Real-time dashboard for monitoring AI autopilot sprint execution
// ABOUTME: Shows active agents, task pipeline, and execution progress

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, Pause, Bot, CheckCircle, XCircle, Clock, 
  Activity, TrendingUp, Code, FileText, TestTube,
  GitBranch, Zap, AlertCircle, ChevronRight
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: 'claude' | 'gpt4' | 'local';
  status: 'idle' | 'working' | 'error';
  currentTask?: {
    id: string;
    title: string;
    progress: number;
    startedAt: Date;
  };
  tasksCompleted: number;
  tokensUsed: number;
  successRate: number;
}

interface TaskPipeline {
  queued: number;
  inProgress: number;
  review: number;
  completed: number;
  failed: number;
}

interface ExecutionLog {
  id: string;
  timestamp: Date;
  type: 'task_start' | 'task_complete' | 'error' | 'agent_assign';
  message: string;
  agentId?: string;
  taskId?: string;
  severity: 'info' | 'warning' | 'error' | 'success';
}

interface AutopilotSession {
  id: string;
  projectName: string;
  sprintName: string;
  status: 'running' | 'paused' | 'completed';
  startedAt: Date;
  estimatedCompletion: Date;
  progress: number;
  metrics: {
    totalTasks: number;
    completedTasks: number;
    failedTasks: number;
    averageTimePerTask: number;
    estimatedCost: number;
  };
}

const AutopilotDashboard: React.FC = () => {
  const [session, setSession] = useState<AutopilotSession | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [pipeline, setPipeline] = useState<TaskPipeline>({
    queued: 0,
    inProgress: 0,
    review: 0,
    completed: 0,
    failed: 0
  });
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const ws = new WebSocket('ws://localhost:8000/autopilot/stream');
    
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleRealtimeUpdate(data);
    };

    return () => ws.close();
  }, []);

  const handleRealtimeUpdate = (data: any) => {
    switch (data.type) {
      case 'session_update':
        setSession(data.session);
        break;
      case 'agent_update':
        updateAgent(data.agent);
        break;
      case 'pipeline_update':
        setPipeline(data.pipeline);
        break;
      case 'log_entry':
        addLogEntry(data.log);
        break;
    }
  };

  const updateAgent = (updatedAgent: Agent) => {
    setAgents(prev => {
      const index = prev.findIndex(a => a.id === updatedAgent.id);
      if (index >= 0) {
        const newAgents = [...prev];
        newAgents[index] = updatedAgent;
        return newAgents;
      }
      return [...prev, updatedAgent];
    });
  };

  const addLogEntry = (log: ExecutionLog) => {
    setLogs(prev => [log, ...prev].slice(0, 100)); // Keep last 100 logs
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'claude': return '🤖';
      case 'gpt4': return '🧠';
      case 'local': return '💻';
      default: return '🔧';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'working': return 'text-green-400';
      case 'idle': return 'text-gray-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Zap className="w-8 h-8 text-yellow-400" />
              AI Autopilot Dashboard
              {isConnected && (
                <span className="text-xs bg-green-500 px-2 py-1 rounded-full">
                  LIVE
                </span>
              )}
            </h1>
            {session && (
              <p className="text-gray-400 mt-2">
                {session.projectName} / {session.sprintName}
              </p>
            )}
          </div>
          
          <div className="flex gap-4">
            <button className="px-6 py-2 bg-green-600 rounded-lg hover:bg-green-700 flex items-center gap-2">
              <Play className="w-4 h-4" />
              Resume
            </button>
            <button className="px-6 py-2 bg-yellow-600 rounded-lg hover:bg-yellow-700 flex items-center gap-2">
              <Pause className="w-4 h-4" />
              Pause
            </button>
          </div>
        </div>
      </div>

      {/* Progress Overview */}
      {session && (
        <div className="bg-gray-800 rounded-xl p-6 mb-6">
          <div className="grid grid-cols-4 gap-6">
            <div>
              <p className="text-gray-400 text-sm">Progress</p>
              <div className="mt-2">
                <div className="text-2xl font-bold">{session.progress}%</div>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full transition-all"
                    style={{ width: `${session.progress}%` }}
                  />
                </div>
              </div>
            </div>
            
            <div>
              <p className="text-gray-400 text-sm">Time Elapsed</p>
              <p className="text-2xl font-bold mt-2">
                {formatDuration(Date.now() - session.startedAt.getTime())}
              </p>
            </div>
            
            <div>
              <p className="text-gray-400 text-sm">Est. Completion</p>
              <p className="text-2xl font-bold mt-2">
                {formatDuration(session.estimatedCompletion.getTime() - Date.now())}
              </p>
            </div>
            
            <div>
              <p className="text-gray-400 text-sm">Est. Cost</p>
              <p className="text-2xl font-bold mt-2">
                ${session.metrics.estimatedCost.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Active Agents */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Active Agents
          </h2>
          
          <div className="space-y-4">
            {agents.map(agent => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-gray-700 rounded-lg p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getAgentIcon(agent.type)}</span>
                    <div>
                      <p className="font-medium">{agent.name}</p>
                      <p className={`text-sm ${getStatusColor(agent.status)}`}>
                        {agent.status === 'working' ? 'Working' : 'Idle'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <p className="text-gray-400">Tasks: {agent.tasksCompleted}</p>
                    <p className="text-gray-400">Success: {agent.successRate}%</p>
                  </div>
                </div>
                
                {agent.currentTask && (
                  <div className="mt-3 pt-3 border-t border-gray-600">
                    <p className="text-sm text-gray-400 mb-1">Current Task:</p>
                    <p className="text-sm font-medium">{agent.currentTask.title}</p>
                    <div className="mt-2">
                      <div className="w-full bg-gray-600 rounded-full h-1">
                        <motion.div 
                          className="bg-blue-500 h-1 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${agent.currentTask.progress}%` }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Task Pipeline */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Task Pipeline
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-gray-400" />
                <span>Queued</span>
              </div>
              <span className="text-2xl font-bold">{pipeline.queued}</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-blue-900 rounded-lg">
              <div className="flex items-center gap-3">
                <Code className="w-5 h-5 text-blue-400" />
                <span>In Progress</span>
              </div>
              <span className="text-2xl font-bold">{pipeline.inProgress}</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-yellow-900 rounded-lg">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-yellow-400" />
                <span>Review</span>
              </div>
              <span className="text-2xl font-bold">{pipeline.review}</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-green-900 rounded-lg">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span>Completed</span>
              </div>
              <span className="text-2xl font-bold">{pipeline.completed}</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-red-900 rounded-lg">
              <div className="flex items-center gap-3">
                <XCircle className="w-5 h-5 text-red-400" />
                <span>Failed</span>
              </div>
              <span className="text-2xl font-bold">{pipeline.failed}</span>
            </div>
          </div>
        </div>

        {/* Execution Stream */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            Execution Stream
          </h2>
          
          <div className="space-y-2 max-h-96 overflow-y-auto">
            <AnimatePresence>
              {logs.map(log => (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={`text-sm p-2 rounded ${
                    log.severity === 'error' ? 'bg-red-900' :
                    log.severity === 'success' ? 'bg-green-900' :
                    log.severity === 'warning' ? 'bg-yellow-900' :
                    'bg-gray-700'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-gray-400 text-xs">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <ChevronRight className="w-3 h-3 text-gray-400 mt-0.5" />
                    <span className="flex-1">{log.message}</span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Task Details Modal (if needed) */}
      {/* Add modal for detailed task view */}
    </div>
  );
};

export default AutopilotDashboard;