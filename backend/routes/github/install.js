// GitHub App install flow + installation management per project.
//
// Flow:
//   1. Frontend calls GET /api/github/install-url?projectId=X → we return a URL
//      to github.com/apps/<slug>/installations/new with a signed `state` param
//      so we can tie the install callback back to the project.
//   2. User picks repos on GitHub; GitHub redirects to
//      GET /api/github/install-callback?installation_id=Y&state=Z (public —
//      GitHub's server calls this, not the user's browser session).
//   3. We validate the state JWT, look up which project it belonged to,
//      verify the caller owns the project, fetch installation details via the
//      App, store in project_github_installations, kick off initial sync, and
//      302-redirect the browser back to the frontend.

const express = require('express');
const crypto = require('crypto');
const { isConfigured, installationUrl, getAppOctokit, getInstallationOctokit } = require('../../lib/github/app');

const STATE_SECRET =
  process.env.GITHUB_APP_STATE_SECRET || process.env.JWT_SECRET || 'dev-state-secret-change-me';
const STATE_TTL_MS = 15 * 60 * 1000;

function signState(payload) {
  const body = Buffer.from(JSON.stringify({ ...payload, exp: Date.now() + STATE_TTL_MS })).toString('base64url');
  const sig = crypto.createHmac('sha256', STATE_SECRET).update(body).digest('base64url');
  return `${body}.${sig}`;
}

function verifyState(state) {
  if (!state || typeof state !== 'string' || !state.includes('.')) return null;
  const [body, sig] = state.split('.');
  const expected = crypto.createHmac('sha256', STATE_SECRET).update(body).digest('base64url');
  if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) return null;
  let decoded;
  try {
    decoded = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
  } catch {
    return null;
  }
  if (!decoded.exp || decoded.exp < Date.now()) return null;
  return decoded;
}

module.exports = function githubInstallRoutes(pool) {
  const router = express.Router();

  // GET /api/github/install-url?projectId=...
  router.get('/github/install-url', async (req, res) => {
    try {
      if (!isConfigured()) return res.status(503).json({ error: 'GitHub App not configured on server' });

      const projectId = req.query.projectId;
      if (!projectId) return res.status(400).json({ error: 'projectId required' });

      // Ownership check: only the project owner can initiate install.
      const { rows } = await pool.query(
        `SELECT id FROM projects WHERE id = $1 AND (owner_id = $2 OR owner_id IS NULL) LIMIT 1`,
        [projectId, req.user.id]
      );
      if (rows.length === 0) return res.status(404).json({ error: 'Project not found' });

      const state = signState({ projectId, userId: req.user.id });
      return res.json({ url: installationUrl(state) });
    } catch (err) {
      console.error('install-url failed:', err);
      return res.status(500).json({ error: 'Failed to build install URL' });
    }
  });

  // GET /api/github/install-callback?installation_id=...&state=...&setup_action=install
  // Public endpoint — GitHub calls it, not an authenticated user.
  router.get('/github/install-callback', async (req, res) => {
    try {
      const { installation_id, state } = req.query;
      if (!installation_id) return res.status(400).send('Missing installation_id');

      const decoded = state ? verifyState(state) : null;
      if (!decoded) return res.status(400).send('Invalid or expired state');

      const { projectId } = decoded;

      // Fetch installation details (repos, owner).
      const app = getAppOctokit();
      const { data: installation } = await app.request('GET /app/installations/{installation_id}', {
        installation_id,
      });

      const installOcto = getInstallationOctokit(installation_id);
      const { data: reposResp } = await installOcto.request('GET /installation/repositories', { per_page: 1 });

      // If the installation covers exactly one repo, link it automatically.
      // If multiple, link the first and let the UI offer a picker later.
      const repo = reposResp.repositories[0];
      if (!repo) {
        return res.status(400).send('Installation has no accessible repositories');
      }

      await pool.query(
        `INSERT INTO project_github_installations
           (project_id, installation_id, repo_owner, repo_name, repo_id, default_branch, sync_status)
         VALUES ($1, $2, $3, $4, $5, $6, 'idle')
         ON CONFLICT (project_id) DO UPDATE SET
           installation_id = EXCLUDED.installation_id,
           repo_owner = EXCLUDED.repo_owner,
           repo_name = EXCLUDED.repo_name,
           repo_id = EXCLUDED.repo_id,
           default_branch = EXCLUDED.default_branch,
           sync_status = 'idle',
           sync_error = NULL`,
        [
          projectId,
          installation.id,
          repo.owner.login,
          repo.name,
          repo.id,
          repo.default_branch,
        ]
      );

      await pool.query(`UPDATE projects SET mode = 'github' WHERE id = $1`, [projectId]);

      // Kick off initial sync in background; don't block the redirect.
      try {
        const { initialSync } = require('../../lib/github/sync');
        setImmediate(() => initialSync(pool, projectId).catch((e) => console.error('initialSync:', e.message)));
      } catch (e) {
        console.warn('initialSync not available yet:', e.message);
      }

      // Bounce the user back to the frontend.
      return res.redirect(302, `/?onboarded=github&project=${encodeURIComponent(projectId)}`);
    } catch (err) {
      console.error('install-callback failed:', err);
      return res.status(500).send('Install callback failed');
    }
  });

  // GET /api/github/installations/:projectId
  router.get('/github/installations/:projectId', async (req, res) => {
    try {
      const { rows } = await pool.query(
        `SELECT i.*
         FROM project_github_installations i
         JOIN projects p ON p.id = i.project_id
         WHERE i.project_id = $1 AND (p.owner_id = $2 OR p.owner_id IS NULL)`,
        [req.params.projectId, req.user.id]
      );
      if (rows.length === 0) return res.status(404).json({ error: 'No installation' });
      return res.json(rows[0]);
    } catch (err) {
      console.error('get installation failed:', err);
      return res.status(500).json({ error: 'Failed to fetch installation' });
    }
  });

  // DELETE /api/github/installations/:projectId — disconnect the repo.
  router.delete('/github/installations/:projectId', async (req, res) => {
    try {
      const { rowCount } = await pool.query(
        `DELETE FROM project_github_installations
         WHERE project_id = $1
           AND project_id IN (SELECT id FROM projects WHERE owner_id = $2 OR owner_id IS NULL)`,
        [req.params.projectId, req.user.id]
      );
      if (rowCount === 0) return res.status(404).json({ error: 'No installation' });
      await pool.query(`UPDATE projects SET mode = 'mcp_only' WHERE id = $1`, [req.params.projectId]);
      return res.json({ disconnected: true });
    } catch (err) {
      console.error('delete installation failed:', err);
      return res.status(500).json({ error: 'Failed to disconnect' });
    }
  });

  return router;
};
