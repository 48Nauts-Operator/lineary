// Pull latest changes from GitHub + drain the outbox every N minutes.
// Cheap enough to run in-process inside the backend container. Upgrade to
// BullMQ if this becomes a bottleneck.

const { pollSync } = require('../lib/github/sync');
const { drainOutbox } = require('../lib/github/outbox');
const { isConfigured } = require('../lib/github/app');

const INTERVAL_MS = parseInt(process.env.GITHUB_POLL_INTERVAL_MS || String(5 * 60 * 1000), 10);

async function tick(pool) {
  if (!isConfigured()) return; // no GitHub App creds yet; nothing to do
  try {
    const { rows } = await pool.query(
      `SELECT project_id FROM project_github_installations WHERE sync_status IN ('live','idle','error')`
    );
    for (const row of rows) {
      try {
        await pollSync(pool, row.project_id);
        await drainOutbox(pool, row.project_id);
      } catch (err) {
        console.error('[github-poller] project', row.project_id, err.message);
      }
    }
  } catch (err) {
    console.error('[github-poller] tick failed:', err.message);
  }
}

function start(pool) {
  console.log(`[github-poller] starting (interval ${INTERVAL_MS}ms)`);
  // Fire once at boot after a small delay, then on the cadence.
  setTimeout(() => tick(pool), 30_000);
  setInterval(() => tick(pool), INTERVAL_MS);
}

module.exports = { start, tick };
