# Lineary - Project Instructions for Claude

## Project Overview
Lineary is a new project to build an AI version of the beautiful minimalistic Project Management Tool Linear.

GitHub-Repo: git@github.com:48Nauts-Operator/lineary.git
Website Port: 3399
Website: https://lineary.blockonauts.io


## Development Guidelines

### Code Style
- Follow existing patterns in the codebase
- Use clear, descriptive names
- Write comprehensive tests
- Document complex logic

### Architecture
- Frontend: React with TypeScript
- Backend: Node.js/Express or Python/FastAPI
- Database: PostgreSQL
- Cache: Redis
- Vector DB: Qdrant (if needed)

### Testing
- Write unit tests for all new functions
- Integration tests for API endpoints
- E2E tests for critical user flows

### Git Workflow
- Create feature branches for new work
- Write clear commit messages
- Test before committing

## Project Structure
```
Lineary/
├── frontend/          # React frontend
├── backend/           # API backend
├── hooks/            # Claude hooks (pre/post tools)
├── scripts/          # Utility scripts
├── docs/             # Documentation
├── tests/            # Test suites
└── docker-compose.yml # Service orchestration
```
## Important Notes
- Never commit sensitive data
- Always test before deploying
- Document significant changes
- Use semantic versioning
