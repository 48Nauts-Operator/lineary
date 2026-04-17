const axios = require('axios');

const PROJECT_ID = process.env.STACK_PROJECT_ID;
const SECRET_KEY = process.env.STACK_SECRET_SERVER_KEY;
const BASE = 'https://api.stack-auth.com/api/v1';

if (!PROJECT_ID || !SECRET_KEY) {
  console.warn('[stackAuth] STACK_PROJECT_ID or STACK_SECRET_SERVER_KEY missing — auth will reject every request');
}

const cache = new Map();
const CACHE_TTL_MS = 60_000;

async function verifyAccessToken(accessToken) {
  if (!accessToken) return null;

  const cached = cache.get(accessToken);
  if (cached && cached.expires > Date.now()) return cached.user;

  try {
    const resp = await axios.get(`${BASE}/users/me`, {
      headers: {
        'x-stack-access-token': accessToken,
        'x-stack-project-id': PROJECT_ID,
        'x-stack-secret-server-key': SECRET_KEY,
        'x-stack-access-type': 'server',
      },
      timeout: 5000,
    });
    const data = resp.data;
    const user = {
      id: data.id,
      email: data.primary_email || data.primaryEmail,
      display_name: data.display_name || data.displayName || null,
    };
    cache.set(accessToken, { user, expires: Date.now() + CACHE_TTL_MS });
    return user;
  } catch (err) {
    if (err.response?.status === 401) return null;
    console.error('[stackAuth] verify failed:', err.response?.status, err.response?.data || err.message);
    return null;
  }
}

async function upsertLocalUser(db, user) {
  await db.query(
    `INSERT INTO users (id, email, display_name, last_seen_at)
     VALUES ($1, $2, $3, NOW())
     ON CONFLICT (id) DO UPDATE SET
       email = EXCLUDED.email,
       display_name = EXCLUDED.display_name,
       last_seen_at = NOW()`,
    [user.id, user.email, user.display_name]
  );
}

module.exports = { verifyAccessToken, upsertLocalUser };
