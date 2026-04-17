const { verifyAccessToken, upsertLocalUser } = require('../lib/stackAuth');
const { verifyKey } = require('../lib/apiKeys');

const BYPASS_PATHS = [
  /^\/api\/health$/,
  /^\/api\/webhooks\/(github|gitlab)\//,
  /^\/api\/github\/webhook$/,
  /^\/api\/auth\/oauth\//,
];

function isBypass(reqPath) {
  return BYPASS_PATHS.some((re) => re.test(reqPath));
}

function requireAuth(db) {
  return async function (req, res, next) {
    if (isBypass(req.path)) return next();

    const apiKey = req.headers['x-api-key'];
    if (apiKey) {
      const user = await verifyKey(db, apiKey);
      if (!user) return res.status(401).json({ error: 'Invalid API key' });
      req.user = user;
      return next();
    }

    const auth = req.headers.authorization || '';
    const token = auth.startsWith('Bearer ') ? auth.slice(7) : null;
    if (!token) return res.status(401).json({ error: 'Missing Authorization or X-API-Key' });

    const user = await verifyAccessToken(token);
    if (!user) return res.status(401).json({ error: 'Invalid or expired access token' });

    try {
      await upsertLocalUser(db, user);
    } catch (err) {
      console.error('[requireAuth] upsert user failed:', err.message);
      return res.status(500).json({ error: 'Failed to persist user' });
    }

    req.user = user;
    return next();
  };
}

async function userOwnsProject(db, userId, projectId) {
  if (!userId || !projectId) return false;
  const { rows } = await db.query(
    `SELECT 1 FROM projects WHERE id = $1 AND (owner_id = $2 OR owner_id IS NULL) LIMIT 1`,
    [projectId, userId]
  );
  return rows.length > 0;
}

async function projectIdForIssue(db, issueId) {
  const { rows } = await db.query(`SELECT project_id FROM issues WHERE id = $1`, [issueId]);
  return rows[0]?.project_id || null;
}

async function projectIdForSprint(db, sprintId) {
  const { rows } = await db.query(`SELECT project_id FROM sprints WHERE id = $1`, [sprintId]);
  return rows[0]?.project_id || null;
}

function requireProjectOwnership(db, extract) {
  return async function (req, res, next) {
    const projectId = await extract(req, db);
    if (!projectId) return res.status(404).json({ error: 'Resource not found' });
    const ok = await userOwnsProject(db, req.user.id, projectId);
    if (!ok) return res.status(403).json({ error: 'Forbidden' });
    req.projectId = projectId;
    return next();
  };
}

module.exports = {
  requireAuth,
  userOwnsProject,
  projectIdForIssue,
  projectIdForSprint,
  requireProjectOwnership,
};
