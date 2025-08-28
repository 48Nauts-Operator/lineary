# Claude GitHub App + Webhooks - Complete Setup Guide

## Overview
This guide will help you create a sophisticated GitHub App that integrates Claude across all your repositories. Unlike GitHub Actions (per-repo), a GitHub App works organization-wide and provides more advanced features.

## Prerequisites
- GitHub account with organization admin access (or personal account)
- Node.js/Python development environment
- Anthropic API account and API key
- A server to host your app (we'll cover deployment options)

## Part 1: Create the GitHub App

### Step 1: Register Your GitHub App

1. Go to GitHub Settings:
   - **For personal account**: Settings → Developer settings → GitHub Apps
   - **For organization**: Your Org → Settings → Developer settings → GitHub Apps

2. Click **New GitHub App**

3. Fill out the form:
   - **App name**: `Claude Code Reviewer` (must be unique)
   - **Description**: `AI-powered code review using Claude`
   - **Homepage URL**: Your website or repo URL
   - **Webhook URL**: `https://yourdomain.com/webhook` (we'll set this up later)
   - **Webhook secret**: Generate a strong secret and save it

### Step 2: Set App Permissions

**Repository permissions:**
- Contents: Read
- Issues: Write
- Metadata: Read
- Pull requests: Write
- Actions: Read (optional)

**Subscribe to events:**
- Pull request
- Push
- Issue comment
- Pull request review comment

### Step 3: Generate and Save Keys

1. **After creating the app**, scroll to "Private keys"
2. Click **Generate a private key**
3. Download the `.pem` file and keep it secure
4. **Save these values** (you'll need them later):
   - App ID
   - Private key (the .pem file)
   - Webhook secret
   - Anthropic API key

## Part 2: Build the Webhook Server

### Step 1: Initialize Your Project

```bash
mkdir claude-github-app
cd claude-github-app
npm init -y
npm install express @octokit/app @octokit/rest crypto axios dotenv
```

### Step 2: Create Environment Configuration

Create `.env` file:
```env
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY_PATH=./path-to-your-private-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret
ANTHROPIC_API_KEY=your_anthropic_api_key
PORT=3000
```

### Step 3: Main Application Code

Create `app.js`:

```javascript
require('dotenv').config();
const express = require('express');
const crypto = require('crypto');
const { App } = require('@octokit/app');
const { Octokit } = require('@octokit/rest');
const axios = require('axios');
const fs = require('fs');

const app = express();
app.use(express.json());

// Initialize GitHub App
const githubApp = new App({
  appId: process.env.GITHUB_APP_ID,
  privateKey: fs.readFileSync(process.env.GITHUB_PRIVATE_KEY_PATH, 'utf8'),
});

// Webhook signature verification
function verifySignature(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload, 'utf8')
    .digest('hex');
  
  const expectedBuffer = Buffer.from(`sha256=${expectedSignature}`, 'utf8');
  const actualBuffer = Buffer.from(signature, 'utf8');
  
  return crypto.timingSafeEqual(expectedBuffer, actualBuffer);
}

// Claude API helper
async function callClaude(prompt) {
  try {
    const response = await axios.post('https://api.anthropic.com/v1/messages', {
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4000,
      messages: [{
        role: 'user',
        content: prompt
      }]
    }, {
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      }
    });

    return response.data.content[0].text;
  } catch (error) {
    console.error('Claude API Error:', error.response?.data || error.message);
    throw error;
  }
}

// Get changed files in PR
async function getChangedFiles(octokit, owner, repo, pullNumber) {
  try {
    const { data: files } = await octokit.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: pullNumber,
    });

    // Filter for code files and get content
    const codeExtensions = ['.js', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb', '.swift', '.kt'];
    const codeFiles = files.filter(file => 
      codeExtensions.some(ext => file.filename.endsWith(ext)) &&
      file.status !== 'removed' &&
      file.changes < 1000 // Skip very large files
    );

    const fileContents = await Promise.all(
      codeFiles.slice(0, 10).map(async (file) => { // Limit to 10 files
        try {
          const { data } = await octokit.rest.repos.getContent({
            owner,
            repo,
            path: file.filename,
            ref: `refs/pull/${pullNumber}/head`
          });

          const content = Buffer.from(data.content, 'base64').toString('utf8');
          return {
            filename: file.filename,
            content: content.slice(0, 5000), // Limit file size
            status: file.status,
            additions: file.additions,
            deletions: file.deletions
          };
        } catch (error) {
          console.log(`Could not fetch ${file.filename}:`, error.message);
          return null;
        }
      })
    );

    return fileContents.filter(Boolean);
  } catch (error) {
    console.error('Error getting changed files:', error.message);
    return [];
  }
}

// Main webhook handler
app.post('/webhook', async (req, res) => {
  const signature = req.headers['x-hub-signature-256'];
  const payload = JSON.stringify(req.body);

  // Verify webhook signature
  if (!verifySignature(payload, signature, process.env.GITHUB_WEBHOOK_SECRET)) {
    return res.status(401).send('Unauthorized');
  }

  const { action, pull_request, repository, installation, comment } = req.body;

  // Handle different webhook events
  try {
    if (req.headers['x-github-event'] === 'pull_request') {
      await handlePullRequest(action, pull_request, repository, installation);
    } else if (req.headers['x-github-event'] === 'issue_comment') {
      await handleComment(action, comment, pull_request, repository, installation);
    }

    res.status(200).send('OK');
  } catch (error) {
    console.error('Webhook handler error:', error.message);
    res.status(500).send('Internal Server Error');
  }
});

// Handle pull request events
async function handlePullRequest(action, pullRequest, repository, installation) {
  if (!['opened', 'synchronize', 'reopened'].includes(action)) {
    return;
  }

  console.log(`PR ${action}: ${pullRequest.title} in ${repository.full_name}`);

  // Get authenticated Octokit instance
  const octokit = await githubApp.getInstallationOctokit(installation.id);

  // Get changed files
  const changedFiles = await getChangedFiles(
    octokit,
    repository.owner.login,
    repository.name,
    pullRequest.number
  );

  if (changedFiles.length === 0) {
    console.log('No code files to review');
    return;
  }

  // Prepare prompt for Claude
  const filesText = changedFiles.map(file => 
    `## ${file.filename} (${file.status}, +${file.additions}/-${file.deletions})\n\`\`\`\n${file.content}\n\`\`\``
  ).join('\n\n');

  const prompt = `Please review this pull request for:

**Code Quality & Maintainability:**
- Clean code principles
- Proper naming conventions
- Code organization and structure

**Potential Issues:**
- Bugs or logic errors
- Security vulnerabilities
- Performance concerns
- Edge cases not handled

**Best Practices:**
- Framework/language-specific best practices
- Error handling
- Testing considerations

**Suggestions:**
- Improvements and optimizations
- Documentation needs

Please be constructive and specific. Format as markdown with clear sections.

**Pull Request:** ${pullRequest.title}
**Description:** ${pullRequest.body || 'No description provided'}

**Files Changed:**
${filesText}`;

  // Get Claude's review
  const review = await callClaude(prompt);

  // Post review comment
  await octokit.rest.issues.createComment({
    owner: repository.owner.login,
    repo: repository.name,
    issue_number: pullRequest.number,
    body: `## 🤖 Claude Code Review\n\n${review}\n\n---\n*Powered by Claude Sonnet 4 | [Report issues](${repository.html_url}/issues)*`
  });

  console.log('Review posted successfully');
}

// Handle comments (for interactive features)
async function handleComment(action, comment, pullRequest, repository, installation) {
  if (action !== 'created' || !pullRequest) return;

  const commentBody = comment.body.toLowerCase();
  
  // Check if Claude is mentioned
  if (!commentBody.includes('@claude') && !commentBody.includes('claude review')) {
    return;
  }

  console.log('Claude mentioned in comment');

  const octokit = await githubApp.getInstallationOctokit(installation.id);

  // Determine what type of help is requested
  let prompt;
  if (commentBody.includes('security')) {
    prompt = 'Focus specifically on security vulnerabilities and best practices in this PR.';
  } else if (commentBody.includes('performance')) {
    prompt = 'Focus specifically on performance optimizations and potential bottlenecks in this PR.';
  } else if (commentBody.includes('explain')) {
    prompt = 'Explain what this code does and any complex logic in simple terms.';
  } else {
    prompt = 'Provide a quick focused review of the most important issues in this PR.';
  }

  // Get files and review
  const changedFiles = await getChangedFiles(
    octokit,
    repository.owner.login,
    repository.name,
    pullRequest.number
  );

  if (changedFiles.length === 0) {
    await octokit.rest.issues.createComment({
      owner: repository.owner.login,
      repo: repository.name,
      issue_number: pullRequest.number,
      body: '🤖 No code files found to review in this PR.'
    });
    return;
  }

  const filesText = changedFiles.map(file => 
    `## ${file.filename}\n\`\`\`\n${file.content}\n\`\`\``
  ).join('\n\n');

  const fullPrompt = `${prompt}\n\n**Files:**\n${filesText}`;
  const review = await callClaude(fullPrompt);

  // Reply to the comment
  await octokit.rest.issues.createComment({
    owner: repository.owner.login,
    repo: repository.name,
    issue_number: pullRequest.number,
    body: `## 🤖 Claude Response\n\n${review}\n\n---\n*Responding to: @${comment.user.login}*`
  });
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Claude GitHub App running on port ${PORT}`);
});

module.exports = app;
```

## Part 3: Advanced Features

### Step 1: Add Custom Commands

Users can trigger specific reviews by mentioning Claude:
- `@claude security` - Security-focused review
- `@claude performance` - Performance analysis
- `@claude explain` - Code explanation
- `@claude full-review` - Comprehensive analysis

### Step 2: File-Specific Line Comments

Create `line-comments.js`:

```javascript
// Post comments on specific lines
async function postLineComments(octokit, owner, repo, pullNumber, suggestions) {
  for (const suggestion of suggestions) {
    await octokit.rest.pulls.createReviewComment({
      owner,
      repo,
      pull_number: pullNumber,
      body: suggestion.comment,
      commit_id: suggestion.commitId,
      path: suggestion.filename,
      line: suggestion.line,
    });
  }
}
```

### Step 3: Integration with Issue Tracking

```javascript
// Auto-create issues for critical problems
async function createIssueForCriticalIssues(octokit, owner, repo, issues, pullRequest) {
  const criticalIssues = issues.filter(issue => issue.severity === 'critical');
  
  for (const issue of criticalIssues) {
    await octokit.rest.issues.create({
      owner,
      repo,
      title: `Security Issue: ${issue.title}`,
      body: `Found in PR #${pullRequest.number}\n\n${issue.description}`,
      labels: ['security', 'claude-detected']
    });
  }
}
```

## Part 4: Deployment Options

### Option 1: Heroku (Easiest)

1. **Install Heroku CLI**
2. **Create Heroku app:**
   ```bash
   heroku create your-claude-app
   ```

3. **Set environment variables:**
   ```bash
   heroku config:set GITHUB_APP_ID=your_app_id
   heroku config:set GITHUB_WEBHOOK_SECRET=your_secret
   heroku config:set ANTHROPIC_API_KEY=your_key
   heroku config:set GITHUB_PRIVATE_KEY="$(cat private-key.pem)"
   ```

4. **Deploy:**
   ```bash
   git push heroku main
   ```

5. **Update webhook URL** in GitHub App settings to: `https://your-claude-app.herokuapp.com/webhook`

### Option 2: Vercel (Serverless)

Create `api/webhook.js`:
```javascript
const { App } = require('@octokit/app');
// ... (same webhook logic but as serverless function)

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }
  
  // Handle webhook logic here
  // ... (webhook handling code)
};
```

Deploy:
```bash
vercel deploy
```

### Option 3: Self-Hosted Server

Use PM2 or Docker to run on your own server:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["node", "app.js"]
```

## Part 5: Install Your App

### Step 1: Install on Repositories

1. Go to your GitHub App settings
2. Click **Install App**
3. Choose **All repositories** or select specific repos
4. Authorize the installation

### Step 2: Test the Installation

1. Create a test PR in one of your repos
2. Check your server logs
3. Verify Claude posts a review comment

## Part 6: Advanced Configurations

### Custom Review Prompts by File Type

```javascript
const getReviewPrompt = (filename, content) => {
  const ext = filename.split('.').pop();
  
  const prompts = {
    'js': 'Focus on JavaScript best practices, async/await usage, and potential runtime errors.',
    'ts': 'Focus on TypeScript types, interfaces, and type safety.',
    'py': 'Focus on Python PEP 8, error handling, and performance.',
    'java': 'Focus on Java best practices, null checks, and exception handling.',
    'go': 'Focus on Go idioms, error handling, and concurrency safety.',
  };

  return prompts[ext] || 'Provide a general code review focusing on quality and best practices.';
};
```

### Rate Limiting and Caching

```javascript
// Simple rate limiting
const reviewCache = new Map();
const rateLimits = new Map();

function shouldSkipReview(repoId, prNumber) {
  const key = `${repoId}-${prNumber}`;
  const now = Date.now();
  
  // Rate limit: max 1 review per PR per 5 minutes
  if (rateLimits.has(key)) {
    const lastReview = rateLimits.get(key);
    if (now - lastReview < 5 * 60 * 1000) {
      return true;
    }
  }
  
  rateLimits.set(key, now);
  return false;
}
```

### Integration with Slack/Discord

```javascript
// Notify team of critical issues
async function notifyTeam(webhook, message) {
  if (!webhook) return;
  
  await axios.post(webhook, {
    text: `🚨 Claude found critical issues: ${message}`
  });
}
```

## Part 7: Monitoring and Maintenance

### Logging Setup

```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console()
  ]
});
```

### Health Monitoring

```javascript
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    github_app_id: process.env.GITHUB_APP_ID
  });
});

// API status endpoint
app.get('/status', async (req, res) => {
  try {
    // Test GitHub API
    const octokit = await githubApp.getInstallationOctokit(installation.id);
    await octokit.rest.users.getAuthenticated();
    
    // Test Claude API (simple ping)
    await callClaude('Hello, just testing the connection. Please respond with "OK".');
    
    res.json({ github: 'connected', claude: 'connected' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

## Part 8: Organization-Wide Automation

### Auto-Install on New Repos

```javascript
// Listen for repository creation
app.post('/webhook', async (req, res) => {
  // ... existing webhook code ...
  
  if (req.headers['x-github-event'] === 'repository') {
    await handleNewRepository(req.body);
  }
});

async function handleNewRepository(payload) {
  if (payload.action === 'created') {
    console.log(`New repo created: ${payload.repository.full_name}`);
    // Auto-install your app or set up branch protection rules
    
    const octokit = await githubApp.getInstallationOctokit(payload.installation.id);
    
    // Example: Auto-enable branch protection with Claude review
    await octokit.rest.repos.updateBranchProtection({
      owner: payload.repository.owner.login,
      repo: payload.repository.name,
      branch: 'main',
      required_status_checks: {
        strict: true,
        contexts: ['claude-review']
      },
      enforce_admins: false,
      required_pull_request_reviews: {
        required_approving_review_count: 1
      }
    });
  }
}
```

### Organization Settings Integration

Add this to your GitHub App to automatically configure new repositories:

```javascript
// Auto-add Claude review to branch protection rules
async function setupBranchProtection(octokit, owner, repo) {
  try {
    await octokit.rest.repos.updateBranchProtection({
      owner,
      repo,
      branch: 'main',
      required_status_checks: {
        strict: true,
        contexts: ['claude-review/complete']
      },
      required_pull_request_reviews: {
        required_approving_review_count: 1,
        dismiss_stale_reviews: true
      },
      enforce_admins: false
    });
  } catch (error) {
    console.log(`Could not set up branch protection for ${owner}/${repo}:`, error.message);
  }
}
```

## Part 9: Testing Your Setup

### Local Testing

1. **Use ngrok for local development:**
   ```bash
   npm install -g ngrok
   ngrok http 3000
   ```

2. **Update webhook URL** to your ngrok URL temporarily

3. **Test with a real PR** in a test repository

### Automated Testing

Create `test/webhook.test.js`:
```javascript
const request = require('supertest');
const app = require('../app');

describe('Webhook Endpoints', () => {
  test('Health check works', async () => {
    const response = await request(app).get('/health');
    expect(response.status).toBe(200);
  });

  test('Webhook signature verification', async () => {
    // Test invalid signature
    const response = await request(app)
      .post('/webhook')
      .send({ test: 'data' });
    expect(response.status).toBe(401);
  });
});
```

## Part 10: Security Best Practices

### Environment Security
- Never commit `.env` files or private keys
- Use secrets management in production
- Rotate keys regularly
- Implement proper HTTPS

### Webhook Security
- Always verify webhook signatures
- Validate all incoming data
- Implement rate limiting
- Log security events

### API Security
- Store API keys securely
- Implement request timeouts
- Handle API rate limits gracefully
- Monitor for unusual usage patterns

## Troubleshooting Guide

### Common Issues:

**Webhook not receiving events:**
- Check webhook URL is accessible publicly
- Verify webhook secret matches
- Check GitHub App permissions

**API authentication failures:**
- Verify App ID and private key
- Check installation ID is correct
- Ensure app is installed on the repository

**Claude API errors:**
- Verify API key is correct
- Check rate limits and quotas
- Monitor for content policy issues

**Performance issues:**
- Implement caching for repeated requests
- Add file size limits
- Use async processing for large PRs

## Cost and Usage Management

- Monitor API usage in Anthropic Console
- Implement daily/monthly spending alerts
- Add usage analytics to your app
- Consider caching reviews for similar code

## Next Steps

Once your GitHub App is running:
1. Add more sophisticated code analysis
2. Integrate with your team's workflow tools
3. Create custom review templates for different project types
4. Add metrics and analytics dashboard
5. Scale to handle multiple organizations

This GitHub App approach gives you much more power and flexibility than the GitHub Actions method, allowing for real-time interactions and organization-wide deployment!