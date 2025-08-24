// ABOUTME: Lineary backend server - Main API for task management platform
// ABOUTME: Handles projects, issues, sprints, and AI integrations

const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const Redis = require('redis');
const app = express();

// Configuration
const PORT = process.env.PORT || 8000;
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://lineary:linearypassword@postgres:5432/lineary_db';
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379';

// Database connection
const pool = new Pool({
  connectionString: DATABASE_URL,
});

// Redis connection
const redis = Redis.createClient({
  url: REDIS_URL
});

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoints
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'lineary-backend',
    timestamp: new Date().toISOString() 
  });
});

app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'lineary-backend',
    timestamp: new Date().toISOString() 
  });
});

// Projects API
app.get('/api/projects', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM projects ORDER BY created_at DESC');
    res.json({ projects: result.rows });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/projects', async (req, res) => {
  const { name, description, color, icon } = req.body;
  try {
    // Generate slug from name
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    
    const result = await pool.query(
      'INSERT INTO projects (name, description, slug, color, icon) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [name, description, slug, color || '#8B5CF6', icon || 'folder']
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Issues API
app.get('/api/issues', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM issues ORDER BY created_at DESC');
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/issues', async (req, res) => {
  const { title, description, project_id, priority } = req.body;
  try {
    // TODO: Add Sprint Poker estimation here for story_points and estimated_hours
    const storyPoints = Math.floor(Math.random() * 8) + 1; // Temporary random
    const estimatedHours = storyPoints * 2; // Temporary calculation
    
    const result = await pool.query(
      'INSERT INTO issues (project_id, title, description, priority, story_points, estimated_hours, status) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *',
      [project_id, title, description, priority || 3, storyPoints, estimatedHours, 'backlog']
    );
    
    // TODO: Create Git worktree
    
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Sprints API
app.get('/api/sprints', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM sprints ORDER BY created_at DESC');
    res.json({ sprints: result.rows });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/sprints/create', async (req, res) => {
  const { name, duration_hours, project_id, issue_ids } = req.body;
  try {
    const result = await pool.query(
      'INSERT INTO sprints (name, duration_hours, project_id, issue_ids, status) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [name, duration_hours, project_id, issue_ids || [], 'planning']
    );
    res.json({ sprint: result.rows[0] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Code Review API (AI Integration)
app.post('/api/ai/review', async (req, res) => {
  const { issue_id, diff } = req.body;
  try {
    // TODO: Integrate with AI service for code review
    res.json({ 
      review: {
        issues_found: [],
        suggestions: [],
        quality_score: 0
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Test Generation API (AI Integration)
app.post('/api/ai/generate-tests', async (req, res) => {
  const { code, test_type } = req.body;
  try {
    // TODO: Integrate with AI service for test generation
    res.json({ 
      tests: [],
      coverage: 0
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
async function startServer() {
  try {
    // Connect to Redis
    await redis.connect();
    console.log('Connected to Redis');
    
    // Test database connection
    await pool.query('SELECT NOW()');
    console.log('Connected to PostgreSQL');
    
    app.listen(PORT, () => {
      console.log(`Lineary backend running on port ${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();