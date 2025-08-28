// ABOUTME: API endpoints for project documentation management
// ABOUTME: Handles CRUD operations for documentation pages with markdown support

const express = require('express');
const router = express.Router();
const { Pool } = require('pg');

// Database connection
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://lineary:lineary_password@postgres:5432/lineary_db';
const pool = new Pool({
  connectionString: DATABASE_URL,
});

// Get all docs for a project
router.get('/project/:projectId', async (req, res) => {
  try {
    const { projectId } = req.params;
    const result = await pool.query(
      'SELECT * FROM docs WHERE project_id = $1 ORDER BY category, title',
      [projectId]
    );
    res.json(result.rows);
  } catch (error) {
    console.error('Error fetching docs:', error);
    res.status(500).json({ error: 'Failed to fetch documentation' });
  }
});

// Get single doc
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT * FROM docs WHERE id = $1', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Document not found' });
    }
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching doc:', error);
    res.status(500).json({ error: 'Failed to fetch document' });
  }
});

// Create new doc
router.post('/', async (req, res) => {
  try {
    const { title, content, category, project_id, related_issues } = req.body;
    const result = await pool.query(
      `INSERT INTO docs (title, content, category, project_id, related_issues, created_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
       RETURNING *`,
      [title, content, category, project_id, related_issues || []]
    );
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error creating doc:', error);
    res.status(500).json({ error: 'Failed to create document' });
  }
});

// Update doc
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { title, content, category, related_issues } = req.body;
    const result = await pool.query(
      `UPDATE docs 
       SET title = $1, content = $2, category = $3, related_issues = $4, updated_at = NOW()
       WHERE id = $5
       RETURNING *`,
      [title, content, category, related_issues || [], id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Document not found' });
    }
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error updating doc:', error);
    res.status(500).json({ error: 'Failed to update document' });
  }
});

// Delete doc
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('DELETE FROM docs WHERE id = $1 RETURNING id', [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Document not found' });
    }
    res.json({ message: 'Document deleted successfully' });
  } catch (error) {
    console.error('Error deleting doc:', error);
    res.status(500).json({ error: 'Failed to delete document' });
  }
});

// Search docs
router.get('/search/:projectId', async (req, res) => {
  try {
    const { projectId } = req.params;
    const { q } = req.query;
    const result = await pool.query(
      `SELECT * FROM docs 
       WHERE project_id = $1 
       AND (title ILIKE $2 OR content ILIKE $2)
       ORDER BY category, title`,
      [projectId, `%${q}%`]
    );
    res.json(result.rows);
  } catch (error) {
    console.error('Error searching docs:', error);
    res.status(500).json({ error: 'Failed to search documentation' });
  }
});

module.exports = router;