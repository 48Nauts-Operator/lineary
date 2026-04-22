// Pair auto_handle issues with idle runners and create pending dispatches.
// Runs every 10s. Bounded per-runner concurrency: one in-flight dispatch.

const INTERVAL_MS = 10_000;

function pickRuntime(issuePref, runnerPrefs) {
  if (Array.isArray(runnerPrefs) && runnerPrefs.length > 0) {
    if (issuePref && issuePref !== 'any' && runnerPrefs.includes(issuePref)) return issuePref;
    return runnerPrefs[0];
  }
  return 'claude';
}

async function tick(db) {
  try {
    // Find issues needing dispatch (auto_handle, not done, no active dispatch yet).
    const { rows: candidates } = await db.query(
      `SELECT i.id, i.project_id, i.runner_preference, p.owner_id
       FROM issues i
       JOIN projects p ON p.id = i.project_id
       WHERE i.auto_handle = TRUE
         AND i.status IN ('backlog','todo','in_progress')
         AND NOT EXISTS (
           SELECT 1 FROM runner_dispatches d
           WHERE d.issue_id = i.id
             AND d.status IN ('pending','claimed','running')
         )
       ORDER BY i.priority DESC, i.created_at ASC
       LIMIT 25`
    );
    if (candidates.length === 0) return;

    // Free runners per user: idle AND no in-flight dispatch.
    const { rows: freeRunners } = await db.query(
      `SELECT r.id, r.user_id, r.runtime_preferences
       FROM runners r
       WHERE r.status = 'idle'
         AND r.last_seen_at > NOW() - INTERVAL '2 minutes'
         AND NOT EXISTS (
           SELECT 1 FROM runner_dispatches d
           WHERE d.runner_id = r.id
             AND d.status IN ('pending','claimed','running')
         )`
    );
    if (freeRunners.length === 0) return;

    const byUser = new Map();
    for (const r of freeRunners) {
      const list = byUser.get(r.user_id) || [];
      list.push(r);
      byUser.set(r.user_id, list);
    }

    for (const issue of candidates) {
      const pool = byUser.get(issue.owner_id) || [];
      if (pool.length === 0) continue;
      // Match runtime preference
      const match = pool.find((r) => {
        const prefs = Array.isArray(r.runtime_preferences) ? r.runtime_preferences : [];
        return issue.runner_preference === 'any' || prefs.includes(issue.runner_preference);
      });
      if (!match) continue;
      const runtime = pickRuntime(issue.runner_preference, match.runtime_preferences);
      try {
        await db.query(
          `INSERT INTO runner_dispatches (runner_id, issue_id, project_id, runtime, status)
           VALUES ($1, $2, $3, $4, 'pending')`,
          [match.id, issue.id, issue.project_id, runtime]
        );
        // Drop this runner from the pool for this tick to avoid double-assignment.
        byUser.set(issue.owner_id, pool.filter((r) => r.id !== match.id));
      } catch (err) {
        console.error('[dispatcher] insert failed:', err.message);
      }
    }
  } catch (err) {
    console.error('[dispatcher] tick failed:', err.message);
  }
}

function startDispatcher(db) {
  console.log('[dispatcher] starting; interval=', INTERVAL_MS, 'ms');
  const t = setInterval(() => tick(db), INTERVAL_MS);
  tick(db); // run once at boot
  return () => clearInterval(t);
}

module.exports = { startDispatcher };
