// Runner registration + dispatch endpoints.
// User-auth routes (require req.user): register/list/delete + dispatch SSE stream.
// Runner-token routes (X-Runner-Token header): long-poll + stdout + complete.

const express = require('express');
const { generateToken, hashToken, tokenPrefix, verifyRunnerToken } = require('../lib/runnerTokens');

module.exports = function runnerRoutes(db) {
  const router = express.Router();

  // ── user-auth: register / list / revoke ──────────────────────────────────

  router.get('/runners', async (req, res) => {
    try {
      const { rows } = await db.query(
        `SELECT r.id, r.name, r.hostname, r.runtime_preferences, r.status, r.last_seen_at, r.created_at,
                t.prefix AS token_prefix
         FROM runners r
         LEFT JOIN runner_tokens t ON t.runner_id = r.id AND t.revoked_at IS NULL
         WHERE r.user_id = $1
         ORDER BY r.created_at DESC`,
        [req.user.id]
      );
      res.json(rows);
    } catch (err) {
      console.error('list runners failed:', err);
      res.status(500).json({ error: 'Failed to list runners' });
    }
  });

  router.post('/runners', async (req, res) => {
    try {
      const name = (req.body?.name || '').trim();
      if (!name) return res.status(400).json({ error: 'name required' });
      const runtimes = Array.isArray(req.body?.runtime_preferences)
        ? req.body.runtime_preferences.filter((r) => ['claude', 'codex', 'opencode'].includes(r))
        : ['claude'];
      if (runtimes.length === 0) return res.status(400).json({ error: 'pick at least one runtime' });

      const client = await db.connect();
      try {
        await client.query('BEGIN');
        const { rows: rr } = await client.query(
          `INSERT INTO runners (user_id, name, runtime_preferences)
           VALUES ($1, $2, $3::jsonb) RETURNING id, name, runtime_preferences, status, created_at`,
          [req.user.id, name, JSON.stringify(runtimes)]
        );
        const runner = rr[0];
        const raw = generateToken();
        await client.query(
          `INSERT INTO runner_tokens (runner_id, token_hash, prefix) VALUES ($1, $2, $3)`,
          [runner.id, hashToken(raw), tokenPrefix(raw)]
        );
        await client.query('COMMIT');
        return res.status(201).json({ ...runner, token: raw });
      } catch (err) {
        await client.query('ROLLBACK');
        throw err;
      } finally {
        client.release();
      }
    } catch (err) {
      console.error('create runner failed:', err);
      res.status(500).json({ error: 'Failed to create runner' });
    }
  });

  router.delete('/runners/:id', async (req, res) => {
    try {
      const { rowCount } = await db.query(
        `DELETE FROM runners WHERE id = $1 AND user_id = $2`,
        [req.params.id, req.user.id]
      );
      if (rowCount === 0) return res.status(404).json({ error: 'Runner not found' });
      res.json({ deleted: true });
    } catch (err) {
      console.error('delete runner failed:', err);
      res.status(500).json({ error: 'Failed to delete runner' });
    }
  });

  // ── runner-token: long-poll + stdout + complete ──────────────────────────

  async function runnerAuth(req, res, next) {
    const token = req.header('X-Runner-Token');
    const ctx = await verifyRunnerToken(db, token);
    if (!ctx) return res.status(401).json({ error: 'invalid runner token' });
    // require the path :id to match the authenticated runner
    if (req.params.id && req.params.id !== ctx.runner_id) {
      return res.status(403).json({ error: 'runner mismatch' });
    }
    req.runner = ctx;
    // heartbeat
    db.query(`UPDATE runners SET last_seen_at = NOW(), status = 'idle' WHERE id = $1 AND status <> 'busy'`, [ctx.runner_id]).catch(() => {});
    next();
  }

  // Long-poll: up to 25s wait for a pending dispatch addressed to this runner.
  router.get('/runners/:id/next-dispatch', runnerAuth, async (req, res) => {
    const deadline = Date.now() + 25_000;
    const attempt = async () => {
      const { rows } = await db.query(
        `UPDATE runner_dispatches d
         SET status = 'claimed', claimed_at = NOW()
         WHERE d.id = (
           SELECT id FROM runner_dispatches
           WHERE runner_id = $1 AND status = 'pending'
           ORDER BY created_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED
         )
         RETURNING id, issue_id, project_id, runtime`,
        [req.runner.runner_id]
      );
      if (rows.length === 0) return null;
      const d = rows[0];
      const { rows: iRows } = await db.query(
        `SELECT i.id, i.title, i.description, i.priority, i.labels, i.github_issue_number,
                p.name AS project_name, p.slug AS project_slug
         FROM issues i JOIN projects p ON p.id = i.project_id WHERE i.id = $1`,
        [d.issue_id]
      );
      return { dispatch_id: d.id, runtime: d.runtime, project_id: d.project_id, issue: iRows[0] };
    };

    try {
      let payload = await attempt();
      while (!payload && Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, 2000));
        payload = await attempt();
      }
      if (!payload) return res.status(204).end();
      db.query(`UPDATE runners SET status = 'busy' WHERE id = $1`, [req.runner.runner_id]).catch(() => {});
      return res.json(payload);
    } catch (err) {
      console.error('next-dispatch failed:', err);
      return res.status(500).json({ error: 'poll failed' });
    }
  });

  router.post('/runners/:id/dispatches/:did/stdout', runnerAuth, async (req, res) => {
    const line = typeof req.body?.line === 'string' ? req.body.line : null;
    if (!line) return res.status(400).json({ error: 'line required' });
    try {
      await db.query(
        `UPDATE runner_dispatches
         SET stdout_lines = stdout_lines || jsonb_build_array(jsonb_build_object('t', NOW()::text, 'l', $3::text)),
             status = CASE WHEN status IN ('pending','claimed') THEN 'running' ELSE status END,
             started_at = COALESCE(started_at, NOW())
         WHERE id = $1 AND runner_id = $2`,
        [req.params.did, req.runner.runner_id, line]
      );
      res.json({ ok: true });
    } catch (err) {
      console.error('stdout append failed:', err);
      res.status(500).json({ error: 'append failed' });
    }
  });

  router.post('/runners/:id/dispatches/:did/complete', runnerAuth, async (req, res) => {
    const { pr_url, pr_number, status, error } = req.body || {};
    const finalStatus = status === 'failed' ? 'failed' : 'completed';
    try {
      await db.query(
        `UPDATE runner_dispatches
         SET status = $3, pr_url = $4, pr_number = $5, error = $6, completed_at = NOW()
         WHERE id = $1 AND runner_id = $2`,
        [req.params.did, req.runner.runner_id, finalStatus, pr_url || null, pr_number || null, error || null]
      );
      db.query(`UPDATE runners SET status = 'idle' WHERE id = $1`, [req.runner.runner_id]).catch(() => {});
      res.json({ ok: true });
    } catch (err) {
      console.error('complete failed:', err);
      res.status(500).json({ error: 'complete failed' });
    }
  });

  // ── user-auth SSE tail for frontend ──────────────────────────────────────

  router.get('/dispatches/:id/stream', async (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders?.();

    let lastCount = 0;
    let closed = false;
    req.on('close', () => {
      closed = true;
    });

    const pump = async () => {
      while (!closed) {
        try {
          const { rows } = await db.query(
            `SELECT d.status, d.stdout_lines, d.pr_url, d.pr_number, d.error, d.completed_at
             FROM runner_dispatches d JOIN issues i ON i.id = d.issue_id JOIN projects p ON p.id = i.project_id
             WHERE d.id = $1 AND p.owner_id = $2`,
            [req.params.id, req.user.id]
          );
          if (rows.length === 0) {
            res.write(`event: error\ndata: ${JSON.stringify({ error: 'not found' })}\n\n`);
            return res.end();
          }
          const d = rows[0];
          const lines = d.stdout_lines || [];
          if (lines.length > lastCount) {
            for (const l of lines.slice(lastCount)) {
              res.write(`event: line\ndata: ${JSON.stringify(l)}\n\n`);
            }
            lastCount = lines.length;
          }
          if (d.status === 'completed' || d.status === 'failed' || d.status === 'cancelled') {
            res.write(`event: done\ndata: ${JSON.stringify({ status: d.status, pr_url: d.pr_url, pr_number: d.pr_number, error: d.error })}\n\n`);
            return res.end();
          }
        } catch (err) {
          console.error('sse pump error:', err);
          res.write(`event: error\ndata: ${JSON.stringify({ error: 'stream error' })}\n\n`);
          return res.end();
        }
        await new Promise((r) => setTimeout(r, 1500));
      }
    };
    pump();
  });

  // ── user-auth dispatch summary (used by frontend issue panel) ────────────

  router.get('/issues/:id/dispatches', async (req, res) => {
    try {
      const { rows } = await db.query(
        `SELECT d.id, d.runtime, d.status, d.pr_url, d.pr_number, d.started_at, d.completed_at,
                r.name AS runner_name
         FROM runner_dispatches d
         LEFT JOIN runners r ON r.id = d.runner_id
         JOIN issues i ON i.id = d.issue_id
         JOIN projects p ON p.id = i.project_id
         WHERE d.issue_id = $1 AND p.owner_id = $2
         ORDER BY d.created_at DESC LIMIT 20`,
        [req.params.id, req.user.id]
      );
      res.json(rows);
    } catch (err) {
      console.error('list dispatches failed:', err);
      res.status(500).json({ error: 'failed' });
    }
  });

  return router;
};
