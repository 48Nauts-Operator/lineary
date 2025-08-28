// ABOUTME: Bug reporting system with automatic issue creation and tracking
// ABOUTME: Handles bug submissions, status updates, and resolution workflow

const express = require('express');
const router = express.Router();

module.exports = (pool) => {
  // Submit new bug report
  router.post('/bugs/report', async (req, res) => {
    const {
      project_id,
      title,
      description,
      severity = 'medium',
      reporter_email,
      reporter_name,
      environment,
      steps_to_reproduce,
      expected_behavior,
      actual_behavior,
      error_message,
      stack_trace,
      screenshot_url,
      browser_info,
      system_info
    } = req.body;
    
    try {
      const client = await pool.connect();
      
      try {
        await client.query('BEGIN');
        
        // Create bug report
        const bugResult = await client.query(`
          INSERT INTO bug_reports (
            project_id, title, description, severity,
            reporter_email, reporter_name, environment,
            steps_to_reproduce, expected_behavior, actual_behavior,
            error_message, stack_trace, screenshot_url,
            browser_info, system_info
          )
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
          RETURNING *
        `, [
          project_id, title, description, severity,
          reporter_email, reporter_name, environment,
          steps_to_reproduce, expected_behavior, actual_behavior,
          error_message, stack_trace, screenshot_url,
          browser_info, system_info
        ]);
        
        const bug = bugResult.rows[0];
        
        // Auto-create issue for high severity bugs
        if (severity === 'critical' || severity === 'high') {
          const issueResult = await client.query(`
            INSERT INTO issues (
              project_id, title, description, status, priority, labels
            )
            VALUES ($1, $2, $3, 'todo', $4, ARRAY['bug', $5])
            RETURNING id
          `, [
            project_id,
            `[BUG] ${title}`,
            `**Bug Report #${bug.id}**\n\n${description}\n\n**Severity:** ${severity}\n**Reporter:** ${reporter_name || 'Anonymous'}`,
            severity === 'critical' ? 5 : 4,
            severity
          ]);
          
          // Link bug report to issue
          await client.query(`
            UPDATE bug_reports SET issue_id = $1 WHERE id = $2
          `, [issueResult.rows[0].id, bug.id]);
          
          bug.issue_id = issueResult.rows[0].id;
        }
        
        await client.query('COMMIT');
        
        res.json({
          success: true,
          bug_report: bug,
          message: severity === 'critical' || severity === 'high' 
            ? 'Bug reported and issue created for immediate attention'
            : 'Bug report submitted successfully'
        });
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      console.error('Bug report error:', error);
      res.status(500).json({ error: error.message });
    }
  });
  
  // Get all bug reports for a project
  router.get('/bugs/project/:projectId', async (req, res) => {
    const { projectId } = req.params;
    const { status, severity, limit = 50, offset = 0 } = req.query;
    
    try {
      let query = `
        SELECT br.*, 
               i.title as issue_title,
               i.status as issue_status,
               COUNT(bc.id) as comment_count
        FROM bug_reports br
        LEFT JOIN issues i ON br.issue_id = i.id
        LEFT JOIN bug_comments bc ON br.id = bc.bug_report_id
        WHERE br.project_id = $1
      `;
      
      const params = [projectId];
      let paramCount = 1;
      
      if (status) {
        paramCount++;
        query += ` AND br.status = $${paramCount}`;
        params.push(status);
      }
      
      if (severity) {
        paramCount++;
        query += ` AND br.severity = $${paramCount}`;
        params.push(severity);
      }
      
      query += `
        GROUP BY br.id, i.title, i.status
        ORDER BY 
          CASE br.severity
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
          END,
          br.created_at DESC
        LIMIT $${paramCount + 1} OFFSET $${paramCount + 2}
      `;
      
      params.push(limit, offset);
      
      const result = await pool.query(query, params);
      res.json(result.rows);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Get bug report details
  router.get('/bugs/:bugId', async (req, res) => {
    const { bugId } = req.params;
    
    try {
      const bugResult = await pool.query(`
        SELECT br.*, 
               i.title as issue_title,
               i.status as issue_status
        FROM bug_reports br
        LEFT JOIN issues i ON br.issue_id = i.id
        WHERE br.id = $1
      `, [bugId]);
      
      if (bugResult.rows.length === 0) {
        return res.status(404).json({ error: 'Bug report not found' });
      }
      
      const commentsResult = await pool.query(`
        SELECT * FROM bug_comments
        WHERE bug_report_id = $1
        ORDER BY created_at DESC
      `, [bugId]);
      
      res.json({
        ...bugResult.rows[0],
        comments: commentsResult.rows
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Update bug report status
  router.put('/bugs/:bugId/status', async (req, res) => {
    const { bugId } = req.params;
    const { status, resolution_notes, assigned_to } = req.body;
    
    try {
      const result = await pool.query(`
        UPDATE bug_reports
        SET status = COALESCE($2, status),
            resolution_notes = COALESCE($3, resolution_notes),
            assigned_to = COALESCE($4, assigned_to),
            resolved_at = CASE WHEN $2 IN ('resolved', 'closed') THEN CURRENT_TIMESTAMP ELSE resolved_at END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        RETURNING *
      `, [bugId, status, resolution_notes, assigned_to]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Bug report not found' });
      }
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Add comment to bug report
  router.post('/bugs/:bugId/comments', async (req, res) => {
    const { bugId } = req.params;
    const { author, comment, is_internal = false } = req.body;
    
    try {
      const result = await pool.query(`
        INSERT INTO bug_comments (bug_report_id, author, comment, is_internal)
        VALUES ($1, $2, $3, $4)
        RETURNING *
      `, [bugId, author, comment, is_internal]);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Get bug statistics
  router.get('/bugs/stats/:projectId', async (req, res) => {
    const { projectId } = req.params;
    
    try {
      const stats = await pool.query(`
        SELECT 
          COUNT(*) FILTER (WHERE status = 'new') as new_bugs,
          COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed_bugs,
          COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_bugs,
          COUNT(*) FILTER (WHERE status = 'resolved') as resolved_bugs,
          COUNT(*) FILTER (WHERE severity = 'critical') as critical_bugs,
          COUNT(*) FILTER (WHERE severity = 'high') as high_bugs,
          COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '7 days') as bugs_this_week,
          COUNT(*) FILTER (WHERE resolved_at > CURRENT_DATE - INTERVAL '7 days') as resolved_this_week,
          AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) FILTER (WHERE resolved_at IS NOT NULL) as avg_resolution_hours
        FROM bug_reports
        WHERE project_id = $1
      `, [projectId]);
      
      res.json(stats.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  return router;
};