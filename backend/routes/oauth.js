// ABOUTME: OAuth authentication routes for GitHub and GitLab
// ABOUTME: Handles OAuth flow, token management, and repository fetching

const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const axios = require('axios');

// OAuth configuration (in production, use environment variables)
const OAUTH_CONFIG = {
  github: {
    clientId: process.env.GITHUB_CLIENT_ID || 'your_github_client_id',
    clientSecret: process.env.GITHUB_CLIENT_SECRET || 'your_github_client_secret',
    authorizeUrl: 'https://github.com/login/oauth/authorize',
    tokenUrl: 'https://github.com/login/oauth/access_token',
    apiBaseUrl: 'https://api.github.com',
    scope: 'repo user:email'
  },
  gitlab: {
    clientId: process.env.GITLAB_CLIENT_ID || 'your_gitlab_client_id',
    clientSecret: process.env.GITLAB_CLIENT_SECRET || 'your_gitlab_client_secret',
    authorizeUrl: 'https://gitlab.com/oauth/authorize',
    tokenUrl: 'https://gitlab.com/oauth/token',
    apiBaseUrl: 'https://gitlab.com/api/v4',
    scope: 'api read_user read_repository write_repository'
  }
};

// Temporary storage for OAuth states (use Redis in production)
const oauthStates = new Map();

module.exports = (pool) => {
  // Initiate OAuth flow
  router.post('/auth/oauth/initiate', async (req, res) => {
    const { provider, projectId, redirectUri } = req.body;

    if (!['github', 'gitlab'].includes(provider)) {
      return res.status(400).json({ error: 'Invalid provider' });
    }

    const config = OAUTH_CONFIG[provider];
    const state = crypto.randomBytes(32).toString('hex');
    
    // Store state with project info
    oauthStates.set(state, {
      provider,
      projectId,
      redirectUri,
      createdAt: new Date()
    });

    // Build authorization URL
    const params = new URLSearchParams({
      client_id: config.clientId,
      redirect_uri: redirectUri,
      scope: config.scope,
      state: state,
      response_type: 'code'
    });

    const authUrl = `${config.authorizeUrl}?${params.toString()}`;

    res.json({ authUrl, state });
  });

  // Handle OAuth callback
  router.post('/auth/oauth/callback', async (req, res) => {
    const { provider, code, state, projectId } = req.body;

    try {
      // Validate state
      const stateData = oauthStates.get(state);
      if (!stateData || stateData.provider !== provider) {
        return res.status(400).json({ error: 'Invalid state' });
      }

      // Clean up state
      oauthStates.delete(state);

      const config = OAUTH_CONFIG[provider];

      // Exchange code for access token
      const tokenResponse = await axios.post(
        config.tokenUrl,
        {
          client_id: config.clientId,
          client_secret: config.clientSecret,
          code: code,
          grant_type: 'authorization_code',
          redirect_uri: stateData.redirectUri
        },
        {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        }
      );

      const { access_token, refresh_token, expires_in } = tokenResponse.data;

      // Get user info
      const userResponse = await axios.get(
        provider === 'github' ? `${config.apiBaseUrl}/user` : `${config.apiBaseUrl}/user`,
        {
          headers: {
            'Authorization': `Bearer ${access_token}`,
            'Accept': 'application/json'
          }
        }
      );

      const user = userResponse.data;

      // Get user's repositories
      const reposResponse = await axios.get(
        provider === 'github' 
          ? `${config.apiBaseUrl}/user/repos?per_page=100&sort=updated`
          : `${config.apiBaseUrl}/projects?membership=true&per_page=100`,
        {
          headers: {
            'Authorization': `Bearer ${access_token}`,
            'Accept': 'application/json'
          }
        }
      );

      const repositories = reposResponse.data.map(repo => {
        if (provider === 'github') {
          return {
            id: String(repo.id),
            name: repo.name,
            fullName: repo.full_name,
            url: repo.html_url,
            defaultBranch: repo.default_branch,
            private: repo.private
          };
        } else {
          return {
            id: String(repo.id),
            name: repo.name,
            fullName: repo.path_with_namespace,
            url: repo.web_url,
            defaultBranch: repo.default_branch,
            private: repo.visibility === 'private'
          };
        }
      });

      // Store connection in database
      const expiresAt = expires_in 
        ? new Date(Date.now() + expires_in * 1000).toISOString()
        : null;

      await pool.query(`
        INSERT INTO project_git_connections (
          project_id, provider, access_token, refresh_token, 
          expires_at, user_id, username, email, repositories
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (project_id, provider) 
        DO UPDATE SET 
          access_token = EXCLUDED.access_token,
          refresh_token = EXCLUDED.refresh_token,
          expires_at = EXCLUDED.expires_at,
          user_id = EXCLUDED.user_id,
          username = EXCLUDED.username,
          email = EXCLUDED.email,
          repositories = EXCLUDED.repositories,
          updated_at = CURRENT_TIMESTAMP
      `, [
        projectId || stateData.projectId,
        provider,
        access_token,
        refresh_token,
        expiresAt,
        String(user.id),
        user.login || user.username,
        user.email,
        JSON.stringify(repositories)
      ]);

      res.json({ 
        success: true,
        username: user.login || user.username,
        email: user.email,
        repositoryCount: repositories.length
      });
    } catch (error) {
      console.error('OAuth callback error:', error);
      res.status(500).json({ error: 'OAuth authentication failed' });
    }
  });

  // Get Git connections for a project
  router.get('/projects/:id/git-connections', async (req, res) => {
    try {
      const result = await pool.query(
        'SELECT * FROM project_git_connections WHERE project_id = $1',
        [req.params.id]
      );

      const connections = {};
      for (const row of result.rows) {
        connections[row.provider] = {
          provider: row.provider,
          connected: true,
          username: row.username,
          email: row.email,
          repositories: JSON.parse(row.repositories || '[]'),
          selectedRepo: row.selected_repository_id,
          expiresAt: row.expires_at
        };
      }

      // Include disconnected providers
      if (!connections.github) {
        connections.github = { provider: 'github', connected: false };
      }
      if (!connections.gitlab) {
        connections.gitlab = { provider: 'gitlab', connected: false };
      }

      res.json(connections);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Select repository for a connection
  router.post('/projects/:id/git-connections/:provider/select-repo', async (req, res) => {
    const { repositoryId } = req.body;
    
    try {
      await pool.query(
        `UPDATE project_git_connections 
         SET selected_repository_id = $1, updated_at = CURRENT_TIMESTAMP
         WHERE project_id = $2 AND provider = $3`,
        [repositoryId, req.params.id, req.params.provider]
      );

      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Refresh repository list
  router.post('/projects/:id/git-connections/:provider/refresh-repos', async (req, res) => {
    try {
      // Get stored access token
      const connResult = await pool.query(
        'SELECT access_token FROM project_git_connections WHERE project_id = $1 AND provider = $2',
        [req.params.id, req.params.provider]
      );

      if (connResult.rows.length === 0) {
        return res.status(404).json({ error: 'Connection not found' });
      }

      const { access_token } = connResult.rows[0];
      const config = OAUTH_CONFIG[req.params.provider];

      // Fetch fresh repository list
      const reposResponse = await axios.get(
        req.params.provider === 'github' 
          ? `${config.apiBaseUrl}/user/repos?per_page=100&sort=updated`
          : `${config.apiBaseUrl}/projects?membership=true&per_page=100`,
        {
          headers: {
            'Authorization': `Bearer ${access_token}`,
            'Accept': 'application/json'
          }
        }
      );

      const repositories = reposResponse.data.map(repo => {
        if (req.params.provider === 'github') {
          return {
            id: String(repo.id),
            name: repo.name,
            fullName: repo.full_name,
            url: repo.html_url,
            defaultBranch: repo.default_branch,
            private: repo.private
          };
        } else {
          return {
            id: String(repo.id),
            name: repo.name,
            fullName: repo.path_with_namespace,
            url: repo.web_url,
            defaultBranch: repo.default_branch,
            private: repo.visibility === 'private'
          };
        }
      });

      // Update stored repositories
      await pool.query(
        `UPDATE project_git_connections 
         SET repositories = $1, updated_at = CURRENT_TIMESTAMP
         WHERE project_id = $2 AND provider = $3`,
        [JSON.stringify(repositories), req.params.id, req.params.provider]
      );

      res.json({ repositories });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // Disconnect provider
  router.delete('/projects/:id/git-connections/:provider', async (req, res) => {
    try {
      await pool.query(
        'DELETE FROM project_git_connections WHERE project_id = $1 AND provider = $2',
        [req.params.id, req.params.provider]
      );

      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  return router;
};