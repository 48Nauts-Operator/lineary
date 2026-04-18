// Outbox: reliable reverse-sync queue (Lineary → GitHub).
// Writes enqueue rows; the drain worker (called by the poller) fulfils them.

const { getInstallationOctokit } = require('./app');

async function enqueue(pool, { projectId, kind, payload, linearyRef }) {
  await pool.query(
    `INSERT INTO github_sync_outbox (project_id, kind, payload, lineary_ref)
     VALUES ($1, $2, $3, $4)`,
    [projectId, kind, payload, linearyRef || null]
  );
}

async function getInstallation(pool, projectId) {
  const { rows } = await pool.query(
    `SELECT installation_id, repo_owner, repo_name FROM project_github_installations WHERE project_id = $1`,
    [projectId]
  );
  return rows[0] || null;
}

// Drain a limited batch of pending outbox rows for a single project.
async function drainOutbox(pool, projectId, maxBatch = 20) {
  const inst = await getInstallation(pool, projectId);
  if (!inst) return { drained: 0, reason: 'no_installation' };

  // Claim up to maxBatch pending rows with row-level locks.
  const claim = await pool.query(
    `UPDATE github_sync_outbox
     SET status = 'in_flight'
     WHERE id IN (
       SELECT id FROM github_sync_outbox
       WHERE project_id = $1 AND status = 'pending'
       ORDER BY created_at ASC
       FOR UPDATE SKIP LOCKED
       LIMIT $2
     )
     RETURNING *`,
    [projectId, maxBatch]
  );

  const octo = getInstallationOctokit(inst.installation_id);
  let drained = 0;

  for (const row of claim.rows) {
    try {
      await applyOutboxRow(pool, octo, inst, row);
      await pool.query(
        `UPDATE github_sync_outbox SET status = 'done', done_at = NOW() WHERE id = $1`,
        [row.id]
      );
      drained++;
    } catch (err) {
      const attempts = (row.attempts || 0) + 1;
      const done = attempts >= 5;
      await pool.query(
        `UPDATE github_sync_outbox
         SET status = $1, attempts = $2, last_error = $3
         WHERE id = $4`,
        [done ? 'failed' : 'pending', attempts, String(err?.message || err).slice(0, 500), row.id]
      );
      console.error(`[outbox] ${row.kind} failed (attempt ${attempts}): ${err?.message || err}`);
    }
  }

  return { drained };
}

async function applyOutboxRow(pool, octo, inst, row) {
  const { kind, payload } = row;
  switch (kind) {
    case 'issue.create': {
      const resp = await octo.rest.issues.create({
        owner: inst.repo_owner,
        repo: inst.repo_name,
        title: payload.title,
        body: payload.body || '',
        labels: payload.labels || undefined,
      });
      // Write back the GH number/id/url on the Lineary issue.
      await pool.query(
        `UPDATE issues
         SET github_issue_number = $1, github_issue_id = $2, github_issue_url = $3,
             last_github_synced_at = NOW()
         WHERE id = $4`,
        [resp.data.number, resp.data.id, resp.data.html_url, row.lineary_ref]
      );
      break;
    }
    case 'issue.update': {
      if (!payload.github_issue_number) break;
      await octo.rest.issues.update({
        owner: inst.repo_owner,
        repo: inst.repo_name,
        issue_number: payload.github_issue_number,
        title: payload.title,
        body: payload.body,
      });
      break;
    }
    case 'issue.close': {
      if (!payload.github_issue_number) break;
      await octo.rest.issues.update({
        owner: inst.repo_owner,
        repo: inst.repo_name,
        issue_number: payload.github_issue_number,
        state: 'closed',
      });
      break;
    }
    case 'issue.reopen': {
      if (!payload.github_issue_number) break;
      await octo.rest.issues.update({
        owner: inst.repo_owner,
        repo: inst.repo_name,
        issue_number: payload.github_issue_number,
        state: 'open',
      });
      break;
    }
    case 'comment.create': {
      if (!payload.github_issue_number) break;
      const resp = await octo.rest.issues.createComment({
        owner: inst.repo_owner,
        repo: inst.repo_name,
        issue_number: payload.github_issue_number,
        body: payload.body,
      });
      await pool.query(
        `UPDATE issue_comments SET github_comment_id = $1 WHERE id = $2`,
        [resp.data.id, row.lineary_ref]
      );
      break;
    }
    case 'comment.update': {
      if (!payload.github_comment_id) break;
      await octo.rest.issues.updateComment({
        owner: inst.repo_owner,
        repo: inst.repo_name,
        comment_id: payload.github_comment_id,
        body: payload.body,
      });
      break;
    }
    case 'comment.delete': {
      if (!payload.github_comment_id) break;
      await octo.rest.issues.deleteComment({
        owner: inst.repo_owner,
        repo: inst.repo_name,
        comment_id: payload.github_comment_id,
      });
      break;
    }
    default:
      throw new Error(`unknown outbox kind: ${kind}`);
  }
}

module.exports = { enqueue, drainOutbox };
