// AI-first review layer: agents registry, proposals (propose/approve/intervene),
// agent presence for the live strip.

const express = require('express');

module.exports = function agentsRoutes(pool) {
  const router = express.Router();

  // Verify the caller owns the project (inline — the global guard already
  // covers /api/projects/:id/... paths, but these endpoints use different
  // URL shapes so we check explicitly on each).
  async function ownsProject(userId, projectId) {
    if (!userId || !projectId) return false;
    const { rows } = await pool.query(
      `SELECT 1 FROM projects WHERE id = $1 AND (owner_id = $2 OR owner_id IS NULL) LIMIT 1`,
      [projectId, userId]
    );
    return rows.length > 0;
  }

  // ───── Agents ─────────────────────────────────────────────────────────

  router.get('/agents', async (req, res) => {
    try {
      const { rows } = await pool.query(
        `SELECT id, slug, display_name, model, specialty, color, is_active, last_seen_at
         FROM agents WHERE user_id = $1 AND is_active = true
         ORDER BY display_name ASC`,
        [req.user.id]
      );
      res.json({ agents: rows });
    } catch (err) {
      console.error('list agents:', err);
      res.status(500).json({ error: 'Failed to list agents' });
    }
  });

  router.post('/agents', async (req, res) => {
    const { slug, display_name, model, specialty, color } = req.body || {};
    if (!slug || !display_name) return res.status(400).json({ error: 'slug and display_name required' });
    try {
      const { rows } = await pool.query(
        `INSERT INTO agents (user_id, slug, display_name, model, specialty, color)
         VALUES ($1, $2, $3, $4, $5, COALESCE($6, '#6EA0F5'))
         ON CONFLICT (user_id, slug) DO UPDATE SET
           display_name = EXCLUDED.display_name,
           model = EXCLUDED.model,
           specialty = EXCLUDED.specialty,
           color = EXCLUDED.color,
           is_active = true
         RETURNING *`,
        [req.user.id, slug, display_name, model || null, specialty || null, color || null]
      );
      res.status(201).json(rows[0]);
    } catch (err) {
      console.error('create agent:', err);
      res.status(500).json({ error: 'Failed to create agent' });
    }
  });

  // ───── Proposals ──────────────────────────────────────────────────────

  // Agent creates a proposal. Agents call this via their API key (X-API-Key)
  // so req.user is the key owner; we look up the agent by slug on the body.
  router.post('/proposals', async (req, res) => {
    const {
      project_id,
      agent_slug,
      kind,
      target_issue_id,
      target_label,
      payload,
      reasoning,
      confidence,
      blast_radius,
      urgency,
      auto_approve_seconds,
    } = req.body || {};

    if (!project_id || !kind) return res.status(400).json({ error: 'project_id and kind required' });
    if (!(await ownsProject(req.user.id, project_id))) return res.status(404).json({ error: 'Project not found' });

    let agentId = null;
    if (agent_slug) {
      const { rows } = await pool.query(
        `INSERT INTO agents (user_id, slug, display_name)
         VALUES ($1, $2, $2)
         ON CONFLICT (user_id, slug) DO UPDATE SET last_seen_at = NOW()
         RETURNING id`,
        [req.user.id, agent_slug]
      );
      agentId = rows[0].id;
    }

    try {
      const autoApproveAt =
        typeof auto_approve_seconds === 'number' && auto_approve_seconds > 0
          ? new Date(Date.now() + auto_approve_seconds * 1000)
          : null;

      const { rows } = await pool.query(
        `INSERT INTO proposals
          (project_id, agent_id, kind, target_issue_id, target_label, payload,
           reasoning, confidence, blast_radius, urgency, auto_approve_at)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,COALESCE($9,'low'),COALESCE($10,'normal'),$11)
         RETURNING *`,
        [
          project_id,
          agentId,
          kind,
          target_issue_id || null,
          target_label || null,
          payload || {},
          reasoning || null,
          typeof confidence === 'number' ? confidence : null,
          blast_radius || null,
          urgency || null,
          autoApproveAt,
        ]
      );
      res.status(201).json(rows[0]);
    } catch (err) {
      console.error('create proposal:', err);
      res.status(500).json({ error: 'Failed to create proposal' });
    }
  });

  // Pending queue across ALL projects the user owns.
  router.get('/proposals/pending', async (req, res) => {
    try {
      const { rows } = await pool.query(
        `SELECT p.*,
                pr.name AS project_name,
                i.title AS issue_title,
                i.status AS issue_status,
                substring(i.id::text from 1 for 7) AS issue_key,
                i.github_issue_number,
                a.slug AS agent_slug,
                a.display_name AS agent_name,
                a.model AS agent_model,
                a.specialty AS agent_specialty,
                a.color AS agent_color
         FROM proposals p
         JOIN projects pr ON pr.id = p.project_id
         LEFT JOIN issues i ON i.id = p.target_issue_id
         LEFT JOIN agents a ON a.id = p.agent_id
         WHERE (pr.owner_id = $1 OR pr.owner_id IS NULL)
           AND p.status = 'pending'
         ORDER BY
           CASE p.urgency WHEN 'urgent' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END,
           p.created_at DESC`,
        [req.user.id]
      );
      res.json({ proposals: rows });
    } catch (err) {
      console.error('list pending:', err);
      res.status(500).json({ error: 'Failed to list proposals' });
    }
  });

  router.post('/proposals/:id/approve', async (req, res) => {
    try {
      const { rows } = await pool.query(
        `UPDATE proposals p
         SET status = 'approved', resolved_at = NOW(), resolved_by = $2
         FROM projects pr
         WHERE p.id = $1
           AND p.project_id = pr.id
           AND (pr.owner_id = $2 OR pr.owner_id IS NULL)
           AND p.status = 'pending'
         RETURNING p.*`,
        [req.params.id, req.user.id]
      );
      if (rows.length === 0) return res.status(404).json({ error: 'Proposal not found or already resolved' });
      res.json(rows[0]);
    } catch (err) {
      console.error('approve proposal:', err);
      res.status(500).json({ error: 'Failed to approve' });
    }
  });

  router.post('/proposals/:id/intervene', async (req, res) => {
    const response = (req.body?.response || '').toString().slice(0, 2000);
    try {
      const { rows } = await pool.query(
        `UPDATE proposals p
         SET status = 'intervened', resolved_at = NOW(), resolved_by = $2, human_response = $3
         FROM projects pr
         WHERE p.id = $1
           AND p.project_id = pr.id
           AND (pr.owner_id = $2 OR pr.owner_id IS NULL)
           AND p.status = 'pending'
         RETURNING p.*`,
        [req.params.id, req.user.id, response || null]
      );
      if (rows.length === 0) return res.status(404).json({ error: 'Proposal not found or already resolved' });
      res.json(rows[0]);
    } catch (err) {
      console.error('intervene:', err);
      res.status(500).json({ error: 'Failed to intervene' });
    }
  });

  // ───── Presence (live strip) ──────────────────────────────────────────

  router.post('/agents/presence', async (req, res) => {
    const { agent_slug, project_id, status, current_task, current_target } = req.body || {};
    if (!agent_slug) return res.status(400).json({ error: 'agent_slug required' });
    try {
      const { rows: aRows } = await pool.query(
        `INSERT INTO agents (user_id, slug, display_name)
         VALUES ($1, $2, $2)
         ON CONFLICT (user_id, slug) DO UPDATE SET last_seen_at = NOW()
         RETURNING id`,
        [req.user.id, agent_slug]
      );
      const agentId = aRows[0].id;

      // Close stale sessions for this agent (>5 min old) then upsert current.
      await pool.query(
        `UPDATE agent_sessions SET ended_at = NOW()
         WHERE agent_id = $1 AND ended_at IS NULL AND last_seen_at < NOW() - INTERVAL '5 minutes'`,
        [agentId]
      );
      const { rows: sRows } = await pool.query(
        `INSERT INTO agent_sessions (agent_id, project_id, status, current_task, current_target)
         VALUES ($1, $2, COALESCE($3,'active'), $4, $5)
         RETURNING *`,
        [agentId, project_id || null, status || null, current_task || null, current_target || null]
      );
      res.status(201).json(sRows[0]);
    } catch (err) {
      console.error('presence:', err);
      res.status(500).json({ error: 'Failed to record presence' });
    }
  });

  router.get('/agents/presence', async (req, res) => {
    try {
      const { rows } = await pool.query(
        `SELECT s.id, s.status, s.current_task, s.current_target, s.started_at, s.last_seen_at,
                a.slug AS agent_slug, a.display_name AS agent_name,
                a.model, a.specialty, a.color,
                pr.name AS project_name, pr.id AS project_id
         FROM agent_sessions s
         JOIN agents a ON a.id = s.agent_id
         LEFT JOIN projects pr ON pr.id = s.project_id
         WHERE a.user_id = $1
           AND s.ended_at IS NULL
           AND s.last_seen_at > NOW() - INTERVAL '5 minutes'
         ORDER BY s.last_seen_at DESC
         LIMIT 12`,
        [req.user.id]
      );
      res.json({ sessions: rows });
    } catch (err) {
      console.error('get presence:', err);
      res.status(500).json({ error: 'Failed to fetch presence' });
    }
  });

  return router;
};
