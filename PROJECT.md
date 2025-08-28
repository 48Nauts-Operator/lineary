# Lineary Project Documentation

## Overview
Lineary is an AI-powered project management tool inspired by Linear's minimalistic design, with advanced analytics and AI assistance features.

## Tech Stack
- **Frontend**: React + TypeScript + Vite
- **Backend**: Node.js + Express
- **Database**: PostgreSQL
- **Cache**: Redis
- **Deployment**: Docker Compose
- **Domain**: https://ai-linear.blockonauts.io

## Database Schema

### Core Tables

#### projects
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#8B5CF6',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### issues
```sql
CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'todo',
    priority INTEGER DEFAULT 3,
    assignee VARCHAR(255),
    labels TEXT[],
    story_points INTEGER DEFAULT 0,
    estimated_hours DECIMAL(10, 2),
    completed_at TIMESTAMPTZ,
    token_cost DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### sprints
```sql
CREATE TABLE sprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'planning',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### sprint_issues
```sql
CREATE TABLE sprint_issues (
    sprint_id UUID NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sprint_id, issue_id)
);
```

#### comments
```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    author VARCHAR(255),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### Analytics Tables

#### project_activity
```sql
CREATE TABLE project_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, activity_date, activity_type)
);
```

#### token_usage
```sql
CREATE TABLE token_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,
    model_name VARCHAR(100),
    input_tokens INTEGER DEFAULT 0,  -- Note: was prompt_tokens in old schema
    output_tokens INTEGER DEFAULT 0, -- Note: was completion_tokens in old schema
    total_tokens INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### time_tracking
```sql
CREATE TABLE time_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,
    user_id VARCHAR(255),
    time_spent_minutes INTEGER DEFAULT 0,
    ai_time_saved_minutes INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### daily_analytics
```sql
CREATE TABLE daily_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    issues_created INTEGER DEFAULT 0,
    issues_completed INTEGER DEFAULT 0,
    story_points_completed INTEGER DEFAULT 0,
    commits_count INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    ai_interactions INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, date)
);
```

#### docs
```sql
CREATE TABLE docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    category VARCHAR(100) DEFAULT 'general',
    slug VARCHAR(255) NOT NULL,
    is_published BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, slug)
);
```

## API Endpoints

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/:id` - Get project details
- `PUT /api/projects/:id` - Update project
- `DELETE /api/projects/:id` - Delete project

### Issues
- `GET /api/issues` - List issues (with filters)
- `POST /api/issues` - Create new issue
- `GET /api/issues/:id` - Get issue details
- `PUT /api/issues/:id` - Update issue
- `DELETE /api/issues/:id` - Delete issue

### Analytics
- `GET /api/analytics/dashboard/:projectId` - Get comprehensive dashboard data
- `POST /api/analytics/activity` - Record activity
- `POST /api/analytics/token-usage` - Record token usage
- `POST /api/analytics/time-tracking` - Record time tracking
- `GET /api/analytics/heatmap/:projectId` - Get activity heatmap
- `GET /api/analytics/ai-time-saved/:projectId` - Get AI time saved metrics

### Documentation
- `GET /api/docs/:projectId` - List project docs
- `POST /api/docs` - Create new doc
- `GET /api/docs/:projectId/:slug` - Get doc by slug
- `PUT /api/docs/:id` - Update doc
- `DELETE /api/docs/:id` - Delete doc

### AI Features
- `POST /api/ai/generate-tasks` - Generate task breakdown from feature description
- `POST /api/ai/suggest-labels` - Suggest labels for an issue
- `POST /api/ai/estimate` - Estimate story points and hours

## Environment Variables

### Backend (.env)
```env
PORT=8000
DATABASE_URL=postgresql://lineary:secure_password_123@postgres:5432/lineary
REDIS_URL=redis://redis:6379
JWT_SECRET=your_jwt_secret_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### Frontend
Frontend uses environment variables defined in the build process:
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000/api)

## Docker Services

### docker-compose.yml
```yaml
services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "10620:5432"
    environment:
      POSTGRES_USER: lineary
      POSTGRES_PASSWORD: secure_password_123
      POSTGRES_DB: lineary

  redis:
    image: redis:7-alpine
    ports:
      - "13620:6379"

  backend:
    build: ./backend
    ports:
      - "3134:8000"
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3399:80"
    depends_on:
      - backend
```

## Development

### Local Setup
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Run migrations
cat backend/migrations/*.sql | docker exec -i lineary_postgres psql -U lineary -d lineary
```

### Database Migrations
Migrations are stored in `backend/migrations/` and should be run in order:
1. `001_initial.sql` - Core tables
2. `002_sprints.sql` - Sprint management
3. `003_analytics_fixed.sql` - Analytics tables
4. `004_fix_time_tracking.sql` - Time tracking schema fix
5. `create_docs_table.sql` - Documentation system

### Testing
```bash
# Backend tests
docker exec lineary_backend npm test

# Frontend tests
docker exec lineary_frontend npm test
```

## Features

### Core Features
- Project management
- Issue tracking with status workflow
- Sprint planning and management
- Comments and collaboration
- User assignments and labels

### Analytics Features
- GitHub-style activity heatmap
- AI time saved counter
- Token usage tracking
- Velocity charts
- Cycle time metrics
- Issue distribution
- Sprint burndown

### AI Features
- Task generation from feature descriptions
- Story point estimation
- Time estimation
- Label suggestions
- Smart task breakdown

## MCP Server
A standalone MCP (Model Context Protocol) server is available in the `mcp-server-standalone` directory for Claude Desktop integration. It provides tools for:
- Project management
- Issue creation and updates
- Sprint management
- Analytics access
- AI task generation

## Known Issues & Solutions

### Analytics Page Blank Screen
**Issue**: Analytics page shows blank/black screen
**Cause**: Database schema mismatch or API errors
**Solution**: 
1. Check backend logs: `docker-compose logs backend`
2. Verify database schema matches PROJECT.md
3. Run migration 004_fix_time_tracking.sql if needed
4. Restart backend: `docker-compose restart backend`

### API 404 Errors
**Issue**: API endpoints return 404
**Cause**: Incorrect API_URL configuration
**Solution**: Ensure frontend uses correct API URL: `https://ai-linear.blockonauts.io:3134/api`

## Security Notes
- Never expose database credentials in logs
- Use environment variables for sensitive data
- Sanitize API keys in error messages
- Implement proper authentication before production

## Deployment

### Production Deployment
1. Update environment variables for production
2. Enable SSL/TLS certificates
3. Configure proper database backups
4. Set up monitoring and alerting
5. Implement rate limiting
6. Add authentication middleware

### Health Checks
All services include health checks:
- Frontend: `curl http://localhost:3399/`
- Backend: `curl http://localhost:3134/health`
- Postgres: `pg_isready`
- Redis: `redis-cli ping`