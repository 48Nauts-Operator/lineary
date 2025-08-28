// ABOUTME: File attachment endpoints for issue ticket uploads
// ABOUTME: Handles file uploads, downloads, and attachment management

const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const crypto = require('crypto');

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../uploads');
    await fs.mkdir(uploadDir, { recursive: true });
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = crypto.randomBytes(16).toString('hex');
    const ext = path.extname(file.originalname);
    cb(null, `${uniqueSuffix}${ext}`);
  }
});

const upload = multer({ 
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB max file size
  },
  fileFilter: (req, file, cb) => {
    // Allow common file types
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'application/pdf', 'text/plain', 'text/csv',
      'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/zip', 'application/json'
    ];
    
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error(`File type ${file.mimetype} not allowed`), false);
    }
  }
});

module.exports = (pool) => {
  // Upload attachment to issue
  router.post('/attachments/upload/:issueId', upload.single('file'), async (req, res) => {
    const { issueId } = req.params;
    const file = req.file;
    
    if (!file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }
    
    try {
      const client = await pool.connect();
      
      try {
        // Begin transaction
        await client.query('BEGIN');
        
        // Insert attachment record
        const attachmentResult = await client.query(`
          INSERT INTO attachments (
            issue_id, filename, original_name, mime_type, 
            size_bytes, storage_path, uploaded_by
          )
          VALUES ($1, $2, $3, $4, $5, $6, $7)
          RETURNING *
        `, [
          issueId,
          file.filename,
          file.originalname,
          file.mimetype,
          file.size,
          file.path,
          req.user?.id || 'system'
        ]);
        
        // Update attachment count on issue
        await client.query(`
          UPDATE issues 
          SET attachment_count = attachment_count + 1,
              updated_at = CURRENT_TIMESTAMP
          WHERE id = $1
        `, [issueId]);
        
        await client.query('COMMIT');
        
        res.json({
          success: true,
          attachment: attachmentResult.rows[0]
        });
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      console.error('Upload error:', error);
      // Clean up uploaded file on error
      if (file.path) {
        await fs.unlink(file.path).catch(() => {});
      }
      res.status(500).json({ error: error.message });
    }
  });
  
  // Get attachments for an issue
  router.get('/attachments/issue/:issueId', async (req, res) => {
    const { issueId } = req.params;
    
    try {
      const result = await pool.query(`
        SELECT * FROM attachments
        WHERE issue_id = $1
        ORDER BY uploaded_at DESC
      `, [issueId]);
      
      res.json(result.rows);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Download attachment
  router.get('/attachments/download/:attachmentId', async (req, res) => {
    const { attachmentId } = req.params;
    
    try {
      const result = await pool.query(`
        SELECT * FROM attachments WHERE id = $1
      `, [attachmentId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Attachment not found' });
      }
      
      const attachment = result.rows[0];
      const filePath = attachment.storage_path;
      
      // Check if file exists
      await fs.access(filePath);
      
      // Set headers
      res.set({
        'Content-Type': attachment.mime_type,
        'Content-Disposition': `attachment; filename="${attachment.original_name}"`,
        'Content-Length': attachment.size_bytes
      });
      
      // Stream file to response
      const readStream = require('fs').createReadStream(filePath);
      readStream.pipe(res);
    } catch (error) {
      console.error('Download error:', error);
      res.status(404).json({ error: 'File not found' });
    }
  });
  
  // Delete attachment
  router.delete('/attachments/:attachmentId', async (req, res) => {
    const { attachmentId } = req.params;
    
    try {
      const client = await pool.connect();
      
      try {
        await client.query('BEGIN');
        
        // Get attachment details
        const attachmentResult = await client.query(`
          SELECT * FROM attachments WHERE id = $1
        `, [attachmentId]);
        
        if (attachmentResult.rows.length === 0) {
          await client.query('ROLLBACK');
          return res.status(404).json({ error: 'Attachment not found' });
        }
        
        const attachment = attachmentResult.rows[0];
        
        // Delete database record
        await client.query(`
          DELETE FROM attachments WHERE id = $1
        `, [attachmentId]);
        
        // Update attachment count
        await client.query(`
          UPDATE issues 
          SET attachment_count = attachment_count - 1,
              updated_at = CURRENT_TIMESTAMP
          WHERE id = $1
        `, [attachment.issue_id]);
        
        await client.query('COMMIT');
        
        // Delete file from filesystem
        await fs.unlink(attachment.storage_path).catch(() => {});
        
        res.json({ success: true });
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
  
  return router;
};