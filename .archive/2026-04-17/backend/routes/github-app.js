// ABOUTME: GitHub App webhook receiver and Claude review integration for Lineary
// ABOUTME: Handles PR events, triggers Claude reviews, and syncs with Lineary issues

const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const axios = require('axios');
const { App } = require('@octokit/app');
const { Octokit } = require('@octokit/rest');
const fs = require('fs');
const path = require('path');

// Configuration
const config = {
  githubAppId: process.env.GITHUB_APP_ID,
  githubPrivateKeyPath: process.env.GITHUB_PRIVATE_KEY_PATH,
  githubWebhookSecret: process.env.GITHUB_WEBHOOK_SECRET,
  anthropicApiKey: process.env.ANTHROPIC_API_KEY,
  linearyApiUrl: process.env.LINEARY_API_URL || 'https://ai-linear.blockonauts.io/api'
};

// Initialize GitHub App (if configured)
let githubApp = null;
if (config.githubAppId && config.githubPrivateKeyPath && fs.existsSync(config.githubPrivateKeyPath)) {
  githubApp = new App({
    appId: config.githubAppId,
    privateKey: fs.readFileSync(config.githubPrivateKeyPath, 'utf8'),
  });
}

// Webhook signature verification
function verifyGitHubSignature(payload, signature, secret) {
  if (!secret) return false;
  
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload, 'utf8')
    .digest('hex');
  
  const expectedBuffer = Buffer.from(`sha256=${expectedSignature}`, 'utf8');
  const actualBuffer = Buffer.from(signature || '', 'utf8');
  
  return crypto.timingSafeEqual(expectedBuffer, actualBuffer);
}

// Claude API helper
async function callClaude(prompt) {
  if (!config.anthropicApiKey) {
    console.log('Claude API key not configured');
    return null;
  }

  try {
    const response = await axios.post('https://api.anthropic.com/v1/messages', {
      model: 'claude-3-sonnet-20240229',
      max_tokens: 4000,
      messages: [{
        role: 'user',
        content: prompt
      }]
    }, {
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': config.anthropicApiKey,
        'anthropic-version': '2023-06-01'
      }
    });

    return response.data.content[0].text;
  } catch (error) {
    console.error('Claude API Error:', error.response?.data || error.message);
    return null;
  }
}

// Link PR to Lineary Issue
async function linkPRToIssue(pullRequest, repository, db) {
  try {
    // Extract issue number from PR title or body
    const issuePattern = /#(\d+)|LIN-(\d+)/gi;
    const titleMatches = pullRequest.title.match(issuePattern);
    const bodyMatches = pullRequest.body?.match(issuePattern);
    
    const matches = [...(titleMatches || []), ...(bodyMatches || [])];
    if (matches.length === 0) return null;

    // Get the issue number
    const issueNumber = matches[0].replace(/[^0-9]/g, '');
    
    // Find the issue in Lineary
    const issue = await db.oneOrNone(
      'SELECT * FROM issues WHERE id = $1 OR number = $1',
      [issueNumber]
    );

    if (issue) {
      // Update issue with PR information
      await db.none(`
        UPDATE issues 
        SET 
          github_pr_url = $1,
          github_pr_number = $2,
          github_pr_status = $3,
          updated_at = CURRENT_TIMESTAMP
        WHERE id = $4
      `, [
        pullRequest.html_url,
        pullRequest.number,
        pullRequest.state,
        issue.id
      ]);

      // Log activity
      await db.none(`
        INSERT INTO activities (issue_id, type, description, metadata)
        VALUES ($1, 'github_pr_linked', $2, $3)
      `, [
        issue.id,
        `Pull Request #${pullRequest.number} linked`,
        JSON.stringify({
          pr_url: pullRequest.html_url,
          pr_number: pullRequest.number,
          pr_title: pullRequest.title,
          repository: repository.full_name
        })
      ]);

      return issue;
    }
  } catch (error) {
    console.error('Error linking PR to issue:', error);
  }
  return null;
}

// Store Claude review insights
async function storeReviewInsights(review, pullRequest, repository, db) {
  try {
    // Parse review for insights
    const insights = {
      hasSecurityIssues: review.toLowerCase().includes('security'),
      hasPerformanceIssues: review.toLowerCase().includes('performance'),
      hasBugs: review.toLowerCase().includes('bug') || review.toLowerCase().includes('error'),
      codeQualityScore: calculateQualityScore(review),
      suggestions: extractSuggestions(review)
    };

    // Store in database
    await db.none(`
      INSERT INTO code_reviews 
      (pr_number, pr_url, repository, review_text, insights, created_at)
      VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
    `, [
      pullRequest.number,
      pullRequest.html_url,
      repository.full_name,
      review,
      JSON.stringify(insights)
    ]);

    // Update project metrics if linked to an issue
    const issue = await linkPRToIssue(pullRequest, repository, db);
    if (issue && issue.project_id) {
      await db.none(`
        INSERT INTO project_metrics 
        (project_id, metric_type, value, metadata, created_at)
        VALUES ($1, 'code_quality', $2, $3, CURRENT_TIMESTAMP)
      `, [
        issue.project_id,
        insights.codeQualityScore,
        JSON.stringify({
          pr_number: pullRequest.number,
          repository: repository.full_name,
          insights
        })
      ]);
    }

    return insights;
  } catch (error) {
    console.error('Error storing review insights:', error);
    return null;
  }
}

// Calculate code quality score from review
function calculateQualityScore(review) {
  const positiveKeywords = ['good', 'excellent', 'clean', 'well', 'proper', 'correct', 'efficient'];
  const negativeKeywords = ['issue', 'problem', 'error', 'bug', 'vulnerability', 'concern', 'improvement needed'];
  
  const text = review.toLowerCase();
  let score = 70; // Base score
  
  positiveKeywords.forEach(word => {
    if (text.includes(word)) score += 5;
  });
  
  negativeKeywords.forEach(word => {
    if (text.includes(word)) score -= 5;
  });
  
  return Math.max(0, Math.min(100, score));
}

// Extract actionable suggestions from review
function extractSuggestions(review) {
  const suggestions = [];
  const lines = review.split('\n');
  
  lines.forEach(line => {
    if (line.includes('should') || line.includes('consider') || line.includes('recommend')) {
      suggestions.push(line.trim());
    }
  });
  
  return suggestions.slice(0, 5); // Limit to 5 suggestions
}

// Get changed files in PR
async function getChangedFiles(octokit, owner, repo, pullNumber) {
  try {
    const { data: files } = await octokit.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: pullNumber,
    });

    // Filter for code files
    const codeExtensions = ['.js', '.ts', '.tsx', '.jsx', '.py', '.java', '.cpp', '.c', '.go', '.rs'];
    const codeFiles = files.filter(file => 
      codeExtensions.some(ext => file.filename.endsWith(ext)) &&
      file.status !== 'removed' &&
      file.changes < 1000
    );

    const fileContents = await Promise.all(
      codeFiles.slice(0, 10).map(async (file) => {
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
            content: content.slice(0, 5000),
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

// Main webhook endpoint
router.post('/github/webhook', async (req, res) => {
  const signature = req.headers['x-hub-signature-256'];
  const payload = JSON.stringify(req.body);

  // Verify webhook signature if secret is configured
  if (config.githubWebhookSecret) {
    if (!verifyGitHubSignature(payload, signature, config.githubWebhookSecret)) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
  }

  const { action, pull_request, repository, installation } = req.body;
  const eventType = req.headers['x-github-event'];

  try {
    // Handle pull request events
    if (eventType === 'pull_request' && ['opened', 'synchronize', 'reopened'].includes(action)) {
      await handlePullRequest(pull_request, repository, installation, req.db);
    }
    
    // Handle PR review comments
    else if (eventType === 'pull_request_review_comment' && action === 'created') {
      await handleReviewComment(req.body.comment, pull_request, repository, req.db);
    }
    
    // Handle PR closed/merged
    else if (eventType === 'pull_request' && action === 'closed') {
      await handlePRClosed(pull_request, repository, req.db);
    }

    res.status(200).json({ status: 'ok' });
  } catch (error) {
    console.error('Webhook handler error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Handle pull request events
async function handlePullRequest(pullRequest, repository, installation, db) {
  console.log(`PR ${pullRequest.title} in ${repository.full_name}`);

  if (!githubApp || !config.anthropicApiKey) {
    console.log('GitHub App or Claude not configured');
    return;
  }

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

  const prompt = `Please review this pull request for a project management tool called Lineary.

**Focus Areas:**
1. Code Quality & Best Practices
2. Security vulnerabilities
3. Performance optimizations
4. Error handling
5. Testing considerations

**Pull Request:** ${pullRequest.title}
**Description:** ${pullRequest.body || 'No description provided'}

**Files Changed:**
${filesText}

Please provide constructive feedback with specific line references where applicable.`;

  // Get Claude's review
  const review = await callClaude(prompt);
  if (!review) return;

  // Post review comment
  await octokit.rest.issues.createComment({
    owner: repository.owner.login,
    repo: repository.name,
    issue_number: pullRequest.number,
    body: `## 🤖 Claude Code Review

${review}

---
*This review is powered by Claude AI integrated with Lineary • [View Dashboard](https://ai-linear.blockonauts.io)*`
  });

  // Store insights in Lineary
  await storeReviewInsights(review, pullRequest, repository, db);
  
  // Link to Lineary issue
  await linkPRToIssue(pullRequest, repository, db);

  console.log('Review posted and insights stored');
}

// Handle PR closed/merged
async function handlePRClosed(pullRequest, repository, db) {
  if (pullRequest.merged) {
    // Update linked issue status
    const issue = await db.oneOrNone(
      'SELECT * FROM issues WHERE github_pr_number = $1',
      [pullRequest.number]
    );

    if (issue) {
      // Move issue to done status
      await db.none(
        'UPDATE issues SET status = $1, completed_at = CURRENT_TIMESTAMP WHERE id = $2',
        ['done', issue.id]
      );

      // Log activity
      await db.none(`
        INSERT INTO activities (issue_id, type, description, metadata)
        VALUES ($1, 'github_pr_merged', $2, $3)
      `, [
        issue.id,
        `Pull Request #${pullRequest.number} merged`,
        JSON.stringify({
          pr_url: pullRequest.html_url,
          pr_number: pullRequest.number,
          merged_by: pullRequest.merged_by?.login,
          merged_at: pullRequest.merged_at
        })
      ]);
    }
  }
}

// Handle review comments
async function handleReviewComment(comment, pullRequest, repository, db) {
  // Store comment in Lineary
  try {
    await db.none(`
      INSERT INTO review_comments 
      (pr_number, comment_text, author, created_at)
      VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
    `, [
      pullRequest.number,
      comment.body,
      comment.user.login
    ]);
  } catch (error) {
    console.error('Error storing review comment:', error);
  }
}

// Get review insights for a project
router.get('/github/insights/:projectId', async (req, res) => {
  try {
    const { projectId } = req.params;
    
    // Get review metrics
    const metrics = await req.db.one(`
      SELECT 
        COUNT(DISTINCT cr.id) as total_reviews,
        AVG((cr.insights->>'codeQualityScore')::float) as avg_quality_score,
        COUNT(CASE WHEN cr.insights->>'hasSecurityIssues' = 'true' THEN 1 END) as security_issues,
        COUNT(CASE WHEN cr.insights->>'hasPerformanceIssues' = 'true' THEN 1 END) as performance_issues
      FROM code_reviews cr
      JOIN issues i ON i.github_pr_number = cr.pr_number
      WHERE i.project_id = $1
    `, [projectId]);

    // Get recent reviews
    const recentReviews = await req.db.any(`
      SELECT cr.*, i.title as issue_title
      FROM code_reviews cr
      JOIN issues i ON i.github_pr_number = cr.pr_number
      WHERE i.project_id = $1
      ORDER BY cr.created_at DESC
      LIMIT 10
    `, [projectId]);

    res.json({
      metrics,
      recentReviews
    });
  } catch (error) {
    console.error('Error getting review insights:', error);
    res.status(500).json({ error: 'Failed to get review insights' });
  }
});

// Configure GitHub App for a project
router.post('/github/configure', async (req, res) => {
  try {
    const { projectId, repository, installationId } = req.body;

    // Store GitHub configuration for project
    await req.db.none(`
      INSERT INTO project_github_config 
      (project_id, repository, installation_id, created_at)
      VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
      ON CONFLICT (project_id) 
      DO UPDATE SET 
        repository = $2,
        installation_id = $3,
        updated_at = CURRENT_TIMESTAMP
    `, [projectId, repository, installationId]);

    res.json({ success: true });
  } catch (error) {
    console.error('Error configuring GitHub:', error);
    res.status(500).json({ error: 'Failed to configure GitHub' });
  }
});

module.exports = router;