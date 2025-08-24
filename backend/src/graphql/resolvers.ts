// ABOUTME: GraphQL resolvers for Lineary API
// ABOUTME: Implements query and mutation logic for all GraphQL operations

export const resolvers = {
  Query: {
    // Projects
    projects: async (parent: any, args: any, context: any) => {
      return await context.db.getProjects();
    },

    project: async (parent: any, { id }: { id: string }, context: any) => {
      return await context.db.getProjectById(id);
    },

    // Issues
    issues: async (parent: any, { project_id }: { project_id?: string }, context: any) => {
      return await context.db.getIssues(project_id);
    },

    issue: async (parent: any, { id }: { id: string }, context: any) => {
      return await context.db.getIssueById(id);
    },

    // Sprints
    sprints: async (parent: any, { project_id }: { project_id?: string }, context: any) => {
      return await context.db.getSprints(project_id);
    },

    sprint: async (parent: any, { id }: { id: string }, context: any) => {
      return await context.db.getSprintById(id);
    },

    // Activity
    activityLog: async (parent: any, { entity_type, entity_id, limit = 50 }: any, context: any) => {
      // This would be implemented in the database service
      return [];
    },

    // Analytics
    projectStats: async (parent: any, { project_id }: { project_id: string }, context: any) => {
      const issues = await context.db.getIssues(project_id);
      const sprints = await context.db.getSprints(project_id);

      return {
        total_issues: issues.length,
        backlog_issues: issues.filter((i: any) => i.status === 'backlog').length,
        in_progress_issues: issues.filter((i: any) => i.status === 'in_progress').length,
        completed_issues: issues.filter((i: any) => i.status === 'done').length,
        total_sprints: sprints.length,
        active_sprints: sprints.filter((s: any) => s.status === 'active').length,
        total_story_points: issues.reduce((sum: number, i: any) => sum + (i.story_points || 0), 0),
        avg_story_points: issues.length > 0 
          ? issues.reduce((sum: number, i: any) => sum + (i.story_points || 0), 0) / issues.length 
          : 0
      };
    },

    sprintStats: async (parent: any, { sprint_id }: { sprint_id: string }, context: any) => {
      const sprint = await context.db.getSprintById(sprint_id);
      const issues = await context.db.getSprintIssues(sprint_id);

      if (!sprint) return null;

      const completedIssues = issues.filter((i: any) => i.status === 'done');
      const totalPoints = issues.reduce((sum: number, i: any) => sum + (i.story_points || 0), 0);
      const completedPoints = completedIssues.reduce((sum: number, i: any) => sum + (i.story_points || 0), 0);

      return {
        total_issues: issues.length,
        completed_issues: completedIssues.length,
        total_points: totalPoints,
        completed_points: completedPoints,
        completion_rate: issues.length > 0 ? (completedIssues.length / issues.length) * 100 : 0,
        velocity: completedPoints,
        estimated_hours: issues.reduce((sum: number, i: any) => sum + (i.estimated_hours || 0), 0),
        actual_hours: issues.reduce((sum: number, i: any) => sum + (i.actual_hours || 0), 0)
      };
    }
  },

  Mutation: {
    // Projects
    createProject: async (parent: any, { input }: any, context: any) => {
      const project = await context.db.createProject(input);
      await context.db.logActivity('project', project.id, 'created', input);
      context.broadcast('project_created', project);
      return project;
    },

    updateProject: async (parent: any, { id, input }: any, context: any) => {
      const project = await context.db.updateProject(id, input);
      await context.db.logActivity('project', id, 'updated', input);
      context.broadcast('project_updated', project);
      return project;
    },

    deleteProject: async (parent: any, { id }: { id: string }, context: any) => {
      // Soft delete by setting is_active to false
      await context.db.updateProject(id, { is_active: false });
      await context.db.logActivity('project', id, 'deleted');
      context.broadcast('project_deleted', { id });
      return true;
    },

    // Issues
    createIssue: async (parent: any, { input }: any, context: any) => {
      // Get AI estimation
      let estimation = null;
      if (input.description) {
        try {
          estimation = await context.sprintPoker.estimateTask(input.description, input.title);
        } catch (error) {
          console.warn('AI estimation failed:', error);
        }
      }

      // Create issue
      const issue = await context.db.createIssue({
        ...input,
        story_points: estimation?.story_points,
        estimated_hours: estimation?.estimated_hours,
        ai_estimation: estimation
      });

      // Create Git worktree
      try {
        await context.git.initialize();
        const worktree = await context.git.createIssueWorktree(issue.id, input.title);
        await context.db.updateIssue(issue.id, {
          branch_name: worktree.branch,
          worktree_path: worktree.path
        });
        issue.branch_name = worktree.branch;
        issue.worktree_path = worktree.path;
      } catch (error) {
        console.warn('Git worktree creation failed:', error);
      }

      await context.db.logActivity('issue', issue.id, 'created', { ...input, estimation });
      context.broadcast('issue_created', issue);
      return issue;
    },

    updateIssue: async (parent: any, { id, input }: any, context: any) => {
      const issue = await context.db.updateIssue(id, input);
      await context.db.logActivity('issue', id, 'updated', input);
      context.broadcast('issue_updated', issue);
      return issue;
    },

    deleteIssue: async (parent: any, { id }: { id: string }, context: any) => {
      const issue = await context.db.getIssueById(id);
      if (issue && issue.branch_name) {
        try {
          await context.git.removeIssueWorktree(id, issue.title);
        } catch (error) {
          console.warn('Failed to remove worktree:', error);
        }
      }
      
      // Delete issue (hard delete for now)
      // await context.db.deleteIssue(id);
      await context.db.logActivity('issue', id, 'deleted');
      context.broadcast('issue_deleted', { id });
      return true;
    },

    estimateIssue: async (parent: any, { id }: { id: string }, context: any) => {
      const issue = await context.db.getIssueById(id);
      if (!issue) throw new Error('Issue not found');

      const estimation = await context.sprintPoker.estimateTask(
        issue.description || '',
        issue.title
      );

      // Update issue with new estimation
      await context.db.updateIssue(id, {
        story_points: estimation.story_points,
        estimated_hours: estimation.estimated_hours,
        ai_estimation: estimation
      });

      return estimation;
    },

    // Sprints
    createSprint: async (parent: any, { input }: any, context: any) => {
      const sprint = await context.db.createSprint(input);
      await context.db.logActivity('sprint', sprint.id, 'created', input);
      context.broadcast('sprint_created', sprint);
      return sprint;
    },

    addIssuesToSprint: async (parent: any, { sprint_id, issue_ids }: any, context: any) => {
      const sprint = await context.db.getSprintById(sprint_id);
      if (!sprint) throw new Error('Sprint not found');

      // Get issues and analyze capacity
      const issues = await Promise.all(
        issue_ids.map((id: string) => context.db.getIssueById(id))
      );

      const validIssues = issues.filter(issue => issue && issue.description);

      const capacity = await context.sprintPoker.analyzeSprintCapacity(
        sprint.duration_hours,
        validIssues.map(issue => ({
          id: issue.id,
          title: issue.title,
          description: issue.description
        }))
      );

      // Add recommended issues to sprint
      await context.db.addIssuesToSprint(sprint_id, capacity.recommended);

      await context.db.logActivity('sprint', sprint_id, 'issues_added', {
        issue_count: capacity.recommended.length,
        total_points: capacity.total_points
      });

      context.broadcast('sprint_updated', { sprint, capacity });
      return capacity;
    },

    startSprint: async (parent: any, { id }: { id: string }, context: any) => {
      const sprint = await context.db.getSprintById(id);
      if (!sprint) throw new Error('Sprint not found');
      if (sprint.status !== 'planned') throw new Error('Sprint must be in planned status');

      const startDate = new Date();
      const endDate = new Date(startDate.getTime() + sprint.duration_hours * 60 * 60 * 1000);

      const updatedSprint = await context.db.updateSprint(id, {
        status: 'active',
        start_date: startDate,
        end_date: endDate
      });

      await context.db.logActivity('sprint', id, 'started');
      context.broadcast('sprint_started', updatedSprint);
      return updatedSprint;
    },

    completeSprint: async (parent: any, { id }: { id: string }, context: any) => {
      const sprint = await context.db.getSprintById(id);
      if (!sprint) throw new Error('Sprint not found');
      if (sprint.status !== 'active') throw new Error('Sprint must be active');

      const issues = await context.db.getSprintIssues(id);
      const completedIssues = issues.filter((issue: any) => issue.status === 'done');
      const completedPoints = completedIssues.reduce((sum: number, issue: any) => sum + (issue.story_points || 0), 0);

      const updatedSprint = await context.db.updateSprint(id, {
        status: 'completed',
        end_date: new Date(),
        velocity: completedPoints
      });

      await context.db.logActivity('sprint', id, 'completed', {
        completed_issues: completedIssues.length,
        velocity: completedPoints
      });

      context.broadcast('sprint_completed', updatedSprint);
      return updatedSprint;
    },

    // AI Features
    reviewCode: async (parent: any, { issue_id }: { issue_id: string }, context: any) => {
      const issue = await context.db.getIssueById(issue_id);
      if (!issue || !issue.branch_name) throw new Error('Issue or branch not found');

      const diff = await context.git.getDiff(issue.branch_name);
      if (!diff) throw new Error('No changes found');

      const review = await context.ai.reviewCode(diff);
      
      // Update issue with review
      await context.db.updateIssue(issue_id, { ai_review: review });
      
      context.broadcast('code_review_completed', { issue_id, review });
      return review;
    },

    generateTests: async (parent: any, { issue_id, file_path }: any, context: any) => {
      const issue = await context.db.getIssueById(issue_id);
      if (!issue || !issue.worktree_path) throw new Error('Issue or worktree not found');

      const tests = await context.ai.generateTests(file_path, issue.worktree_path);
      
      // Mark issue as having AI-generated tests
      await context.db.updateIssue(issue_id, { ai_tests_generated: true });
      
      context.broadcast('tests_generated', { issue_id, tests });
      return tests;
    },

    runQualityCheck: async (parent: any, { issue_id }: { issue_id: string }, context: any) => {
      const issue = await context.db.getIssueById(issue_id);
      if (!issue || !issue.worktree_path) throw new Error('Issue or worktree not found');

      const report = await context.codeQuality.runPipeline(issue_id);
      
      context.broadcast('quality_check_completed', { issue_id, report });
      return report;
    },

    // Capacity Planning
    analyzeCapacity: async (parent: any, { available_hours, issue_ids }: any, context: any) => {
      const issues = await Promise.all(
        issue_ids.map((id: string) => context.db.getIssueById(id))
      );

      const validIssues = issues.filter(issue => issue && issue.description);

      return await context.sprintPoker.analyzeSprintCapacity(
        available_hours,
        validIssues.map(issue => ({
          id: issue.id,
          title: issue.title,
          description: issue.description
        }))
      );
    }
  },

  // Field resolvers
  Project: {
    issues: async (parent: any, args: any, context: any) => {
      return await context.db.getIssues(parent.id);
    },
    sprints: async (parent: any, args: any, context: any) => {
      return await context.db.getSprints(parent.id);
    }
  },

  Issue: {
    project: async (parent: any, args: any, context: any) => {
      return await context.db.getProjectById(parent.project_id);
    }
  },

  Sprint: {
    project: async (parent: any, args: any, context: any) => {
      return await context.db.getProjectById(parent.project_id);
    },
    issues: async (parent: any, args: any, context: any) => {
      return await context.db.getSprintIssues(parent.id);
    }
  }
};