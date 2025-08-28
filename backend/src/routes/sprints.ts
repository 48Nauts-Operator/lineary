// ABOUTME: REST API routes for sprint management
// ABOUTME: Handles sprint creation, planning, and capacity analysis

import { Router, Request, Response } from 'express';

const router = Router();

export function sprintRoutes(context: any) {
  const { db, sprintPoker, broadcast } = context;

  // Get all sprints
  router.get('/', async (req: Request, res: Response) => {
    try {
      const { project_id } = req.query;
      const sprints = await db.getSprints(project_id as string);
      res.json(sprints);
    } catch (error) {
      console.error('Get sprints error:', error);
      res.status(500).json({ error: 'Failed to fetch sprints' });
    }
  });

  // Get sprint by ID
  router.get('/:id', async (req: Request, res: Response) => {
    try {
      const sprint = await db.getSprintById(req.params.id);
      if (!sprint) {
        return res.status(404).json({ error: 'Sprint not found' });
      }
      
      // Get sprint issues
      const issues = await db.getSprintIssues(sprint.id);
      
      res.json({ ...sprint, issues });
    } catch (error) {
      console.error('Get sprint error:', error);
      res.status(500).json({ error: 'Failed to fetch sprint' });
    }
  });

  // Create new sprint
  router.post('/', async (req: Request, res: Response) => {
    try {
      const { project_id, name, goal, duration_hours } = req.body;
      
      if (!project_id || !name || !duration_hours) {
        return res.status(400).json({ 
          error: 'Project ID, name, and duration are required' 
        });
      }

      if (![2, 4, 8, 24].includes(duration_hours)) {
        return res.status(400).json({ 
          error: 'Duration must be 2, 4, 8, or 24 hours' 
        });
      }

      const sprint = await db.createSprint({
        project_id,
        name,
        goal,
        duration_hours
      });

      await db.logActivity('sprint', sprint.id, 'created', { name, duration_hours });
      broadcast('sprint_created', sprint);

      res.status(201).json(sprint);
    } catch (error) {
      console.error('Create sprint error:', error);
      res.status(500).json({ error: 'Failed to create sprint' });
    }
  });

  // Add issues to sprint with capacity analysis
  router.post('/:id/issues', async (req: Request, res: Response) => {
    try {
      const { issue_ids } = req.body;
      
      if (!Array.isArray(issue_ids) || issue_ids.length === 0) {
        return res.status(400).json({ error: 'Issue IDs array is required' });
      }

      const sprint = await db.getSprintById(req.params.id);
      if (!sprint) {
        return res.status(404).json({ error: 'Sprint not found' });
      }

      // Get issues and analyze capacity
      const issues = await Promise.all(
        issue_ids.map(id => db.getIssueById(id))
      );

      const validIssues = issues.filter(issue => issue && issue.description);
      
      if (validIssues.length === 0) {
        return res.status(400).json({ error: 'No valid issues found' });
      }

      // Analyze sprint capacity
      const capacity = await sprintPoker.analyzeSprintCapacity(
        sprint.duration_hours,
        validIssues.map(issue => ({
          id: issue.id,
          title: issue.title,
          description: issue.description
        }))
      );

      // Add recommended issues to sprint
      await db.addIssuesToSprint(sprint.id, capacity.recommended);

      // Update sprint velocity
      await db.updateSprint(sprint.id, { velocity: capacity.total_points });

      await db.logActivity('sprint', sprint.id, 'issues_added', {
        issue_count: capacity.recommended.length,
        total_points: capacity.total_points,
        total_hours: capacity.total_hours
      });

      broadcast('sprint_updated', { sprint, capacity });

      res.json({
        sprint,
        capacity,
        added_issues: capacity.recommended
      });
    } catch (error) {
      console.error('Add sprint issues error:', error);
      res.status(500).json({ error: 'Failed to add issues to sprint' });
    }
  });

  // Start sprint
  router.post('/:id/start', async (req: Request, res: Response) => {
    try {
      const sprint = await db.getSprintById(req.params.id);
      if (!sprint) {
        return res.status(404).json({ error: 'Sprint not found' });
      }

      if (sprint.status !== 'planned') {
        return res.status(400).json({ error: 'Sprint must be in planned status to start' });
      }

      const startDate = new Date();
      const endDate = new Date(startDate.getTime() + sprint.duration_hours * 60 * 60 * 1000);

      const updatedSprint = await db.updateSprint(sprint.id, {
        status: 'active',
        start_date: startDate,
        end_date: endDate
      });

      await db.logActivity('sprint', sprint.id, 'started', { start_date: startDate });
      broadcast('sprint_started', updatedSprint);

      res.json(updatedSprint);
    } catch (error) {
      console.error('Start sprint error:', error);
      res.status(500).json({ error: 'Failed to start sprint' });
    }
  });

  // Complete sprint
  router.post('/:id/complete', async (req: Request, res: Response) => {
    try {
      const sprint = await db.getSprintById(req.params.id);
      if (!sprint) {
        return res.status(404).json({ error: 'Sprint not found' });
      }

      if (sprint.status !== 'active') {
        return res.status(400).json({ error: 'Sprint must be active to complete' });
      }

      // Get sprint statistics
      const issues = await db.getSprintIssues(sprint.id);
      const completedIssues = issues.filter(issue => issue.status === 'done');
      const totalPoints = issues.reduce((sum, issue) => sum + (issue.story_points || 0), 0);
      const completedPoints = completedIssues.reduce((sum, issue) => sum + (issue.story_points || 0), 0);

      const updatedSprint = await db.updateSprint(sprint.id, {
        status: 'completed',
        end_date: new Date(),
        velocity: completedPoints
      });

      await db.logActivity('sprint', sprint.id, 'completed', {
        total_issues: issues.length,
        completed_issues: completedIssues.length,
        total_points: totalPoints,
        completed_points: completedPoints,
        velocity: completedPoints
      });

      broadcast('sprint_completed', {
        sprint: updatedSprint,
        stats: {
          total_issues: issues.length,
          completed_issues: completedIssues.length,
          total_points: totalPoints,
          completed_points: completedPoints
        }
      });

      res.json(updatedSprint);
    } catch (error) {
      console.error('Complete sprint error:', error);
      res.status(500).json({ error: 'Failed to complete sprint' });
    }
  });

  // Get sprint capacity analysis
  router.post('/:id/analyze-capacity', async (req: Request, res: Response) => {
    try {
      const { available_hours, issue_ids } = req.body;
      
      if (!available_hours || !Array.isArray(issue_ids)) {
        return res.status(400).json({ 
          error: 'Available hours and issue IDs are required' 
        });
      }

      // Get issues
      const issues = await Promise.all(
        issue_ids.map(id => db.getIssueById(id))
      );

      const validIssues = issues.filter(issue => issue && issue.description);

      const capacity = await sprintPoker.analyzeSprintCapacity(
        available_hours,
        validIssues.map(issue => ({
          id: issue.id,
          title: issue.title,
          description: issue.description
        }))
      );

      res.json(capacity);
    } catch (error) {
      console.error('Capacity analysis error:', error);
      res.status(500).json({ error: 'Failed to analyze capacity' });
    }
  });

  return router;
}