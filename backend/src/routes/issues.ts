// ABOUTME: REST API routes for issue management
// ABOUTME: Handles CRUD operations for issues with AI estimation and Git integration

import { Router, Request, Response } from 'express';

const router = Router();

export function issueRoutes(context: any) {
  const { db, git, sprintPoker, codeQuality, ai, broadcast } = context;

  // Get all issues
  router.get('/', async (req: Request, res: Response) => {
    try {
      const { project_id } = req.query;
      const issues = await db.getIssues(project_id as string);
      res.json(issues);
    } catch (error) {
      console.error('Get issues error:', error);
      res.status(500).json({ error: 'Failed to fetch issues' });
    }
  });

  // Get issue by ID
  router.get('/:id', async (req: Request, res: Response) => {
    try {
      const issue = await db.getIssueById(req.params.id);
      if (!issue) {
        return res.status(404).json({ error: 'Issue not found' });
      }
      res.json(issue);
    } catch (error) {
      console.error('Get issue error:', error);
      res.status(500).json({ error: 'Failed to fetch issue' });
    }
  });

  // Create new issue with AI estimation
  router.post('/', async (req: Request, res: Response) => {
    try {
      const { project_id, title, description, assignee, labels, priority } = req.body;
      
      if (!project_id || !title) {
        return res.status(400).json({ error: 'Project ID and title are required' });
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
        labels: labels || [],
        priority: priority || 3,
        story_points: estimation?.story_points,
        estimated_hours: estimation?.estimated_hours,
        ai_estimation: estimation
      });

      // Create Git worktree
      try {
        await git.initialize();
        const worktree = await git.createIssueWorktree(issue.id, title);
        await db.updateIssue(issue.id, {
          branch_name: worktree.branch,
          worktree_path: worktree.path
        });
        issue.branch_name = worktree.branch;
        issue.worktree_path = worktree.path;
      } catch (error) {
        console.warn('Git worktree creation failed:', error);
      }

      await db.logActivity('issue', issue.id, 'created', { title, estimation });
      broadcast('issue_created', issue);

      res.status(201).json(issue);
    } catch (error) {
      console.error('Create issue error:', error);
      res.status(500).json({ error: 'Failed to create issue' });
    }
  });

  // Update issue
  router.put('/:id', async (req: Request, res: Response) => {
    try {
      const updateData = req.body;
      delete updateData.id; // Prevent ID updates
      
      const issue = await db.updateIssue(req.params.id, updateData);
      
      await db.logActivity('issue', issue.id, 'updated', updateData);
      broadcast('issue_updated', issue);

      res.json(issue);
    } catch (error) {
      console.error('Update issue error:', error);
      res.status(500).json({ error: 'Failed to update issue' });
    }
  });

  // Get issue estimation
  router.post('/:id/estimate', async (req: Request, res: Response) => {
    try {
      const issue = await db.getIssueById(req.params.id);
      if (!issue) {
        return res.status(404).json({ error: 'Issue not found' });
      }

      const estimation = await sprintPoker.estimateTask(
        issue.description || '',
        issue.title
      );

      // Update issue with new estimation
      await db.updateIssue(issue.id, {
        story_points: estimation.story_points,
        estimated_hours: estimation.estimated_hours,
        ai_estimation: estimation
      });

      res.json(estimation);
    } catch (error) {
      console.error('Issue estimation error:', error);
      res.status(500).json({ error: 'Failed to estimate issue' });
    }
  });

  // Run quality check on issue
  router.post('/:id/quality-check', async (req: Request, res: Response) => {
    try {
      const issue = await db.getIssueById(req.params.id);
      if (!issue || !issue.worktree_path) {
        return res.status(404).json({ error: 'Issue or worktree not found' });
      }

      const qualityReport = await codeQuality.runPipeline(issue.id);
      
      broadcast('quality_check_completed', { issue_id: issue.id, report: qualityReport });

      res.json(qualityReport);
    } catch (error) {
      console.error('Quality check error:', error);
      res.status(500).json({ error: 'Failed to run quality check' });
    }
  });

  // Get AI code review
  router.post('/:id/code-review', async (req: Request, res: Response) => {
    try {
      const issue = await db.getIssueById(req.params.id);
      if (!issue || !issue.branch_name) {
        return res.status(404).json({ error: 'Issue or branch not found' });
      }

      const diff = await git.getDiff(issue.branch_name);
      if (!diff) {
        return res.status(400).json({ error: 'No changes found' });
      }

      const review = await ai.reviewCode(diff);
      
      // Update issue with review
      await db.updateIssue(issue.id, { ai_review: review });
      
      broadcast('code_review_completed', { issue_id: issue.id, review });

      res.json(review);
    } catch (error) {
      console.error('Code review error:', error);
      res.status(500).json({ error: 'Failed to review code' });
    }
  });

  // Generate tests for issue
  router.post('/:id/generate-tests', async (req: Request, res: Response) => {
    try {
      const issue = await db.getIssueById(req.params.id);
      if (!issue || !issue.worktree_path) {
        return res.status(404).json({ error: 'Issue or worktree not found' });
      }

      const { file_path } = req.body;
      if (!file_path) {
        return res.status(400).json({ error: 'File path is required' });
      }

      const tests = await ai.generateTests(file_path, issue.worktree_path);
      
      // Mark issue as having AI-generated tests
      await db.updateIssue(issue.id, { ai_tests_generated: true });
      
      broadcast('tests_generated', { issue_id: issue.id, tests });

      res.json(tests);
    } catch (error) {
      console.error('Test generation error:', error);
      res.status(500).json({ error: 'Failed to generate tests' });
    }
  });

  return router;
}