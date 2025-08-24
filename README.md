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

## ✨ Features

### Core Project Management
- **Projects & Issues** - Organize work with unlimited projects and issues
- **Sprint Planning** - AI-assisted sprint planning and management
- **Kanban Boards** - Visual task management with drag-and-drop
- **Activity Tracking** - Complete audit trail of all changes
- **Comments & Collaboration** - Team discussions on every issue

### AI Capabilities
- **Smart Story Points** - AI-powered estimation based on issue complexity
- **Test Generation** - Automatic Gherkin test case creation
- **Issue Breakdown** - Split large tasks into manageable subtasks
- **Sprint Planning Assistant** - AI helps optimize sprint capacity

### Integrations (Community Edition)
- **GitHub** - Full OAuth integration with webhook support
- **GitLab** - Complete GitLab integration
- **BitBucket** - Repository sync and PR tracking
- **Slack** - Real-time notifications and commands
- **Notion** - Bi-directional page synchronization

### Developer Tools
- **MCP Server** - Claude Code integration for AI-assisted development
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

### GitHub Integration Setup

1. Create a GitHub OAuth App:
   - Go to GitHub Settings > Developer settings > OAuth Apps
   - Create new OAuth App
   - Set callback URL: `http://your-domain/api/auth/oauth/callback`

2. Add credentials to `.env`:
```env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

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