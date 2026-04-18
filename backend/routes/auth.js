const express = require('express');
const { generateKey, hashKey, keyPrefix } = require('../lib/apiKeys');

const STARTER_ISSUES = [
  {
    title: 'Welcome — try closing this issue',
    description:
      'Lineary is your AI-first project canvas. Click this issue, switch the status to Done, and notice it closes with the same motion a human would use elsewhere.',
    priority: 4,
  },
  {
    title: 'Wire an agent: paste the snippet from Welcome into Claude Desktop',
    description:
      "Grab the JSON shown right after signup and drop it into ~/Library/Application Support/Claude/claude_desktop_config.json. Restart Claude. Your agent will show up in the Live strip at the top of the Review tab.",
    priority: 3,
  },
  {
    title: 'Ask your agent to propose a split on this issue',
    description:
      "Once connected, say to your agent: 'Use Lineary. Split this issue into 3 sub-issues for the pretend feature X.' You'll see a proposal appear in the Review queue — click Approve to see the sub-issues land here.",
    priority: 3,
  },
];

module.exports = function authRoutes(db) {
  const router = express.Router();

  router.get('/auth/me', (req, res) => {
    res.json(req.user);
  });

  // Idempotent first-login bootstrap. If the user has never been onboarded:
  //  - Create a starter "My Lineary" project (mcp_only mode)
  //  - Seed 3 tutorial issues
  //  - Mint an API key named "Starter key"
  //  - Mark onboarded_at
  // Returns `is_new_user: true` and a welcome_kit containing the one-time raw
  // key + the prefilled Claude Desktop MCP config snippet. On subsequent
  // calls returns `is_new_user: false` with no secrets.
  router.post('/auth/bootstrap', async (req, res) => {
    try {
      const { rows: uRows } = await pool.query(
        `SELECT id, email, display_name, onboarded_at FROM users WHERE id = $1`,
        [req.user.id]
      );
      const existing = uRows[0];
      if (existing?.onboarded_at) {
        return res.json({ is_new_user: false });
      }

      // Transactionally create project + seed issues + key. Keep it simple —
      // if anything fails we rollback and the user can retry on next load.
      const client = await pool.connect();
      try {
        await client.query('BEGIN');

        const displayName = existing?.display_name || (existing?.email?.split('@')[0]) || 'friend';
        const projectName = 'My Lineary';
        const slug = `my-lineary-${String(req.user.id).slice(0, 8)}`;

        const { rows: projRows } = await client.query(
          `INSERT INTO projects (name, description, slug, color, icon, owner_id, mode)
           VALUES ($1, $2, $3, $4, $5, $6, 'mcp_only')
           RETURNING *`,
          [
            projectName,
            `Welcome, ${displayName}. This is your starter project. Delete or rename it whenever you like.`,
            slug,
            '#9B8CFF',
            'sparkles',
            req.user.id,
          ]
        );
        const project = projRows[0];

        for (const seed of STARTER_ISSUES) {
          await client.query(
            `INSERT INTO issues (project_id, title, description, priority, story_points, estimated_hours, status)
             VALUES ($1, $2, $3, $4, 1, 1, 'todo')`,
            [project.id, seed.title, seed.description, seed.priority]
          );
        }

        const rawKey = generateKey();
        const { rows: keyRows } = await client.query(
          `INSERT INTO api_keys (user_id, name, key_hash, key_prefix)
           VALUES ($1, 'Starter key', $2, $3)
           RETURNING id, name, key_prefix, created_at`,
          [req.user.id, hashKey(rawKey), keyPrefix(rawKey)]
        );

        await client.query(`UPDATE users SET onboarded_at = NOW() WHERE id = $1`, [req.user.id]);
        await client.query('COMMIT');

        return res.json({
          is_new_user: true,
          user: { name: displayName, email: existing?.email },
          project: {
            id: project.id,
            name: project.name,
            slug: project.slug,
            mode: project.mode,
          },
          api_key: { ...keyRows[0], raw: rawKey },
          starter_issues: STARTER_ISSUES.length,
        });
      } catch (err) {
        await client.query('ROLLBACK');
        throw err;
      } finally {
        client.release();
      }
    } catch (err) {
      console.error('bootstrap failed:', err);
      return res.status(500).json({ error: 'Bootstrap failed' });
    }
  });

  router.post('/auth/claim-orphans', async (req, res) => {
    try {
      const { rowCount } = await db.query(
        `UPDATE projects SET owner_id = $1 WHERE owner_id IS NULL`,
        [req.user.id]
      );
      return res.json({ claimed: rowCount });
    } catch (err) {
      console.error('claim-orphans failed:', err);
      return res.status(500).json({ error: 'Claim failed' });
    }
  });

  router.get('/auth/keys', async (req, res) => {
    try {
      const { rows } = await db.query(
        `SELECT id, name, key_prefix, created_at, last_used_at, revoked_at
         FROM api_keys WHERE user_id = $1 ORDER BY created_at DESC`,
        [req.user.id]
      );
      return res.json(rows);
    } catch (err) {
      console.error('list keys failed:', err);
      return res.status(500).json({ error: 'Failed to list keys' });
    }
  });

  router.post('/auth/keys', async (req, res) => {
    try {
      const name = (req.body?.name || '').trim();
      if (!name) return res.status(400).json({ error: 'name required' });

      const raw = generateKey();
      const { rows } = await db.query(
        `INSERT INTO api_keys (user_id, name, key_hash, key_prefix)
         VALUES ($1, $2, $3, $4)
         RETURNING id, name, key_prefix, created_at`,
        [req.user.id, name, hashKey(raw), keyPrefix(raw)]
      );
      return res.status(201).json({ ...rows[0], key: raw });
    } catch (err) {
      console.error('create key failed:', err);
      return res.status(500).json({ error: 'Failed to create key' });
    }
  });

  router.delete('/auth/keys/:id', async (req, res) => {
    try {
      const { rowCount } = await db.query(
        `UPDATE api_keys SET revoked_at = NOW()
         WHERE id = $1 AND user_id = $2 AND revoked_at IS NULL`,
        [req.params.id, req.user.id]
      );
      if (rowCount === 0) return res.status(404).json({ error: 'Key not found' });
      return res.json({ revoked: true });
    } catch (err) {
      console.error('revoke key failed:', err);
      return res.status(500).json({ error: 'Failed to revoke key' });
    }
  });

  return router;
};
