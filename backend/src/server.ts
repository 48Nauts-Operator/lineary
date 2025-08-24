// ABOUTME: Main server entry point for Lineary backend
// ABOUTME: Sets up Express server with GraphQL, WebSocket, and REST endpoints

import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { WebSocketServer } from 'ws';
import { ApolloServer } from 'apollo-server-express';
import { Pool } from 'pg';
import Redis from 'redis';
import dotenv from 'dotenv';

import { typeDefs } from './graphql/schema';
import { resolvers } from './graphql/resolvers';
import { DatabaseService } from './services/DatabaseService';
import { GitService } from './services/GitService';
import { SprintPokerEngine } from './services/SprintPokerEngine';
import { CodeQualityEngine } from './services/CodeQualityEngine';
import { AIOrchestrator } from './services/AIOrchestrator';
import { projectRoutes } from './routes/projects';
import { issueRoutes } from './routes/issues';
import { sprintRoutes } from './routes/sprints';
import { mcpRoutes } from './routes/mcp';
import { healthRoutes } from './routes/health';
import { aiRoutes } from './routes/ai';

dotenv.config();

const app = express();
const httpServer = createServer(app);
const PORT = process.env.PORT || 8000;

// Database connection
const pgPool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Redis connection
const redisClient = Redis.createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379'
});

// WebSocket server for real-time updates
const wss = new WebSocketServer({ 
  server: httpServer,
  path: '/api/ws'
});

// Initialize services
const dbService = new DatabaseService(pgPool);
const gitService = new GitService();
const sprintPoker = new SprintPokerEngine();
const codeQuality = new CodeQualityEngine(pgPool);
const aiOrchestrator = new AIOrchestrator(pgPool, {
  openai_api_key: process.env.OPENAI_API_KEY || '',
  anthropic_api_key: process.env.ANTHROPIC_API_KEY,
  anthropic_base_url: process.env.ANTHROPIC_BASE_URL,
  default_model: process.env.DEFAULT_AI_MODEL || 'gpt-4',
  max_tokens: parseInt(process.env.MAX_TOKENS || '4000'),
  temperature: parseFloat(process.env.AI_TEMPERATURE || '0.1')
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Context for GraphQL resolvers
const context = {
  db: dbService,
  git: gitService,
  sprintPoker,
  codeQuality,
  ai: aiOrchestrator,
  redis: redisClient,
  broadcast: (event: string, data: any) => {
    wss.clients.forEach(client => {
      if (client.readyState === 1) {
        client.send(JSON.stringify({ event, data }));
      }
    });
  }
};

// REST Routes
app.use('/api/health', healthRoutes);
app.use('/api/projects', projectRoutes(context));
app.use('/api/issues', issueRoutes(context));
app.use('/api/sprints', sprintRoutes(context));
app.use('/api/mcp', mcpRoutes(context));
app.use('/api/ai', aiRoutes(context));

// WebSocket connection handler
wss.on('connection', (ws) => {
  console.log('New WebSocket connection');
  
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString());
      console.log('WebSocket message:', data);
      
      // Handle different message types
      switch(data.type) {
        case 'subscribe':
          ws.send(JSON.stringify({ type: 'subscribed', channel: data.channel }));
          break;
        case 'ping':
          ws.send(JSON.stringify({ type: 'pong' }));
          break;
      }
    } catch (error) {
      console.error('WebSocket message error:', error);
    }
  });
  
  ws.on('close', () => {
    console.log('WebSocket connection closed');
  });
});

// Initialize server
async function startServer() {
  try {
    // Connect to Redis
    await redisClient.connect();
    console.log('✅ Connected to Redis');
    
    // Initialize database
    await dbService.initialize();
    console.log('✅ Database initialized');
    
    // Initialize AI services
    await aiOrchestrator.initialize();
    console.log('✅ AI Orchestrator initialized');
    
    await codeQuality.initialize();
    console.log('✅ Code Quality Engine initialized');
    
    // Setup Apollo Server
    const apolloServer = new ApolloServer({
      typeDefs,
      resolvers,
      context: () => context,
    });
    
    await apolloServer.start();
    apolloServer.applyMiddleware({ app, path: '/api/graphql' });
    
    // Start HTTP server
    httpServer.listen(PORT, () => {
      console.log(`🚀 Lineary server running on port ${PORT}`);
      console.log(`🌐 Public URL: https://lineary.blockonauts.io`);
      console.log(`📊 GraphQL endpoint: https://lineary.blockonauts.io/api/graphql`);
      console.log(`🔌 WebSocket endpoint: wss://lineary.blockonauts.io/api/ws`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('Shutting down gracefully...');
  await pgPool.end();
  await redisClient.quit();
  httpServer.close();
  process.exit(0);
});

startServer();