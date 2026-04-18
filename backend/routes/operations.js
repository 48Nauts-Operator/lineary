// Operations — the AI-era replacement for classic "Analytics".
// Metrics that actually matter when agents are the operators:
//   - proposals resolved (approved vs intervened)
//   - auto-approve hit rate
//   - human-intervention rate
//   - active vs idle agents
//   - issues closed (last 7/30 days)
//   - merged PRs (last 7/30 days)
//
// All queries scoped to projects the caller owns.

const express = require('express');

module.exports = function operationsRoutes(pool) {
  const router = express.Router();

  router.get('/operations/summary', async (req, res) => {
    const days = Math.min(parseInt(req.query.days) || 7, 90);
    try {
      const projectScope = `
        SELECT id FROM projects WHERE owner_id = $1 OR owner_id IS NULL
      `;
      const [
        proposalsRes,
        autoRes,
        issuesClosedRes,
        prsMergedRes,
        agentsRes,
      ] = await Promise.all([
        pool.query(
          `SELECT
             COUNT(*) FILTER (WHERE status = 'approved') AS approved,
             COUNT(*) FILTER (WHERE status = 'intervened') AS intervened,
             COUNT(*) FILTER (WHERE status = 'pending') AS pending,
             COUNT(*) FILTER (WHERE status = 'expired') AS expired
           FROM proposals
           WHERE project_id IN (${projectScope})
             AND created_at > NOW() - ($2 || ' days')::interval`,
          [req.user.id, String(days)]
        ),
        pool.query(
          `SELECT COUNT(*) AS auto_approved
           FROM autonomy_audit
           WHERE project_id IN (${projectScope})
             AND created_at > NOW() - ($2 || ' days')::interval`,
          [req.user.id, String(days)]
        ),
        pool.query(
          `SELECT COUNT(*) AS closed
           FROM issues i
           WHERE i.project_id IN (${projectScope})
             AND i.status = 'done'
             AND i.completed_at > NOW() - ($2 || ' days')::interval`,
          [req.user.id, String(days)]
        ),
        pool.query(
          `SELECT COUNT(*) AS merged
           FROM issue_activities a
           JOIN issues i ON i.id = a.issue_id
           WHERE i.project_id IN (${projectScope})
             AND a.activity_type = 'pr_merged'
             AND a.created_at > NOW() - ($2 || ' days')::interval`,
          [req.user.id, String(days)]
        ),
        pool.query(
          `SELECT
             COUNT(DISTINCT a.id) AS total,
             COUNT(DISTINCT CASE WHEN a.last_seen_at > NOW() - INTERVAL '15 minutes' THEN a.id END) AS active_now
           FROM agents a
           WHERE a.user_id = $1 AND a.is_active = true`,
          [req.user.id]
        ),
      ]);

      const p = proposalsRes.rows[0];
      const autoApproved = Number(autoRes.rows[0].auto_approved) || 0;
      const approved = Number(p.approved) || 0;
      const intervened = Number(p.intervened) || 0;
      const total = approved + intervened + Number(p.expired || 0);

      res.json({
        window_days: days,
        proposals: {
          pending: Number(p.pending) || 0,
          approved,
          intervened,
          expired: Number(p.expired) || 0,
          resolved: approved + intervened,
        },
        auto_approve_hit_rate: total > 0 ? autoApproved / total : null,
        human_intervention_rate: total > 0 ? intervened / total : null,
        auto_approved_count: autoApproved,
        issues_closed: Number(issuesClosedRes.rows[0].closed) || 0,
        prs_merged: Number(prsMergedRes.rows[0].merged) || 0,
        agents: {
          total: Number(agentsRes.rows[0].total) || 0,
          active_now: Number(agentsRes.rows[0].active_now) || 0,
        },
      });
    } catch (err) {
      console.error('operations summary:', err);
      res.status(500).json({ error: 'Failed to compute operations summary' });
    }
  });

  // Daily buckets for the last N days (for sparkline/bar chart).
  router.get('/operations/timeseries', async (req, res) => {
    const days = Math.min(parseInt(req.query.days) || 14, 90);
    try {
      const { rows } = await pool.query(
        `
        WITH series AS (
          SELECT generate_series(
            date_trunc('day', NOW() - ($1 || ' days')::interval),
            date_trunc('day', NOW()),
            '1 day'
          )::date AS day
        ),
        my_projects AS (
          SELECT id FROM projects WHERE owner_id = $2 OR owner_id IS NULL
        ),
        approvals AS (
          SELECT date_trunc('day', resolved_at)::date AS day, COUNT(*) AS n
          FROM proposals
          WHERE status = 'approved'
            AND resolved_at > NOW() - ($1 || ' days')::interval
            AND project_id IN (SELECT id FROM my_projects)
          GROUP BY 1
        ),
        interventions AS (
          SELECT date_trunc('day', resolved_at)::date AS day, COUNT(*) AS n
          FROM proposals
          WHERE status = 'intervened'
            AND resolved_at > NOW() - ($1 || ' days')::interval
            AND project_id IN (SELECT id FROM my_projects)
          GROUP BY 1
        ),
        merges AS (
          SELECT date_trunc('day', a.created_at)::date AS day, COUNT(*) AS n
          FROM issue_activities a
          JOIN issues i ON i.id = a.issue_id
          WHERE a.activity_type = 'pr_merged'
            AND a.created_at > NOW() - ($1 || ' days')::interval
            AND i.project_id IN (SELECT id FROM my_projects)
          GROUP BY 1
        )
        SELECT
          to_char(s.day, 'YYYY-MM-DD') AS day,
          COALESCE(a.n, 0)::int AS approvals,
          COALESCE(i.n, 0)::int AS interventions,
          COALESCE(m.n, 0)::int AS merges
        FROM series s
        LEFT JOIN approvals a ON a.day = s.day
        LEFT JOIN interventions i ON i.day = s.day
        LEFT JOIN merges m ON m.day = s.day
        ORDER BY s.day ASC
        `,
        [String(days), req.user.id]
      );
      res.json({ series: rows });
    } catch (err) {
      console.error('operations timeseries:', err);
      res.status(500).json({ error: 'Failed to compute timeseries' });
    }
  });

  return router;
};
