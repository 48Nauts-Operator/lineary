// ABOUTME: REST API routes for project management
// ABOUTME: Handles CRUD operations for projects with AI estimation integration

import { Router, Request, Response } from 'express';

const router = Router();

export function projectRoutes(context: any) {
  const { db, sprintPoker, broadcast } = context;

  // Get all projects
  router.get('/', async (req: Request, res: Response) => {
    try {
      const projects = await db.getProjects();
      res.json(projects);
    } catch (error) {
      console.error('Get projects error:', error);
      res.status(500).json({ error: 'Failed to fetch projects' });
    }
  });

  // Get project by ID
  router.get('/:id', async (req: Request, res: Response) => {
    try {
      const project = await db.getProjectById(req.params.id);
      if (!project) {
        return res.status(404).json({ error: 'Project not found' });
      }
      res.json(project);
    } catch (error) {
      console.error('Get project error:', error);
      res.status(500).json({ error: 'Failed to fetch project' });
    }
  });

  // Create new project
  router.post('/', async (req: Request, res: Response) => {
    try {
      const { name, description, color, icon } = req.body;
      
      if (!name) {
        return res.status(400).json({ error: 'Project name is required' });
      }

      const project = await db.createProject({
        name,
        description,
        color,
        icon
      });

      await db.logActivity('project', project.id, 'created', { name });
      broadcast('project_created', project);

      res.status(201).json(project);
    } catch (error) {
      console.error('Create project error:', error);
      res.status(500).json({ error: 'Failed to create project' });
    }
  });

  // Update project
  router.put('/:id', async (req: Request, res: Response) => {
    try {
      const { name, description, color, icon, is_active } = req.body;
      
      const project = await db.updateProject(req.params.id, {
        name,
        description,
        color,
        icon,
        is_active
      });

      await db.logActivity('project', project.id, 'updated', { name });
      broadcast('project_updated', project);

      res.json(project);
    } catch (error) {
      console.error('Update project error:', error);
      res.status(500).json({ error: 'Failed to update project' });
    }
  });

  // Get project issues
  router.get('/:id/issues', async (req: Request, res: Response) => {
    try {
      const issues = await db.getIssues(req.params.id);
      res.json(issues);
    } catch (error) {
      console.error('Get project issues error:', error);
      res.status(500).json({ error: 'Failed to fetch project issues' });
    }
  });

  // Get project sprints
  router.get('/:id/sprints', async (req: Request, res: Response) => {
    try {
      const sprints = await db.getSprints(req.params.id);
      res.json(sprints);
    } catch (error) {
      console.error('Get project sprints error:', error);
      res.status(500).json({ error: 'Failed to fetch project sprints' });
    }
  });

  return router;
}