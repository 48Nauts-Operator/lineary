// ABOUTME: MCP (Model Context Protocol) routes for Claude integration
// ABOUTME: Provides MCP-compatible endpoints for AI assistant integration

import { Router, Request, Response } from 'express';

const router = Router();

export function mcpRoutes(context: any) {
  const { db, git, sprintPoker, codeQuality, ai, broadcast } = context;

  // MCP Tool: Create issue with AI estimation
  router.post('/create-issue', async (req: Request, res: Response) => {
    try {
      const { project_id, title, description, assignee, priority } = req.body;
      
      if (!project_id || !title) {
        return res.status(400).json({ 
          error: 'project_id and title are required',
          success: false 
        });
      }

      // Get AI estimation
      let estimation = null;
      if (description) {
        try {
          estimation = await sprintPoker.estimateTask(description, title);
        } catch (error) {
          console.warn('AI estimation failed:', error);
        }
      }

      // Create issue
      const issue = await db.createIssue({
        project_id,
        title,
        description,
        assignee,
        priority: priority || 3,
        story_points: estimation?.story_points,
        estimated_hours: estimation?.estimated_hours,
        ai_estimation: estimation
      });

      // Create Git worktree
      let worktree = null;
      try {
        await git.initialize();
        worktree = await git.createIssueWorktree(issue.id, title);
        await db.updateIssue(issue.id, {
          branch_name: worktree.branch,
          worktree_path: worktree.path
        });
      } catch (error) {
        console.warn('Git worktree creation failed:', error);
      }

      await db.logActivity('issue', issue.id, 'created_via_mcp', { title, estimation });
      broadcast('issue_created', issue);

      res.json({
        success: true,
        issue: {
          id: issue.id,
          title: issue.title,
          status: issue.status,
          story_points: issue.story_points,
          estimated_hours: issue.estimated_hours,
          branch_name: worktree?.branch,
          worktree_path: worktree?.path
        },
        estimation,
        message: `Issue "${title}" created with ${estimation?.story_points || 'unknown'} story points`
      });
    } catch (error) {
      console.error('MCP create issue error:', error);
      res.status(500).json({ 
        success: false,
        error: 'Failed to create issue' 
      });
    }
  });

  // MCP Tool: Start AI-optimized sprint
  router.post('/start-sprint', async (req: Request, res: Response) => {
    try {
      const { project_id, hours, name } = req.body;
      
      if (!project_id || !hours) {
        return res.status(400).json({ 
          error: 'project_id and hours are required',
          success: false 
        });
      }

      if (![2, 4, 8, 24].includes(hours)) {
        return res.status(400).json({ 
          error: 'Hours must be 2, 4, 8, or 24',
          success: false 
        });
      }

      // Get available issues
      const issues = await db.getIssues(project_id);
      const backlogIssues = issues.filter(issue => 
        issue.status === 'backlog' && issue.description
      );

      if (backlogIssues.length === 0) {
        return res.status(400).json({ 
          error: 'No available issues in backlog',
          success: false 
        });
      }

      // Analyze capacity and select optimal issues
      const capacity = await sprintPoker.analyzeSprintCapacity(
        hours,
        backlogIssues.map(issue => ({
          id: issue.id,
          title: issue.title,
          description: issue.description
        }))
      );

      // Create sprint
      const sprint = await db.createSprint({
        project_id,
        name: name || `${hours}h Sprint - ${new Date().toLocaleDateString()}`,
        duration_hours: hours,
        status: 'planned'
      });

      // Add selected issues to sprint
      if (capacity.recommended.length > 0) {
        await db.addIssuesToSprint(sprint.id, capacity.recommended);
        
        // Update issues status to 'todo'
        await Promise.all(
          capacity.recommended.map(issueId =>
            db.updateIssue(issueId, { status: 'todo' })
          )
        );
      }

      await db.logActivity('sprint', sprint.id, 'created_via_mcp', {
        duration_hours: hours,
        selected_issues: capacity.recommended.length,
        total_points: capacity.total_points
      });

      broadcast('sprint_created', sprint);

      res.json({
        success: true,
        sprint: {
          id: sprint.id,
          name: sprint.name,
          duration_hours: sprint.duration_hours,
          status: sprint.status
        },
        capacity,
        message: `Sprint created with ${capacity.recommended.length} issues (${capacity.total_points} points, ${capacity.total_hours}h)`
      });
    } catch (error) {
      console.error('MCP start sprint error:', error);
      res.status(500).json({ 
        success: false,
        error: 'Failed to start sprint' 
      });
    }
  });

  // MCP Tool: Get AI code review
  router.post('/review-code', async (req: Request, res: Response) => {
    try {
      const { issue_id } = req.body;
      
      if (!issue_id) {
        return res.status(400).json({ 
          error: 'issue_id is required',
          success: false 
        });
      }

      const issue = await db.getIssueById(issue_id);
      if (!issue) {
        return res.status(404).json({ 
          error: 'Issue not found',
          success: false 
        });
      }

      if (!issue.branch_name) {
        return res.status(400).json({ 
          error: 'Issue has no associated branch',
          success: false 
        });
      }

      const diff = await git.getDiff(issue.branch_name);
      if (!diff) {
        return res.status(400).json({ 
          error: 'No changes found in branch',
          success: false 
        });
      }

      const review = await ai.reviewCode(diff);
      
      // Update issue with review
      await db.updateIssue(issue.id, { ai_review: review });
      
      await db.logActivity('issue', issue.id, 'code_reviewed_via_mcp');
      broadcast('code_review_completed', { issue_id: issue.id, review });

      res.json({
        success: true,
        review,
        message: `Code review completed for issue "${issue.title}"`
      });
    } catch (error) {
      console.error('MCP code review error:', error);
      res.status(500).json({ 
        success: false,
        error: 'Failed to review code' 
      });
    }
  });

  // MCP Tool: Run quality check
  router.post('/run-quality-check', async (req: Request, res: Response) => {
    try {
      const { issue_id } = req.body;
      
      if (!issue_id) {
        return res.status(400).json({ 
          error: 'issue_id is required',
          success: false 
        });
      }

      const issue = await db.getIssueById(issue_id);
      if (!issue) {
        return res.status(404).json({ 
          error: 'Issue not found',
          success: false 
        });
      }

      if (!issue.worktree_path) {
        return res.status(400).json({ 
          error: 'Issue has no associated worktree',
          success: false 
        });
      }

      const qualityReport = await codeQuality.runPipeline(issue.id);
      
      await db.logActivity('issue', issue.id, 'quality_check_via_mcp');
      broadcast('quality_check_completed', { issue_id: issue.id, report: qualityReport });

      res.json({
        success: true,
        report: qualityReport,
        message: `Quality check completed for issue "${issue.title}"`
      });
    } catch (error) {
      console.error('MCP quality check error:', error);
      res.status(500).json({ 
        success: false,
        error: 'Failed to run quality check' 
      });
    }
  });

  // MCP Tool: Get project summary
  router.get('/project-summary/:project_id', async (req: Request, res: Response) => {
    try {
      const { project_id } = req.params;
      
      const project = await db.getProjectById(project_id);
      if (!project) {
        return res.status(404).json({ 
          error: 'Project not found',
          success: false 
        });
      }

      const issues = await db.getIssues(project_id);
      const sprints = await db.getSprints(project_id);

      const summary = {
        project: {
          id: project.id,
          name: project.name,
          description: project.description
        },
        stats: {
          total_issues: issues.length,
          backlog_issues: issues.filter(i => i.status === 'backlog').length,
          in_progress_issues: issues.filter(i => i.status === 'in_progress').length,
          completed_issues: issues.filter(i => i.status === 'done').length,
          total_sprints: sprints.length,
          active_sprints: sprints.filter(s => s.status === 'active').length,
          total_story_points: issues.reduce((sum, i) => sum + (i.story_points || 0), 0)
        },
        recent_activity: await this.getRecentActivity(project_id)
      };

      res.json({
        success: true,
        summary,
        message: `Project summary for "${project.name}"`
      });
    } catch (error) {
      console.error('MCP project summary error:', error);
      res.status(500).json({ 
        success: false,
        error: 'Failed to get project summary' 
      });
    }
  });

  // Helper method for recent activity (would be implemented in database service)
  async function getRecentActivity(projectId: string) {
    // This would query the activity_log table
    return [];
  }

  return router;
}