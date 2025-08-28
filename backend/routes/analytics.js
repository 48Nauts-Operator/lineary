// ABOUTME: Analytics endpoints for project metrics, activity tracking, and insights
// ABOUTME: Provides real-time data for dashboards and reporting

const express = require('express');
const router = express.Router();

module.exports = (pool) => {
  // Get comprehensive dashboard data
  router.get('/analytics/dashboard/:projectId', async (req, res) => {
    const { projectId } = req.params;
    const { days = 30 } = req.query;
    
    try {
      const client = await pool.connect();
      
      try {
        // Get project basic stats
        const projectStats = await client.query(`
          SELECT 
            p.id,
            p.name,
            p.created_at,
            COUNT(DISTINCT i.id) as total_issues,
            COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'done') as completed_issues,
            COUNT(DISTINCT i.id) FILTER (WHERE i.status IN ('todo', 'in_progress')) as active_issues,
            COUNT(DISTINCT i.assignee) as team_members,
            AVG(CASE WHEN i.status = 'done' AND i.completed_at IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (i.completed_at - i.created_at))/3600 
                ELSE NULL END) as avg_cycle_time_hours
          FROM projects p
          LEFT JOIN issues i ON p.id = i.project_id
          WHERE p.id = $1
          GROUP BY p.id, p.name, p.created_at
        `, [projectId]);

        // Get activity heatmap data
        const activityData = await client.query(`
          SELECT 
            DATE(activity_date) as date,
            activity_type,
            SUM(activity_count) as count
          FROM project_activity
          WHERE project_id = $1
          AND activity_date > CURRENT_DATE - INTERVAL '${parseInt(days)} days'
          GROUP BY DATE(activity_date), activity_type
          ORDER BY date DESC
        `, [projectId]);

        // Get token usage
        const tokenUsage = await client.query(`
          SELECT 
            DATE(created_at) as date,
            SUM(prompt_tokens) as prompt_tokens,
            SUM(completion_tokens) as completion_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(cost) as total_cost,
            COUNT(*) as usage_count
          FROM token_usage
          WHERE project_id = $1
          AND created_at > CURRENT_DATE - INTERVAL '${parseInt(days)} days'
          GROUP BY DATE(created_at)
          ORDER BY date DESC
        `, [projectId]);

        // Get time tracking data
        const timeTracking = await client.query(`
          SELECT 
            DATE(created_at) as date,
            SUM(hours_estimated) as hours_estimated,
            SUM(hours_actual) as hours_actual,
            SUM(hours_saved) as hours_saved,
            COUNT(*) as tasks_tracked
          FROM time_tracking
          WHERE project_id = $1
          AND created_at > CURRENT_DATE - INTERVAL '${parseInt(days)} days'
          GROUP BY DATE(created_at)
          ORDER BY date DESC
        `, [projectId]);

        // Calculate AI time saved
        const aiTimeSaved = await client.query(`
          SELECT 
            COALESCE(SUM(hours_saved), 0) as total_hours_saved,
            COUNT(*) as ai_assisted_tasks
          FROM time_tracking
          WHERE project_id = $1
          AND hours_saved > 0
        `, [projectId]);

        // Get recent issues velocity
        const velocity = await client.query(`
          SELECT 
            DATE_TRUNC('week', completed_at) as week,
            COUNT(*) as issues_completed,
            SUM(story_points) as story_points_completed
          FROM issues
          WHERE project_id = $1
          AND status = 'done'
          AND completed_at IS NOT NULL
          AND completed_at > CURRENT_DATE - INTERVAL '${parseInt(days)} days'
          GROUP BY DATE_TRUNC('week', completed_at)
          ORDER BY week DESC
        `, [projectId]);

        // Get issue distribution
        const issueDistribution = await client.query(`
          SELECT 
            status,
            priority,
            COUNT(*) as count
          FROM issues
          WHERE project_id = $1
          GROUP BY status, priority
        `, [projectId]);

        res.json({
          project: projectStats.rows[0] || {},
          activity: {
            heatmap: activityData.rows,
            summary: {
              total_activities: activityData.rows.reduce((sum, row) => sum + parseInt(row.count), 0),
              active_days: new Set(activityData.rows.map(r => r.date)).size
            }
          },
          tokenUsage: {
            daily: tokenUsage.rows,
            summary: {
              total_tokens: tokenUsage.rows.reduce((sum, row) => sum + (parseInt(row.total_tokens) || 0), 0),
              total_cost: tokenUsage.rows.reduce((sum, row) => sum + (parseFloat(row.total_cost) || 0), 0)
            }
          },
          timeTracking: {
            daily: timeTracking.rows,
            aiSaved: aiTimeSaved.rows[0]
          },
          velocity: velocity.rows,
          distribution: issueDistribution.rows
        });
      } finally {
        client.release();
      }
    } catch (error) {
      console.error('Analytics dashboard error:', error);
      res.status(500).json({ error: error.message });
    }
  });

  // Record activity
  router.post('/analytics/activity', async (req, res) => {
    const { project_id, activity_type, activity_count = 1 } = req.body;
    
    try {
      const result = await pool.query(`
        INSERT INTO project_activity (project_id, activity_date, activity_type, activity_count)
        VALUES ($1, CURRENT_DATE, $2, $3)
        ON CONFLICT (project_id, activity_date, activity_type)
        DO UPDATE SET activity_count = project_activity.activity_count + $3
        RETURNING *
      `, [project_id, activity_type, activity_count]);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Record token usage
  router.post('/analytics/token-usage', async (req, res) => {
    const { 
      project_id, 
      model_name, 
      prompt_tokens, 
      completion_tokens, 
      total_tokens,
      cost = 0 
    } = req.body;
    
    try {
      const result = await pool.query(`
        INSERT INTO token_usage 
        (project_id, model_name, prompt_tokens, completion_tokens, total_tokens, cost)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
      `, [project_id, model_name, prompt_tokens, completion_tokens, total_tokens, cost]);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Record time tracking
  router.post('/analytics/time-tracking', async (req, res) => {
    const { 
      project_id,
      issue_id,
      hours_estimated = 0,
      hours_actual = 0,
      hours_saved = 0
    } = req.body;
    
    try {
      const result = await pool.query(`
        INSERT INTO time_tracking 
        (project_id, issue_id, hours_estimated, hours_actual, hours_saved)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
      `, [project_id, issue_id, hours_estimated, hours_actual, hours_saved]);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get activity heatmap
  router.get('/analytics/heatmap/:projectId', async (req, res) => {
    const { projectId } = req.params;
    const { days = 365 } = req.query;
    
    try {
      const result = await pool.query(`
        SELECT 
          DATE(activity_date) as date,
          SUM(activity_count) as count,
          array_agg(DISTINCT activity_type) as types
        FROM project_activity
        WHERE project_id = $1
        AND activity_date > CURRENT_DATE - INTERVAL '${parseInt(days)} days'
        GROUP BY DATE(activity_date)
        ORDER BY date
      `, [projectId]);
      
      // Format for GitHub-style heatmap
      const heatmap = {};
      result.rows.forEach(row => {
        heatmap[row.date] = {
          count: parseInt(row.count),
          level: getActivityLevel(parseInt(row.count)),
          types: row.types
        };
      });
      
      res.json(heatmap);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get AI time saved counter
  router.get('/analytics/ai-time-saved/:projectId', async (req, res) => {
    const { projectId } = req.params;
    
    try {
      const result = await pool.query(`
        SELECT 
          COALESCE(SUM(hours_saved), 0) as total_hours_saved,
          COUNT(DISTINCT issue_id) as ai_assisted_issues,
          AVG(hours_saved) as avg_hours_per_issue
        FROM time_tracking
        WHERE project_id = $1
        AND hours_saved > 0
      `, [projectId]);
      
      const data = result.rows[0];
      
      res.json({
        totalHoursSaved: parseFloat(data.total_hours_saved),
        displayValue: formatHoursSaved(parseFloat(data.total_hours_saved)),
        aiAssistedIssues: parseInt(data.ai_assisted_issues),
        avgHoursPerIssue: parseFloat(data.avg_hours_per_issue || 0)
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Utility functions
  function getActivityLevel(count) {
    if (count === 0) return 0;
    if (count <= 3) return 1;
    if (count <= 7) return 2;
    if (count <= 15) return 3;
    return 4;
  }

  function formatHoursSaved(hours) {
    if (hours < 1) {
      return `${Math.round(hours * 60)} minutes`;
    } else if (hours < 24) {
      return `${hours.toFixed(1)} hours`;
    } else {
      const days = Math.floor(hours / 8); // Assuming 8-hour workday
      return `${days} ${days === 1 ? 'day' : 'days'}`;
    }
  }

  return router;
};