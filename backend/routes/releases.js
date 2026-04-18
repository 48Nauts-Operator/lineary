// Releases — human-readable bundles of merged work. Auto-drafted from merged
// PR activity since the last published release; human can edit and publish.

const express = require('express');

module.exports = function releasesRoutes(pool) {
  const router = express.Router();

  async function ownsProject(userId, projectId) {
    const { rows } = await pool.query(
      `SELECT 1 FROM projects WHERE id = $1 AND (owner_id = $2 OR owner_id IS NULL) LIMIT 1`,
      [projectId, userId]
    );
    return rows.length > 0;
  }

  router.get('/projects/:id/releases', async (req, res) => {
    if (!(await ownsProject(req.user.id, req.params.id))) return res.status(404).json({ error: 'Project not found' });
    try {
      const { rows } = await pool.query(
        `SELECT id, name, tag, status, body, pr_numbers, issue_ids, published_at, created_at, updated_at
         FROM releases WHERE project_id = $1 ORDER BY COALESCE(published_at, created_at) DESC`,
        [req.params.id]
      );
      res.json({ releases: rows });
    } catch (err) {
      console.error('list releases:', err);
      res.status(500).json({ error: 'Failed to list releases' });
    }
  });

  // Auto-draft: gather merged PRs since the last published release and build a draft.
  router.post('/projects/:id/releases/auto-draft', async (req, res) => {
    if (!(await ownsProject(req.user.id, req.params.id))) return res.status(404).json({ error: 'Project not found' });
    try {
      // Find last published release cutoff
      const cutoffRow = await pool.query(
        `SELECT COALESCE(MAX(published_at), TO_TIMESTAMP(0)) AS cutoff FROM releases WHERE project_id = $1 AND status = 'published'`,
        [req.params.id]
      );
      const cutoff = cutoffRow.rows[0].cutoff;

      const { rows: merged } = await pool.query(
        `SELECT a.metadata, a.description, a.created_at, a.issue_id
         FROM issue_activities a
         JOIN issues i ON i.id = a.issue_id
         WHERE i.project_id = $1 AND a.activity_type = 'pr_merged'
           AND a.created_at > $2
         ORDER BY a.created_at DESC
         LIMIT 200`,
        [req.params.id, cutoff]
      );

      if (merged.length === 0) {
        return res.json({ release: null, reason: 'no merges since last published release' });
      }

      const prNumbers = [];
      const issueIds = new Set();
      const bullets = merged.map((m) => {
        const n = m.metadata?.pr_number;
        if (typeof n === 'number') prNumbers.push(n);
        if (m.issue_id) issueIds.add(m.issue_id);
        const title = (m.description || '').replace(/^Pull Request #\d+ \S+:\s*/, '');
        return `- ${n ? `#${n} ` : ''}${title}`;
      });

      const name = `Release ${new Date().toISOString().slice(0, 10)}`;
      const body = [
        `## What changed`,
        '',
        ...bullets,
        '',
        `_${merged.length} merged pull request${merged.length === 1 ? '' : 's'} since last release._`,
      ].join('\n');

      const ins = await pool.query(
        `INSERT INTO releases (project_id, name, status, body, pr_numbers, issue_ids)
         VALUES ($1, $2, 'draft', $3, $4, $5) RETURNING *`,
        [req.params.id, name, body, prNumbers, [...issueIds]]
      );
      res.status(201).json({ release: ins.rows[0] });
    } catch (err) {
      console.error('auto-draft:', err);
      res.status(500).json({ error: 'Failed to auto-draft release' });
    }
  });

  router.patch('/projects/:id/releases/:release_id', async (req, res) => {
    if (!(await ownsProject(req.user.id, req.params.id))) return res.status(404).json({ error: 'Project not found' });
    const { name, tag, body } = req.body || {};
    try {
      const { rows } = await pool.query(
        `UPDATE releases SET
           name = COALESCE($3, name),
           tag = COALESCE($4, tag),
           body = COALESCE($5, body),
           updated_at = NOW()
         WHERE id = $2 AND project_id = $1 RETURNING *`,
        [req.params.id, req.params.release_id, name || null, tag || null, body || null]
      );
      if (rows.length === 0) return res.status(404).json({ error: 'Release not found' });
      res.json(rows[0]);
    } catch (err) {
      console.error('patch release:', err);
      res.status(500).json({ error: 'Failed to update release' });
    }
  });

  router.post('/projects/:id/releases/:release_id/publish', async (req, res) => {
    if (!(await ownsProject(req.user.id, req.params.id))) return res.status(404).json({ error: 'Project not found' });
    try {
      const { rows } = await pool.query(
        `UPDATE releases SET status = 'published', published_at = NOW(), updated_at = NOW()
         WHERE id = $2 AND project_id = $1 AND status = 'draft'
         RETURNING *`,
        [req.params.id, req.params.release_id]
      );
      if (rows.length === 0) return res.status(404).json({ error: 'Draft release not found' });
      res.json(rows[0]);
    } catch (err) {
      console.error('publish release:', err);
      res.status(500).json({ error: 'Failed to publish' });
    }
  });

  router.delete('/projects/:id/releases/:release_id', async (req, res) => {
    if (!(await ownsProject(req.user.id, req.params.id))) return res.status(404).json({ error: 'Project not found' });
    try {
      const { rowCount } = await pool.query(
        `DELETE FROM releases WHERE id = $2 AND project_id = $1`,
        [req.params.id, req.params.release_id]
      );
      if (rowCount === 0) return res.status(404).json({ error: 'Release not found' });
      res.json({ deleted: true });
    } catch (err) {
      console.error('delete release:', err);
      res.status(500).json({ error: 'Failed to delete' });
    }
  });

  return router;
};
