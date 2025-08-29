// ABOUTME: Enhanced Lineary backend with advanced features
// ABOUTME: Supports dependencies, timelines, documentation, and analytics

const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const Redis = require('redis');
const TokenEstimator = require('./services/tokenEstimator');
const docsRouter = require('./routes/docs');
const app = express();

// Initialize services
const tokenEstimator = new TokenEstimator();

// Configuration
const PORT = process.env.PORT || 8000;
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://lineary:lineary_password@postgres:5432/lineary_db';
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379';

// Database connection
const pool = new Pool({
  connectionString: DATABASE_URL,
});

// Redis connection
const redis = Redis.createClient({
  url: REDIS_URL
});

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoints
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'lineary-backend',
    timestamp: new Date().toISOString() 
  });
});

app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'lineary-backend',
    timestamp: new Date().toISOString() 
  });
});

// ============ PROJECTS API ============
app.get('/api/projects', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM projects ORDER BY created_at DESC');
    res.json({ projects: result.rows });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get project settings
app.get('/api/projects/:id/settings', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT 
        id, name, github_repo, gitlab_repo, repo_type,
        webhook_secret, auto_create_issues, auto_sync_enabled,
        settings
      FROM projects WHERE id = $1`,
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    const project = result.rows[0];
    res.json({
      github_repo: project.github_repo || '',
      gitlab_repo: project.gitlab_repo || '',
      repo_type: project.repo_type || 'github',
      webhook_secret: project.webhook_secret || '',
      auto_create_issues: project.auto_create_issues || false,
      auto_sync_enabled: project.auto_sync_enabled || false,
      ...project.settings
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update project settings
app.put('/api/projects/:id/settings', async (req, res) => {
  const { 
    github_repo, gitlab_repo, repo_type, webhook_secret,
    auto_create_issues, auto_sync_enabled 
  } = req.body;
  
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');
    
    // Update project settings
    const result = await client.query(
      `UPDATE projects SET 
        github_repo = $1,
        gitlab_repo = $2,
        repo_type = $3,
        webhook_secret = $4,
        auto_create_issues = $5,
        auto_sync_enabled = $6,
        updated_at = CURRENT_TIMESTAMP
      WHERE id = $7 RETURNING *`,
      [
        github_repo || null,
        gitlab_repo || null,
        repo_type || 'github',
        webhook_secret || null,
        auto_create_issues || false,
        auto_sync_enabled || false,
        req.params.id
      ]
    );
    
    if (result.rows.length === 0) {
      throw new Error('Project not found');
    }
    
    // Log settings change
    await client.query(
      `INSERT INTO project_settings_history 
        (project_id, changed_by, changes) 
      VALUES ($1, $2, $3)`,
      [
        req.params.id,
        'user',
        JSON.stringify(req.body)
      ]
    );
    
    await client.query('COMMIT');
    res.json({ success: true, project: result.rows[0] });
  } catch (error) {
    await client.query('ROLLBACK');
    res.status(500).json({ error: error.message });
  } finally {
    client.release();
  }
});

// Test repository connection
app.post('/api/projects/:id/test-repo-connection', async (req, res) => {
  const { repo_url, repo_type } = req.body;
  
  try {
    // Parse repository URL
    const urlPattern = repo_type === 'github' 
      ? /github\.com\/([^\/]+)\/([^\/]+)/
      : /gitlab\.com\/([^\/]+)\/([^\/]+)/;
    
    const match = repo_url.match(urlPattern);
    
    if (!match) {
      return res.json({ 
        success: false, 
        message: `Invalid ${repo_type} repository URL format` 
      });
    }
    
    const [, owner, repo] = match;
    
    // For now, we'll do a basic URL validation
    // In production, you'd actually test the API connection
    if (owner && repo) {
      res.json({ 
        success: true, 
        message: `Successfully validated ${repo_type} repository`,
        details: {
          owner,
          repository: repo.replace(/\.git$/, '')
        }
      });
    } else {
      res.json({ 
        success: false, 
        message: 'Could not parse repository information' 
      });
    }
  } catch (error) {
    res.status(500).json({ 
      success: false,
      message: error.message 
    });
  }
});

app.post('/api/projects', async (req, res) => {
  const { name, description, color, icon } = req.body;
  try {
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    
    const result = await pool.query(
      'INSERT INTO projects (name, description, slug, color, icon) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [name, description, slug, color || '#8B5CF6', icon || 'folder']
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get project by ID
app.get('/api/projects/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM projects WHERE id = $1',
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update project
app.patch('/api/projects/:id', async (req, res) => {
  const updates = req.body;
  const allowedFields = [
    'name', 'description', 'color', 'icon', 'status',
    'github_repo', 'gitlab_repo', 'repo_type'
  ];
  
  try {
    const setClause = [];
    const values = [];
    let paramCount = 1;
    
    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        setClause.push(`${key} = $${paramCount}`);
        values.push(value);
        paramCount++;
      }
    }
    
    if (setClause.length === 0) {
      return res.status(400).json({ error: 'No valid fields to update' });
    }
    
    values.push(req.params.id);
    const query = `UPDATE projects SET ${setClause.join(', ')}, updated_at = CURRENT_TIMESTAMP WHERE id = $${paramCount} RETURNING *`;
    
    const result = await pool.query(query, values);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Project documentation
app.get('/api/projects/:id/documentation', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM project_documentation WHERE project_id = $1 ORDER BY section, created_at DESC',
      [req.params.id]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/projects/:id/documentation', async (req, res) => {
  const { title, content, section } = req.body;
  try {
    const result = await pool.query(
      'INSERT INTO project_documentation (project_id, title, content, section) VALUES ($1, $2, $3, $4) RETURNING *',
      [req.params.id, title, content, section]
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============ ISSUES API ============
app.get('/api/issues', async (req, res) => {
  const { project_id, sprint_id, parent_id } = req.query;
  try {
    let query = `
      SELECT i.*, 
        p.name as project_name,
        parent.title as parent_title,
        COUNT(sub.id) as subtask_count,
        array_agg(DISTINCT dep_issue.title) FILTER (WHERE dep_issue.id IS NOT NULL) as dependency_titles
      FROM issues i
      LEFT JOIN projects p ON i.project_id = p.id
      LEFT JOIN issues parent ON i.parent_issue_id = parent.id
      LEFT JOIN issues sub ON sub.parent_issue_id = i.id
      LEFT JOIN issues dep_issue ON dep_issue.id = ANY(i.depends_on)
      WHERE 1=1
    `;
    const params = [];
    let paramCount = 0;

    if (project_id) {
      params.push(project_id);
      query += ` AND i.project_id = $${++paramCount}`;
    }
    if (sprint_id) {
      params.push(sprint_id);
      query += ` AND i.sprint_id = $${++paramCount}`;
    }
    if (parent_id) {
      params.push(parent_id);
      query += ` AND i.parent_issue_id = $${++paramCount}`;
    }

    query += ' GROUP BY i.id, p.name, parent.title ORDER BY i.created_at DESC';
    
    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/issues', async (req, res) => {
  const { 
    title, description, project_id, priority, 
    parent_issue_id, depends_on, start_date, end_date,
    ai_prompt 
  } = req.body;
  
  try {
    // Generate AI prompt if not provided
    let finalPrompt = ai_prompt;
    if (!finalPrompt && description) {
      finalPrompt = `Task: ${title}\n\nContext: ${description}\n\nRequirements:\n- Implement efficiently\n- Include tests\n- Document changes\n\nSuccess Criteria:\n- All tests pass\n- Code review approved\n- Documentation updated`;
    }
    
    // Calculate story points if not provided
    const storyPoints = req.body.story_points || Math.ceil(description ? description.length / 200 : 3);
    
    // Use TokenEstimator for accurate predictions
    const estimation = tokenEstimator.estimateIssueTokens({
      title,
      description,
      story_points: storyPoints,
      priority: priority || 3,
      ai_docs_generated: true
    });
    
    const estimatedHours = Math.ceil(estimation.estimated_minutes / 60);
    
    const result = await pool.query(
      `INSERT INTO issues (
        project_id, title, description, priority, 
        parent_issue_id, depends_on, start_date, end_date,
        story_points, estimated_hours, status, ai_prompt,
        token_cost, ai_confidence
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) RETURNING *`,
      [
        project_id, title, description, priority || 3,
        parent_issue_id, depends_on || [], start_date, end_date,
        storyPoints, estimatedHours, 'backlog', finalPrompt,
        estimation.token_cost, estimation.ai_confidence
      ]
    );
    
    // Log activity
    await pool.query(
      'INSERT INTO issue_activities (issue_id, activity_type, description) VALUES ($1, $2, $3)',
      [result.rows[0].id, 'created', `Issue created: ${title}`]
    );
    
    // Record project activity for analytics
    await pool.query(
      `INSERT INTO project_activity (project_id, activity_date, activity_type, activity_count)
       VALUES ($1, CURRENT_DATE, 'issue_created', 1)
       ON CONFLICT (project_id, activity_date, activity_type)
       DO UPDATE SET activity_count = project_activity.activity_count + 1`,
      [project_id]
    );
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.patch('/api/issues/:id', async (req, res) => {
  const updates = req.body;
  const allowedFields = [
    'title', 'description', 'status', 'priority', 
    'completion_scope', 'start_date', 'end_date', 
    'token_cost', 'ai_prompt', 'sprint_id'
  ];
  
  try {
    const setClause = [];
    const values = [];
    let paramCount = 1;
    
    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        setClause.push(`${key} = $${paramCount}`);
        values.push(value);
        paramCount++;
      }
    }
    
    if (setClause.length === 0) {
      return res.status(400).json({ error: 'No valid fields to update' });
    }
    
    values.push(req.params.id);
    const query = `UPDATE issues SET ${setClause.join(', ')}, updated_at = CURRENT_TIMESTAMP WHERE id = $${paramCount} RETURNING *`;
    
    const result = await pool.query(query, values);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Issue not found' });
    }
    
    // Record activity if status changed to done
    if (updates.status === 'done') {
      await pool.query(
        `UPDATE issues SET completed_at = CURRENT_TIMESTAMP WHERE id = $1 AND completed_at IS NULL`,
        [req.params.id]
      );
      
      await pool.query(
        `INSERT INTO project_activity (project_id, activity_date, activity_type, activity_count)
         VALUES ($1, CURRENT_DATE, 'issue_completed', 1)
         ON CONFLICT (project_id, activity_date, activity_type)
         DO UPDATE SET activity_count = project_activity.activity_count + 1`,
        [result.rows[0].project_id]
      );
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Issue activities/timeline
app.get('/api/issues/:id/activities', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM issue_activities WHERE issue_id = $1 ORDER BY created_at DESC',
      [req.params.id]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Estimate or re-estimate token cost for an issue
app.post('/api/issues/:id/estimate-tokens', async (req, res) => {
  const { id } = req.params;
  
  try {
    // Fetch the issue
    const issueResult = await pool.query(
      'SELECT * FROM issues WHERE id = $1',
      [id]
    );
    
    if (issueResult.rows.length === 0) {
      return res.status(404).json({ error: 'Issue not found' });
    }
    
    const issue = issueResult.rows[0];
    
    // Calculate token estimation
    const estimation = tokenEstimator.estimateIssueTokens(issue);
    
    // Update the issue with new estimates
    await pool.query(
      `UPDATE issues 
       SET token_cost = $1, 
           ai_confidence = $2,
           estimated_hours = $3
       WHERE id = $4`,
      [
        estimation.token_cost,
        estimation.ai_confidence,
        Math.ceil(estimation.estimated_minutes / 60),
        id
      ]
    );
    
    res.json({
      issue_id: id,
      ...estimation,
      estimated_cost_usd: tokenEstimator.calculateCost(estimation.token_cost)
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/issues/:id/activities', async (req, res) => {
  const { 
    activity_type, 
    description, 
    metadata,
    user_type,
    token_cost,
    execution_time_ms,
    ai_model
  } = req.body;
  
  try {
    const result = await pool.query(
      `INSERT INTO issue_activities (
        issue_id, activity_type, description, metadata, 
        user_type, token_cost, execution_time_ms, ai_model
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *`,
      [
        req.params.id, 
        activity_type, 
        description, 
        metadata || {},
        user_type || 'human',
        token_cost || 0,
        execution_time_ms || null,
        ai_model || null
      ]
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Sub-tasks
app.get('/api/issues/:id/subtasks', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM issues WHERE parent_issue_id = $1 ORDER BY priority, created_at',
      [req.params.id]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============ SPRINTS API ============
app.get('/api/sprints', async (req, res) => {
  const { project_id, status } = req.query;
  try {
    let query = `
      SELECT s.*, 
        COUNT(DISTINCT i.id) as issue_count,
        COUNT(DISTINCT CASE WHEN i.status = 'done' THEN i.id END) as completed_count,
        COUNT(DISTINCT CASE WHEN i.status IN ('in_progress', 'in_review') THEN i.id END) as in_progress_count,
        SUM(i.story_points) as total_points,
        SUM(CASE WHEN i.status = 'done' THEN i.story_points ELSE 0 END) as completed_points,
        AVG(i.completion_scope) as avg_completion
      FROM sprints s
      LEFT JOIN issues i ON i.sprint_id = s.id
      WHERE 1=1
    `;
    const params = [];
    let paramCount = 0;

    if (project_id) {
      params.push(project_id);
      query += ` AND s.project_id = $${++paramCount}`;
    }
    if (status) {
      params.push(status);
      query += ` AND s.status = $${++paramCount}`;
    }

    query += ' GROUP BY s.id ORDER BY s.created_at DESC';
    
    const result = await pool.query(query, params);
    
    // Also fetch the actual issues for each sprint
    for (let sprint of result.rows) {
      const issuesResult = await pool.query(
        'SELECT * FROM issues WHERE sprint_id = $1',
        [sprint.id]
      );
      sprint.issues = issuesResult.rows;
    }
    
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/sprints', async (req, res) => {
  const { name, project_id, start_date, end_date, duration_hours, issue_ids } = req.body;
  try {
    // Calculate planned story points
    let plannedPoints = 0;
    if (issue_ids && issue_ids.length > 0) {
      const pointsResult = await pool.query(
        'SELECT SUM(story_points) as total FROM issues WHERE id = ANY($1)',
        [issue_ids]
      );
      plannedPoints = pointsResult.rows[0].total || 0;
    }
    
    // For continuous execution, we don't need an end_date
    // Use duration_hours or calculate from issues
    const sprintDuration = duration_hours || 8; // Default 8 hours if not specified
    const calculatedEndDate = end_date || new Date(new Date(start_date).getTime() + sprintDuration * 60 * 60 * 1000).toISOString();
    
    // Create sprint
    const result = await pool.query(
      `INSERT INTO sprints (name, project_id, start_date, end_date, status, planned_story_points, duration_hours) 
       VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *`,
      [name, project_id, start_date, calculatedEndDate, 'planned', plannedPoints, sprintDuration]
    );
    
    // Assign issues to sprint
    if (issue_ids && issue_ids.length > 0) {
      await pool.query(
        'UPDATE issues SET sprint_id = $1 WHERE id = ANY($2)',
        [result.rows[0].id, issue_ids]
      );
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Sprint planning - get available issues
app.get('/api/sprints/planning/issues', async (req, res) => {
  const { project_id } = req.query;
  try {
    const query = `
      SELECT i.*, p.name as project_name
      FROM issues i
      JOIN projects p ON i.project_id = p.id
      WHERE i.sprint_id IS NULL 
      AND i.status NOT IN ('done', 'cancelled')
      ${project_id ? 'AND i.project_id = $1' : ''}
      ORDER BY i.priority, i.created_at
    `;
    
    const result = await pool.query(query, project_id ? [project_id] : []);
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Add/remove issues from sprint
app.post('/api/sprints/:id/issues', async (req, res) => {
  const { issue_ids } = req.body;
  try {
    await pool.query(
      'UPDATE issues SET sprint_id = $1 WHERE id = ANY($2)',
      [req.params.id, issue_ids]
    );
    
    // Recalculate sprint points
    const pointsResult = await pool.query(
      'SELECT SUM(story_points) as total FROM issues WHERE sprint_id = $1',
      [req.params.id]
    );
    
    await pool.query(
      'UPDATE sprints SET planned_story_points = $1 WHERE id = $2',
      [pointsResult.rows[0].total || 0, req.params.id]
    );
    
    res.json({ success: true, total_points: pointsResult.rows[0].total });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Sprint burndown data
app.get('/api/sprints/:id/burndown', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT calculate_sprint_burndown($1) as burndown',
      [req.params.id]
    );
    res.json(result.rows[0].burndown || []);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============ CONTINUOUS SPRINT EXECUTION API ============
// Initialize continuous sprint execution
app.post('/api/continuous/sprint/:sprintId/start', async (req, res) => {
  try {
    const { sprintId } = req.params;
    
    // Fetch all tasks in the sprint
    const tasksResult = await pool.query(`
      SELECT i.* 
      FROM issues i
      WHERE i.sprint_id = $1
      ORDER BY i.priority DESC, i.created_at
    `, [sprintId]);

    const tasks = tasksResult.rows;
    
    // Get sprint details
    const sprintResult = await pool.query(
      'SELECT * FROM sprints WHERE id = $1',
      [sprintId]
    );
    const sprint = sprintResult.rows[0];

    // Generate continuation instructions
    const taskList = tasks.map((t, idx) => 
      `${idx + 1}. [${t.status}] ${t.title} (ID: ${t.id})`
    ).join('\n');

    const instructions = `
=== CONTINUOUS SPRINT EXECUTION ACTIVATED ===

Sprint: ${sprint.name}
Total Tasks: ${tasks.length}

CRITICAL INSTRUCTIONS:
1. Complete ALL tasks without stopping
2. After each task, IMMEDIATELY continue to the next
3. Mark each completed: POST /api/continuous/sprint/${sprintId}/task/{taskId}/complete
4. Continue until ALL ${tasks.length} tasks are done

TASKS TO COMPLETE:
${taskList}

Start with task #1 now and DON'T STOP!
`;

    // Store session in Redis
    await redis.set(`continuous:${sprintId}`, JSON.stringify({
      sprintId,
      tasks: tasks.map(t => t.id),
      completed: [],
      current: tasks[0]?.id,
      startedAt: new Date()
    }));

    res.json({
      success: true,
      instructions,
      taskCount: tasks.length
    });
  } catch (error) {
    console.error('Failed to start continuous execution:', error);
    res.status(500).json({ error: error.message });
  }
});

// Mark task complete and get next
app.post('/api/continuous/sprint/:sprintId/task/:taskId/complete', async (req, res) => {
  try {
    const { sprintId, taskId } = req.params;
    
    // Get session from Redis
    const sessionData = await redis.get(`continuous:${sprintId}`);
    if (!sessionData) {
      return res.status(404).json({ error: 'No active continuous session' });
    }
    
    const session = JSON.parse(sessionData);
    
    // Mark task complete
    await pool.query(
      "UPDATE issues SET status = 'done', completed_at = NOW() WHERE id = $1",
      [taskId]
    );
    
    // Update session
    session.completed.push(taskId);
    const currentIndex = session.tasks.indexOf(taskId);
    const nextTaskId = session.tasks[currentIndex + 1];
    
    if (nextTaskId) {
      session.current = nextTaskId;
      await redis.set(`continuous:${sprintId}`, JSON.stringify(session));
      
      // Get next task details
      const nextTask = await pool.query('SELECT * FROM issues WHERE id = $1', [nextTaskId]);
      
      res.json({
        success: true,
        nextInstructions: `
✅ Task completed: ${session.completed.length}/${session.tasks.length}

NEXT TASK: ${nextTask.rows[0].title}
ID: ${nextTaskId}

CONTINUE IMMEDIATELY - Do not stop!
`,
        continueExecution: true
      });
    } else {
      // Sprint complete!
      res.json({
        success: true,
        nextInstructions: `
🎉 SPRINT COMPLETED! 
All ${session.tasks.length} tasks done!
`,
        continueExecution: false
      });
    }
  } catch (error) {
    console.error('Failed to mark task complete:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get continuous session status
app.get('/api/continuous/sprint/:sprintId/status', async (req, res) => {
  try {
    const sessionData = await redis.get(`continuous:${req.params.sprintId}`);
    if (!sessionData) {
      return res.status(404).json({ error: 'No active session' });
    }
    
    const session = JSON.parse(sessionData);
    res.json({
      success: true,
      status: {
        ...session,
        progress: {
          completed: session.completed.length,
          total: session.tasks.length,
          percentage: Math.round((session.completed.length / session.tasks.length) * 100)
        }
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============ ANALYTICS API ============
// Mount comprehensive analytics routes
const analyticsRoutes = require('./routes/analytics');
app.use('/api', analyticsRoutes(pool));

// ============ ATTACHMENTS API ============
// Mount file attachment routes
const attachmentsRoutes = require('./routes/attachments');
app.use('/api', attachmentsRoutes(pool));

// ============ VERSIONING API ============
// Mount auto-versioning routes
const versioningRoutes = require('./routes/versioning');
app.use('/api', versioningRoutes(pool));

// ============ BUG REPORTING API ============
// Mount bug reporting routes
const bugsRoutes = require('./routes/bugs');
app.use('/api', bugsRoutes(pool));

// ============ AI PROMPT TEMPLATES ============
app.get('/api/prompts/templates', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM prompt_templates ORDER BY category, name');
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/prompts/generate', async (req, res) => {
  const { issue_id, template_id, variables } = req.body;
  try {
    // Get template
    const templateResult = await pool.query(
      'SELECT * FROM prompt_templates WHERE id = $1',
      [template_id]
    );
    
    if (templateResult.rows.length === 0) {
      return res.status(404).json({ error: 'Template not found' });
    }
    
    // Generate prompt by replacing variables
    let prompt = templateResult.rows[0].template;
    for (const [key, value] of Object.entries(variables || {})) {
      prompt = prompt.replace(new RegExp(`{${key}}`, 'g'), value);
    }
    
    // Update issue with generated prompt
    if (issue_id) {
      await pool.query(
        'UPDATE issues SET ai_prompt = $1 WHERE id = $2',
        [prompt, issue_id]
      );
    }
    
    res.json({ prompt });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Mount activity routes
const activityRoutes = require('./routes/activities');
app.use('/api', activityRoutes(pool));

// Mount OAuth routes
const oauthRoutes = require('./routes/oauth');
app.use('/api', oauthRoutes(pool));

// Mount webhook routes
const webhookRoutes = require('./routes/webhooks');
const githubAppRoutes = require('./routes/github-app');
const aiFeedbackRoutes = require('./routes/ai-feedback');
app.use('/api', webhookRoutes(pool));

// Add database to request for GitHub App and AI feedback routes
app.use((req, res, next) => {
  req.db = pool;
  next();
});
app.use('/api', githubAppRoutes);
app.use('/api', aiFeedbackRoutes);

// ============ TAGS API ============
app.get('/api/tags', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM tags ORDER BY name');
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create a new tag
app.post('/api/tags', async (req, res) => {
  const { name, color, description } = req.body;
  try {
    // Check if tag already exists
    const existing = await pool.query(
      'SELECT * FROM tags WHERE LOWER(name) = LOWER($1)',
      [name]
    );
    
    if (existing.rows.length > 0) {
      return res.status(409).json({ error: 'Tag already exists' });
    }
    
    const result = await pool.query(
      'INSERT INTO tags (name, color, description) VALUES ($1, $2, $3) RETURNING *',
      [name.toLowerCase(), color || '#8B5CF6', description || '']
    );
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get tags for a specific issue
app.get('/api/issues/:id/tags', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT tags FROM issues WHERE id = $1',
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Issue not found' });
    }
    
    res.json({ tags: result.rows[0].tags || [] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Add a single tag to an issue
app.post('/api/issues/:id/tags', async (req, res) => {
  const { tag } = req.body;
  try {
    // Get current tags
    const currentResult = await pool.query(
      'SELECT tags FROM issues WHERE id = $1',
      [req.params.id]
    );
    
    if (currentResult.rows.length === 0) {
      return res.status(404).json({ error: 'Issue not found' });
    }
    
    const currentTags = currentResult.rows[0].tags || [];
    
    // Add new tag if not already present
    if (!currentTags.includes(tag)) {
      currentTags.push(tag);
      
      await pool.query(
        'UPDATE issues SET tags = $1 WHERE id = $2',
        [currentTags, req.params.id]
      );
    }
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Remove a tag from an issue
app.delete('/api/issues/:id/tags/:tagName', async (req, res) => {
  try {
    const { id, tagName } = req.params;
    
    // Get current tags
    const currentResult = await pool.query(
      'SELECT tags FROM issues WHERE id = $1',
      [id]
    );
    
    if (currentResult.rows.length === 0) {
      return res.status(404).json({ error: 'Issue not found' });
    }
    
    const currentTags = currentResult.rows[0].tags || [];
    const updatedTags = currentTags.filter(t => t !== tagName);
    
    await pool.query(
      'UPDATE issues SET tags = $1 WHERE id = $2',
      [updatedTags, id]
    );
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============ TEST CASES API ============
app.get('/api/issues/:id/test-cases', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM issue_test_cases WHERE issue_id = $1 ORDER BY priority, created_at',
      [req.params.id]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/issues/:id/test-cases', async (req, res) => {
  const { title, test_type, gherkin_scenario, given_steps, when_steps, then_steps, priority } = req.body;
  try {
    const result = await pool.query(`
      INSERT INTO issue_test_cases (
        issue_id, title, test_type, gherkin_scenario,
        given_steps, when_steps, then_steps, priority
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *
    `, [
      req.params.id, title, test_type || 'functional', gherkin_scenario,
      given_steps || [], when_steps || [], then_steps || [], priority || 3
    ]);
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/issues/:id/test-cases/auto-generate', async (req, res) => {
  try {
    await pool.query('SELECT auto_generate_test_cases($1)', [req.params.id]);
    
    const result = await pool.query(
      'SELECT * FROM issue_test_cases WHERE issue_id = $1 ORDER BY created_at DESC LIMIT 3',
      [req.params.id]
    );
    
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.patch('/api/test-cases/:id', async (req, res) => {
  const { status, last_run_result, last_run_duration_ms } = req.body;
  try {
    const result = await pool.query(`
      UPDATE issue_test_cases 
      SET status = $1, last_run_result = $2, last_run_duration_ms = $3, 
          last_run_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
      WHERE id = $4 RETURNING *
    `, [status, last_run_result, last_run_duration_ms, req.params.id]);
    
    // Log test execution
    if (status && result.rows.length > 0) {
      await pool.query(`
        INSERT INTO test_executions (
          test_case_id, issue_id, execution_status, duration_ms
        ) VALUES ($1, $2, $3, $4)
      `, [req.params.id, result.rows[0].issue_id, status, last_run_duration_ms]);
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============ ENHANCED FEATURES API ============

// Get token summary for an issue
app.get('/api/issues/:id/token-summary', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        COALESCE(SUM(token_cost), 0) as total_tokens,
        COALESCE(SUM(token_cost * 0.00002), 0) as cost_usd,
        COUNT(*) as activities_count
      FROM issue_activities 
      WHERE issue_id = $1 AND user_type = 'ai'
    `, [req.params.id]);
    
    const summary = result.rows[0] || {};
    
    res.json({
      total_tokens: parseInt(summary.total_tokens) || 0,
      total_cost: parseInt(summary.total_tokens) || 0,
      input_tokens: Math.floor((parseInt(summary.total_tokens) || 0) * 0.6),
      output_tokens: Math.floor((parseInt(summary.total_tokens) || 0) * 0.4),
      cost_usd: parseFloat(summary.cost_usd) || 0,
      activities_count: parseInt(summary.activities_count) || 0
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get documentation links for an issue
app.get('/api/issues/:id/doc-links', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM issue_documentation_links WHERE issue_id = $1 ORDER BY created_at DESC',
      [req.params.id]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Add documentation link to an issue
app.post('/api/issues/:id/doc-links', async (req, res) => {
  const { title, url, type } = req.body;
  try {
    const result = await pool.query(
      'INSERT INTO issue_documentation_links (issue_id, title, url, link_type) VALUES ($1, $2, $3, $4) RETURNING *',
      [req.params.id, title, url, type || 'spec']
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get git links for an issue
app.get('/api/issues/:id/git-links', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM issue_git_links WHERE issue_id = $1 ORDER BY created_at DESC',
      [req.params.id]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get comments for an issue
app.get('/api/issues/:id/comments', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM issue_comments WHERE issue_id = $1 ORDER BY created_at DESC',
      [req.params.id]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Add comment to an issue
app.post('/api/issues/:id/comments', async (req, res) => {
  const { content, author } = req.body;
  try {
    const result = await pool.query(
      'INSERT INTO issue_comments (issue_id, content, author) VALUES ($1, $2, $3) RETURNING *',
      [req.params.id, content, author || 'Anonymous']
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Convert comment to ticket
app.post('/api/comments/:id/convert-to-ticket', async (req, res) => {
  try {
    // Get the comment
    const commentResult = await pool.query(
      'SELECT * FROM issue_comments WHERE id = $1',
      [req.params.id]
    );
    
    if (commentResult.rows.length === 0) {
      return res.status(404).json({ error: 'Comment not found' });
    }
    
    const comment = commentResult.rows[0];
    
    // Create a new issue from the comment
    const issueResult = await pool.query(
      `INSERT INTO issues (
        project_id, title, description, status, priority, parent_issue_id
      ) VALUES (
        (SELECT project_id FROM issues WHERE id = $1), 
        $2, $3, 'backlog', 3, $1
      ) RETURNING *`,
      [comment.issue_id, 'Sub-task: ' + comment.content.substring(0, 100), comment.content]
    );
    
    // Update comment with converted ticket ID
    await pool.query(
      'UPDATE issue_comments SET converted_to_ticket = $1 WHERE id = $2',
      [issueResult.rows[0].id, req.params.id]
    );
    
    res.json(issueResult.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get detailed activities for an issue
app.get('/api/issues/:id/activities/detailed', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        ia.*,
        ia.activity_type as type,
        ia.token_cost,
        ia.execution_time_ms,
        ia.ai_model as model_used,
        ia.user_type,
        ia.token_cost * 0.6 as input_tokens,
        ia.token_cost * 0.4 as output_tokens,
        ia.token_cost * 0.00002 as cost_usd
      FROM issue_activities ia
      WHERE ia.issue_id = $1
      ORDER BY ia.created_at DESC
    `, [req.params.id]);
    
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete project
app.delete('/api/projects/:id', async (req, res) => {
  try {
    // First delete all issues associated with the project
    await pool.query('DELETE FROM issues WHERE project_id = $1', [req.params.id]);
    
    // Then delete the project
    const result = await pool.query(
      'DELETE FROM projects WHERE id = $1 RETURNING *',
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    res.json({ message: 'Project deleted successfully', project: result.rows[0] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete issue
app.delete('/api/issues/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'DELETE FROM issues WHERE id = $1 RETURNING *',
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Issue not found' });
    }
    
    res.json({ message: 'Issue deleted successfully', issue: result.rows[0] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============ SUB-TASKS API ============

// Create sub-task for an issue
app.post('/api/issues/:id/subtasks', async (req, res) => {
  const parentId = req.params.id;
  const { title, description, priority, estimated_hours, assignee } = req.body;
  
  try {
    // Get parent issue to inherit project_id
    const parentResult = await pool.query(
      'SELECT project_id FROM issues WHERE id = $1',
      [parentId]
    );
    
    if (parentResult.rows.length === 0) {
      return res.status(404).json({ error: 'Parent issue not found' });
    }
    
    // Create sub-task
    const result = await pool.query(
      `INSERT INTO issues (
        project_id, parent_issue_id, title, description, 
        priority, estimated_hours, assignee, issue_type, status
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'subtask', 'backlog') 
      RETURNING *`,
      [
        parentResult.rows[0].project_id, parentId, title, description,
        priority || 3, estimated_hours, assignee
      ]
    );
    
    // Log activity
    await pool.query(
      'INSERT INTO issue_activities (issue_id, activity_type, description) VALUES ($1, $2, $3)',
      [parentId, 'subtask_added', `Sub-task added: ${title}`]
    );
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Convert issue to sub-task
app.post('/api/issues/:id/convert-to-subtask', async (req, res) => {
  const { parent_issue_id } = req.body;
  
  try {
    const result = await pool.query(
      `UPDATE issues 
       SET parent_issue_id = $1, issue_type = 'subtask', updated_at = CURRENT_TIMESTAMP
       WHERE id = $2 
       RETURNING *`,
      [parent_issue_id, req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Issue not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Promote sub-task to issue
app.post('/api/issues/:id/promote-to-issue', async (req, res) => {
  try {
    const result = await pool.query(
      `UPDATE issues 
       SET parent_issue_id = NULL, issue_type = 'issue', updated_at = CURRENT_TIMESTAMP
       WHERE id = $1 
       RETURNING *`,
      [req.params.id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Sub-task not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get issue with all its sub-tasks
app.get('/api/issues/:id/with-subtasks', async (req, res) => {
  try {
    // Get parent issue
    const parentResult = await pool.query(
      'SELECT * FROM issues WHERE id = $1',
      [req.params.id]
    );
    
    if (parentResult.rows.length === 0) {
      return res.status(404).json({ error: 'Issue not found' });
    }
    
    // Get sub-tasks
    const subtasksResult = await pool.query(
      'SELECT * FROM issues WHERE parent_issue_id = $1 ORDER BY priority, created_at',
      [req.params.id]
    );
    
    // Calculate completion based on sub-tasks
    let completion = 0;
    if (subtasksResult.rows.length > 0) {
      const completedCount = subtasksResult.rows.filter(s => s.status === 'done').length;
      completion = Math.round((completedCount / subtasksResult.rows.length) * 100);
    }
    
    res.json({
      ...parentResult.rows[0],
      subtasks: subtasksResult.rows,
      subtask_count: subtasksResult.rows.length,
      calculated_completion: completion
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============ INTEGRATIONS API ============

// OAuth integration endpoints
app.post('/api/projects/:id/integrations/connect', async (req, res) => {
  const { provider } = req.body;
  const projectId = req.params.id;
  
  try {
    // Generate OAuth URLs for each provider
    const oauthConfigs = {
      github: {
        authUrl: `https://github.com/login/oauth/authorize?client_id=${process.env.GITHUB_CLIENT_ID || 'dummy_id'}&redirect_uri=${encodeURIComponent('https://ai-linear.blockonauts.io/api/oauth/callback/github')}&scope=repo,read:user&state=${projectId}`,
        name: 'GitHub'
      },
      gitlab: {
        authUrl: `https://gitlab.com/oauth/authorize?client_id=${process.env.GITLAB_CLIENT_ID || 'dummy_id'}&redirect_uri=${encodeURIComponent('https://ai-linear.blockonauts.io/api/oauth/callback/gitlab')}&response_type=code&scope=api+read_repository&state=${projectId}`,
        name: 'GitLab'
      },
      bitbucket: {
        authUrl: `https://bitbucket.org/site/oauth2/authorize?client_id=${process.env.BITBUCKET_CLIENT_ID || 'dummy_id'}&response_type=code&scope=repository:read+pullrequest:read&state=${projectId}`,
        name: 'Bitbucket'
      },
      slack: {
        authUrl: `https://slack.com/oauth/v2/authorize?client_id=${process.env.SLACK_CLIENT_ID || 'dummy_id'}&scope=chat:write,channels:read,groups:read&redirect_uri=${encodeURIComponent('https://ai-linear.blockonauts.io/api/oauth/callback/slack')}&state=${projectId}`,
        name: 'Slack'
      }
    };
    
    const config = oauthConfigs[provider];
    if (!config) {
      return res.status(400).json({ error: 'Invalid provider' });
    }
    
    // In production, you would store the state in Redis for validation
    if (process.env.NODE_ENV === 'production' && !process.env[`${provider.toUpperCase()}_CLIENT_ID`]) {
      // For now, return a message that OAuth is not configured
      return res.json({ 
        message: `${config.name} OAuth is not configured yet. Please set up OAuth credentials.`,
        requiresSetup: true 
      });
    }
    
    res.json({ authUrl: config.authUrl });
  } catch (error) {
    console.error(`Error initiating ${provider} OAuth:`, error);
    res.status(500).json({ error: error.message });
  }
});

// OAuth callback endpoints (would handle the actual OAuth flow)
app.get('/api/oauth/callback/:provider', async (req, res) => {
  const { provider } = req.params;
  const { code, state: projectId, error } = req.query;
  
  if (error) {
    // Redirect back to the app with error
    return res.redirect(`https://ai-linear.blockonauts.io/projects/${projectId}/settings?error=${error}`);
  }
  
  try {
    // In production, you would:
    // 1. Exchange code for access token
    // 2. Store token securely
    // 3. Update project integration status
    
    // For now, just redirect back with success message
    res.redirect(`https://ai-linear.blockonauts.io/projects/${projectId}/settings?integration=${provider}&status=connected`);
  } catch (error) {
    console.error(`OAuth callback error for ${provider}:`, error);
    res.redirect(`https://ai-linear.blockonauts.io/projects/${projectId}/settings?error=oauth_failed`);
  }
});

// Get integration status
app.get('/api/projects/:id/integrations', async (req, res) => {
  try {
    // In production, fetch from database
    // For now, return mock status
    res.json({
      github: false,
      gitlab: false,
      bitbucket: false,
      slack: false
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Disconnect integration
app.delete('/api/projects/:id/integrations/:provider', async (req, res) => {
  const { provider } = req.params;
  
  try {
    // In production, remove tokens and update database
    // For now, just return success
    res.json({ 
      success: true, 
      message: `${provider} integration disconnected` 
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Documentation routes
app.use('/api/docs', docsRouter);

// Start server
async function startServer() {
  try {
    await redis.connect();
    console.log('Connected to Redis');
    
    // Test database connection
    await pool.query('SELECT 1');
    console.log('Connected to PostgreSQL');
    
    app.listen(PORT, () => {
      console.log(`Lineary backend running on port ${PORT}`);
      console.log(`Public URL: https://lineary.blockonauts.io`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();