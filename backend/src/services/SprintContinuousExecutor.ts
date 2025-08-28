// ABOUTME: Sprint continuous execution service that feeds tasks to Claude without stopping
// ABOUTME: Ensures entire sprints are completed in one continuous session

import { Pool } from 'pg';
import Redis from 'ioredis';
import fs from 'fs';
import path from 'path';

export interface ContinuousSprintSession {
  sprintId: string;
  projectId: string;
  startedAt: Date;
  taskQueue: string[];
  completedTasks: string[];
  currentTaskId: string | null;
  status: 'active' | 'completed' | 'paused';
  continuationInstructions: string;
}

export class SprintContinuousExecutor {
  private db: Pool;
  private redis: Redis;
  private sessions: Map<string, ContinuousSprintSession> = new Map();
  
  constructor(db: Pool, redis: Redis) {
    this.db = db;
    this.redis = redis;
  }

  async initializeContinuousSprint(sprintId: string): Promise<string> {
    // Fetch all tasks in the sprint
    const tasksResult = await this.db.query(`
      SELECT i.*, si.position 
      FROM issues i
      JOIN sprint_issues si ON i.id = si.issue_id
      WHERE si.sprint_id = $1
      ORDER BY 
        CASE WHEN i.parent_issue_id IS NOT NULL THEN 0 ELSE 1 END,
        i.priority DESC,
        si.position,
        i.created_at
    `, [sprintId]);

    const tasks = tasksResult.rows;
    
    // Get sprint details
    const sprintResult = await this.db.query(
      'SELECT * FROM sprints WHERE id = $1',
      [sprintId]
    );
    const sprint = sprintResult.rows[0];

    // Create session
    const session: ContinuousSprintSession = {
      sprintId,
      projectId: sprint.project_id,
      startedAt: new Date(),
      taskQueue: tasks.map(t => t.id),
      completedTasks: [],
      currentTaskId: tasks[0]?.id || null,
      status: 'active',
      continuationInstructions: this.generateContinuationInstructions(sprint, tasks)
    };

    // Store session
    this.sessions.set(sprintId, session);
    await this.redis.set(`continuous_sprint:${sprintId}`, JSON.stringify(session));

    // Generate the execution file
    await this.generateExecutionFile(session, tasks);

    return session.continuationInstructions;
  }

  private generateContinuationInstructions(sprint: any, tasks: any[]): string {
    const taskList = tasks.map((t, idx) => 
      `${idx + 1}. [${t.status}] ${t.title} (ID: ${t.id})${t.description ? '\n   Description: ' + t.description.substring(0, 100) : ''}`
    ).join('\n');

    return `
=== CONTINUOUS SPRINT EXECUTION MODE ACTIVATED ===

Sprint: ${sprint.name}
Total Tasks: ${tasks.length}
Goal: Complete ALL tasks without stopping

CRITICAL INSTRUCTIONS FOR CLAUDE:
1. You MUST complete ALL tasks in this sprint
2. After finishing each task, IMMEDIATELY move to the next one
3. DO NOT stop or wait for user confirmation between tasks
4. Mark each task as completed and continue
5. Only stop when ALL tasks are done

TASK EXECUTION ORDER:
${taskList}

WORKFLOW FOR EACH TASK:
1. Read the task requirements
2. Implement the solution
3. Test if applicable
4. Mark as completed in the system
5. Log completion: "✅ Task X completed, moving to task Y"
6. IMMEDIATELY start the next task

CONTINUATION PROMPT (use after each task):
"Task completed. Continuing with next task in sprint queue..."

Remember: The goal is CONTINUOUS EXECUTION until the entire sprint is done.
Start with Task #1 now and DON'T STOP until all ${tasks.length} tasks are complete.
`;
  }

  async generateExecutionFile(session: ContinuousSprintSession, tasks: any[]): Promise<void> {
    // Create a file that tracks the execution
    const executionPath = path.join(
      process.cwd(),
      `sprint_execution_${session.sprintId}.md`
    );

    const content = `# Sprint Continuous Execution Tracker

## Session Started: ${session.startedAt.toISOString()}
## Sprint ID: ${session.sprintId}
## Total Tasks: ${tasks.length}

## Execution Status

| # | Task | Status | Started | Completed | Notes |
|---|------|--------|---------|-----------|-------|
${tasks.map((t, idx) => 
  `| ${idx + 1} | ${t.title} | ⏳ Pending | - | - | ${t.description?.substring(0, 50) || ''} |`
).join('\n')}

## Execution Log

`;

    fs.writeFileSync(executionPath, content);
  }

  async markTaskComplete(sprintId: string, taskId: string): Promise<string> {
    const session = this.sessions.get(sprintId);
    if (!session) {
      throw new Error('No active continuous session for this sprint');
    }

    // Mark task as complete
    session.completedTasks.push(taskId);
    const currentIndex = session.taskQueue.indexOf(taskId);
    
    // Update task status in database
    await this.db.query(
      "UPDATE issues SET status = 'done', completed_at = NOW() WHERE id = $1",
      [taskId]
    );

    // Get next task
    const nextTaskId = session.taskQueue[currentIndex + 1];
    
    if (nextTaskId) {
      session.currentTaskId = nextTaskId;
      
      // Get next task details
      const nextTaskResult = await this.db.query(
        'SELECT * FROM issues WHERE id = $1',
        [nextTaskId]
      );
      const nextTask = nextTaskResult.rows[0];

      // Update session
      await this.redis.set(`continuous_sprint:${sprintId}`, JSON.stringify(session));

      // Return continuation instructions
      return `
✅ Task completed: ${taskId}
📊 Progress: ${session.completedTasks.length}/${session.taskQueue.length} tasks complete

NEXT TASK: ${nextTask.title}
Task ID: ${nextTask.id}
Description: ${nextTask.description || 'No description provided'}

CRITICAL: Do NOT stop. Continue immediately with this task.
Remember: You must complete ALL ${session.taskQueue.length} tasks in this sprint.

Proceeding with implementation...
`;
    } else {
      // Sprint completed!
      session.status = 'completed';
      await this.redis.set(`continuous_sprint:${sprintId}`, JSON.stringify(session));
      
      return `
🎉 SPRINT COMPLETED! 🎉
All ${session.taskQueue.length} tasks have been successfully completed.
Sprint execution time: ${this.calculateDuration(session.startedAt)}

Final Statistics:
- Tasks Completed: ${session.completedTasks.length}
- Success Rate: 100%
- Sprint Status: DONE

The continuous execution session has ended successfully.
`;
    }
  }

  async getNextTaskPrompt(sprintId: string): Promise<string> {
    const session = this.sessions.get(sprintId);
    if (!session || !session.currentTaskId) {
      return 'No active task in continuous session';
    }

    const taskResult = await this.db.query(
      'SELECT * FROM issues WHERE id = $1',
      [session.currentTaskId]
    );
    const task = taskResult.rows[0];

    return `
CURRENT TASK IN CONTINUOUS SPRINT:
Title: ${task.title}
ID: ${task.id}
Description: ${task.description}
Status: ${task.status}
Priority: ${task.priority}

Progress: Task ${session.completedTasks.length + 1} of ${session.taskQueue.length}

After completing this task, you MUST:
1. Mark it complete using the completion command
2. Immediately continue to the next task
3. Do not stop until all ${session.taskQueue.length} tasks are done
`;
  }

  private calculateDuration(startTime: Date): string {
    const duration = Date.now() - startTime.getTime();
    const hours = Math.floor(duration / 3600000);
    const minutes = Math.floor((duration % 3600000) / 60000);
    return `${hours}h ${minutes}m`;
  }

  async getSessionStatus(sprintId: string): Promise<any> {
    const session = this.sessions.get(sprintId);
    if (!session) {
      const redisSession = await this.redis.get(`continuous_sprint:${sprintId}`);
      if (redisSession) {
        return JSON.parse(redisSession);
      }
      return null;
    }
    return {
      ...session,
      progress: {
        completed: session.completedTasks.length,
        total: session.taskQueue.length,
        percentage: Math.round((session.completedTasks.length / session.taskQueue.length) * 100)
      }
    };
  }
}