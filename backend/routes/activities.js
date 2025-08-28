// ABOUTME: Enhanced activity routes for AI tracking and comments
// ABOUTME: Handles human comments, AI executions, and documentation links

const express = require('express');
const router = express.Router();

module.exports = (pool) => {
  // Get detailed activities for an issue
  router.get('/issues/:id/activities/detailed', async (req, res) => {
    try {
      const activities = await pool.query(`
        SELECT 
          ia.*,
          ae.prompt as ai_prompt,
          ae.response as ai_response,
          ae.token_input,
          ae.token_output,
          ae.token_total,
          ae.cost_usd,
          ae.execution_time_ms as ai_execution_time
        FROM issue_activities ia
        LEFT JOIN ai_executions ae ON ia.id = ae.activity_id
        WHERE ia.issue_id = $1
        ORDER BY ia.created_at DESC
      `, [req.params.id]);
      
      res.json(activities.rows);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Add comment or request
  router.post('/issues/:id/comments', async (req, res) => {
    const { content, comment_type, user_id } = req.body;
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');
      
      // Insert comment
      const commentResult = await client.query(`
        INSERT INTO issue_comments (
          issue_id, user_id, comment_type, content, user_type
        ) VALUES ($1, $2, $3, $4, $5) RETURNING *
      `, [req.params.id, user_id || 'user', comment_type || 'comment', content, 'human']);
      
      // Log activity
      await client.query(`
        INSERT INTO issue_activities (
          issue_id, activity_type, description, user_type, metadata
        ) VALUES ($1, $2, $3, $4, $5)
      `, [
        req.params.id,
        comment_type === 'request' ? 'request_added' : 'comment_added',
        `${comment_type === 'request' ? 'Request' : 'Comment'}: ${content.substring(0, 100)}`,
        'human',
        { comment_id: commentResult.rows[0].id }
      ]);
      
      // If it's a request and auto_create_subtask is true, create sub-ticket
      if (comment_type === 'request' && req.body.auto_create_subtask) {
        const subTicketResult = await client.query(
          'SELECT create_sub_ticket_from_request($1, $2, $3)',
          [req.params.id, content, commentResult.rows[0].id]
        );
        commentResult.rows[0].sub_ticket_id = subTicketResult.rows[0].create_sub_ticket_from_request;
      }
      
      await client.query('COMMIT');
      res.json(commentResult.rows[0]);
    } catch (error) {
      await client.query('ROLLBACK');
      res.status(500).json({ error: error.message });
    } finally {
      client.release();
    }
  });

  // Get comments for an issue
  router.get('/issues/:id/comments', async (req, res) => {
    try {
      const result = await pool.query(`
        SELECT 
          c.*,
          sub.title as sub_ticket_title,
          sub.status as sub_ticket_status
        FROM issue_comments c
        LEFT JOIN issues sub ON c.sub_ticket_id = sub.id
        WHERE c.issue_id = $1
        ORDER BY c.created_at DESC
      `, [req.params.id]);
      
      res.json(result.rows);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Add AI execution record
  router.post('/issues/:id/ai-executions', async (req, res) => {
    const { 
      prompt, response, model, token_input, token_output, 
      cost_usd, execution_time_ms, status, metadata 
    } = req.body;
    
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');
      
      // Create AI execution record
      const execResult = await client.query(`
        INSERT INTO ai_executions (
          issue_id, prompt, response, model, token_input, token_output,
          cost_usd, execution_time_ms, status, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING *
      `, [
        req.params.id, prompt, response, model || 'gpt-4', 
        token_input || 0, token_output || 0, cost_usd || 0,
        execution_time_ms, status || 'completed', metadata || {}
      ]);
      
      // Create activity record
      const activityResult = await client.query(`
        INSERT INTO issue_activities (
          issue_id, activity_type, description, user_type, 
          token_cost, ai_model, execution_time_ms, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
      `, [
        req.params.id,
        'ai_execution',
        `AI executed: ${prompt.substring(0, 100)}`,
        'ai',
        token_input + token_output,
        model || 'gpt-4',
        execution_time_ms,
        { execution_id: execResult.rows[0].id }
      ]);
      
      // Link execution to activity
      await client.query(
        'UPDATE ai_executions SET activity_id = $1 WHERE id = $2',
        [activityResult.rows[0].id, execResult.rows[0].id]
      );
      
      // Update issue token cost
      await client.query(`
        UPDATE issues 
        SET token_cost = token_cost + $1 
        WHERE id = $2
      `, [token_input + token_output, req.params.id]);
      
      await client.query('COMMIT');
      res.json(execResult.rows[0]);
    } catch (error) {
      await client.query('ROLLBACK');
      res.status(500).json({ error: error.message });
    } finally {
      client.release();
    }
  });

  // Add documentation link
  router.post('/issues/:id/doc-links', async (req, res) => {
    const { title, url, link_type, description } = req.body;
    
    try {
      const result = await pool.query(`
        INSERT INTO issue_documentation_links (
          issue_id, title, url, link_type, description, created_by
        ) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *
      `, [
        req.params.id, title, url, link_type || 'documentation',
        description, req.body.created_by || 'system'
      ]);
      
      // Log activity
      await pool.query(`
        INSERT INTO issue_activities (
          issue_id, activity_type, description, user_type
        ) VALUES ($1, $2, $3, $4)
      `, [
        req.params.id,
        'doc_link_added',
        `Documentation link added: ${title}`,
        'system'
      ]);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get documentation links
  router.get('/issues/:id/doc-links', async (req, res) => {
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

  // Add git link
  router.post('/issues/:id/git-links', async (req, res) => {
    const { 
      repository_url, branch_name, commit_hash, pull_request_url,
      pr_status, files_changed, lines_added, lines_removed 
    } = req.body;
    
    try {
      const result = await pool.query(`
        INSERT INTO issue_git_links (
          issue_id, repository_url, branch_name, commit_hash,
          pull_request_url, pr_status, files_changed, lines_added, lines_removed
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *
      `, [
        req.params.id, repository_url, branch_name, commit_hash,
        pull_request_url, pr_status, files_changed || 0, 
        lines_added || 0, lines_removed || 0
      ]);
      
      // Log activity
      await pool.query(`
        INSERT INTO issue_activities (
          issue_id, activity_type, description, user_type, metadata
        ) VALUES ($1, $2, $3, $4, $5)
      `, [
        req.params.id,
        'git_link_added',
        `Git ${pull_request_url ? 'PR' : 'commit'} linked: ${branch_name || commit_hash}`,
        'system',
        { git_link_id: result.rows[0].id }
      ]);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get git links
  router.get('/issues/:id/git-links', async (req, res) => {
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

  // Get issue token cost summary
  router.get('/issues/:id/token-summary', async (req, res) => {
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

  // Convert request to sub-ticket
  router.post('/comments/:id/convert-to-ticket', async (req, res) => {
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');
      
      // Get comment details
      const commentResult = await client.query(
        'SELECT * FROM issue_comments WHERE id = $1',
        [req.params.id]
      );
      
      if (commentResult.rows.length === 0) {
        throw new Error('Comment not found');
      }
      
      const comment = commentResult.rows[0];
      
      // Create sub-ticket
      const subTicketResult = await client.query(
        'SELECT create_sub_ticket_from_request($1, $2, $3)',
        [comment.issue_id, comment.content, comment.id]
      );
      
      await client.query('COMMIT');
      res.json({ 
        sub_ticket_id: subTicketResult.rows[0].create_sub_ticket_from_request 
      });
    } catch (error) {
      await client.query('ROLLBACK');
      res.status(500).json({ error: error.message });
    } finally {
      client.release();
    }
  });

  return router;
};