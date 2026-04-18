// GitHub App client factory.
// Uses `octokit` (unified) + `@octokit/auth-app`. CommonJS compatible — unlike
// the retired `@octokit/app`, these two packages load via require() in Node 20.

const { Octokit } = require('octokit');
const { createAppAuth } = require('@octokit/auth-app');

const APP_ID = process.env.GITHUB_APP_ID;
const PRIVATE_KEY = (process.env.GITHUB_APP_PRIVATE_KEY || '').replace(/\\n/g, '\n');
const CLIENT_ID = process.env.GITHUB_APP_CLIENT_ID;
const CLIENT_SECRET = process.env.GITHUB_APP_CLIENT_SECRET;
const SLUG = process.env.GITHUB_APP_SLUG || 'lineary';

let warned = false;
function ensureConfig() {
  if (!APP_ID || !PRIVATE_KEY) {
    if (!warned) {
      console.warn('[github.app] GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY missing — GitHub sync disabled');
      warned = true;
    }
    return false;
  }
  return true;
}

function isConfigured() {
  return Boolean(APP_ID && PRIVATE_KEY);
}

function appSlug() {
  return SLUG;
}

function installationUrl(state) {
  // state is opaque, lets us tie install-callback back to a Lineary project.
  const params = new URLSearchParams({ state });
  return `https://github.com/apps/${SLUG}/installations/new?${params.toString()}`;
}

// Cache installation Octokit clients for 50 minutes (token TTL is 1h).
const installationCache = new Map(); // installationId -> { octokit, expiresAt }

function getAppOctokit() {
  if (!ensureConfig()) throw new Error('GitHub App not configured');
  return new Octokit({
    authStrategy: createAppAuth,
    auth: {
      appId: APP_ID,
      privateKey: PRIVATE_KEY,
      clientId: CLIENT_ID,
      clientSecret: CLIENT_SECRET,
    },
  });
}

function getInstallationOctokit(installationId) {
  if (!ensureConfig()) throw new Error('GitHub App not configured');
  const cached = installationCache.get(installationId);
  if (cached && cached.expiresAt > Date.now()) return cached.octokit;

  const octokit = new Octokit({
    authStrategy: createAppAuth,
    auth: {
      appId: APP_ID,
      privateKey: PRIVATE_KEY,
      installationId,
      clientId: CLIENT_ID,
      clientSecret: CLIENT_SECRET,
    },
  });
  installationCache.set(installationId, {
    octokit,
    expiresAt: Date.now() + 50 * 60 * 1000,
  });
  return octokit;
}

async function exchangeUserCode(code) {
  // OAuth web flow (identifies the Lineary user who installed the App).
  // Only used if we need to correlate installer → Lineary user. Optional.
  if (!CLIENT_ID || !CLIENT_SECRET) return null;
  const resp = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ client_id: CLIENT_ID, client_secret: CLIENT_SECRET, code }),
  });
  if (!resp.ok) return null;
  const data = await resp.json();
  return data.access_token || null;
}

module.exports = {
  isConfigured,
  appSlug,
  installationUrl,
  getAppOctokit,
  getInstallationOctokit,
  exchangeUserCode,
};
