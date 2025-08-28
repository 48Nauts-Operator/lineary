// ABOUTME: API routes for AI feedback loop and improved estimation
// ABOUTME: Handles completion tracking, learning insights, and improved estimates

const express = require('express');
const router = express.Router();
const AIFeedbackLoop = require('../services/aiFeedbackLoop');

// Initialize AI feedback service with database
router.use((req, res, next) => {
  req.aiFeedback = new AIFeedbackLoop(req.db);
  next();
});

// Record issue completion for learning
router.post('/ai/feedback/completion', async (req, res) => {
  try {
    const { issueId, actualHours } = req.body;

    if (!issueId || actualHours === undefined) {
      return res.status(400).json({ 
        error: 'Missing required fields: issueId and actualHours' 
      });
    }

    const result = await req.aiFeedback.recordCompletion(issueId, actualHours);
    res.json(result);
  } catch (error) {
    console.error('Error recording completion:', error);
    res.status(500).json({ error: 'Failed to record completion feedback' });
  }
});

// Get improved estimate based on historical data
router.post('/ai/estimate', async (req, res) => {
  try {
    const { projectId, issueType, complexity } = req.body;

    if (!projectId) {
      return res.status(400).json({ 
        error: 'Missing required field: projectId' 
      });
    }

    const estimate = await req.aiFeedback.getImprovedEstimate(
      projectId,
      issueType,
      complexity
    );

    res.json(estimate);
  } catch (error) {
    console.error('Error getting improved estimate:', error);
    res.status(500).json({ error: 'Failed to generate estimate' });
  }
});

// Get learning insights for a project
router.get('/ai/insights/:projectId', async (req, res) => {
  try {
    const { projectId } = req.params;
    const insights = await req.aiFeedback.getLearningInsights(projectId);
    res.json(insights);
  } catch (error) {
    console.error('Error getting learning insights:', error);
    res.status(500).json({ error: 'Failed to get learning insights' });
  }
});

// Get project AI metrics
router.get('/ai/metrics/:projectId', async (req, res) => {
  try {
    const { projectId } = req.params;
    
    const metrics = await req.db.oneOrNone(`
      SELECT 
        AVG(ai_accuracy_score) as estimation_accuracy,
        AVG(review_quality_score) as review_quality,
        COUNT(*) as total_completions,
        MIN(created_at) as learning_since,
        MAX(created_at) as last_updated
      FROM ai_feedback_loop afl
      JOIN issues i ON i.id = afl.issue_id
      WHERE i.project_id = $1
    `, [projectId]);

    // Get recent improvements
    const improvements = await req.db.any(`
      SELECT 
        DATE_TRUNC('week', created_at) as week,
        AVG(ai_accuracy_score) as accuracy
      FROM ai_feedback_loop afl
      JOIN issues i ON i.id = afl.issue_id
      WHERE i.project_id = $1
        AND created_at > NOW() - INTERVAL '4 weeks'
      GROUP BY week
      ORDER BY week ASC
    `, [projectId]);

    const weeklyImprovement = improvements.length > 1 
      ? improvements[improvements.length - 1].accuracy - improvements[0].accuracy
      : 0;

    res.json({
      ...metrics,
      weekly_improvement: weeklyImprovement,
      is_learning: metrics?.total_completions > 5,
      confidence_level: 
        metrics?.total_completions >= 20 ? 'high' :
        metrics?.total_completions >= 10 ? 'medium' : 'low'
    });
  } catch (error) {
    console.error('Error getting AI metrics:', error);
    res.status(500).json({ error: 'Failed to get AI metrics' });
  }
});

module.exports = router;