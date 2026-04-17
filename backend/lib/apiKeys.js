const crypto = require('crypto');

const PREFIX = 'lnk_';

function generateKey() {
  const random = crypto.randomBytes(20).toString('hex');
  return `${PREFIX}${random}`;
}

function hashKey(key) {
  return crypto.createHash('sha256').update(key).digest('hex');
}

function keyPrefix(key) {
  return key.slice(0, 12);
}

async function verifyKey(db, rawKey) {
  if (!rawKey || !rawKey.startsWith(PREFIX)) return null;
  const hash = hashKey(rawKey);
  const { rows } = await db.query(
    `SELECT k.id AS key_id, k.user_id, u.email, u.display_name
     FROM api_keys k
     JOIN users u ON u.id = k.user_id
     WHERE k.key_hash = $1 AND k.revoked_at IS NULL
     LIMIT 1`,
    [hash]
  );
  if (rows.length === 0) return null;
  db.query(`UPDATE api_keys SET last_used_at = NOW() WHERE id = $1`, [rows[0].key_id]).catch(() => {});
  return {
    id: rows[0].user_id,
    email: rows[0].email,
    display_name: rows[0].display_name,
  };
}

module.exports = { generateKey, hashKey, keyPrefix, verifyKey };
