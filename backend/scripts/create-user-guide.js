// Script to create comprehensive Lineary user guide documentation
const { Pool } = require('pg');

const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://lineary:lineary_password@postgres:5432/lineary_db';
const pool = new Pool({
  connectionString: DATABASE_URL,
});

async function createUserGuide() {
  try {
    // First, get the first project or create a default one
    let projectResult = await pool.query('SELECT * FROM projects LIMIT 1');
    let projectId;
    
    if (projectResult.rows.length === 0) {
      // Create a default project for documentation
      const createProject = await pool.query(
        `INSERT INTO projects (name, description, created_at, updated_at) 
         VALUES ($1, $2, NOW(), NOW()) 
         RETURNING id`,
        ['Lineary Platform', 'The Lineary project management system']
      );
      projectId = createProject.rows[0].id;
    } else {
      projectId = projectResult.rows[0].id;
    }

    // User Guide documents
    const docs = [
      {
        title: 'Lineary User Guide - Getting Started',
        category: 'guides',
        content: `# Lineary User Guide

## Welcome to Lineary

Lineary is an AI-powered project management platform that revolutionizes how teams work together. Built for the age of AI, Lineary seamlessly integrates artificial intelligence into every aspect of project management, making your team more productive and efficient.

## What is Lineary?

Lineary is a modern project management tool inspired by Linear's minimalist design philosophy but rebuilt from the ground up for AI-native workflows. It combines:

- **Traditional Project Management**: Issues, sprints, roadmaps, and team collaboration
- **AI Integration**: Intelligent automation, smart suggestions, and AI agents
- **Developer-First Design**: Clean interface, keyboard shortcuts, and API-first architecture
- **Real-Time Collaboration**: Live updates, instant sync, and team presence

## Key Features

### 📋 **Issue Tracking**
- Create, assign, and track issues with rich descriptions
- Set priorities, story points, and custom labels
- Link related issues and dependencies
- Track progress with customizable statuses

### 🏃 **Sprint Management**
- Plan and execute sprints with AI assistance
- Automatic sprint planning based on velocity
- Real-time burndown charts and progress tracking
- AI-powered sprint retrospectives

### 🤖 **AI Autopilot**
- Continuous sprint execution with AI agents
- Automatic task breakdown and estimation
- Intelligent issue routing and assignment
- Smart notifications and escalations

### 📊 **Analytics & Insights**
- Team velocity and performance metrics
- Predictive delivery timelines
- Bottleneck identification
- Custom dashboards and reports

### 📚 **Documentation**
- Integrated documentation for each project
- Markdown support with syntax highlighting
- Link docs to issues and sprints
- Version control and history

## Getting Started

### 1. Creating Your First Project

1. Click the **"New Project"** button in the sidebar
2. Enter a project name and description
3. Choose your project template (optional)
4. Click **Create Project**

Your project is now ready! You'll be taken to the project dashboard where you can start adding issues and team members.

### 2. Setting Up Your Team

1. Navigate to **Settings → Team**
2. Click **"Invite Members"**
3. Enter email addresses or share the invite link
4. Set roles and permissions for each member

Team members will receive an invitation and can join immediately.

### 3. Creating Your First Issue

1. Press **C** (keyboard shortcut) or click **"New Issue"**
2. Enter a title and description
3. Set the priority and assignee
4. Add labels and story points
5. Press **Enter** or click **"Create Issue"**

Pro tip: Use markdown in descriptions for formatting!

### 4. Planning a Sprint

1. Go to the **Sprints** tab
2. Click **"New Sprint"**
3. Set sprint duration (default: 2 weeks)
4. Drag issues from the backlog to the sprint
5. Click **"Start Sprint"**

The AI will analyze your sprint and provide recommendations for optimization.

## Keyboard Shortcuts

Lineary is designed for keyboard-first navigation:

- **C** - Create new issue
- **S** - Open search
- **G then I** - Go to issues
- **G then S** - Go to sprints
- **G then D** - Go to docs
- **/** - Quick search
- **Cmd/Ctrl + K** - Command palette
- **ESC** - Close modals/panels

## Working with Issues

### Issue States

Issues in Lineary follow a simple workflow:

1. **Backlog** - Not yet started
2. **Todo** - Ready to work on
3. **In Progress** - Currently being worked on
4. **In Review** - Ready for review
5. **Done** - Completed

### Priority Levels

- 🔴 **Urgent** - Drop everything
- 🟠 **High** - Important, do soon
- 🟡 **Medium** - Normal priority
- 🟢 **Low** - Nice to have

### Using Labels

Labels help categorize and filter issues:

- **bug** - Something isn't working
- **feature** - New functionality
- **improvement** - Enhancement to existing features
- **documentation** - Documentation updates
- **performance** - Performance improvements

Create custom labels for your team's needs!

## AI Features

### AI Autopilot

Enable AI Autopilot to have AI agents continuously work on your sprints:

1. Go to **Settings → AI**
2. Toggle **"Enable Autopilot"**
3. Configure execution frequency
4. Set approval requirements

The AI will:
- Analyze new issues
- Break down complex tasks
- Suggest implementations
- Create pull requests
- Update documentation

### Smart Suggestions

Lineary's AI provides intelligent suggestions:

- **Auto-assignment** based on expertise
- **Time estimates** from historical data
- **Priority recommendations** based on impact
- **Dependency detection** from descriptions
- **Similar issue** identification

### Natural Language Commands

Use natural language in the command palette:

- "Create a bug about login issues"
- "Show me all high priority items"
- "Assign all frontend tasks to Sarah"
- "Start a new sprint next Monday"

## Best Practices

### 1. Write Clear Issue Descriptions

Good issue description:
\`\`\`markdown
## Problem
Users cannot reset their password when using OAuth login

## Steps to Reproduce
1. Login with Google OAuth
2. Go to Settings → Security
3. Click "Reset Password"
4. Observe error message

## Expected Behavior
Show message that OAuth users manage passwords externally

## Actual Behavior
Generic error "Password reset failed"
\`\`\`

### 2. Use Story Points Effectively

- **1 point** - Trivial change (< 1 hour)
- **2 points** - Simple task (2-4 hours)
- **3 points** - Standard task (1 day)
- **5 points** - Complex task (2-3 days)
- **8 points** - Very complex (1 week)
- **13+ points** - Should be broken down

### 3. Maintain Sprint Hygiene

- Review and groom backlog weekly
- Keep sprints focused (80% capacity)
- Update issue status daily
- Close completed issues promptly
- Run retrospectives after each sprint

### 4. Leverage AI Wisely

- Let AI handle routine tasks
- Review AI suggestions before accepting
- Provide feedback to improve AI accuracy
- Use AI for initial drafts, refine manually
- Set clear boundaries for autonomous actions

## Troubleshooting

### Common Issues

**Q: Changes not syncing?**
A: Check your internet connection. Lineary requires a stable connection for real-time sync.

**Q: Can't see a project?**
A: Verify you have the correct permissions. Contact your project admin.

**Q: AI suggestions seem off?**
A: The AI learns from your team's patterns. Give it time and provide feedback.

**Q: Keyboard shortcuts not working?**
A: Ensure you're not in an input field. Press ESC to reset focus.

## Support

Need help? We're here for you:

- 📧 Email: support@lineary.ai
- 💬 Discord: discord.gg/lineary
- 📚 Docs: docs.lineary.ai
- 🐛 Report bugs: github.com/lineary/issues

## Next Steps

Now that you understand the basics:

1. **Explore integrations** - Connect GitHub, Slack, etc.
2. **Customize workflows** - Tailor Lineary to your process
3. **Set up automation** - Create rules and triggers
4. **Train your AI** - Provide feedback for better suggestions
5. **Invite your team** - Collaboration makes everything better!

Welcome to the future of project management with Lineary! 🚀`
      },
      {
        title: 'Advanced Features',
        category: 'guides',
        content: `# Advanced Features

## Automation Rules

Create powerful automation to streamline your workflow:

### Setting Up Automation

1. Go to **Settings → Automation**
2. Click **"New Rule"**
3. Define trigger conditions
4. Set actions to perform
5. Test and activate

### Example Automations

**Auto-assign by label:**
\`\`\`
WHEN issue created
AND label contains "frontend"
THEN assign to frontend-team
\`\`\`

**Escalate stale issues:**
\`\`\`
WHEN issue in-progress > 5 days
AND no activity > 2 days
THEN add label "needs-attention"
AND notify manager
\`\`\`

**Sprint completion:**
\`\`\`
WHEN sprint ends
THEN move incomplete issues to next sprint
AND create retrospective document
AND schedule review meeting
\`\`\`

## Custom Fields

Extend issues with custom data:

1. **Settings → Custom Fields**
2. Click **"Add Field"**
3. Choose field type:
   - Text
   - Number
   - Date
   - Dropdown
   - Multi-select
   - User
   - URL

### Use Cases

- **Customer** - Track which customer reported the bug
- **Revenue Impact** - Estimate financial impact
- **Deploy Date** - Target deployment date
- **Components** - Affected system components
- **Risk Level** - Assessment of risk

## API Integration

Lineary provides a comprehensive REST API:

### Authentication

\`\`\`bash
curl -H "Authorization: Bearer YOUR_API_KEY" \\
  https://api.lineary.ai/v1/issues
\`\`\`

### Creating Issues via API

\`\`\`javascript
const response = await fetch('https://api.lineary.ai/v1/issues', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: 'API Created Issue',
    description: 'This issue was created via the API',
    priority: 'high',
    labels: ['api', 'automation'],
  })
});
\`\`\`

### Webhooks

Receive real-time updates:

1. **Settings → Webhooks**
2. Add endpoint URL
3. Select events to monitor
4. Configure retry policy

## Integrations

### GitHub Integration

Connect GitHub for seamless development:

1. **Settings → Integrations → GitHub**
2. Authorize Lineary
3. Select repositories
4. Configure sync options

Features:
- Auto-link commits to issues
- Create branches from issues
- Sync PR status
- Close issues on merge

### Slack Integration

Stay updated in Slack:

1. **Settings → Integrations → Slack**
2. Add to workspace
3. Select channels
4. Configure notifications

Notifications for:
- Issue assignments
- Status changes
- Sprint updates
- Mentions

## Reporting & Analytics

### Custom Dashboards

Build personalized dashboards:

1. **Analytics → New Dashboard**
2. Add widgets:
   - Velocity chart
   - Burndown chart
   - Issue distribution
   - Team workload
   - Cycle time
3. Configure refresh rate
4. Share with team

### Advanced Metrics

Track sophisticated metrics:

- **Lead Time** - Idea to production
- **Cycle Time** - Start to finish
- **Throughput** - Issues completed per sprint
- **WIP Limits** - Work in progress limits
- **Flow Efficiency** - Active vs wait time

## Team Management

### Roles & Permissions

Fine-grained access control:

- **Admin** - Full access
- **Manager** - Project settings, team management
- **Developer** - Create, edit, close issues
- **Viewer** - Read-only access

### Teams within Teams

Organize large organizations:

1. Create parent team
2. Add sub-teams (Frontend, Backend, QA)
3. Set team-specific:
   - Labels
   - Workflows
   - Notifications
   - Permissions

## Performance Optimization

### Tips for Large Teams

- Use filters aggressively
- Archive completed sprints
- Limit real-time updates to relevant issues
- Use batch operations for bulk changes
- Enable lazy loading for large backlogs

### Search Optimization

Advanced search syntax:

- \`assignee:me\` - Your issues
- \`is:open\` - Open issues
- \`label:bug,urgent\` - Multiple labels
- \`created:>2024-01-01\` - Date ranges
- \`has:attachment\` - Issues with attachments
- \`sprint:current\` - Current sprint issues

## Security & Compliance

### Security Features

- **SSO/SAML** - Enterprise authentication
- **2FA** - Two-factor authentication
- **Audit Logs** - Complete activity history
- **IP Restrictions** - Limit access by IP
- **Data Encryption** - At rest and in transit

### Compliance

- **GDPR** compliant
- **SOC 2** Type II certified
- **ISO 27001** certified
- **HIPAA** compliant (Enterprise)

### Data Export

Export your data anytime:

1. **Settings → Export**
2. Select format:
   - JSON
   - CSV
   - PDF
3. Choose data types
4. Download archive

## Tips & Tricks

### Power User Tips

1. **Bulk Edit**: Select multiple issues with Shift+Click
2. **Quick Add**: Type \`/\` anywhere to quick-add issues
3. **Templates**: Save issue templates for common tasks
4. **Saved Views**: Save complex filters as views
5. **Email to Issue**: Send emails to create issues

### Hidden Features

- **Cmd+Shift+P** - Developer console
- **Double-click status** - Quick status change
- **Drag to multi-select** - In list view
- **@here** - Notify all online team members
- **#sprint** - Link to current sprint`
      },
      {
        title: 'API Reference',
        category: 'api',
        content: `# API Reference

## Overview

The Lineary API is a RESTful API that provides programmatic access to all Lineary features.

Base URL: \`https://api.lineary.ai/v1\`

## Authentication

All API requests require authentication using an API key.

### Getting an API Key

1. Go to **Settings → API**
2. Click **Generate New Key**
3. Copy and store securely

### Using the API Key

Include in the Authorization header:

\`\`\`bash
Authorization: Bearer YOUR_API_KEY
\`\`\`

## Endpoints

### Issues

#### List Issues

\`\`\`http
GET /issues
\`\`\`

Query parameters:
- \`project_id\` - Filter by project
- \`status\` - Filter by status
- \`assignee\` - Filter by assignee
- \`label\` - Filter by label
- \`page\` - Page number (default: 1)
- \`limit\` - Items per page (default: 50)

Response:
\`\`\`json
{
  "data": [
    {
      "id": "ISS-001",
      "title": "Issue title",
      "description": "Issue description",
      "status": "in_progress",
      "priority": "high",
      "assignee": {
        "id": "usr_123",
        "name": "John Doe"
      },
      "labels": ["bug", "urgent"],
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 234
  }
}
\`\`\`

#### Get Issue

\`\`\`http
GET /issues/{id}
\`\`\`

#### Create Issue

\`\`\`http
POST /issues
\`\`\`

Request body:
\`\`\`json
{
  "title": "New issue",
  "description": "Issue description",
  "project_id": "proj_123",
  "priority": "medium",
  "assignee_id": "usr_456",
  "labels": ["feature"],
  "story_points": 3
}
\`\`\`

#### Update Issue

\`\`\`http
PATCH /issues/{id}
\`\`\`

#### Delete Issue

\`\`\`http
DELETE /issues/{id}
\`\`\`

### Projects

#### List Projects

\`\`\`http
GET /projects
\`\`\`

#### Get Project

\`\`\`http
GET /projects/{id}
\`\`\`

#### Create Project

\`\`\`http
POST /projects
\`\`\`

Request body:
\`\`\`json
{
  "name": "New Project",
  "description": "Project description",
  "team_id": "team_123"
}
\`\`\`

### Sprints

#### List Sprints

\`\`\`http
GET /sprints
\`\`\`

Query parameters:
- \`project_id\` - Filter by project
- \`status\` - active, completed, planned

#### Get Sprint

\`\`\`http
GET /sprints/{id}
\`\`\`

#### Create Sprint

\`\`\`http
POST /sprints
\`\`\`

Request body:
\`\`\`json
{
  "name": "Sprint 23",
  "project_id": "proj_123",
  "start_date": "2024-02-01",
  "end_date": "2024-02-14",
  "goal": "Complete authentication system"
}
\`\`\`

#### Start Sprint

\`\`\`http
POST /sprints/{id}/start
\`\`\`

#### Complete Sprint

\`\`\`http
POST /sprints/{id}/complete
\`\`\`

### Users

#### List Users

\`\`\`http
GET /users
\`\`\`

#### Get User

\`\`\`http
GET /users/{id}
\`\`\`

#### Get Current User

\`\`\`http
GET /users/me
\`\`\`

### Comments

#### List Comments

\`\`\`http
GET /issues/{issue_id}/comments
\`\`\`

#### Create Comment

\`\`\`http
POST /issues/{issue_id}/comments
\`\`\`

Request body:
\`\`\`json
{
  "body": "Comment text",
  "mentions": ["usr_123"]
}
\`\`\`

### Webhooks

#### List Webhooks

\`\`\`http
GET /webhooks
\`\`\`

#### Create Webhook

\`\`\`http
POST /webhooks
\`\`\`

Request body:
\`\`\`json
{
  "url": "https://your-server.com/webhook",
  "events": ["issue.created", "issue.updated"],
  "secret": "webhook_secret"
}
\`\`\`

## Rate Limiting

API requests are limited to:
- 1000 requests per hour for Free tier
- 10000 requests per hour for Pro tier
- Unlimited for Enterprise

Rate limit headers:
\`\`\`
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
\`\`\`

## Error Handling

Error response format:
\`\`\`json
{
  "error": {
    "code": "validation_error",
    "message": "Validation failed",
    "details": {
      "title": "Title is required"
    }
  }
}
\`\`\`

Common error codes:
- \`400\` - Bad Request
- \`401\` - Unauthorized
- \`403\` - Forbidden
- \`404\` - Not Found
- \`429\` - Too Many Requests
- \`500\` - Internal Server Error

## Pagination

Use \`page\` and \`limit\` parameters:

\`\`\`http
GET /issues?page=2&limit=25
\`\`\`

Response includes pagination meta:
\`\`\`json
{
  "meta": {
    "page": 2,
    "limit": 25,
    "total": 150,
    "pages": 6
  }
}
\`\`\`

## Filtering

Complex filters using query parameters:

\`\`\`http
GET /issues?status=open&priority=high&label=bug
\`\`\`

## Sorting

Sort results using \`sort\` parameter:

\`\`\`http
GET /issues?sort=-created_at
\`\`\`

- \`-\` prefix for descending order
- No prefix for ascending order

## Webhooks Events

Available webhook events:

- \`issue.created\`
- \`issue.updated\`
- \`issue.deleted\`
- \`issue.status_changed\`
- \`sprint.started\`
- \`sprint.completed\`
- \`project.created\`
- \`comment.created\`

## SDKs

Official SDKs available:

### JavaScript/TypeScript

\`\`\`bash
npm install @lineary/sdk
\`\`\`

\`\`\`javascript
import { LinearyClient } from '@lineary/sdk';

const client = new LinearyClient({
  apiKey: 'YOUR_API_KEY'
});

const issues = await client.issues.list({
  project_id: 'proj_123',
  status: 'open'
});
\`\`\`

### Python

\`\`\`bash
pip install lineary-sdk
\`\`\`

\`\`\`python
from lineary import LinearyClient

client = LinearyClient(api_key='YOUR_API_KEY')

issues = client.issues.list(
  project_id='proj_123',
  status='open'
)
\`\`\`

### Go

\`\`\`bash
go get github.com/lineary/lineary-go
\`\`\`

### Ruby

\`\`\`bash
gem install lineary
\`\`\``
      },
      {
        title: 'Architecture Overview',
        category: 'architecture',
        content: `# Architecture Overview

## System Architecture

Lineary follows a modern microservices architecture designed for scale and reliability.

## Core Components

### Frontend (React + TypeScript)

The frontend is a single-page application built with:

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Query** - Data fetching
- **Socket.io** - Real-time updates

### Backend (Node.js)

The API backend uses:

- **Express.js** - Web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and pub/sub
- **Bull** - Job queues
- **Socket.io** - WebSocket connections

### AI Services (Python)

AI capabilities powered by:

- **FastAPI** - API framework
- **OpenAI GPT-4** - Language model
- **LangChain** - AI orchestration
- **Pinecone** - Vector database
- **Celery** - Task queue

### Infrastructure

Deployed on:

- **AWS ECS** - Container orchestration
- **AWS RDS** - Managed PostgreSQL
- **AWS ElastiCache** - Managed Redis
- **AWS S3** - File storage
- **CloudFlare** - CDN and DDoS protection
- **DataDog** - Monitoring

## Data Flow

\`\`\`mermaid
graph LR
    Client[Web Client] --> CDN[CloudFlare CDN]
    CDN --> ALB[Load Balancer]
    ALB --> API[API Servers]
    API --> Cache{Redis Cache}
    API --> DB[(PostgreSQL)]
    API --> Queue[Job Queue]
    Queue --> Workers[Background Workers]
    Workers --> AI[AI Services]
    AI --> Vector[(Vector DB)]
\`\`\`

## Database Schema

### Core Tables

#### projects
- id (UUID, PK)
- name (VARCHAR)
- description (TEXT)
- team_id (UUID, FK)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

#### issues
- id (UUID, PK)
- project_id (UUID, FK)
- title (VARCHAR)
- description (TEXT)
- status (ENUM)
- priority (ENUM)
- assignee_id (UUID, FK)
- reporter_id (UUID, FK)
- story_points (INT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

#### sprints
- id (UUID, PK)
- project_id (UUID, FK)
- name (VARCHAR)
- goal (TEXT)
- start_date (DATE)
- end_date (DATE)
- status (ENUM)
- created_at (TIMESTAMP)

#### users
- id (UUID, PK)
- email (VARCHAR, UNIQUE)
- name (VARCHAR)
- role (ENUM)
- team_id (UUID, FK)
- created_at (TIMESTAMP)

### Relationships

- Projects → Issues (1:N)
- Projects → Sprints (1:N)
- Sprints → Issues (N:N)
- Users → Issues (1:N as assignee)
- Users → Issues (1:N as reporter)

## Security Architecture

### Authentication & Authorization

- **JWT tokens** for API authentication
- **OAuth 2.0** for third-party integrations
- **RBAC** (Role-Based Access Control)
- **Row-level security** in PostgreSQL

### Data Security

- **TLS 1.3** for all connections
- **AES-256** encryption at rest
- **Secrets management** via AWS Secrets Manager
- **Regular security audits** and penetration testing

### Compliance

- **GDPR** compliant data handling
- **SOC 2** Type II certified
- **ISO 27001** certified infrastructure
- **HIPAA** compliant (Enterprise)

## Performance Optimizations

### Caching Strategy

1. **CDN caching** for static assets
2. **Redis caching** for:
   - User sessions
   - Frequently accessed data
   - Real-time presence
3. **Database query caching**
4. **API response caching** with ETags

### Database Optimizations

- **Connection pooling**
- **Read replicas** for scaling reads
- **Partitioning** for large tables
- **Materialized views** for complex queries
- **Optimized indexes** for common queries

### Frontend Optimizations

- **Code splitting** for faster initial load
- **Lazy loading** of components
- **Virtual scrolling** for large lists
- **Image optimization** and lazy loading
- **Service workers** for offline support

## Scalability Design

### Horizontal Scaling

- **Stateless API servers** - Easy to scale
- **Database read replicas** - Scale read operations
- **Redis cluster** - Distributed caching
- **Queue workers** - Scale background jobs

### Vertical Scaling

- **Auto-scaling groups** - Based on CPU/memory
- **Database instance sizing** - Upgrade as needed
- **Cache instance sizing** - Based on memory needs

### Global Scale

- **Multi-region deployment** - Reduce latency
- **GeoDNS** - Route to nearest region
- **Cross-region replication** - Data availability
- **Edge caching** - Global CDN presence

## Monitoring & Observability

### Metrics

- **Application metrics** - Response times, error rates
- **Infrastructure metrics** - CPU, memory, disk
- **Business metrics** - Active users, issue velocity
- **Custom metrics** - AI usage, feature adoption

### Logging

- **Structured logging** - JSON format
- **Centralized logging** - ELK stack
- **Log aggregation** - Across all services
- **Log retention** - 90 days standard

### Tracing

- **Distributed tracing** - OpenTelemetry
- **Request tracing** - End-to-end visibility
- **Performance profiling** - Identify bottlenecks
- **Error tracking** - Sentry integration

### Alerting

- **PagerDuty** integration
- **Slack notifications**
- **Email alerts**
- **Custom webhooks**

## Disaster Recovery

### Backup Strategy

- **Automated backups** - Every 6 hours
- **Point-in-time recovery** - Up to 35 days
- **Cross-region backups** - Geographic redundancy
- **Backup testing** - Monthly restoration tests

### High Availability

- **Multi-AZ deployment** - No single point of failure
- **Load balancing** - Distribute traffic
- **Health checks** - Automatic failover
- **Circuit breakers** - Prevent cascade failures

### Recovery Procedures

1. **RTO** (Recovery Time Objective): < 1 hour
2. **RPO** (Recovery Point Objective): < 15 minutes
3. **Automated failover** for critical services
4. **Runbooks** for manual intervention
5. **Regular DR drills** quarterly

## Development Workflow

### CI/CD Pipeline

1. **Code commit** → GitHub
2. **Automated tests** → GitHub Actions
3. **Code review** → Pull request
4. **Security scanning** → Snyk
5. **Build & package** → Docker
6. **Deploy to staging** → Automated
7. **Integration tests** → Automated
8. **Deploy to production** → Blue/green

### Environment Strategy

- **Development** - Local development
- **Staging** - Pre-production testing
- **Production** - Live environment
- **DR** - Disaster recovery standby

### Feature Flags

- **LaunchDarkly** integration
- **Gradual rollouts**
- **A/B testing**
- **Quick rollback**`
      },
      {
        title: 'Deployment Guide',
        category: 'deployment',
        content: `# Deployment Guide

## Prerequisites

Before deploying Lineary, ensure you have:

- Docker and Docker Compose installed
- Node.js 18+ and npm
- PostgreSQL 14+
- Redis 6+
- Domain name configured
- SSL certificates

## Local Development Setup

### 1. Clone the Repository

\`\`\`bash
git clone https://github.com/lineary/lineary.git
cd lineary
\`\`\`

### 2. Environment Configuration

Create \`.env\` file:

\`\`\`env
# Database
DATABASE_URL=postgresql://lineary:password@localhost:5432/lineary_db
REDIS_URL=redis://localhost:6379

# API
API_PORT=8000
API_URL=http://localhost:8000

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# AI Services
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key

# Authentication
JWT_SECRET=your_jwt_secret
SESSION_SECRET=your_session_secret

# External Services
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
\`\`\`

### 3. Install Dependencies

\`\`\`bash
# Backend
cd backend
npm install

# Frontend
cd ../frontend
npm install

# AI Services
cd ../ai
pip install -r requirements.txt
\`\`\`

### 4. Database Setup

\`\`\`bash
# Start PostgreSQL
docker run -d \\
  --name lineary-postgres \\
  -e POSTGRES_USER=lineary \\
  -e POSTGRES_PASSWORD=password \\
  -e POSTGRES_DB=lineary_db \\
  -p 5432:5432 \\
  postgres:14

# Run migrations
cd backend
npm run migrate
\`\`\`

### 5. Start Services

\`\`\`bash
# Start all services with Docker Compose
docker-compose up -d

# Or start individually:

# Backend
cd backend
npm run dev

# Frontend
cd frontend
npm run dev

# AI Services
cd ai
uvicorn main:app --reload
\`\`\`

## Production Deployment

### Using Docker Compose

#### 1. Production Configuration

Create \`docker-compose.prod.yml\`:

\`\`\`yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: lineary
      POSTGRES_PASSWORD: \${DB_PASSWORD}
      POSTGRES_DB: lineary_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass \${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://lineary:\${DB_PASSWORD}@postgres:5432/lineary_db
      REDIS_URL: redis://:\${REDIS_PASSWORD}@redis:6379
      JWT_SECRET: \${JWT_SECRET}
      NODE_ENV: production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: https://api.lineary.ai
      VITE_WS_URL: wss://api.lineary.ai
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    restart: unless-stopped

  ai:
    build: ./ai
    environment:
      DATABASE_URL: postgresql://lineary:\${DB_PASSWORD}@postgres:5432/lineary_db
      REDIS_URL: redis://:\${REDIS_PASSWORD}@redis:6379
      OPENAI_API_KEY: \${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
\`\`\`

#### 2. Deploy with Docker Compose

\`\`\`bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
\`\`\`

### Kubernetes Deployment

#### 1. Create Namespace

\`\`\`yaml
apiVersion: v1
kind: Namespace
metadata:
  name: lineary
\`\`\`

#### 2. Database Deployment

\`\`\`yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: lineary
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: lineary_db
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
\`\`\`

#### 3. Backend Deployment

\`\`\`yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: lineary
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: lineary/backend:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secret
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: backend-secret
              key: redis-url
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
\`\`\`

#### 4. Apply Configurations

\`\`\`bash
# Create secrets
kubectl create secret generic postgres-secret \\
  --from-literal=username=lineary \\
  --from-literal=password=your-password \\
  -n lineary

# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n lineary

# View logs
kubectl logs -f deployment/backend -n lineary
\`\`\`

### AWS Deployment

#### 1. Infrastructure as Code (Terraform)

\`\`\`hcl
provider "aws" {
  region = "us-east-1"
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "lineary-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier     = "lineary-db"
  engine         = "postgres"
  engine_version = "14.7"
  instance_class = "db.t3.medium"
  
  allocated_storage     = 100
  storage_encrypted    = true
  
  db_name  = "lineary"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "lineary-final-snapshot"
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "lineary-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Service
resource "aws_ecs_service" "backend" {
  name            = "lineary-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 3
  
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }
  
  network_configuration {
    subnets         = module.vpc.private_subnets
    security_groups = [aws_security_group.ecs.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
}
\`\`\`

#### 2. Deploy with Terraform

\`\`\`bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply configuration
terraform apply

# Destroy resources (when needed)
terraform destroy
\`\`\`

## SSL/TLS Configuration

### Using Let's Encrypt

\`\`\`bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d lineary.ai -d www.lineary.ai

# Auto-renewal
sudo certbot renew --dry-run
\`\`\`

### Nginx Configuration

\`\`\`nginx
server {
    listen 80;
    server_name lineary.ai www.lineary.ai;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lineary.ai www.lineary.ai;
    
    ssl_certificate /etc/letsencrypt/live/lineary.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lineary.ai/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
\`\`\`

## Monitoring Setup

### Prometheus Configuration

\`\`\`yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lineary-backend'
    static_configs:
      - targets: ['backend:8000']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
\`\`\`

### Grafana Dashboards

Import dashboards for:
- Application metrics (ID: 12345)
- PostgreSQL (ID: 9628)
- Redis (ID: 11835)
- Nginx (ID: 12708)

## Backup & Restore

### Automated Backups

\`\`\`bash
#!/bin/bash
# backup.sh

# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Upload to S3
aws s3 cp backup_*.sql s3://lineary-backups/

# Keep only last 30 days
find . -name "backup_*.sql" -mtime +30 -delete
\`\`\`

### Restore Procedure

\`\`\`bash
# Download backup from S3
aws s3 cp s3://lineary-backups/backup_20240115_120000.sql .

# Restore database
psql $DATABASE_URL < backup_20240115_120000.sql
\`\`\`

## Troubleshooting

### Common Issues

**Database connection errors:**
- Check DATABASE_URL format
- Verify network connectivity
- Check PostgreSQL logs

**Redis connection errors:**
- Verify Redis is running
- Check REDIS_URL format
- Review Redis configuration

**Frontend not loading:**
- Check API_URL configuration
- Verify CORS settings
- Review browser console

**AI services not responding:**
- Check API keys are valid
- Verify Python dependencies
- Review service logs

### Debug Commands

\`\`\`bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend

# Enter container
docker exec -it lineary_backend bash

# Database connection test
psql $DATABASE_URL -c "SELECT 1"

# Redis connection test
redis-cli -u $REDIS_URL ping

# API health check
curl http://localhost:8000/health
\`\`\``
      },
      {
        title: 'Troubleshooting Guide',
        category: 'troubleshooting',
        content: `# Troubleshooting Guide

## Common Issues and Solutions

### Authentication Issues

#### "Invalid credentials" error

**Symptoms:**
- Cannot login with correct password
- Getting 401 Unauthorized errors

**Solutions:**
1. Clear browser cache and cookies
2. Check caps lock is off
3. Try password reset
4. Verify account is not locked

\`\`\`bash
# Check user account status
SELECT email, locked, last_login 
FROM users 
WHERE email = 'user@example.com';
\`\`\`

#### "Session expired" errors

**Symptoms:**
- Frequently logged out
- Need to re-authenticate often

**Solutions:**
1. Check system time is synchronized
2. Verify JWT token expiry settings
3. Check Redis session storage

\`\`\`bash
# Check Redis connection
redis-cli ping

# View session data
redis-cli --scan --pattern "sess:*"
\`\`\`

### Performance Issues

#### Slow page loads

**Symptoms:**
- Pages take > 3 seconds to load
- UI feels sluggish

**Diagnosis:**
1. Open browser DevTools
2. Check Network tab for slow requests
3. Review Console for errors

**Solutions:**

1. **Check API response times:**
\`\`\`bash
curl -w "@curl-format.txt" -o /dev/null -s \\
  https://api.lineary.ai/issues
\`\`\`

2. **Clear cache:**
- Browser: Ctrl+Shift+R (hard refresh)
- Redis: \`redis-cli FLUSHDB\`
- CDN: Purge CloudFlare cache

3. **Database optimization:**
\`\`\`sql
-- Check slow queries
SELECT query, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Analyze tables
ANALYZE issues;
VACUUM ANALYZE projects;
\`\`\`

#### High memory usage

**Symptoms:**
- Browser tab using > 500MB RAM
- App becomes unresponsive

**Solutions:**
1. Close unused tabs/windows
2. Reduce pagination size
3. Enable virtual scrolling
4. Clear local storage

\`\`\`javascript
// Clear local storage
localStorage.clear();
sessionStorage.clear();
\`\`\`

### Data Issues

#### Missing issues/projects

**Symptoms:**
- Issues disappeared
- Cannot see projects

**Diagnosis:**
\`\`\`sql
-- Check if data exists
SELECT COUNT(*) FROM issues WHERE project_id = 123;

-- Check permissions
SELECT * FROM project_members 
WHERE user_id = 456 AND project_id = 123;
\`\`\`

**Solutions:**
1. Check filters are not hiding data
2. Verify permissions are correct
3. Check for accidental archival
4. Review audit logs

#### Data not syncing

**Symptoms:**
- Changes not appearing for other users
- Real-time updates not working

**Solutions:**
1. **Check WebSocket connection:**
\`\`\`javascript
// In browser console
console.log(window.socket.connected);
\`\`\`

2. **Verify Redis pub/sub:**
\`\`\`bash
redis-cli PUBSUB CHANNELS
\`\`\`

3. **Check network:**
- Firewall blocking WebSocket
- Proxy configuration
- VPN interference

### Integration Issues

#### GitHub sync not working

**Symptoms:**
- Commits not linking to issues
- PRs not updating issue status

**Solutions:**
1. Re-authorize GitHub app
2. Check webhook delivery:
   - GitHub → Settings → Webhooks
   - View recent deliveries
3. Verify webhook URL is correct
4. Check webhook secret matches

\`\`\`bash
# Test webhook manually
curl -X POST https://api.lineary.ai/webhooks/github \\
  -H "X-GitHub-Event: push" \\
  -H "X-Hub-Signature: sha1=..." \\
  -d @webhook-payload.json
\`\`\`

#### Slack notifications not arriving

**Symptoms:**
- No Slack messages for updates
- Mentions not triggering notifications

**Solutions:**
1. Check Slack app is installed
2. Verify channel is selected
3. Check notification preferences
4. Test Slack webhook:

\`\`\`bash
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \\
  -H 'Content-Type: application/json' \\
  -d '{"text":"Test notification from Lineary"}'
\`\`\`

### AI Features Issues

#### AI suggestions not appearing

**Symptoms:**
- No AI recommendations
- Autopilot not working

**Solutions:**
1. Check AI services are running:
\`\`\`bash
curl http://ai-service:5000/health
\`\`\`

2. Verify API keys:
\`\`\`bash
# Check environment variables
echo $OPENAI_API_KEY | head -c 10
\`\`\`

3. Check rate limits:
- OpenAI dashboard
- Usage quotas

4. Review AI service logs:
\`\`\`bash
docker logs lineary_ai -f
\`\`\`

#### Poor AI quality

**Symptoms:**
- Irrelevant suggestions
- Incorrect estimates

**Solutions:**
1. Provide more context in issues
2. Use consistent terminology
3. Train with feedback
4. Adjust AI parameters:

\`\`\`python
# config.py
AI_CONFIG = {
    "temperature": 0.7,  # Lower for consistency
    "max_tokens": 2000,
    "model": "gpt-4-turbo"
}
\`\`\`

### Deployment Issues

#### Container won't start

**Symptoms:**
- Docker container exits immediately
- Service unhealthy

**Solutions:**
1. Check logs:
\`\`\`bash
docker logs container_name
docker-compose logs service_name
\`\`\`

2. Verify environment variables:
\`\`\`bash
docker exec container_name env
\`\`\`

3. Check port conflicts:
\`\`\`bash
netstat -tulpn | grep :8000
lsof -i :3000
\`\`\`

4. Verify dependencies:
\`\`\`bash
docker exec container_name npm list
docker exec container_name pip freeze
\`\`\`

#### Database migration failures

**Symptoms:**
- Migration scripts fail
- Schema out of sync

**Solutions:**
1. Check migration status:
\`\`\`bash
npm run migrate:status
\`\`\`

2. Rollback if needed:
\`\`\`bash
npm run migrate:rollback
\`\`\`

3. Manual fix:
\`\`\`sql
-- Check migration table
SELECT * FROM migrations ORDER BY id DESC;

-- Fix stuck migration
UPDATE migrations SET completed = true 
WHERE name = 'problematic_migration';
\`\`\`

### Browser-Specific Issues

#### Chrome/Edge

**Issue:** Extensions interfering
**Solution:** Try incognito mode or disable extensions

**Issue:** Cache corruption
**Solution:** 
\`\`\`
Settings → Privacy → Clear browsing data
Select: Cached images and files
\`\`\`

#### Firefox

**Issue:** Tracking protection blocking
**Solution:** Add site to exceptions

**Issue:** WebSocket blocked
**Solution:** Check network.websocket.max-connections in about:config

#### Safari

**Issue:** Third-party cookies blocked
**Solution:** 
\`\`\`
Preferences → Privacy → Uncheck "Prevent cross-site tracking"
\`\`\`

## Diagnostic Tools

### Health Check Script

\`\`\`bash
#!/bin/bash
# health-check.sh

echo "Checking Lineary Health..."

# API Health
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
echo "API Status: $API_STATUS"

# Database
psql $DATABASE_URL -c "SELECT 1" > /dev/null 2>&1
echo "Database: $([ $? -eq 0 ] && echo "OK" || echo "FAIL")"

# Redis
redis-cli ping > /dev/null 2>&1
echo "Redis: $([ $? -eq 0 ] && echo "OK" || echo "FAIL")"

# Disk Space
df -h | grep -E '^/dev/'

# Memory
free -h

# Running Containers
docker ps --format "table {{.Names}}\\t{{.Status}}"
\`\`\`

### Debug Mode

Enable debug logging:

\`\`\`javascript
// Frontend
localStorage.setItem('debug', 'lineary:*');

// Backend
DEBUG=lineary:* npm start

// Database
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();
\`\`\`

## Getting Help

### Before Contacting Support

1. Check this troubleshooting guide
2. Search existing issues on GitHub
3. Review recent changes/deployments
4. Collect diagnostic information

### Information to Provide

When reporting issues, include:

1. **Environment:**
   - Browser version
   - Operating system
   - Network environment (VPN, proxy)

2. **Steps to reproduce:**
   - Exact sequence of actions
   - Expected vs actual behavior
   - Screenshots/recordings

3. **Technical details:**
   - Browser console errors
   - Network requests (HAR file)
   - Related log entries

4. **Diagnostic data:**
\`\`\`bash
# Generate diagnostic bundle
./scripts/collect-diagnostics.sh > diagnostic-bundle.tar.gz
\`\`\`

### Support Channels

- **Email:** support@lineary.ai
- **Discord:** discord.gg/lineary
- **GitHub Issues:** github.com/lineary/lineary/issues
- **Status Page:** status.lineary.ai

### Emergency Procedures

For critical production issues:

1. **Check status page** for known issues
2. **Roll back** recent deployments if needed
3. **Contact on-call** engineer via PagerDuty
4. **Create P0 ticket** with "URGENT" tag
5. **Join war room** Discord channel

Remember: Stay calm, document everything, and communicate clearly!`
      }
    ];

    // Insert all documents
    for (const doc of docs) {
      await pool.query(
        `INSERT INTO docs (title, content, category, project_id, created_at, updated_at)
         VALUES ($1, $2, $3, $4, NOW(), NOW())
         ON CONFLICT DO NOTHING`,
        [doc.title, doc.content, doc.category, projectId]
      );
    }

    console.log(`✅ Successfully created comprehensive Lineary documentation for project ${projectId}`);
    process.exit(0);
  } catch (error) {
    console.error('Error creating user guide:', error);
    process.exit(1);
  }
}

createUserGuide();