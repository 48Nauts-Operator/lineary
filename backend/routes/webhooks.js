// ABOUTME: Webhook handlers for GitHub and GitLab events
// ABOUTME: Processes commits, PRs, and issue events from Git providers

const express = require('express');
const router = express.Router();
const crypto = require('crypto');

module.exports = (pool) => {
  // GitHub webhook endpoint
  router.post('/webhooks/github/:projectId', async (req, res) => {
    const { projectId } = req.params;
    const signature = req.headers['x-hub-signature-256'];
    const event = req.headers['x-github-event'];
    const deliveryId = req.headers['x-github-delivery'];

    try {
      // Verify webhook signature
      const connResult = await pool.query(
        'SELECT webhook_secret FROM project_git_connections WHERE project_id = $1 AND provider = $2',
        [projectId, 'github']
      );

      if (connResult.rows.length > 0 && connResult.rows[0].webhook_secret) {
        const secret = connResult.rows[0].webhook_secret;
        const hmac = crypto.createHmac('sha256', secret);
        const digest = 'sha256=' + hmac.update(JSON.stringify(req.body)).digest('hex');
        
        if (signature !== digest) {
          return res.status(401).json({ error: 'Invalid signature' });
        }
      }

      // Store webhook event for processing
      await pool.query(
        `INSERT INTO git_webhook_events (
          project_id, provider, event_type, event_id, payload
        ) VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (provider, event_id) DO NOTHING`,
        [projectId, 'github', event, deliveryId, req.body]
      );

      // Process event based on type
      switch (event) {
        case 'push':
          await processGitHubPush(pool, projectId, req.body);
          break;
        case 'pull_request':
          await processGitHubPullRequest(pool, projectId, req.body);
          break;
        case 'issues':
          await processGitHubIssue(pool, projectId, req.body);
          break;
        case 'issue_comment':
          await processGitHubIssueComment(pool, projectId, req.body);
          break;
      }

      res.json({ received: true });
    } catch (error) {
      console.error('GitHub webhook error:', error);
      res.status(500).json({ error: 'Webhook processing failed' });
    }
  });

  // GitLab webhook endpoint
  router.post('/webhooks/gitlab/:projectId', async (req, res) => {
    const { projectId } = req.params;
    const token = req.headers['x-gitlab-token'];
    const event = req.headers['x-gitlab-event'];

    try {
      // Verify webhook token
      const connResult = await pool.query(
        'SELECT webhook_secret FROM project_git_connections WHERE project_id = $1 AND provider = $2',
        [projectId, 'gitlab']
      );

      if (connResult.rows.length > 0 && connResult.rows[0].webhook_secret) {
        if (token !== connResult.rows[0].webhook_secret) {
          return res.status(401).json({ error: 'Invalid token' });
        }
      }

      // Store webhook event
      const eventId = req.body.object_attributes?.id || crypto.randomBytes(16).toString('hex');
      await pool.query(
        `INSERT INTO git_webhook_events (
          project_id, provider, event_type, event_id, payload
        ) VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (provider, event_id) DO NOTHING`,
        [projectId, 'gitlab', event, String(eventId), req.body]
      );

      // Process event based on type
      switch (event) {
        case 'Push Hook':
          await processGitLabPush(pool, projectId, req.body);
          break;
        case 'Merge Request Hook':
          await processGitLabMergeRequest(pool, projectId, req.body);
          break;
        case 'Issue Hook':
          await processGitLabIssue(pool, projectId, req.body);
          break;
      }

      res.json({ received: true });
    } catch (error) {
      console.error('GitLab webhook error:', error);
      res.status(500).json({ error: 'Webhook processing failed' });
    }
  });

  return router;
};

// Process GitHub push events
async function processGitHubPush(pool, projectId, payload) {
  const commits = payload.commits || [];
  const repository = payload.repository;

  for (const commit of commits) {
    // Look for issue references in commit message
    const issueRefs = extractIssueReferences(commit.message);
    
    for (const issueRef of issueRefs) {
      // Find issue by reference
      const issueResult = await pool.query(
        'SELECT id FROM issues WHERE project_id = $1 AND (title ILIKE $2 OR id::text = $3)',
        [projectId, `%#${issueRef}%`, issueRef]
      );

      if (issueResult.rows.length > 0) {
        const issueId = issueResult.rows[0].id;

        // Link commit to issue
        await pool.query(
          `INSERT INTO issue_commits (
            issue_id, project_id, commit_sha, commit_message,
            commit_author, commit_date, commit_url, repository_id, branch
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
          ON CONFLICT (issue_id, commit_sha) DO NOTHING`,
          [
            issueId,
            projectId,
            commit.id,
            commit.message,
            commit.author.name,
            commit.timestamp,
            commit.url,
            String(repository.id),
            payload.ref?.replace('refs/heads/', '')
          ]
        );

        // Add activity to issue
        await pool.query(
          `INSERT INTO issue_activities (
            issue_id, activity_type, description, user_type, metadata
          ) VALUES ($1, $2, $3, $4, $5)`,
          [
            issueId,
            'commit_linked',
            `Commit linked: ${commit.id.substring(0, 7)} - ${commit.message.substring(0, 100)}`,
            'system',
            { commit_sha: commit.id, author: commit.author.name }
          ]
        );
      }
    }
  }
}

// Process GitHub pull request events
async function processGitHubPullRequest(pool, projectId, payload) {
  const pr = payload.pull_request;
  const action = payload.action;

  if (!pr) return;

  // Look for issue references in PR title and body
  const issueRefs = [
    ...extractIssueReferences(pr.title),
    ...extractIssueReferences(pr.body || '')
  ];

  for (const issueRef of issueRefs) {
    const issueResult = await pool.query(
      'SELECT id FROM issues WHERE project_id = $1 AND (title ILIKE $2 OR id::text = $3)',
      [projectId, `%#${issueRef}%`, issueRef]
    );

    if (issueResult.rows.length > 0) {
      const issueId = issueResult.rows[0].id;

      // Link PR to issue
      await pool.query(
        `INSERT INTO issue_pull_requests (
          issue_id, project_id, pr_number, pr_title, pr_url,
          pr_state, pr_author, pr_created_at, pr_merged_at,
          pr_closed_at, repository_id, provider
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (issue_id, pr_number, repository_id) 
        DO UPDATE SET 
          pr_state = EXCLUDED.pr_state,
          pr_merged_at = EXCLUDED.pr_merged_at,
          pr_closed_at = EXCLUDED.pr_closed_at,
          updated_at = CURRENT_TIMESTAMP`,
        [
          issueId,
          projectId,
          pr.number,
          pr.title,
          pr.html_url,
          pr.state,
          pr.user.login,
          pr.created_at,
          pr.merged_at,
          pr.closed_at,
          String(payload.repository.id),
          'github'
        ]
      );

      // Update issue status based on PR state
      if (action === 'closed' && pr.merged) {
        await pool.query(
          'UPDATE issues SET status = $1 WHERE id = $2 AND status != $3',
          ['done', issueId, 'done']
        );
      }

      // Add activity
      await pool.query(
        `INSERT INTO issue_activities (
          issue_id, activity_type, description, user_type, metadata
        ) VALUES ($1, $2, $3, $4, $5)`,
        [
          issueId,
          'pr_' + action,
          `Pull Request #${pr.number} ${action}: ${pr.title}`,
          'system',
          { pr_number: pr.number, pr_url: pr.html_url }
        ]
      );
    }
  }
}

// Process GitHub issue events
async function processGitHubIssue(pool, projectId, payload) {
  const issue = payload.issue;
  const action = payload.action;

  if (!issue || action !== 'opened') return;

  // Check if auto-create is enabled
  const settingsResult = await pool.query(
    'SELECT auto_create_issues FROM projects WHERE id = $1',
    [projectId]
  );

  if (settingsResult.rows.length > 0 && settingsResult.rows[0].auto_create_issues) {
    // Create Lineary issue from GitHub issue
    await pool.query(
      `INSERT INTO issues (
        project_id, title, description, status, priority,
        metadata
      ) VALUES ($1, $2, $3, $4, $5, $6)`,
      [
        projectId,
        `[GH#${issue.number}] ${issue.title}`,
        issue.body || '',
        'backlog',
        3,
        { 
          github_issue_number: issue.number,
          github_issue_url: issue.html_url,
          github_author: issue.user.login
        }
      ]
    );
  }
}

// Process GitHub issue comment events
async function processGitHubIssueComment(pool, projectId, payload) {
  const comment = payload.comment;
  const issue = payload.issue;
  
  if (!comment || !issue) return;

  // Find linked Lineary issue
  const issueResult = await pool.query(
    `SELECT id FROM issues 
     WHERE project_id = $1 
     AND (metadata->>'github_issue_number' = $2 OR title ILIKE $3)`,
    [projectId, String(issue.number), `%#${issue.number}%`]
  );

  if (issueResult.rows.length > 0) {
    const issueId = issueResult.rows[0].id;

    // Add comment to issue
    await pool.query(
      `INSERT INTO issue_comments (
        issue_id, content, author, user_type
      ) VALUES ($1, $2, $3, $4)`,
      [
        issueId,
        `[GitHub Comment] ${comment.body}`,
        comment.user.login,
        'external'
      ]
    );
  }
}

// Similar functions for GitLab...
async function processGitLabPush(pool, projectId, payload) {
  // Similar to GitHub but with GitLab payload structure
  const commits = payload.commits || [];
  
  for (const commit of commits) {
    const issueRefs = extractIssueReferences(commit.message);
    // Process similar to GitHub...
  }
}

async function processGitLabMergeRequest(pool, projectId, payload) {
  // Process GitLab merge requests
  const mr = payload.object_attributes;
  if (!mr) return;
  // Process similar to GitHub PRs...
}

async function processGitLabIssue(pool, projectId, payload) {
  // Process GitLab issues
  const issue = payload.object_attributes;
  if (!issue) return;
  // Process similar to GitHub issues...
}

// Extract issue references from text
function extractIssueReferences(text) {
  const refs = [];
  
  // Match #123 style references
  const hashRefs = text.match(/#(\d+)/g) || [];
  refs.push(...hashRefs.map(ref => ref.substring(1)));
  
  // Match issue URLs
  const urlRefs = text.match(/issues\/(\d+)/g) || [];
  refs.push(...urlRefs.map(ref => ref.split('/')[1]));
  
  // Match Lineary issue UUIDs
  const uuidRefs = text.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi) || [];
  refs.push(...uuidRefs);
  
  return [...new Set(refs)];
}