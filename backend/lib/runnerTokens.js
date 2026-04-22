const crypto = require('crypto');

const PREFIX = 'lrn_';

function generateToken() {
  const random = crypto.randomBytes(24).toString('hex');
  return `${PREFIX}${random}`;
}

function hashToken(token) {
  return crypto.createHash('sha256').update(token).digest('hex');
}

function tokenPrefix(token) {
  return token.slice(0, 12);
}

async function verifyRunnerToken(db, rawToken) {
  if (!rawToken || !rawToken.startsWith(PREFIX)) return null;
  const hash = hashToken(rawToken);
  const { rows } = await db.query(
    `SELECT t.id AS token_id, r.id AS runner_id, r.user_id, r.name, r.runtime_preferences
     FROM runner_tokens t
     JOIN runners r ON r.id = t.runner_id
     WHERE t.token_hash = $1 AND t.revoked_at IS NULL
     LIMIT 1`,
    [hash]
  );
  if (rows.length === 0) return null;
  return rows[0];
}

module.exports = { generateToken, hashToken, tokenPrefix, verifyRunnerToken };
