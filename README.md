# Lineary Community Edition

<div align="center">

![Lineary Logo](https://img.shields.io/badge/Lineary-Community-purple?style=for-the-badge&logo=github)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)
![TypeScript](https://img.shields.io/badge/TypeScript-100%25-blue?style=for-the-badge&logo=typescript)

**Project management, rebuilt for AI**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing) • [Support](#-support)

</div>

---

## 🚀 What is Lineary?

Lineary is project management rebuilt from the ground up for the AI era. Designed for software development teams who want to harness AI to ship faster and smarter.

### Why Lineary?

- **🤖 AI-Native**: Built with AI at its core, not bolted on
- **🔒 Privacy-First**: Self-hosted, your data stays yours
- **🎯 Developer-Focused**: Built by developers, for developers
- **💰 Forever Free**: Community Edition is free for teams up to 5 users
- **🔌 Extensible**: Rich integration ecosystem with GitHub, GitLab, Slack, and more

## 🔄 The AI Development Cycle

Lineary implements a complete AI-powered development cycle that learns and improves with every iteration:

```
LLM (Claude/AI) → Lineary (Tasks) → Git (Code) → Claude Review → Lineary (Insights) → AI Learning
```

**How it works:**
1. **AI creates tasks** with time estimates in Lineary
2. **Developers work** on tasks and create PRs (must reference issue #123)
3. **Claude automatically reviews** every PR for quality, security, and performance
4. **Lineary tracks** actual vs estimated time
5. **AI learns** from the data to improve future estimates
6. **System gets smarter** with every completed task

## ✨ Features

### Core Project Management
- **Projects & Issues** - Organize work with unlimited projects and issues
- **Sprint Planning** - AI-assisted sprint planning and management
- **Kanban Boards** - Visual task management with drag-and-drop
- **Activity Tracking** - Complete audit trail of all changes
- **Comments & Collaboration** - Team discussions on every issue

### AI Capabilities
- **Smart Story Points** - AI-powered estimation based on issue complexity
- **Claude Code Reviews** - Automatic AI code review on every PR
- **AI Learning Loop** - Improves estimation accuracy over time (typically 5-10% per sprint)
- **Test Generation** - Automatic Gherkin test case creation
- **Issue Breakdown** - Split large tasks into manageable subtasks
- **Sprint Planning Assistant** - AI helps optimize sprint capacity

### GitHub App Integration (NEW!)
- **Automatic PR Reviews** - Claude reviews every pull request
- **PR-to-Issue Sync** - Automatic linking and status updates
- **Code Quality Metrics** - Track quality trends over time
- **Security Detection** - Identify vulnerabilities before merge
- **Performance Analysis** - Catch performance issues early
- **Learning Insights** - AI improves with every review

### Integrations (Community Edition)
- **GitHub App** - Full webhook integration with Claude AI reviews
- **GitHub OAuth** - Repository access and user authentication
- **GitLab** - Complete GitLab integration
- **BitBucket** - Repository sync and PR tracking
- **Slack** - Real-time notifications and commands
- **Notion** - Bi-directional page synchronization

### Developer Tools
- **MCP Server** - Claude Desktop integration for AI-assisted development
- **REST API** - Comprehensive API for automation
- **Webhooks** - Real-time event notifications
- **CLI Tool** - Command-line interface for power users

## 🏃 Quick Start

### One-Line Install (Coming Soon)
```bash
curl -sSL https://get.lineary.com | sh
```

### Docker Installation (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/lineary/lineary-community.git
cd lineary-community
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Access Lineary**
```
http://localhost:3000
```

Default credentials:
- Username: `admin`
- Password: `changeme`

### Manual Installation

**Prerequisites:**
- Node.js 18+ 
- PostgreSQL 14+ or SQLite
- Redis (optional, for caching)

**Steps:**
```bash
# Clone repository
git clone https://github.com/lineary/lineary-community.git
cd lineary-community

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install

# Build frontend
npm run build

# Initialize database
cd ../backend
npm run db:migrate

# Start services
npm run start:prod
```

## 🔧 Configuration

### GitHub App Setup (For Claude AI Reviews)

Setting up the GitHub App enables automatic Claude AI code reviews on every PR:

#### Step 1: Create GitHub App
1. Go to GitHub Settings → Developer settings → GitHub Apps
2. Click **New GitHub App**
3. Configure with these settings:
   - **Name**: `Lineary-Claude-Reviewer` (must be unique)
   - **Homepage URL**: Your Lineary URL
   - **Webhook URL**: `https://your-lineary-domain/api/github/webhook`
   - **Webhook secret**: Generate and save a strong secret

#### Step 2: Set Permissions
**Repository permissions:**
- Contents: Read
- Issues: Write
- Pull requests: Write
- Metadata: Read

**Subscribe to events:**
- Pull request
- Pull request review comment
- Push

#### Step 3: Generate Private Key
1. After creating the app, scroll to "Private keys"
2. Click "Generate a private key"
3. Save the `.pem` file securely

#### Step 4: Configure Lineary
Add to your `.env`:
```env
# GitHub App Configuration
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY_PATH=./github-app-private-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Claude AI Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key

# GitHub OAuth (for user authentication)
GITHUB_CLIENT_ID=your_oauth_client_id
GITHUB_CLIENT_SECRET=your_oauth_client_secret
```

#### Step 5: Install on Repositories
1. Go to your GitHub App settings
2. Click "Install App"
3. Choose repositories to enable Claude reviews

### 🔴 Critical: Issue Reference Rule

**Every commit and PR MUST reference the Lineary issue:**
```bash
# Correct - enables AI cycle
git commit -m "feat: Add authentication #123"
git commit -m "fix: Memory leak in parser LIN-456"

# Wrong - breaks automation
git commit -m "Add authentication"  # No tracking!
```

Without issue references, you lose:
- Automatic PR tracking
- Claude code reviews with context
- AI learning from actual time
- Sprint velocity calculations

### Slack Integration Setup

1. Create a Slack App:
   - Go to api.slack.com/apps
   - Create new app
   - Add OAuth scopes: `chat:write`, `commands`

2. Add credentials to `.env`:
```env
SLACK_CLIENT_ID=your_client_id
SLACK_CLIENT_SECRET=your_client_secret
SLACK_SIGNING_SECRET=your_signing_secret
```

See full integration guides in our [documentation](#-documentation).

## 📈 AI Learning Metrics

Track how the AI improves over time:

### Estimation Accuracy
- **Initial**: ~60% accuracy (typical for new projects)
- **After 10 tasks**: ~70% accuracy
- **After 50 tasks**: ~80% accuracy
- **After 100 tasks**: ~85-90% accuracy

### Review Quality
The Claude AI reviewer improves by learning from:
- Code patterns in your project
- Common issues in your codebase
- Your team's coding standards
- Historical bug patterns

### Dashboard Metrics
Access insights at `/analytics` in your Lineary instance:
- **Code Quality Trend**: Track quality scores over time
- **Security Issues**: Monitor security vulnerabilities found
- **Performance Metrics**: See performance issue trends
- **AI Accuracy**: View estimation accuracy improvements
- **Sprint Velocity**: Track team velocity with AI-adjusted estimates

## 📚 Documentation

> **Note**: Detailed documentation is available for enterprise customers. Community users can access:

- [Installation Guide](https://github.com/lineary/community/wiki/Installation)
- [Configuration Guide](https://github.com/lineary/community/wiki/Configuration)
- [API Reference](https://github.com/lineary/community/wiki/API)
- [Integration Guides](https://github.com/lineary/community/wiki/Integrations)
- [Troubleshooting](https://github.com/lineary/community/wiki/Troubleshooting)

## 🤝 Contributing

We love contributions! Lineary is a community-driven project and we welcome developers of all skill levels.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/lineary-community.git
cd lineary-community

# Install dependencies
npm run install:all

# Start development servers
npm run dev

# Run tests
npm run test

# Run linting
npm run lint
```

### Contribution Guidelines

- **Code Style**: We use ESLint and Prettier
- **Commits**: Follow conventional commits specification
- **Tests**: Write tests for new features
- **Documentation**: Update docs for API changes
- **Issues**: Check existing issues before creating new ones

### Good First Issues

Looking for something to work on? Check out our [good first issues](https://github.com/lineary/community/labels/good%20first%20issue).

## 🗺️ Roadmap

### Community Edition (Current)
- ✅ Core project management
- ✅ AI features
- ✅ GitHub/GitLab integration
- 🚧 BitBucket integration
- 🚧 Slack integration
- 🚧 Notion sync
- 📋 Plugin system
- 📋 Theme support
- 📋 Mobile app

### Enterprise Edition (Paid)
- Advanced AI models (GPT-4, Claude 3)
- Unlimited users
- Jira/ClickUp integration
- SSO/SAML support
- 24/7 Priority support
- SLA guarantees
- Custom development

## 💬 Community & Support

### Community Support
- **GitHub Discussions**: [github.com/lineary/community/discussions](https://github.com/lineary/community/discussions)
- **Discord**: [discord.gg/lineary](https://discord.gg/lineary)
- **Twitter**: [@lineary](https://twitter.com/lineary)
- **Stack Overflow**: Tag `lineary`

### Reporting Issues
- **Bugs**: [GitHub Issues](https://github.com/lineary/community/issues)
- **Security**: security@lineary.com
- **Feature Requests**: [Discussions](https://github.com/lineary/community/discussions/categories/ideas)

## 📊 Community Stats

![GitHub stars](https://img.shields.io/github/stars/lineary/community?style=social)
![GitHub forks](https://img.shields.io/github/forks/lineary/community?style=social)
![Contributors](https://img.shields.io/github/contributors/lineary/community)
![Discord](https://img.shields.io/discord/123456789?label=Discord&logo=discord)

## 🏢 Enterprise Edition

Need more than 5 users? Advanced features? Professional support?

**Lineary Enterprise** includes:
- Unlimited users
- Advanced AI models
- Jira/ClickUp integration  
- 24/7 Priority support
- SLA guarantees
- Custom development

[Learn more about Enterprise](https://lineary.com/enterprise) | [Contact Sales](mailto:sales@lineary.com)

## 📄 License

Lineary Community Edition is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This means you can:
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Use privately

## 🙏 Acknowledgments

Lineary is built on the shoulders of giants:

- [React](https://reactjs.org/) - UI Framework
- [Node.js](https://nodejs.org/) - Backend runtime
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Docker](https://www.docker.com/) - Containerization
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Tailwind CSS](https://tailwindcss.com/) - Styling

Special thanks to all our [contributors](https://github.com/lineary/community/graphs/contributors)!

## 🚀 Get Started Now

Ready to transform your project management with AI?

```bash
git clone https://github.com/lineary/lineary-community.git
cd lineary-community
docker-compose up -d
```

Visit `http://localhost:3000` and start managing projects smarter!

---

<div align="center">

**Built with ❤️ by the Lineary Community**

[Website](https://lineary.com) • [Blog](https://blog.lineary.com) • [Twitter](https://twitter.com/lineary) • [Discord](https://discord.gg/lineary)

</div>