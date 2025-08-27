// ABOUTME: API endpoints for continuous sprint execution
// ABOUTME: Manages the flow of tasks to Claude without stopping

import express from 'express';
import { SprintContinuousExecutor } from '../services/SprintContinuousExecutor';

const router = express.Router();
let executor: SprintContinuousExecutor;

export function initializeContinuousExecutor(db: any, redis: any) {
  executor = new SprintContinuousExecutor(db, redis);
  return executor;
}

// Start continuous execution for a sprint
router.post('/sprint/:sprintId/start', async (req, res) => {
  try {
    const { sprintId } = req.params;
    const instructions = await executor.initializeContinuousSprint(sprintId);
    
    res.json({
      success: true,
      message: 'Continuous sprint execution initialized',
      instructions,
      sprintId
    });
  } catch (error) {
    console.error('Failed to start continuous execution:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Mark task as complete and get next task
router.post('/sprint/:sprintId/task/:taskId/complete', async (req, res) => {
  try {
    const { sprintId, taskId } = req.params;
    const nextInstructions = await executor.markTaskComplete(sprintId, taskId);
    
    res.json({
      success: true,
      nextInstructions,
      continueExecution: !nextInstructions.includes('SPRINT COMPLETED')
    });
  } catch (error) {
    console.error('Failed to mark task complete:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get current task prompt
router.get('/sprint/:sprintId/current', async (req, res) => {
  try {
    const { sprintId } = req.params;
    const prompt = await executor.getNextTaskPrompt(sprintId);
    
    res.json({
      success: true,
      prompt
    });
  } catch (error) {
    console.error('Failed to get current task:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get session status
router.get('/sprint/:sprintId/status', async (req, res) => {
  try {
    const { sprintId } = req.params;
    const status = await executor.getSessionStatus(sprintId);
    
    if (!status) {
      return res.status(404).json({
        success: false,
        error: 'No continuous session found for this sprint'
      });
    }
    
    res.json({
      success: true,
      status
    });
  } catch (error) {
    console.error('Failed to get session status:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

export default router;