// ABOUTME: AI Autopilot orchestration engine for autonomous sprint execution
// ABOUTME: Manages continuous task execution with multiple AI agents

import { EventEmitter } from 'events';
import { Pool } from 'pg';
import Redis from 'ioredis';

interface Agent {
  id: string;
  type: 'claude' | 'gpt4' | 'local';
  status: 'idle' | 'working' | 'error';
  currentTask?: string;
  capabilities: string[];
  maxConcurrent: number;
  activeCount: number;
}

interface Task {
  id: string;
  issueId: string;
  title: string;
  description: string;
  dependencies: string[];
  priority: number;
  complexity: number;
  status: 'queued' | 'in_progress' | 'completed' | 'failed';
  assignedAgent?: string;
  context?: any;
}

interface AutopilotSession {
  id: string;
  projectId: string;
  sprintId?: string;
  status: 'active' | 'paused' | 'completed';
  startedAt: Date;
  config: {
    maxAgents: number;
    requireReview: boolean;
    continuousMode: boolean;
    costLimit?: number;
  };
  metrics: {
    tasksTotal: number;
    tasksCompleted: number;
    tasksFailed: number;
    totalCost: number;
    averageTimePerTask: number;
  };
}

export class AutopilotOrchestrator extends EventEmitter {
  private db: Pool;
  private redis: Redis;
  private agents: Map<string, Agent> = new Map();
  private sessions: Map<string, AutopilotSession> = new Map();
  private taskQueues: Map<string, Task[]> = new Map();
  private executionContexts: Map<string, any> = new Map();

  constructor(db: Pool, redis: Redis) {
    super();
    this.db = db;
    this.redis = redis;
    this.initializeAgents();
    this.startExecutionLoop();
  }

  private initializeAgents() {
    // Initialize available agents
    const agents: Agent[] = [
      {
        id: 'claude-primary',
        type: 'claude',
        status: 'idle',
        capabilities: ['code', 'test', 'documentation', 'review'],
        maxConcurrent: 1,
        activeCount: 0
      },
      {
        id: 'gpt4-secondary',
        type: 'gpt4',
        status: 'idle',
        capabilities: ['code', 'test', 'analysis'],
        maxConcurrent: 2,
        activeCount: 0
      }
    ];

    agents.forEach(agent => this.agents.set(agent.id, agent));
  }

  async startSprintAutopilot(sprintId: string, config?: any): Promise<string> {
    // Create new autopilot session
    const sessionId = this.generateId();
    
    // Fetch sprint tasks
    const tasks = await this.fetchSprintTasks(sprintId);
    
    // Initialize session
    const session: AutopilotSession = {
      id: sessionId,
      projectId: await this.getProjectIdFromSprint(sprintId),
      sprintId,
      status: 'active',
      startedAt: new Date(),
      config: {
        maxAgents: config?.maxAgents || 3,
        requireReview: config?.requireReview || false,
        continuousMode: true,
        costLimit: config?.costLimit
      },
      metrics: {
        tasksTotal: tasks.length,
        tasksCompleted: 0,
        tasksFailed: 0,
        totalCost: 0,
        averageTimePerTask: 0
      }
    };

    this.sessions.set(sessionId, session);
    
    // Queue tasks with intelligent ordering
    const orderedTasks = this.prioritizeTasks(tasks);
    this.taskQueues.set(sessionId, orderedTasks);
    
    // Start execution
    this.emit('session:started', { sessionId, taskCount: tasks.length });
    
    // Begin processing
    this.processNextTask(sessionId);
    
    return sessionId;
  }

  private async processNextTask(sessionId: string) {
    const session = this.sessions.get(sessionId);
    if (!session || session.status !== 'active') return;

    const queue = this.taskQueues.get(sessionId) || [];
    const nextTask = queue.find(t => t.status === 'queued');

    if (!nextTask) {
      // All tasks completed
      this.completeSession(sessionId);
      return;
    }

    // Find best available agent
    const agent = this.selectBestAgent(nextTask);
    if (!agent) {
      // No agents available, retry in a moment
      setTimeout(() => this.processNextTask(sessionId), 5000);
      return;
    }

    // Assign and execute
    nextTask.status = 'in_progress';
    nextTask.assignedAgent = agent.id;
    agent.status = 'working';
    agent.currentTask = nextTask.id;
    agent.activeCount++;

    this.emit('task:started', { 
      sessionId, 
      taskId: nextTask.id, 
      agentId: agent.id 
    });

    try {
      // Execute task with continuation pattern
      const result = await this.executeTaskWithAgent(
        nextTask, 
        agent, 
        this.executionContexts.get(sessionId)
      );

      // Update context for next task
      this.updateExecutionContext(sessionId, nextTask.id, result);

      // Mark complete
      nextTask.status = 'completed';
      session.metrics.tasksCompleted++;

      this.emit('task:completed', { 
        sessionId, 
        taskId: nextTask.id, 
        result 
      });

      // CRITICAL: Continue immediately to prevent stopping
      this.continuousExecutionChain(sessionId, nextTask, result);

    } catch (error) {
      nextTask.status = 'failed';
      session.metrics.tasksFailed++;
      
      this.emit('task:failed', { 
        sessionId, 
        taskId: nextTask.id, 
        error 
      });

      // Retry or skip based on config
      if (session.config.continuousMode) {
        this.processNextTask(sessionId); // Keep going
      }
    } finally {
      agent.status = 'idle';
      agent.currentTask = undefined;
      agent.activeCount--;
    }
  }

  private continuousExecutionChain(
    sessionId: string, 
    completedTask: Task, 
    result: any
  ) {
    // Key innovation: Chain execution without pause
    const queue = this.taskQueues.get(sessionId) || [];
    
    // Find dependent tasks that can now run
    const unlockedTasks = queue.filter(t => 
      t.dependencies.includes(completedTask.id) &&
      t.status === 'queued'
    );

    // Update their context with the result
    unlockedTasks.forEach(task => {
      task.context = {
        ...task.context,
        previousResult: result,
        continuationPrompt: this.generateContinuationPrompt(completedTask, task)
      };
    });

    // Immediately process next task(s)
    // This prevents the "agent stops" problem
    setImmediate(() => {
      this.processNextTask(sessionId);
      
      // If multiple agents available, process in parallel
      const availableAgents = Array.from(this.agents.values())
        .filter(a => a.status === 'idle');
      
      availableAgents.forEach(() => {
        this.processNextTask(sessionId);
      });
    });
  }

  private generateContinuationPrompt(previous: Task, next: Task): string {
    return `
      Previous task "${previous.title}" completed successfully.
      Continue with the next task: "${next.title}"
      
      Maintain the same:
      - Code style and patterns
      - Testing approach
      - Documentation format
      
      Build upon the previous work without stopping.
      The goal is continuous progress through the entire sprint.
    `;
  }

  private async executeTaskWithAgent(
    task: Task, 
    agent: Agent, 
    context: any
  ): Promise<any> {
    // Agent-specific execution logic
    switch (agent.type) {
      case 'claude':
        return this.executeWithClaude(task, context);
      case 'gpt4':
        return this.executeWithGPT4(task, context);
      default:
        throw new Error(`Unknown agent type: ${agent.type}`);
    }
  }

  private async executeWithClaude(task: Task, context: any): Promise<any> {
    // Claude execution via API or MCP
    const prompt = this.buildTaskPrompt(task, context);
    
    // TODO: Actual Claude API call
    // For now, simulate execution
    await this.simulateWork(2000);
    
    return {
      success: true,
      output: `Completed ${task.title}`,
      codeChanges: [],
      testsAdded: 0,
      documentation: ''
    };
  }

  private async executeWithGPT4(task: Task, context: any): Promise<any> {
    // GPT-4 execution
    const prompt = this.buildTaskPrompt(task, context);
    
    // TODO: Actual GPT-4 API call
    await this.simulateWork(1500);
    
    return {
      success: true,
      output: `Completed ${task.title}`,
      codeChanges: [],
      testsAdded: 0,
      documentation: ''
    };
  }

  private buildTaskPrompt(task: Task, context: any): string {
    return `
      Task: ${task.title}
      Description: ${task.description}
      
      ${context?.continuationPrompt || ''}
      
      Previous Context: ${JSON.stringify(context?.previousResult || {})}
      
      Requirements:
      1. Complete the task fully
      2. Write tests if applicable
      3. Update documentation
      4. Prepare context for next task
      
      Output format: JSON with success, output, codeChanges, testsAdded, documentation
    `;
  }

  private selectBestAgent(task: Task): Agent | null {
    const availableAgents = Array.from(this.agents.values())
      .filter(a => a.status === 'idle' && a.activeCount < a.maxConcurrent);

    if (availableAgents.length === 0) return null;

    // Score agents based on task requirements
    const scores = availableAgents.map(agent => ({
      agent,
      score: this.calculateAgentScore(agent, task)
    }));

    scores.sort((a, b) => b.score - a.score);
    return scores[0]?.agent || null;
  }

  private calculateAgentScore(agent: Agent, task: Task): number {
    let score = 0;

    // Match capabilities
    const taskRequirements = this.extractTaskRequirements(task);
    taskRequirements.forEach(req => {
      if (agent.capabilities.includes(req)) score += 10;
    });

    // Consider agent type preferences
    if (task.complexity > 7 && agent.type === 'claude') score += 5;
    if (task.complexity <= 7 && agent.type === 'gpt4') score += 3;

    // Load balancing
    score -= agent.activeCount * 2;

    return score;
  }

  private extractTaskRequirements(task: Task): string[] {
    const requirements: string[] = [];
    
    if (task.title.toLowerCase().includes('test')) requirements.push('test');
    if (task.title.toLowerCase().includes('doc')) requirements.push('documentation');
    if (task.description.toLowerCase().includes('review')) requirements.push('review');
    requirements.push('code'); // Default

    return requirements;
  }

  private prioritizeTasks(tasks: any[]): Task[] {
    return tasks
      .map(t => ({
        id: this.generateId(),
        issueId: t.id,
        title: t.title,
        description: t.description || '',
        dependencies: t.dependencies || [],
        priority: t.priority || 5,
        complexity: t.story_points || 3,
        status: 'queued' as const
      }))
      .sort((a, b) => {
        // Dependencies first
        if (a.dependencies.length !== b.dependencies.length) {
          return a.dependencies.length - b.dependencies.length;
        }
        // Then priority
        if (a.priority !== b.priority) {
          return b.priority - a.priority;
        }
        // Then complexity (simple first)
        return a.complexity - b.complexity;
      });
  }

  private updateExecutionContext(sessionId: string, taskId: string, result: any) {
    const context = this.executionContexts.get(sessionId) || {};
    context[taskId] = result;
    context.lastCompleted = taskId;
    context.timestamp = new Date();
    this.executionContexts.set(sessionId, context);
  }

  private async fetchSprintTasks(sprintId: string): Promise<any[]> {
    const result = await this.db.query(`
      SELECT i.* 
      FROM issues i
      JOIN sprint_issues si ON i.id = si.issue_id
      WHERE si.sprint_id = $1
      ORDER BY i.priority DESC, i.created_at
    `, [sprintId]);
    
    return result.rows;
  }

  private async getProjectIdFromSprint(sprintId: string): Promise<string> {
    const result = await this.db.query(
      'SELECT project_id FROM sprints WHERE id = $1',
      [sprintId]
    );
    return result.rows[0]?.project_id;
  }

  private completeSession(sessionId: string) {
    const session = this.sessions.get(sessionId);
    if (!session) return;

    session.status = 'completed';
    this.emit('session:completed', { 
      sessionId, 
      metrics: session.metrics 
    });

    // Clean up
    this.taskQueues.delete(sessionId);
    this.executionContexts.delete(sessionId);
  }

  private startExecutionLoop() {
    // Monitor and process tasks continuously
    setInterval(() => {
      this.sessions.forEach((session, sessionId) => {
        if (session.status === 'active') {
          // Check for stuck tasks and restart if needed
          this.checkAndRestartStuckTasks(sessionId);
        }
      });
    }, 10000); // Every 10 seconds
  }

  private checkAndRestartStuckTasks(sessionId: string) {
    const queue = this.taskQueues.get(sessionId) || [];
    const stuckTasks = queue.filter(t => 
      t.status === 'in_progress' && 
      !this.isTaskActivelyProcessing(t.id)
    );

    stuckTasks.forEach(task => {
      task.status = 'queued';
      task.assignedAgent = undefined;
      this.processNextTask(sessionId);
    });
  }

  private isTaskActivelyProcessing(taskId: string): boolean {
    return Array.from(this.agents.values())
      .some(agent => agent.currentTask === taskId);
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private async simulateWork(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Public API
  async pauseSession(sessionId: string) {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.status = 'paused';
      this.emit('session:paused', { sessionId });
    }
  }

  async resumeSession(sessionId: string) {
    const session = this.sessions.get(sessionId);
    if (session && session.status === 'paused') {
      session.status = 'active';
      this.emit('session:resumed', { sessionId });
      this.processNextTask(sessionId);
    }
  }

  getSessionStatus(sessionId: string): AutopilotSession | undefined {
    return this.sessions.get(sessionId);
  }

  getActiveAgents(): Agent[] {
    return Array.from(this.agents.values())
      .filter(a => a.status === 'working');
  }
}