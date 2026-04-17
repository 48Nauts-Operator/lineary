// Core sync engine: pulls from GitHub into Lineary, drains the outbox the other way.
// All upserts from this module set sync_origin='github' so the outbox-enqueue
// logic in server.js can tell webhook/sync-originated writes apart from
// user-originated writes and avoid reverse-sync loops.

const { getInstallationOctokit } = require('./app');

const LINEARY_STATUS_BY_GH = {
  open: 'todo',
  closed: 'done',
};

async function loadInstallation(pool, projectId) {
  const { rows } = await pool.query(
    `SELECT installation_id, repo_owner, repo_name FROM project_github_installations WHERE project_id = $1`,
    [projectId]
  );
  if (rows.length === 0) throw new Error(`no installation for project ${projectId}`);
  return rows[0];
}

async function upsertIssueFromGitHub(pool, projectId, gh) {
  // gh = GitHub issue payload (REST API shape).
  // GitHub's "issue" list includes PRs — caller filters those out.
  const status = LINEARY_STATUS_BY_GH[gh.state] || 'todo';
  const { rows } = await pool.query(
    `INSERT INTO issues
       (project_id, title, description, status, priority, story_points, estimated_hours,
        github_issue_number, github_issue_id, github_issue_url, source, sync_origin,
        last_github_synced_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'github', 'github', NOW())
     ON CONFLICT (project_id, github_issue_number) WHERE github_issue_number IS NOT NULL
     DO UPDATE SET
       title = EXCLUDED.title,
       description = EXCLUDED.description,
       status = EXCLUDED.status,
       github_issue_id = EXCLUDED.github_issue_id,
       github_issue_url = EXCLUDED.github_issue_url,
       source = 'github',
       sync_origin = 'github',
       last_github_synced_at = NOW(),
       updated_at = NOW()
     RETURNING id`,
    [
      projectId,
      gh.title,
      gh.body || '',
      status,
      3,
      1,
      1,
      gh.number,
      gh.id,
      gh.html_url,
    ]
  );
  return rows[0]?.id || null;
}

async function upsertCommentFromGitHub(pool, issueId, ghComment) {
  if (!issueId || !ghComment?.id) return;
  await pool.query(
    `INSERT INTO issue_comments (issue_id, user_id, user_type, comment_type, content, github_comment_id, sync_origin)
     VALUES ($1, $2, 'human', 'comment', $3, $4, 'github')
     ON CONFLICT (github_comment_id) WHERE github_comment_id IS NOT NULL
     DO UPDATE SET
       content = EXCLUDED.content,
       sync_origin = 'github',
       updated_at = NOW()`,
    [issueId, ghComment.user?.login || 'github', ghComment.body || '', ghComment.id]
  );
}

async function initialSync(pool, projectId) {
  const inst = await loadInstallation(pool, projectId);
  await pool.query(
    `UPDATE project_github_installations SET sync_status = 'initial_syncing', sync_error = NULL WHERE project_id = $1`,
    [projectId]
  );

  try {
    const octo = getInstallationOctokit(inst.installation_id);

    // Paginate all issues (state=all). GitHub returns PRs in the same
    // endpoint — skip entries with `pull_request` set.
    const iter = octo.paginate.iterator(octo.rest.issues.listForRepo, {
      owner: inst.repo_owner,
      repo: inst.repo_name,
      state: 'all',
      per_page: 100,
    });

    for await (const page of iter) {
      for (const gh of page.data) {
        if (gh.pull_request) continue; // handled via pull_requests below
        const issueId = await upsertIssueFromGitHub(pool, projectId, gh);
        if (!issueId || gh.comments === 0) continue;

        // Pull comments for this issue.
        const commentsIter = octo.paginate.iterator(octo.rest.issues.listComments, {
          owner: inst.repo_owner,
          repo: inst.repo_name,
          issue_number: gh.number,
          per_page: 100,
        });
        for await (const commentsPage of commentsIter) {
          for (const c of commentsPage.data) {
            await upsertCommentFromGitHub(pool, issueId, c);
          }
        }
      }
    }

    // TODO: PR + commit sync is handled by webhooks.js already; we can
    // backfill via issue_pull_requests here in a follow-up.

    await pool.query(
      `UPDATE project_github_installations
       SET sync_status = 'live', sync_error = NULL, last_synced_at = NOW()
       WHERE project_id = $1`,
      [projectId]
    );
  } catch (err) {
    console.error('[initialSync]', err.message);
    await pool.query(
      `UPDATE project_github_installations SET sync_status = 'error', sync_error = $2 WHERE project_id = $1`,
      [projectId, err.message.slice(0, 500)]
    );
    throw err;
  }
}

// Incremental pull — used by the poller as a webhook fallback.
async function pollSync(pool, projectId) {
  const inst = await loadInstallation(pool, projectId);
  const octo = getInstallationOctokit(inst.installation_id);

  const { rows } = await pool.query(
    `SELECT last_synced_at FROM project_github_installations WHERE project_id = $1`,
    [projectId]
  );
  const since = rows[0]?.last_synced_at ? new Date(rows[0].last_synced_at).toISOString() : undefined;

  const iter = octo.paginate.iterator(octo.rest.issues.listForRepo, {
    owner: inst.repo_owner,
    repo: inst.repo_name,
    state: 'all',
    sort: 'updated',
    direction: 'desc',
    since,
    per_page: 100,
  });

  for await (const page of iter) {
    for (const gh of page.data) {
      if (gh.pull_request) continue;
      await upsertIssueFromGitHub(pool, projectId, gh);
    }
  }

  await pool.query(
    `UPDATE project_github_installations SET last_synced_at = NOW() WHERE project_id = $1`,
    [projectId]
  );
}

module.exports = {
  initialSync,
  pollSync,
  upsertIssueFromGitHub,
  upsertCommentFromGitHub,
};
