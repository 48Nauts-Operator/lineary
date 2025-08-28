// ABOUTME: Auto-versioning system for project releases and version tracking
// ABOUTME: Handles semantic versioning, release notes, and version management

const express = require('express');
const router = express.Router();

module.exports = (pool) => {
  // Get version configuration for project
  router.get('/versions/config/:projectId', async (req, res) => {
    const { projectId } = req.params;
    
    try {
      let result = await pool.query(
        'SELECT * FROM version_config WHERE project_id = $1',
        [projectId]
      );
      
      if (result.rows.length === 0) {
        // Create default config if not exists
        result = await pool.query(`
          INSERT INTO version_config (project_id)
          VALUES ($1)
          RETURNING *
        `, [projectId]);
      }
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Update version configuration
  router.put('/versions/config/:projectId', async (req, res) => {
    const { projectId } = req.params;
    const { auto_version, version_pattern, prefix } = req.body;
    
    try {
      const result = await pool.query(`
        UPDATE version_config
        SET auto_version = COALESCE($2, auto_version),
            version_pattern = COALESCE($3, version_pattern),
            prefix = COALESCE($4, prefix)
        WHERE project_id = $1
        RETURNING *
      `, [projectId, auto_version, version_pattern, prefix]);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Auto-generate next version
  router.post('/versions/auto-generate/:projectId', async (req, res) => {
    const { projectId } = req.params;
    const { releaseType = 'patch', releaseNotes } = req.body;
    
    try {
      const client = await pool.connect();
      
      try {
        await client.query('BEGIN');
        
        // Get version config
        const configResult = await client.query(
          'SELECT * FROM version_config WHERE project_id = $1',
          [projectId]
        );
        
        if (configResult.rows.length === 0) {
          throw new Error('Version configuration not found');
        }
        
        const config = configResult.rows[0];
        let newMajor = config.current_major;
        let newMinor = config.current_minor;
        let newPatch = config.current_patch;
        
        // Increment based on release type
        switch (releaseType) {
          case 'major':
            newMajor++;
            newMinor = 0;
            newPatch = 0;
            break;
          case 'minor':
            newMinor++;
            newPatch = 0;
            break;
          case 'patch':
            newPatch++;
            break;
        }
        
        const versionNumber = `${config.prefix}${newMajor}.${newMinor}.${newPatch}`;
        
        // Create new version
        const versionResult = await client.query(`
          INSERT INTO versions (
            project_id, version_number, release_type, 
            release_notes, status, release_date
          )
          VALUES ($1, $2, $3, $4, 'released', CURRENT_DATE)
          RETURNING *
        `, [projectId, versionNumber, releaseType, releaseNotes]);
        
        // Update config with new version numbers
        await client.query(`
          UPDATE version_config
          SET current_major = $2,
              current_minor = $3,
              current_patch = $4
          WHERE project_id = $1
        `, [projectId, newMajor, newMinor, newPatch]);
        
        // Auto-tag completed issues with this version
        await client.query(`
          UPDATE issues
          SET fixed_in_version = $2
          WHERE project_id = $1
          AND status = 'done'
          AND fixed_in_version IS NULL
        `, [projectId, versionResult.rows[0].id]);
        
        await client.query('COMMIT');
        
        res.json({
          version: versionResult.rows[0],
          message: `Version ${versionNumber} created successfully`
        });
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Get all versions for a project
  router.get('/versions/project/:projectId', async (req, res) => {
    const { projectId } = req.params;
    
    try {
      const result = await pool.query(`
        SELECT v.*, 
               COUNT(DISTINCT i.id) FILTER (WHERE i.fixed_in_version = v.id) as issues_fixed,
               COUNT(DISTINCT i2.id) FILTER (WHERE i2.target_version = v.id) as issues_planned
        FROM versions v
        LEFT JOIN issues i ON i.fixed_in_version = v.id
        LEFT JOIN issues i2 ON i2.target_version = v.id
        WHERE v.project_id = $1
        GROUP BY v.id
        ORDER BY v.created_at DESC
      `, [projectId]);
      
      res.json(result.rows);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Create manual version
  router.post('/versions', async (req, res) => {
    const { project_id, version_number, release_type, release_notes, status } = req.body;
    
    try {
      const result = await pool.query(`
        INSERT INTO versions (
          project_id, version_number, release_type, 
          release_notes, status
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
      `, [project_id, version_number, release_type, release_notes, status || 'planned']);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Update version
  router.put('/versions/:versionId', async (req, res) => {
    const { versionId } = req.params;
    const { release_notes, status, release_date } = req.body;
    
    try {
      const result = await pool.query(`
        UPDATE versions
        SET release_notes = COALESCE($2, release_notes),
            status = COALESCE($3, status),
            release_date = COALESCE($4, release_date),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        RETURNING *
      `, [versionId, release_notes, status, release_date]);
      
      res.json(result.rows[0]);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Get version changelog
  router.get('/versions/changelog/:projectId', async (req, res) => {
    const { projectId } = req.params;
    const { limit = 10 } = req.query;
    
    try {
      const result = await pool.query(`
        SELECT v.*,
               array_agg(
                 json_build_object(
                   'id', i.id,
                   'title', i.title,
                   'status', i.status
                 )
               ) FILTER (WHERE i.id IS NOT NULL) as issues
        FROM versions v
        LEFT JOIN issues i ON i.fixed_in_version = v.id
        WHERE v.project_id = $1
        AND v.status = 'released'
        GROUP BY v.id
        ORDER BY v.release_date DESC
        LIMIT $2
      `, [projectId, parseInt(limit)]);
      
      res.json(result.rows);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  return router;
};