import React, { useState, useEffect, useMemo } from 'react';
import {
  Play,
  Square,
  CheckCircle,
  Ban,
  Edit,
  Trash2,
  TrendingUp,
  Timer,
  DollarSign,
  ClipboardList,
  AlertTriangle,
  AlertCircle,
  Info,
  RefreshCw,
  Plus,
  Filter,
  X,
  Search,
  Zap,
  Bot,
  Activity,
  Clock,
  Target,
  Gauge
} from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import api, { sprintApi, agentApi } from '../services/api';
import EnhancedTaskCreator from '../components/EnhancedTaskCreator';

interface Task {
  id: string;
  task: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  priority: number;
  type: string;
  created: string;
  updated: string;
  session_id?: string;
  extracted_from?: string;
  time_spent?: number; // in minutes
  estimated_time?: number; // in minutes
  assigned_to?: string;
  tags?: string[];
  cost?: number;
  blockers?: string[];
  completion_percentage?: number;
  llm_model?: 'claude-opus' | 'claude-sonnet' | 'claude-haiku';
  token_usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  agent_assigned?: string;
}

interface EnhancedTask {
  id: string;
  task: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  priority: number;
  created: string;
  updated: string;
  description?: {
    description: string;
    acceptance_criteria: string[];
    technical_notes?: string;
    dependencies: string[];
  };
  sprint_estimate?: {
    complexity_score: number;
    story_points: number;
    estimated_hours: number;
    estimated_tokens: number;
    estimated_cost: number;
    confidence_level: number;
    model_used: string;
    analysis_factors: {
      task_type: string;
      scores: {
        code_footprint: number;
        integration_depth: number;
        test_complexity: number;
        uncertainty: number;
        data_volume: number;
      };
      total_score: number;
    };
    similar_tasks: string[];
    reusability_score: number;
    optimization_suggestions: string[];
  };
  git_integration?: {
    branch_name?: string;
    worktree_path?: string;
    commit_hashes: string[];
    pr_url?: string;
    pr_number?: number;
    base_branch: string;
    merge_status: string;
  };
  current_state?: string;
  validation_status: Record<string, string>;
  metrics?: Record<string, any>;
}

interface Sprint {
  id: string;
  title: string;
  duration_type: 'micro' | 'mini' | 'half-day' | 'full-day';
  duration_hours: number;
  status: 'active' | 'completed' | 'planned';
  start_time?: string;
  end_time?: string;
  tasks: string[];
  progress: number;
  cost: number;
  velocity: number;
}

interface Agent {
  id: string;
  name: string;
  type: 'security-auditor' | 'llm-systems-architect' | 'prompt-optimizer' | 'general-purpose' | 'code-reviewer' | 'test-automation-architect' | 'debug-specialist' | 'vulnerability-scanner';
  status: 'active' | 'idle' | 'busy';
  tasks_assigned: number;
  tasks_completed: number;
  success_rate: number;
  cost: number;
  efficiency_score: number;
}

interface TaskStats {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  blocked: number;
  total_time_spent: number;
  estimated_remaining: number;
  total_cost: number;
  completion_rate: number;
}

interface SessionCost {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  input_cost: number;
  output_cost: number;
  total_cost: number;
  session_date: string;
  files_analyzed: number;
  work_completed: string[];
}

interface CostPrediction {
  estimated_remaining_tokens: number;
  estimated_remaining_cost: number;
  projected_session_cost: number;
  cost_per_task: number;
  efficiency_score: number;
}

const PRIORITY_LABELS = {
  1: { label: 'P0 - Critical', color: '#dc2626', bgColor: 'bg-red-600', textColor: 'text-red-600', icon: AlertCircle },
  2: { label: 'P1 - High', color: '#ea580c', bgColor: 'bg-orange-600', textColor: 'text-orange-600', icon: AlertTriangle },
  3: { label: 'P2 - Normal', color: '#2563eb', bgColor: 'bg-blue-600', textColor: 'text-blue-600', icon: Info },
  4: { label: 'P3 - Low', color: '#16a34a', bgColor: 'bg-green-600', textColor: 'text-green-600', icon: null },
  5: { label: 'P4 - Backlog', color: '#6b7280', bgColor: 'bg-gray-600', textColor: 'text-gray-600', icon: null }
};

const STATUS_COLORS = {
  pending: { color: '#6b7280', bgClass: 'bg-gray-600', textClass: 'text-gray-600' },
  in_progress: { color: '#2563eb', bgClass: 'bg-blue-600', textClass: 'text-blue-600' },
  completed: { color: '#16a34a', bgClass: 'bg-green-600', textClass: 'text-green-600' },
  blocked: { color: '#dc2626', bgClass: 'bg-red-600', textClass: 'text-red-600' }
};

// LLM Pricing per 1M tokens (as of 2024)
const LLM_PRICING = {
  'claude-opus': { input: 15.00, output: 75.00 },
  'claude-sonnet': { input: 3.00, output: 15.00 },
  'claude-haiku': { input: 0.25, output: 1.25 }
};

const SPRINT_DURATIONS = {
  micro: { hours: 2, label: 'Micro Sprint (2hr)' },
  mini: { hours: 4, label: 'Mini Sprint (4hr)' },
  'half-day': { hours: 8, label: 'Half-Day Sprint (8hr)' },
  'full-day': { hours: 24, label: 'Full-Day Sprint (24hr)' }
};

export default function TaskManagementDashboard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [enhancedTasks, setEnhancedTasks] = useState<EnhancedTask[]>([]);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [filterPriority, setFilterPriority] = useState<number | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTimer, setActiveTimer] = useState<string | null>(null);
  const [timerSeconds, setTimerSeconds] = useState(0);
  
  // AI Sprint and Agent state
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeSprint, setActiveSprint] = useState<Sprint | null>(null);
  const [sprintDialogOpen, setSprintDialogOpen] = useState(false);
  const [newSprintType, setNewSprintType] = useState<keyof typeof SPRINT_DURATIONS>('mini');
  
  // Cost Prediction and Session Tracking
  const [sessionCost, setSessionCost] = useState<SessionCost | null>(null);
  const [costPrediction, setCostPrediction] = useState<CostPrediction | null>(null);
  const [showCostDetails, setShowCostDetails] = useState(false);

  // Fetch tasks from Betty API
  const fetchTasks = async () => {
    try {
      setRefreshing(true);
      
      // Fetch both regular and enhanced tasks
      const [regularResponse, enhancedResponse] = await Promise.all([
        fetch('/api/tasks/list', {
          headers: { 'X-API-Key': 'betty_dev_key_123' }
        }),
        fetch('/api/enhanced-tasks', {
          headers: { 'X-API-Key': 'betty_dev_key_123' }
        })
      ]);
      
      const regularData = regularResponse.ok ? await regularResponse.json() : { tasks: [] };
      const enhancedData = enhancedResponse.ok ? await enhancedResponse.json() : { tasks: [] };
      
      // Transform and enrich task data
      const allTasks: Task[] = [];
      
      // Add mock enrichment data for demonstration
      const enrichTask = (task: any): Task => {
        const models: Array<'claude-opus' | 'claude-sonnet' | 'claude-haiku'> = ['claude-opus', 'claude-sonnet', 'claude-haiku'];
        const model = models[Math.floor(Math.random() * models.length)];
        const inputTokens = Math.floor(Math.random() * 10000) + 1000;
        const outputTokens = Math.floor(Math.random() * 5000) + 500;
        const tokenCost = (inputTokens * LLM_PRICING[model].input + outputTokens * LLM_PRICING[model].output) / 1000000;
        
        return {
          ...task,
          time_spent: Math.floor(Math.random() * 240), // Random 0-4 hours
          estimated_time: Math.floor(Math.random() * 480) + 60, // Random 1-8 hours
          cost: tokenCost,
          completion_percentage: task.status === 'completed' ? 100 : 
                                task.status === 'in_progress' ? Math.floor(Math.random() * 80) + 20 : 0,
          tags: extractTags(task.task),
          blockers: task.status === 'blocked' ? ['Waiting for API design', 'Security review needed'] : [],
          llm_model: model,
          token_usage: {
            input_tokens: inputTokens,
            output_tokens: outputTokens,
            total_tokens: inputTokens + outputTokens
          },
          agent_assigned: getRandomAgent()
        };
      };
      
      // Process regular tasks
      Object.entries(regularData.by_status || {}).forEach(([status, statusTasks]) => {
        (statusTasks as any[]).forEach(task => {
          const enrichedTask = enrichTask({ ...task, status });
          allTasks.push(enrichedTask);
        });
      });
      
      // Process enhanced tasks and convert to regular task format
      (enhancedData.tasks || []).forEach((enhancedTask: any) => {
        const task = enrichTask({
          id: enhancedTask.id,
          task: enhancedTask.task,
          status: enhancedTask.status || 'pending',
          priority: enhancedTask.priority || 3,
          type: 'enhanced',
          created: enhancedTask.created,
          updated: enhancedTask.updated,
          time_spent: enhancedTask.estimated_hours ? enhancedTask.estimated_hours * 60 : 0,
          estimated_time: enhancedTask.estimated_hours ? enhancedTask.estimated_hours * 60 : 120,
          cost: enhancedTask.estimated_cost || 0,
          session_id: enhancedTask.session_id,
          extracted_from: 'Enhanced Task Management'
        });
        allTasks.push(task);
      });
      
      setTasks(allTasks);
      await fetchSprintsAndAgents();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Fetch enhanced tasks with Sprint Poker estimates
  const fetchEnhancedTasks = async () => {
    try {
      const response = await fetch('/api/enhanced-tasks', {
        headers: { 'X-API-Key': 'betty_dev_key_123' }
      });
      
      if (!response.ok) throw new Error('Failed to fetch enhanced tasks');
      
      const data = await response.json();
      console.log('Enhanced tasks response:', data);
      setEnhancedTasks(data.tasks || []);
      console.log('Enhanced tasks set to:', data.tasks || []);
    } catch (err) {
      console.error('Failed to fetch enhanced tasks:', err);
      // Don't throw error - enhanced tasks are optional feature
    }
  };

  // Extract tags from task description
  const extractTags = (taskText: string): string[] => {
    const tags: string[] = [];
    if (taskText.toLowerCase().includes('api')) tags.push('API');
    if (taskText.toLowerCase().includes('fix')) tags.push('Bug');
    if (taskText.toLowerCase().includes('security')) tags.push('Security');
    if (taskText.toLowerCase().includes('dashboard')) tags.push('UI');
    if (taskText.toLowerCase().includes('test')) tags.push('Testing');
    if (taskText.toLowerCase().includes('docker')) tags.push('DevOps');
    return tags;
  };

  // Get random agent for assignment
  const getRandomAgent = (): string => {
    const agentTypes = ['security-auditor', 'llm-systems-architect', 'prompt-optimizer', 'general-purpose', 'code-reviewer', 'debug-specialist'];
    return agentTypes[Math.floor(Math.random() * agentTypes.length)];
  };

  // Fetch session cost data and calculate predictions
  const fetchSessionCosts = async () => {
    try {
      // Fetch latest session cost data from host server (bypasses Docker isolation)
      const response = await fetch('http://localhost:3035/session-costs/latest').catch(() => null);
      
      if (response?.ok) {
        const data = await response.json();
        if (data.success && data.session_cost) {
          setSessionCost(data.session_cost);
        }
      } else {
        // Fallback: estimate current session cost
        const estimatedCost: SessionCost = {
          input_tokens: allTasks.reduce((sum, t) => sum + (t.token_usage?.input_tokens || 0), 0),
          output_tokens: allTasks.reduce((sum, t) => sum + (t.token_usage?.output_tokens || 0), 0),
          total_tokens: allTasks.reduce((sum, t) => sum + (t.token_usage?.total_tokens || 0), 0),
          input_cost: 0,
          output_cost: 0,
          total_cost: stats?.total_cost || 0,
          session_date: new Date().toISOString(),
          files_analyzed: allTasks.length,
          work_completed: allTasks.filter(t => t.status === 'completed').map(t => t.task)
        };
        
        // Calculate costs based on token usage
        const avgModel = 'claude-sonnet'; // Default model
        estimatedCost.input_cost = (estimatedCost.input_tokens * LLM_PRICING[avgModel].input) / 1000000;
        estimatedCost.output_cost = (estimatedCost.output_tokens * LLM_PRICING[avgModel].output) / 1000000;
        estimatedCost.total_cost = estimatedCost.input_cost + estimatedCost.output_cost;
        
        setSessionCost(estimatedCost);
      }
      
      // Calculate cost predictions based on remaining work
      calculateCostPrediction();
    } catch (error) {
      console.error('Failed to fetch session costs:', error);
    }
  };
  
  // Calculate cost predictions for remaining work
  const calculateCostPrediction = () => {
    if (!stats || !sessionCost) return;
    
    const pendingTasks = stats.pending + stats.in_progress;
    const completedTasks = stats.completed;
    
    if (completedTasks === 0) {
      // No completed tasks to base predictions on
      setCostPrediction({
        estimated_remaining_tokens: pendingTasks * 5000, // Rough estimate
        estimated_remaining_cost: pendingTasks * 0.05, // $0.05 per task estimate
        projected_session_cost: sessionCost.total_cost + (pendingTasks * 0.05),
        cost_per_task: 0.05,
        efficiency_score: 85 // Default score
      });
      return;
    }
    
    // Calculate averages based on completed work
    const avgTokensPerTask = sessionCost.total_tokens / completedTasks;
    const avgCostPerTask = sessionCost.total_cost / completedTasks;
    
    const prediction: CostPrediction = {
      estimated_remaining_tokens: Math.round(pendingTasks * avgTokensPerTask),
      estimated_remaining_cost: pendingTasks * avgCostPerTask,
      projected_session_cost: sessionCost.total_cost + (pendingTasks * avgCostPerTask),
      cost_per_task: avgCostPerTask,
      efficiency_score: Math.min(95, Math.max(60, 100 - (avgCostPerTask * 1000))) // Higher cost = lower efficiency
    };
    
    setCostPrediction(prediction);
  };

  // Fetch sprints and agents data from real APIs
  const fetchSprintsAndAgents = async () => {
    try {
      // Fetch real sprint data
      const [sprintsResponse, activeSprintResponse] = await Promise.all([
        sprintApi.listSprints(),
        sprintApi.getActiveSprint().catch(() => ({ data: { success: false } }))
      ]);
      
      // Handle sprint list response format: {success: true, sprints: []}
      const sprintList = sprintsResponse.data?.sprints || [];
      setSprints(sprintList);
      
      // Handle active sprint response
      if (activeSprintResponse.data?.success && activeSprintResponse.data?.sprint) {
        setActiveSprint(activeSprintResponse.data.sprint);
      } else {
        setActiveSprint(sprintList.find((s: Sprint) => s.status === 'active') || null);
      }
      
      // Fetch real agent usage data
      const agentResponse = await agentApi.getUsageStats();
      // Handle agent response format: {success: true, agents: [], top_agents: []}
      const agentData = agentResponse.data?.agents || [];
      
      // Transform agent usage data to match our Agent interface
      const transformedAgents: Agent[] = agentData.map((agent: any, index: number) => ({
        id: agent.agent_id || `agent-${index}`,
        name: agent.agent_type?.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) || 'Unknown Agent',
        type: agent.agent_type || 'general-purpose',
        status: agent.last_used ? 
          (new Date().getTime() - new Date(agent.last_used).getTime() < 300000 ? 'active' : 'idle') : 
          'idle',
        tasks_assigned: agent.total_tasks || 0,
        tasks_completed: agent.completed_tasks || 0,
        success_rate: agent.success_rate || 0,
        cost: agent.total_cost || 0,
        efficiency_score: agent.avg_efficiency || 0
      }));
      
      setAgents(transformedAgents);
    } catch (error) {
      console.error('Failed to fetch sprints and agents:', error);
    }
  };

  // Calculate statistics
  const calculateStats = (taskList: Task[]) => {
    const stats: TaskStats = {
      total: taskList.length,
      pending: taskList.filter(t => t.status === 'pending').length,
      in_progress: taskList.filter(t => t.status === 'in_progress').length,
      completed: taskList.filter(t => t.status === 'completed').length,
      blocked: taskList.filter(t => t.status === 'blocked').length,
      total_time_spent: taskList.reduce((sum, t) => sum + (t.time_spent || 0), 0),
      estimated_remaining: taskList
        .filter(t => t.status !== 'completed')
        .reduce((sum, t) => sum + (t.estimated_time || 0), 0),
      total_cost: taskList.reduce((sum, t) => sum + (t.cost || 0), 0),
      completion_rate: taskList.length > 0 
        ? (taskList.filter(t => t.status === 'completed').length / taskList.length) * 100
        : 0
    };
    setStats(stats);
  };

  // Combine regular and enhanced tasks for unified display
  const allTasks = useMemo(() => {
    // Convert enhanced tasks to regular task format for unified display
    const convertedEnhancedTasks = enhancedTasks.map((enhancedTask): Task => ({
      id: enhancedTask.id,
      task: enhancedTask.task,
      status: enhancedTask.status,
      priority: enhancedTask.priority,
      type: 'enhanced',
      created: enhancedTask.created,
      updated: enhancedTask.updated,
      session_id: '',
      extracted_from: 'enhanced_system',
      time_spent: enhancedTask.sprint_estimate?.estimated_hours ? enhancedTask.sprint_estimate.estimated_hours * 60 : 0,
      estimated_time: enhancedTask.sprint_estimate?.estimated_hours ? enhancedTask.sprint_estimate.estimated_hours * 60 : 60,
      assigned_to: 'system',
      tags: ['enhanced', enhancedTask.current_state || 'planning'],
      cost: enhancedTask.sprint_estimate?.estimated_cost || 0,
      blockers: [],
      completion_percentage: enhancedTask.status === 'completed' ? 100 : 
                            enhancedTask.status === 'in_progress' ? 50 : 0,
      llm_model: 'claude-sonnet',
      token_usage: {
        input_tokens: enhancedTask.sprint_estimate?.estimated_tokens ? Math.floor(enhancedTask.sprint_estimate.estimated_tokens * 0.7) : 1000,
        output_tokens: enhancedTask.sprint_estimate?.estimated_tokens ? Math.floor(enhancedTask.sprint_estimate.estimated_tokens * 0.3) : 500,
        total_tokens: enhancedTask.sprint_estimate?.estimated_tokens || 1500
      },
      agent_assigned: enhancedTask.current_state === 'implementing' ? 'general-purpose' : 'llm-systems-architect'
    }));
    
    return [...tasks, ...convertedEnhancedTasks];
  }, [tasks, enhancedTasks]);

  // Filter tasks
  const filteredTasks = useMemo(() => {
    return allTasks.filter(task => {
      if (filterPriority !== 'all' && task.priority !== filterPriority) return false;
      if (filterStatus !== 'all' && task.status !== filterStatus) return false;
      if (searchTerm && !task.task.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      return true;
    });
  }, [allTasks, filterPriority, filterStatus, searchTerm]);

  // Chart data - use allTasks for comprehensive charts
  const priorityChartData = useMemo(() => {
    const data = Object.entries(PRIORITY_LABELS).map(([priority, config]) => ({
      name: config.label.split(' - ')[0],
      value: allTasks.filter(t => t.priority === parseInt(priority)).length,
      color: config.color
    }));
    return data.filter(d => d.value > 0);
  }, [allTasks]);

  const workloadChartData = useMemo(() => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return date.toISOString().split('T')[0];
    });

    return last7Days.map(date => ({
      date: new Date(date).toLocaleDateString('en', { weekday: 'short' }),
      created: allTasks.filter(t => t.created.startsWith(date)).length,
      completed: allTasks.filter(t => t.status === 'completed' && t.updated.startsWith(date)).length
    }));
  }, [allTasks]);

  // Timer effect
  useEffect(() => {
    let interval: number;
    if (activeTimer) {
      interval = window.setInterval(() => {
        setTimerSeconds(prev => prev + 1);
      }, 1000);
    }
    return () => window.clearInterval(interval);
  }, [activeTimer]);

  // Initial fetch
  useEffect(() => {
    fetchTasks();
    fetchEnhancedTasks();
    fetchSprintsAndAgents();
    fetchSessionCosts();
    const interval = setInterval(() => {
      fetchTasks();
      fetchEnhancedTasks();
      fetchSprintsAndAgents();
      fetchSessionCosts();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);
  
  // Recalculate stats when allTasks changes
  useEffect(() => {
    if (allTasks.length > 0) {
    }
  }, [allTasks]);

  // Recalculate predictions when tasks or stats change
  useEffect(() => {
    if (stats && sessionCost) {
      calculateCostPrediction();
    }
  }, [stats, sessionCost, allTasks]);

  // Format time display
  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  // Format timer display
  const formatTimer = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle task actions
  const handleStartTask = (taskId: string) => {
    setActiveTimer(taskId);
    setTimerSeconds(0);
    // TODO: Update task status via API
  };

  const handleStopTask = () => {
    if (activeTimer) {
      const task = allTasks.find(t => t.id === activeTimer);
      if (task) {
        task.time_spent = (task.time_spent || 0) + Math.floor(timerSeconds / 60);
        // Cost already calculated from token usage, no need to recalculate
        
        // Update in the appropriate list
        if (task.type === 'enhanced') {
          fetchEnhancedTasks();
        } else {
          setTasks([...tasks]);
        }
      }
    }
    setActiveTimer(null);
    setTimerSeconds(0);
  };

  const handleCompleteTask = async (taskId: string) => {
    try {
      const task = allTasks.find(t => t.id === taskId);
      if (task) {
        if (task.type === 'enhanced') {
          // Update enhanced task via API
          await fetch(`/api/enhanced-tasks/${taskId}/update`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'X-API-Key': 'betty_dev_key_123'
            },
            body: JSON.stringify({
              status: 'completed'
            })
          });
          fetchEnhancedTasks();
        } else {
          // Update regular task
          task.status = 'completed';
          task.completion_percentage = 100;
          setTasks([...tasks]);
        }
      }
    } catch (error) {
      console.error('Failed to complete task:', error);
      setError('Failed to complete task. Please try again.');
    }
  };

  // Sprint management functions
  const handleStartSprint = async (type: keyof typeof SPRINT_DURATIONS, title: string) => {
    try {
      // Call real API to start sprint
      const response = await sprintApi.startSprint({
        title,
        duration_type: type.toLowerCase().replace('_', '-'),
        tasks: [] // Start with empty tasks, can be added later
      });
      
      const newSprint = response.data;
      setSprints(prev => [...prev, newSprint]);
      setActiveSprint(newSprint);
      setSprintDialogOpen(false);
      
      // Refresh sprints and agents data
      fetchSprintsAndAgents();
    } catch (error) {
      console.error('Failed to start sprint:', error);
      setError('Failed to start sprint. Please try again.');
    }
  };

  const handleCompleteSprint = async (sprintId: string) => {
    try {
      // Call real API to complete sprint
      await sprintApi.completeSprint(sprintId);
      
      // Update local state
      const updatedSprints = sprints.map(s => 
        s.id === sprintId ? { ...s, status: 'completed' as const, end_time: new Date().toISOString() } : s
      );
      setSprints(updatedSprints);
      
      if (activeSprint?.id === sprintId) {
        setActiveSprint(null);
      }
      
      // Refresh data
      fetchSprintsAndAgents();
    } catch (error) {
      console.error('Failed to complete sprint:', error);
      setError('Failed to complete sprint. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <Bot className="w-8 h-8 mr-3 text-blue-600" />
          <h1 className="text-3xl font-bold text-white">AI Task Management Dashboard</h1>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setDialogOpen(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Task
          </button>
          <button
            onClick={fetchTasks}
            disabled={refreshing}
            className={`p-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors ${
              refreshing ? 'animate-spin' : ''
            }`}
          >
            <RefreshCw className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex justify-between items-center">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-600 hover:text-red-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* AI Sprint Management Section */}
      <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center">
            <Zap className="w-6 h-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-white">AI Sprint Management</h2>
          </div>
          <button
            onClick={() => setSprintDialogOpen(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Sprint
          </button>
        </div>
        
        {activeSprint ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-white">{activeSprint?.title}</h3>
                <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                  {SPRINT_DURATIONS[activeSprint.duration_type]?.label || 'Unknown Duration'}
                </span>
              </div>
              <div className="flex items-center mb-2">
                <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${activeSprint?.progress || 0}%` }}
                  ></div>
                </div>
                <span className="text-sm text-gray-600">{activeSprint?.progress || 0}%</span>
              </div>
              <p className="text-sm text-white/70">
                Started: {activeSprint?.start_time ? new Date(activeSprint.start_time).toLocaleTimeString() : 'N/A'}
              </p>
            </div>
            
            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg p-4 shadow-sm">
              <div className="flex items-center mb-2">
                <Target className="w-4 h-4 text-blue-600 mr-2" />
                <h4 className="font-semibold text-white">Metrics</h4>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-white/70">Completion Rate:</span>
                  <span className="font-medium">{activeSprint?.progress || 0}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/70">Cost:</span>
                  <span className="font-medium">${activeSprint?.cost?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Velocity:</span>
                  <span className="font-medium">{activeSprint?.velocity || 0} tasks/hr</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">Quick Actions</h4>
              </div>
              <div className="space-y-2">
                <button
                  onClick={() => activeSprint && handleCompleteSprint(activeSprint.id)}
                  className="w-full flex items-center justify-center px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Complete Sprint
                </button>
                <div className="text-center">
                  <span className="text-xs text-gray-500">
                    {activeSprint?.tasks?.length || 0} tasks assigned
                  </span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <Gauge className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No active sprint. Start one to track your AI development progress.</p>
          </div>
        )}
      </div>

      {/* Agent Usage Panel */}
      <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6 mb-6">
        <div className="flex items-center mb-4">
          <Activity className="w-6 h-6 text-purple-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-900">AI Agent Usage</h2>
        </div>
        
        {agents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {agents.map((agent) => (
              <div key={agent.id} className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-white text-sm">{agent.name}</h3>
                <span className={`w-2 h-2 rounded-full ${
                  agent.status === 'active' ? 'bg-green-400' :
                  agent.status === 'busy' ? 'bg-yellow-400' : 'bg-gray-400'
                }`}></span>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-white/70">Success Rate:</span>
                  <span className="font-medium text-white">{agent.success_rate}%</span>
                </div>
                
                <div className="w-full bg-white/20 rounded-full h-1.5">
                  <div 
                    className={`h-1.5 rounded-full ${
                      agent.success_rate >= 90 ? 'bg-green-500' :
                      agent.success_rate >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${agent.success_rate}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between text-xs">
                  <span className="text-white/70">Cost:</span>
                  <span className="font-medium text-purple-400">${agent.cost.toFixed(2)}</span>
                </div>
                
                <div className="flex justify-between text-xs">
                  <span className="text-white/70">Tasks:</span>
                  <span className="font-medium text-white">{agent.tasks_completed}/{agent.tasks_assigned}</span>
                </div>
                
                <div className="flex justify-between text-xs">
                  <span className="text-white/70">Efficiency:</span>
                  <span className="font-medium text-white">{agent.efficiency_score}%</span>
                </div>
              </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <Bot className="w-12 h-12 text-white/30 mx-auto mb-3" />
            <p className="text-white/70 text-lg font-medium">Agent Usage Coming Soon</p>
            <p className="text-white/50 text-sm">Agent tracking data will appear here once agents are actively used</p>
          </div>
        )}
      </div>

      {/* Cost Prediction & Session Tracking */}
      <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center">
            <DollarSign className="w-6 h-6 text-green-400 mr-2" />
            <h2 className="text-xl font-semibold text-white">Cost Prediction & Token Tracking</h2>
          </div>
          <button
            onClick={() => setShowCostDetails(!showCostDetails)}
            className="text-white/70 hover:text-white transition-colors text-sm"
          >
            {showCostDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Current Session Cost */}
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-white text-sm">Session Cost</h3>
              <span className="w-2 h-2 rounded-full bg-blue-400"></span>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-white">
                ${sessionCost?.total_cost?.toFixed(4) || '0.0000'}
              </div>
              <div className="text-xs text-white/70">
                {sessionCost?.total_tokens?.toLocaleString() || '0'} tokens
              </div>
              {showCostDetails && (
                <div className="text-xs text-white/60 space-y-1">
                  <div>Input: {sessionCost?.input_tokens?.toLocaleString() || '0'}</div>
                  <div>Output: {sessionCost?.output_tokens?.toLocaleString() || '0'}</div>
                </div>
              )}
            </div>
          </div>
          
          {/* Predicted Remaining Cost */}
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-white text-sm">Remaining Est.</h3>
              <span className="w-2 h-2 rounded-full bg-orange-400"></span>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-white">
                ${costPrediction?.estimated_remaining_cost?.toFixed(4) || '0.0000'}
              </div>
              <div className="text-xs text-white/70">
                {costPrediction?.estimated_remaining_tokens?.toLocaleString() || '0'} tokens
              </div>
              {showCostDetails && (
                <div className="text-xs text-white/60">
                  {stats?.pending || 0} + {stats?.in_progress || 0} tasks left
                </div>
              )}
            </div>
          </div>
          
          {/* Projected Total */}
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-white text-sm">Projected Total</h3>
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-white">
                ${costPrediction?.projected_session_cost?.toFixed(4) || '0.0000'}
              </div>
              <div className="text-xs text-white/70">
                Est. completion cost
              </div>
              {showCostDetails && (
                <div className="text-xs text-white/60">
                  ${costPrediction?.cost_per_task?.toFixed(4) || '0.0000'}/task avg
                </div>
              )}
            </div>
          </div>
          
          {/* Efficiency Score */}
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-white text-sm">Efficiency</h3>
              <Gauge className="w-4 h-4 text-green-400" />
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-white">
                {costPrediction?.efficiency_score || 85}%
              </div>
              <div className="w-full bg-white/20 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    (costPrediction?.efficiency_score || 85) >= 90 ? 'bg-green-500' :
                    (costPrediction?.efficiency_score || 85) >= 75 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${costPrediction?.efficiency_score || 85}%` }}
                ></div>
              </div>
              {showCostDetails && (
                <div className="text-xs text-white/60">
                  Token efficiency rating
                </div>
              )}
            </div>
          </div>
        </div>
        
        {showCostDetails && sessionCost && (
          <div className="mt-4 pt-4 border-t border-white/10">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-white mb-2">Session Progress</h4>
                <div className="space-y-1 text-xs text-white/70">
                  <div>Files analyzed: {sessionCost.files_analyzed}</div>
                  <div>Started: {new Date(sessionCost.session_date).toLocaleTimeString()}</div>
                  <div>Your actual cost: $0.00 (Claude Max)</div>
                </div>
              </div>
              <div>
                <h4 className="text-sm font-medium text-white mb-2">Recent Work</h4>
                <div className="space-y-1 text-xs text-white/70 max-h-20 overflow-y-auto">
                  {sessionCost.work_completed.slice(0, 3).map((work, i) => (
                    <div key={i}>• {work.length > 40 ? work.substring(0, 40) + '...' : work}</div>
                  ))}
                  {sessionCost.work_completed.length > 3 && (
                    <div className="text-white/50">+{sessionCost.work_completed.length - 3} more...</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-white/70">Total Tasks</p>
                <p className="text-3xl font-bold text-white">{stats.total}</p>
                <p className="text-sm text-white/60">{stats.in_progress} in progress</p>
              </div>
              <ClipboardList className="w-10 h-10 text-blue-600 opacity-30" />
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6">
            <div className="flex justify-between items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-white/70">Completion Rate</p>
                <p className="text-3xl font-bold text-white">{stats.completion_rate.toFixed(1)}%</p>
                <div className="w-full bg-white/20 rounded-full h-2 mt-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${stats.completion_rate}%` }}
                  ></div>
                </div>
              </div>
              <TrendingUp className="w-10 h-10 text-green-600 opacity-30" />
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-white/70">Time Tracking</p>
                <p className="text-2xl font-bold text-white">{formatTime(stats.total_time_spent)}</p>
                <p className="text-sm text-white/60">{formatTime(stats.estimated_remaining)} remaining</p>
                {activeTimer && (
                  <div className="mt-2 p-2 bg-blue-600 text-white rounded text-center">
                    <span className="text-sm font-mono">Active: {formatTimer(timerSeconds)}</span>
                  </div>
                )}
              </div>
              <Timer className="w-10 h-10 text-orange-600 opacity-30" />
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-white/70">Total LLM Cost</p>
                <p className="text-3xl font-bold text-white">${stats.total_cost.toFixed(2)}</p>
                <div className="text-xs text-white/60 space-y-1 mt-2">
                  <div className="flex justify-between">
                    <span>Claude Opus:</span>
                    <span>${(stats.total_cost * 0.6).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Claude Sonnet:</span>
                    <span>${(stats.total_cost * 0.3).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Claude Haiku:</span>
                    <span>${(stats.total_cost * 0.1).toFixed(2)}</span>
                  </div>
                </div>
              </div>
              <DollarSign className="w-10 h-10 text-purple-600 opacity-30" />
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Priority Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={priorityChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {priorityChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <ChartTooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="lg:col-span-2 bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-white mb-4">7-Day Workload Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={workloadChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <ChartTooltip />
              <Legend />
              <Bar dataKey="created" fill="#2563eb" name="Created" />
              <Bar dataKey="completed" fill="#16a34a" name="Completed" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search tasks..."
              className="w-full pl-10 pr-4 py-2 border border-white/10 bg-white/5 text-white placeholder-white/50 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div>
            <select
              className="w-full px-3 py-2 border border-white/10 bg-white/5 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
            >
              <option value="all">All Priorities</option>
              {Object.entries(PRIORITY_LABELS).map(([priority, config]) => (
                <option key={priority} value={priority}>
                  {config.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <select
              className="w-full px-3 py-2 border border-white/10 bg-white/5 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="blocked">Blocked</option>
            </select>
          </div>
        </div>
      </div>

      {/* Task Tabs */}
      <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-lg shadow">
        <div className="border-b border-white/10">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setSelectedTab(0)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 0
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-white/70 hover:text-white hover:border-white/30'
              }`}
            >
              All Tasks ({filteredTasks.length})
            </button>
            <button
              onClick={() => setSelectedTab(1)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 1
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-white/70 hover:text-white hover:border-white/30'
              }`}
            >
              Critical ({filteredTasks.filter(t => t.priority <= 2).length})
            </button>
            <button
              onClick={() => setSelectedTab(2)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 2
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-white/70 hover:text-white hover:border-white/30'
              }`}
            >
              Blocked ({filteredTasks.filter(t => t.status === 'blocked').length})
            </button>
            <button
              onClick={() => setSelectedTab(3)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 3
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-white/70 hover:text-white hover:border-white/30'
              }`}
            >
              Backlog ({filteredTasks.filter(t => t.priority >= 4).length})
            </button>
            <button
              onClick={() => setSelectedTab(4)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 4
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-white/70 hover:text-white hover:border-white/30'
              }`}
            >
              🎯 Enhanced Tasks ({enhancedTasks.length})
            </button>
          </nav>
        </div>

        {/* Task Table */}
        <div className="overflow-x-auto">
          {selectedTab === 4 ? (
            /* Enhanced Tasks Table */
            <table className="min-w-full divide-y divide-white/10">
              <thead className="bg-white/5">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Task</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Sprint Poker</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Cost Est.</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">State</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white/5 divide-y divide-white/10">
                {enhancedTasks.map((task) => {
                  const priorityConfig = PRIORITY_LABELS[task.priority as keyof typeof PRIORITY_LABELS];
                  const statusConfig = STATUS_COLORS[task.status];
                  
                  return (
                    <tr key={task.id} className="hover:bg-white/10">
                      <td className="px-3 py-2 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-3 ${priorityConfig.color}`}></div>
                          <div>
                            <div className="text-sm font-medium text-white">{task.task}</div>
                            {task.description && (
                              <div className="text-xs text-white/60 mt-1">{task.description.description.slice(0, 100)}...</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {task.sprint_estimate ? (
                          <div className="space-y-1">
                            <div className="flex items-center space-x-2">
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                {task.sprint_estimate.story_points} pts
                              </span>
                              <span className="text-xs text-white/70">{task.sprint_estimate.estimated_hours}h</span>
                            </div>
                            <div className="text-xs text-white/60">
                              Complexity: {task.sprint_estimate.complexity_score}/13
                            </div>
                            <div className="text-xs text-white/60">
                              Confidence: {Math.round(task.sprint_estimate.confidence_level * 100)}%
                            </div>
                          </div>
                        ) : (
                          <span className="text-xs text-white/50">No estimate</span>
                        )}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgClass} ${statusConfig.textClass}`}>
                          {task.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {task.sprint_estimate ? (
                          <div className="space-y-1">
                            <div className="text-sm font-medium text-white">${task.sprint_estimate.estimated_cost.toFixed(3)}</div>
                            <div className="text-xs text-white/60">{task.sprint_estimate.estimated_tokens.toLocaleString()} tokens</div>
                          </div>
                        ) : (
                          <span className="text-xs text-white/50">No cost estimate</span>
                        )}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {task.current_state || 'planning'}
                        </span>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-right text-sm font-medium">
                        <button 
                          onClick={() => setSelectedTask(task as any)}
                          className="text-indigo-400 hover:text-indigo-300 mr-2"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            /* Regular Tasks Table */
            <table className="min-w-full divide-y divide-white/10">
              <thead className="bg-white/5">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Task</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Priority</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Progress</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">LLM Model</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Cost/Tokens</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Agent</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-white/70 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white/5 divide-y divide-white/10">
                {filteredTasks
                  .filter(task => {
                    if (selectedTab === 1) return task.priority <= 2;
                    if (selectedTab === 2) return task.status === 'blocked';
                    if (selectedTab === 3) return task.priority >= 4;
                    return true;
                  })
                  .slice(0, 20)
                  .map((task) => {
                  const priorityConfig = PRIORITY_LABELS[task.priority as keyof typeof PRIORITY_LABELS];
                  const statusConfig = STATUS_COLORS[task.status];
                  const IconComponent = priorityConfig.icon;
                  
                  return (
                    <tr key={task.id} className="hover:bg-white/10">
                      <td className="px-3 py-2 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-white">
                            {task.task.length > 60 ? task.task.substring(0, 60) + '...' : task.task}
                          </div>
                          <div className="text-sm text-white/60">
                            Created: {new Date(task.created).toLocaleDateString()}
                          </div>
                          {task.blockers && task.blockers.length > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {task.blockers.map((blocker, i) => (
                                <span
                                  key={i}
                                  className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-red-100 text-red-800 border border-red-200"
                                >
                                  {blocker}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium text-white ${priorityConfig.bgColor}`}>
                          {IconComponent && <IconComponent className="w-3 h-3 mr-1" />}
                          {priorityConfig.label}
                        </span>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium text-white ${statusConfig.bgClass} capitalize`}>
                          {task.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                              style={{ width: `${task.completion_percentage || 0}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-white/70">{task.completion_percentage || 0}%</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-white">
                        <div className="flex items-center">
                          <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                            task.llm_model === 'claude-opus' ? 'bg-purple-100 text-purple-800' :
                            task.llm_model === 'claude-sonnet' ? 'bg-blue-100 text-blue-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {task.llm_model || 'N/A'}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-white">
                        <div>
                          <div className="font-medium">${task.cost?.toFixed(3) || '0.000'}</div>
                          {task.token_usage && (
                            <div className="text-xs text-white/60">
                              {(task.token_usage.total_tokens / 1000).toFixed(1)}K tokens
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <div className="text-sm text-white">
                          <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-indigo-100 text-indigo-800">
                            {task.agent_assigned || 'unassigned'}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          {task.status === 'pending' && (
                            <button
                              title="Start Task"
                              onClick={() => handleStartTask(task.id)}
                              disabled={activeTimer !== null && activeTimer !== task.id}
                              className="text-blue-600 hover:text-blue-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          )}
                          {activeTimer === task.id && (
                            <button
                              title="Stop Timer"
                              onClick={handleStopTask}
                              className="text-red-600 hover:text-red-900"
                            >
                              <Square className="w-4 h-4" />
                            </button>
                          )}
                          {task.status !== 'completed' && (
                            <button
                              title="Mark Complete"
                              onClick={() => handleCompleteTask(task.id)}
                              className="text-green-600 hover:text-green-900"
                            >
                              <CheckCircle className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            title="Edit Task"
                            onClick={() => {
                              setSelectedTask(task);
                              setDialogOpen(true);
                            }}
                            className="text-gray-600 hover:text-gray-900"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Task Dialog */}
      {dialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-96">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedTask ? 'Edit Task' : 'New Task'}
              </h3>
              <button
                onClick={() => setDialogOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Task Description
                  </label>
                  <textarea
                    placeholder="Enter task description..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-24 resize-none"
                    id="task-description"
                    defaultValue={selectedTask?.task || ''}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Priority
                    </label>
                    <select
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      id="task-priority"
                      defaultValue={selectedTask?.priority || 3}
                    >
                      <option value={1}>P0 - Critical</option>
                      <option value={2}>P1 - High</option>
                      <option value={3}>P2 - Normal</option>
                      <option value={4}>P3 - Low</option>
                      <option value={5}>P4 - Backlog</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Status
                    </label>
                    <select
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      id="task-status"
                      defaultValue={selectedTask?.status || 'pending'}
                    >
                      <option value="pending">Pending</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                      <option value="blocked">Blocked</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setDialogOpen(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button 
                onClick={async () => {
                  const taskDescription = (document.getElementById('task-description') as HTMLTextAreaElement)?.value;
                  const taskPriority = parseInt((document.getElementById('task-priority') as HTMLSelectElement)?.value || '3');
                  const taskStatus = (document.getElementById('task-status') as HTMLSelectElement)?.value || 'pending';
                  
                  if (!taskDescription.trim()) {
                    setError('Task description is required');
                    return;
                  }
                  
                  try {
                    if (selectedTask) {
                      // Update existing task logic would go here
                      console.log('Update task:', selectedTask.id, { task: taskDescription, priority: taskPriority, status: taskStatus });
                    } else {
                      // Create new enhanced task
                      const response = await fetch('/api/enhanced-tasks/create', {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'X-API-Key': 'betty_dev_key_123'
                        },
                        body: JSON.stringify({
                          task: taskDescription,
                          priority: taskPriority,
                          status: taskStatus
                        })
                      });
                      
                      if (!response.ok) {
                        throw new Error('Failed to create task');
                      }
                      
                      // Refresh both task lists
                      fetchTasks();
                      fetchEnhancedTasks();
                    }
                    
                    setDialogOpen(false);
                    setSelectedTask(null);
                    setError(null);
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'Failed to save task');
                  }
                }}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
              >
                {selectedTask ? 'Update' : 'Create'} Task
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sprint Dialog */}
      {sprintDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Start New AI Sprint</h3>
              <button
                onClick={() => setSprintDialogOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sprint Duration
                  </label>
                  <select
                    value={newSprintType}
                    onChange={(e) => setNewSprintType(e.target.value as keyof typeof SPRINT_DURATIONS)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {Object.entries(SPRINT_DURATIONS).map(([key, config]) => (
                      <option key={key} value={key}>{config.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sprint Title
                  </label>
                  <input
                    type="text"
                    placeholder="Enter sprint title..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    id="sprint-title"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setSprintDialogOpen(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  const titleInput = document.getElementById('sprint-title') as HTMLInputElement;
                  const title = titleInput?.value || `${SPRINT_DURATIONS[newSprintType].label} Sprint`;
                  handleStartSprint(newSprintType, title);
                }}
                className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
              >
                <Zap className="w-4 h-4 mr-2" />
                Start Sprint
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Enhanced Task Creator Floating Button */}
      <EnhancedTaskCreator onTaskCreated={(task) => {
        console.log('Enhanced task created:', task);
        fetchTasks(); // Refresh regular tasks
        fetchEnhancedTasks(); // Refresh enhanced tasks
      }} />
    </div>
  );
}