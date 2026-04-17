const express = require('express');
const { generateKey, hashKey, keyPrefix } = require('../lib/apiKeys');

module.exports = function authRoutes(db) {
  const router = express.Router();

  router.get('/auth/me', (req, res) => {
    res.json(req.user);
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
