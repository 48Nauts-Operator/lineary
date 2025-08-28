// ABOUTME: API endpoints for AI Autopilot sprint execution
// ABOUTME: Handles session management, real-time updates, and agent control

import express from 'express';
import { WebSocketServer } from 'ws';
import { AutopilotOrchestrator } from '../services/AutopilotOrchestrator';

const router = express.Router();

// Initialize orchestrator (should be singleton)
let orchestrator: AutopilotOrchestrator;

export function initializeAutopilot(db: any, redis: any) {
  orchestrator = new AutopilotOrchestrator(db, redis);
  
  // Set up event listeners for WebSocket broadcasting
  orchestrator.on('session:started', broadcastUpdate);
  orchestrator.on('session:completed', broadcastUpdate);
  orchestrator.on('task:started', broadcastUpdate);
  orchestrator.on('task:completed', broadcastUpdate);
  orchestrator.on('task:failed', broadcastUpdate);
  
  return orchestrator;
}

// WebSocket connections for real-time updates
const wsClients = new Set<any>();

export function setupWebSocket(server: any) {
  const wss = new WebSocketServer({ 
    server,
    path: '/autopilot/stream' 
  });

  wss.on('connection', (ws) => {
    wsClients.add(ws);
    
    // Send initial state
    ws.send(JSON.stringify({
      type: 'connection',
      message: 'Connected to Autopilot stream'
    }));

    ws.on('close', () => {
      wsClients.delete(ws);
    });
  });
}

function broadcastUpdate(data: any) {
  const message = JSON.stringify({
    type: data.type || 'update',
    timestamp: new Date(),
    ...data
  });

  wsClients.forEach(client => {
    if (client.readyState === 1) { // WebSocket.OPEN
      client.send(message);
    }
  });
}

// Start autopilot for a sprint
router.post('/sprint/:sprintId/start', async (req, res) => {
  try {
    const { sprintId } = req.params;
    const config = req.body;
    
    const sessionId = await orchestrator.startSprintAutopilot(sprintId, config);
    
    res.json({
      success: true,
      sessionId,
      message: 'Autopilot session started'
    });
  } catch (error) {
    console.error('Failed to start autopilot:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to start autopilot session'
    });
  }
});

// Start autopilot for selected issues
router.post('/issues/start', async (req, res) => {
  try {
    const { issueIds, config } = req.body;
    
    // Create virtual sprint from issues
    const sessionId = await orchestrator.startIssuesAutopilot(issueIds, config);
    
    res.json({
      success: true,
      sessionId,
      message: 'Autopilot session started for selected issues'
    });
  } catch (error) {
    console.error('Failed to start autopilot:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to start autopilot session'
    });
  }
});

// Get session status
router.get('/session/:sessionId', async (req, res) => {
  try {
    const { sessionId } = req.params;
    const status = orchestrator.getSessionStatus(sessionId);
    
    if (!status) {
      return res.status(404).json({
        success: false,
        error: 'Session not found'
      });
    }
    
    res.json({
      success: true,
      session: status
    });
  } catch (error) {
    console.error('Failed to get session status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get session status'
    });
  }
});

// Pause session
router.post('/session/:sessionId/pause', async (req, res) => {
  try {
    const { sessionId } = req.params;
    await orchestrator.pauseSession(sessionId);
    
    res.json({
      success: true,
      message: 'Session paused'
    });
  } catch (error) {
    console.error('Failed to pause session:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to pause session'
    });
  }
});

// Resume session
router.post('/session/:sessionId/resume', async (req, res) => {
  try {
    const { sessionId } = req.params;
    await orchestrator.resumeSession(sessionId);
    
    res.json({
      success: true,
      message: 'Session resumed'
    });
  } catch (error) {
    console.error('Failed to resume session:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to resume session'
    });
  }
});

// Cancel session
router.post('/session/:sessionId/cancel', async (req, res) => {
  try {
    const { sessionId } = req.params;
    await orchestrator.cancelSession(sessionId);
    
    res.json({
      success: true,
      message: 'Session cancelled'
    });
  } catch (error) {
    console.error('Failed to cancel session:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to cancel session'
    });
  }
});

// Get active agents
router.get('/agents', async (req, res) => {
  try {
    const agents = orchestrator.getActiveAgents();
    
    res.json({
      success: true,
      agents
    });
  } catch (error) {
    console.error('Failed to get agents:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get agents'
    });
  }
});

// Get execution logs
router.get('/session/:sessionId/logs', async (req, res) => {
  try {
    const { sessionId } = req.params;
    const { limit = 100, offset = 0 } = req.query;
    
    const logs = await orchestrator.getExecutionLogs(
      sessionId, 
      parseInt(limit as string), 
      parseInt(offset as string)
    );
    
    res.json({
      success: true,
      logs
    });
  } catch (error) {
    console.error('Failed to get logs:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get execution logs'
    });
  }
});

// Get task pipeline status
router.get('/session/:sessionId/pipeline', async (req, res) => {
  try {
    const { sessionId } = req.params;
    const pipeline = await orchestrator.getTaskPipeline(sessionId);
    
    res.json({
      success: true,
      pipeline
    });
  } catch (error) {
    console.error('Failed to get pipeline:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get task pipeline'
    });
  }
});

// Configure agent settings
router.post('/agents/configure', async (req, res) => {
  try {
    const { agentId, settings } = req.body;
    await orchestrator.configureAgent(agentId, settings);
    
    res.json({
      success: true,
      message: 'Agent configured'
    });
  } catch (error) {
    console.error('Failed to configure agent:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to configure agent'
    });
  }
});

// Get cost estimate for sprint
router.get('/sprint/:sprintId/estimate', async (req, res) => {
  try {
    const { sprintId } = req.params;
    const estimate = await orchestrator.estimateSprintCost(sprintId);
    
    res.json({
      success: true,
      estimate
    });
  } catch (error) {
    console.error('Failed to estimate cost:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to estimate sprint cost'
    });
  }
});

// Get execution metrics
router.get('/metrics', async (req, res) => {
  try {
    const metrics = await orchestrator.getGlobalMetrics();
    
    res.json({
      success: true,
      metrics
    });
  } catch (error) {
    console.error('Failed to get metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get metrics'
    });
  }
});

export default router;