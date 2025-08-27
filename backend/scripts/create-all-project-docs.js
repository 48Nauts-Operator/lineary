// Script to create documentation for all projects
const { Pool } = require('pg');

const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://lineary:lineary_password@postgres:5432/lineary_db';
const pool = new Pool({
  connectionString: DATABASE_URL,
});

const projectDocs = {
  '77d460e2-0587-4b68-a200-2fb931566549': {
    name: 'Claude-Tasker Simple',
    docs: [
      {
        title: 'Claude-Tasker Simple Overview',
        category: 'overview',
        content: `# Claude-Tasker Simple

## Overview

Ultra-simple autonomous task execution for Claude - file-based and browser extension approaches for seamless AI task automation.

## Key Features

### 🤖 Autonomous Execution
- Continuous task processing without manual intervention
- Smart task prioritization based on dependencies
- Automatic error recovery and retry logic

### 📁 File-Based Approach
- Simple JSON task definitions
- File system monitoring for new tasks
- Results written back to filesystem

### 🌐 Browser Extension
- Direct integration with Claude.ai interface
- One-click task submission
- Real-time status monitoring

## Architecture

The system consists of two main components:

1. **File Watcher Service**
   - Monitors designated directories for task files
   - Parses and validates task definitions
   - Queues tasks for execution

2. **Browser Extension**
   - Injects controls into Claude interface
   - Manages task queue in browser storage
   - Handles authentication and session management

## Getting Started

### Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/yourusername/claude-tasker-simple

# Install dependencies
npm install

# Start the file watcher
npm run watch
\`\`\`

### Creating Tasks

Tasks are defined in JSON format:

\`\`\`json
{
  "name": "Research Task",
  "description": "Research latest AI developments",
  "priority": "high",
  "steps": [
    "Search for recent papers",
    "Summarize key findings",
    "Create report"
  ]
}
\`\`\`

## API Reference

### Task Definition Schema

| Field | Type | Description |
|-------|------|-------------|
| name | string | Task identifier |
| description | string | Detailed task description |
| priority | string | low, medium, high, urgent |
| steps | array | Sequential steps to execute |
| dependencies | array | Task IDs that must complete first |

## Best Practices

1. **Keep tasks atomic** - Each task should have a single, clear objective
2. **Use descriptive names** - Make task purpose immediately obvious
3. **Set appropriate priorities** - Reserve 'urgent' for truly critical tasks
4. **Chain related tasks** - Use dependencies to maintain execution order`
      }
    ]
  },
  '3056dd6d-1009-425e-beaa-aa1930e911d3': {
    name: 'Betty - Active Work',
    docs: [
      {
        title: 'Betty Active Work Documentation',
        category: 'overview',
        content: `# Betty - Active Work

## Overview

Active development and maintenance tasks for Betty Memory System - the intelligent memory and knowledge management platform.

## Current Sprint Focus

### 🎯 Priority Tasks

1. **Memory Optimization**
   - Implement efficient vector storage
   - Optimize retrieval algorithms
   - Reduce memory footprint

2. **Context Building**
   - Enhanced pattern recognition
   - Improved semantic understanding
   - Cross-reference capabilities

3. **User Interface**
   - Streamlined memory browsing
   - Advanced search features
   - Visualization improvements

## Development Guidelines

### Code Standards

- **TypeScript** for type safety
- **Test Coverage** minimum 80%
- **Documentation** for all public APIs
- **Code Review** required for all PRs

### Architecture Principles

1. **Modularity** - Loosely coupled components
2. **Scalability** - Horizontal scaling capability
3. **Resilience** - Graceful error handling
4. **Performance** - Sub-second response times

## API Endpoints

### Memory Operations

\`\`\`typescript
// Store new memory
POST /api/memories
{
  content: string,
  tags: string[],
  metadata: object
}

// Retrieve memories
GET /api/memories?query=<search>&limit=10

// Update memory
PUT /api/memories/:id

// Delete memory
DELETE /api/memories/:id
\`\`\`

### Context Building

\`\`\`typescript
// Build context from memories
POST /api/context/build
{
  query: string,
  depth: number,
  filters: object
}

// Get related memories
GET /api/context/related/:memoryId
\`\`\`

## Testing

### Unit Tests
\`\`\`bash
npm run test:unit
\`\`\`

### Integration Tests
\`\`\`bash
npm run test:integration
\`\`\`

### E2E Tests
\`\`\`bash
npm run test:e2e
\`\`\`

## Deployment

### Staging Environment
\`\`\`bash
npm run deploy:staging
\`\`\`

### Production Deployment
\`\`\`bash
npm run deploy:production
\`\`\`

## Monitoring

- **Performance Metrics**: DataDog dashboards
- **Error Tracking**: Sentry integration
- **Uptime Monitoring**: StatusPage.io
- **Log Aggregation**: ELK Stack`
      }
    ]
  },
  '2e8d3dbc-9f13-40a8-96ad-640c879f5aad': {
    name: 'Daily Planet - Medium MCP',
    docs: [
      {
        title: 'Daily Planet Medium MCP Documentation',
        category: 'overview',
        content: `# Daily Planet - Medium MCP

## Overview

MCP (Model Context Protocol) server for Medium.com integration - enables AI agents to create drafts, manage publications, and analyze content performance.

## Features

### 📝 Content Creation
- AI-powered article generation
- SEO optimization
- Automatic formatting
- Image suggestions

### 📊 Analytics Integration
- Real-time performance metrics
- Engagement tracking
- Audience insights
- Trending topic analysis

### 🚀 Publication Management
- Draft management
- Scheduled publishing
- Multi-publication support
- Tag optimization

## MCP Protocol Implementation

### Server Configuration

\`\`\`json
{
  "name": "daily-planet-medium",
  "version": "1.0.0",
  "protocol": "mcp",
  "capabilities": {
    "tools": true,
    "resources": true,
    "prompts": true
  }
}
\`\`\`

### Available Tools

#### CreateDraft
\`\`\`typescript
{
  tool: "createDraft",
  parameters: {
    title: string,
    content: string,
    tags: string[],
    publication?: string
  }
}
\`\`\`

#### PublishArticle
\`\`\`typescript
{
  tool: "publishArticle",
  parameters: {
    draftId: string,
    scheduledTime?: Date,
    notifyFollowers?: boolean
  }
}
\`\`\`

#### AnalyzePerformance
\`\`\`typescript
{
  tool: "analyzePerformance",
  parameters: {
    articleId?: string,
    timeRange?: string,
    metrics?: string[]
  }
}
\`\`\`

## Integration Setup

### 1. Medium API Token

1. Go to Medium Settings
2. Navigate to Integration Tokens
3. Generate new token
4. Add to environment variables:

\`\`\`bash
export MEDIUM_API_TOKEN=your_token_here
\`\`\`

### 2. MCP Server Installation

\`\`\`bash
# Install MCP server
npm install @daily-planet/medium-mcp

# Start server
npm run mcp:start
\`\`\`

### 3. Client Configuration

\`\`\`javascript
const mcp = new MCPClient({
  server: 'daily-planet-medium',
  endpoint: 'http://localhost:3000/mcp'
});

// Create article draft
const draft = await mcp.call('createDraft', {
  title: 'AI and the Future of Writing',
  content: '...',
  tags: ['AI', 'Writing', 'Technology']
});
\`\`\`

## Content Guidelines

### SEO Best Practices

1. **Title Optimization**
   - 60 characters or less
   - Include primary keyword
   - Make it compelling

2. **Meta Description**
   - 155 characters maximum
   - Clear value proposition
   - Call to action

3. **Content Structure**
   - Use H2/H3 headings
   - Short paragraphs (3-4 lines)
   - Include images every 300 words
   - Add relevant internal links

## Analytics Dashboard

### Key Metrics

- **Views**: Total article views
- **Reads**: Complete article reads
- **Read Ratio**: Reads/Views percentage
- **Fans**: Number of claps received
- **Engagement**: Comments and highlights

### Performance Benchmarks

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Read Ratio | <20% | 20-40% | 40-60% | >60% |
| Engagement | <2% | 2-5% | 5-10% | >10% |
| Fans/View | <0.05 | 0.05-0.1 | 0.1-0.2 | >0.2 |`
      }
    ]
  },
  '36d40f5e-e45f-4941-a959-0ae37762ecb5': {
    name: 'Betty Memory System',
    docs: [
      {
        title: 'Betty Memory System Documentation',
        category: 'overview',
        content: `# Betty Memory System

## Overview

AI-powered memory and knowledge management system with comprehensive pattern recognition, context building, and intelligent assistance capabilities.

## Core Concepts

### 🧠 Memory Architecture

Betty uses a hierarchical memory structure:

1. **Short-term Memory**
   - Recent interactions (last 24 hours)
   - Active context window
   - Quick retrieval cache

2. **Long-term Memory**
   - Persistent knowledge store
   - Vector-indexed for semantic search
   - Compressed and optimized storage

3. **Episodic Memory**
   - Event-based memories
   - Temporal relationships
   - Causal chains

### 🔍 Pattern Recognition

Advanced pattern detection across:
- **Behavioral Patterns**: User interaction trends
- **Knowledge Patterns**: Information relationships
- **Temporal Patterns**: Time-based correlations
- **Semantic Patterns**: Meaning connections

## System Architecture

\`\`\`mermaid
graph TB
    UI[User Interface] --> API[API Gateway]
    API --> MS[Memory Service]
    API --> CS[Context Service]
    API --> PS[Pattern Service]
    
    MS --> VDB[(Vector Database)]
    MS --> RDB[(Relational DB)]
    CS --> Cache[(Redis Cache)]
    PS --> ML[ML Pipeline]
\`\`\`

## API Reference

### Memory Management

#### Store Memory
\`\`\`http
POST /api/v1/memories
{
  "content": "Memory content",
  "type": "factual|episodic|procedural",
  "tags": ["tag1", "tag2"],
  "metadata": {
    "source": "user_input",
    "confidence": 0.95
  }
}
\`\`\`

#### Query Memories
\`\`\`http
GET /api/v1/memories/search
?query=search_term
&type=factual
&limit=10
&threshold=0.8
\`\`\`

#### Build Context
\`\`\`http
POST /api/v1/context/build
{
  "seed": "initial query or memory id",
  "depth": 3,
  "max_nodes": 50,
  "filters": {
    "time_range": "last_30_days",
    "min_relevance": 0.7
  }
}
\`\`\`

### Pattern Recognition

#### Detect Patterns
\`\`\`http
POST /api/v1/patterns/detect
{
  "memory_ids": ["id1", "id2", "id3"],
  "pattern_types": ["behavioral", "semantic"],
  "min_confidence": 0.8
}
\`\`\`

## Configuration

### Environment Variables

\`\`\`env
# Database
DATABASE_URL=postgresql://user:pass@localhost/betty
VECTOR_DB_URL=http://localhost:8000

# Redis
REDIS_URL=redis://localhost:6379

# ML Services
ML_API_ENDPOINT=http://ml-service:5000
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Performance
MAX_MEMORY_SIZE=10000
CACHE_TTL=3600
BATCH_SIZE=100
\`\`\`

### Memory Retention Policy

\`\`\`yaml
retention:
  short_term:
    duration: 24h
    max_items: 1000
  
  long_term:
    compression: true
    indexing: semantic
    pruning:
      - inactive_days: 90
      - low_relevance: 0.3
  
  episodic:
    group_by: session
    merge_similar: true
    threshold: 0.85
\`\`\`

## Performance Optimization

### Indexing Strategy

1. **Primary Indexes**
   - Memory ID (B-tree)
   - Timestamp (B-tree)
   - User ID (Hash)

2. **Secondary Indexes**
   - Tags (GIN)
   - Full-text search (GiST)
   - Vector similarity (IVFFlat)

### Caching Layers

- **L1 Cache**: In-memory (application)
- **L2 Cache**: Redis (distributed)
- **L3 Cache**: CDN (static resources)

## Deployment

### Docker Deployment

\`\`\`bash
# Build image
docker build -t betty-memory:latest .

# Run container
docker run -d \\
  -p 8080:8080 \\
  -e DATABASE_URL=$DATABASE_URL \\
  -e REDIS_URL=$REDIS_URL \\
  betty-memory:latest
\`\`\`

### Kubernetes Deployment

\`\`\`yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: betty-memory
spec:
  replicas: 3
  selector:
    matchLabels:
      app: betty-memory
  template:
    metadata:
      labels:
        app: betty-memory
    spec:
      containers:
      - name: betty
        image: betty-memory:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: betty-secrets
              key: database-url
\`\`\``
      }
    ]
  },
  'b545a5b9-a504-430e-90b7-8f9d1cfb9237': {
    name: 'Lineary Development',
    docs: [
      {
        title: 'Lineary Development Documentation',
        category: 'overview',
        content: `# Lineary Development

## Overview

Building Lineary - the AI-native project management platform that revolutionizes how teams work together.

## Development Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for blazing fast builds
- **Tailwind CSS** for styling
- **Zustand** for state management
- **React Query** for data fetching

### Backend
- **Node.js** with Express
- **PostgreSQL** for data persistence
- **Redis** for caching
- **Socket.io** for real-time updates

### AI Integration
- **OpenAI GPT-4** for intelligence
- **LangChain** for orchestration
- **Pinecone** for vector storage
- **Custom agents** for automation

## Project Structure

\`\`\`
Lineary/
├── frontend/          # React application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
├── backend/          # API server
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── migrations/
├── ai/              # AI services
│   ├── agents/
│   ├── prompts/
│   └── workflows/
└── docker-compose.yml
\`\`\`

## Development Setup

### Prerequisites
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 6+

### Local Development

\`\`\`bash
# Clone repository
git clone https://github.com/lineary/lineary

# Install dependencies
cd frontend && npm install
cd ../backend && npm install

# Start services
docker-compose up -d

# Run development servers
npm run dev # in both frontend and backend
\`\`\`

## Key Features Implementation

### Issue Management
- Real-time updates via WebSockets
- Optimistic UI updates
- Conflict resolution
- Offline support

### Sprint Planning
- AI-powered sprint suggestions
- Velocity calculations
- Burndown charts
- Capacity planning

### AI Autopilot
- Continuous sprint execution
- Task breakdown
- Code generation
- PR creation

## API Design

### RESTful Endpoints

\`\`\`typescript
// Projects
GET    /api/projects
POST   /api/projects
GET    /api/projects/:id
PUT    /api/projects/:id
DELETE /api/projects/:id

// Issues
GET    /api/issues
POST   /api/issues
GET    /api/issues/:id
PUT    /api/issues/:id
DELETE /api/issues/:id

// Sprints
GET    /api/sprints
POST   /api/sprints
POST   /api/sprints/:id/start
POST   /api/sprints/:id/complete
\`\`\`

### WebSocket Events

\`\`\`javascript
// Client → Server
socket.emit('subscribe', { project_id })
socket.emit('issue:update', { id, changes })

// Server → Client
socket.on('issue:created', (issue) => {})
socket.on('issue:updated', (issue) => {})
socket.on('sprint:started', (sprint) => {})
\`\`\`

## Testing Strategy

### Unit Tests
- Component testing with React Testing Library
- Service layer testing with Jest
- Minimum 80% coverage

### Integration Tests
- API endpoint testing
- Database integration
- External service mocking

### E2E Tests
- Critical user flows
- Cross-browser testing
- Performance benchmarks

## Deployment Pipeline

### CI/CD Flow

1. **Code Push** → GitHub
2. **CI Pipeline** → GitHub Actions
   - Linting & formatting
   - Unit tests
   - Build verification
3. **Staging Deployment**
   - Automated deployment
   - Integration tests
   - Performance tests
4. **Production Release**
   - Blue-green deployment
   - Health checks
   - Rollback capability

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Page Load | <2s | 1.8s |
| API Response | <200ms | 150ms |
| WebSocket Latency | <50ms | 30ms |
| Lighthouse Score | >90 | 92 |

## Security Measures

- JWT authentication
- Rate limiting
- SQL injection prevention
- XSS protection
- CSRF tokens
- Content Security Policy
- Regular dependency updates

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests
4. Submit pull request
5. Code review
6. Merge to main

## Roadmap

### Q1 2024
- ✅ Core issue management
- ✅ Sprint planning
- ✅ Basic AI integration
- ✅ Documentation system

### Q2 2024
- Advanced AI agents
- Mobile applications
- Enterprise features
- Marketplace

### Q3 2024
- Self-hosted version
- Advanced analytics
- Custom workflows
- API v2`
      }
    ]
  }
};

async function createAllProjectDocs() {
  try {
    for (const [projectId, projectData] of Object.entries(projectDocs)) {
      console.log(`Creating docs for ${projectData.name}...`);
      
      for (const doc of projectData.docs) {
        try {
          await pool.query(
            `INSERT INTO docs (title, content, category, project_id, created_at, updated_at)
             VALUES ($1, $2, $3, $4, NOW(), NOW())
             ON CONFLICT DO NOTHING`,
            [doc.title, doc.content, doc.category, projectId]
          );
          console.log(`  ✓ Created: ${doc.title}`);
        } catch (error) {
          console.error(`  ✗ Failed to create ${doc.title}:`, error.message);
        }
      }
    }
    
    console.log('\n✅ Documentation creation complete!');
    process.exit(0);
  } catch (error) {
    console.error('Error creating documentation:', error);
    process.exit(1);
  }
}

createAllProjectDocs();