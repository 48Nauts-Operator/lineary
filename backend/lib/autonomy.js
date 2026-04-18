// Autonomy evaluator — decides whether an incoming proposal can be
// auto-approved based on per-project rules. Runs inline at proposal
// creation time; keep it fast and stateless.

// Known rule keys (also exposed to the UI for toggling):
//   auto_approve_low_risk  — approve any proposal where blast_radius='low'
//                             AND confidence >= min_confidence (default 0.85)
//   auto_merge_small_pr    — approve merge_pr kind when payload.diff_files <= max_files
//                             AND payload.diff_additions <= max_additions (defaults: 5 files, 200 additions)
//   auto_approve_split     — approve split_issue kind when blast_radius != 'high'
//   auto_close_safe        — approve close_issue kind when blast_radius='low'
//
// Each rule has an `enabled` flag and a `config` JSONB for parameters.

async function loadRules(pool, projectId) {
  const { rows } = await pool.query(
    `SELECT rule_key, enabled, config FROM autonomy_rules WHERE project_id = $1 AND enabled = true`,
    [projectId]
  );
  return rows;
}

function matches(rule, proposal) {
  const cfg = rule.config || {};
  const payload = proposal.payload || {};
  const conf = typeof proposal.confidence === 'number' ? proposal.confidence : 0;

  switch (rule.rule_key) {
    case 'auto_approve_low_risk': {
      const min = typeof cfg.min_confidence === 'number' ? cfg.min_confidence : 0.85;
      return proposal.blast_radius === 'low' && conf >= min;
    }
    case 'auto_merge_small_pr': {
      if (proposal.kind !== 'merge_pr') return false;
      const maxFiles = typeof cfg.max_files === 'number' ? cfg.max_files : 5;
      const maxAdditions = typeof cfg.max_additions === 'number' ? cfg.max_additions : 200;
      const files = payload.diff_files ?? payload.files ?? Infinity;
      const additions = payload.diff_additions ?? payload.additions ?? Infinity;
      return files <= maxFiles && additions <= maxAdditions;
    }
    case 'auto_approve_split':
      return proposal.kind === 'split_issue' && proposal.blast_radius !== 'high';
    case 'auto_close_safe':
      return proposal.kind === 'close_issue' && proposal.blast_radius === 'low';
    default:
      return false;
  }
}

/**
 * Evaluate a freshly-created proposal against the project's autonomy rules.
 * If any rule matches, mutates the proposal status to 'approved' in the DB
 * and returns the matching rule_key. Otherwise returns null.
 */
async function maybeAutoApprove(pool, proposal) {
  try {
    const rules = await loadRules(pool, proposal.project_id);
    for (const rule of rules) {
      if (matches(rule, proposal)) {
        await pool.query(
          `UPDATE proposals SET status = 'approved', resolved_at = NOW() WHERE id = $1 AND status = 'pending'`,
          [proposal.id]
        );
        await pool.query(
          `INSERT INTO autonomy_audit (project_id, proposal_id, rule_key, agent_slug, kind)
           VALUES ($1, $2, $3, (SELECT slug FROM agents WHERE id = $4), $5)`,
          [proposal.project_id, proposal.id, rule.rule_key, proposal.agent_id, proposal.kind]
        );
        return rule.rule_key;
      }
    }
  } catch (err) {
    console.error('[autonomy] evaluator error:', err.message);
  }
  return null;
}

const KNOWN_RULES = [
  {
    key: 'auto_approve_low_risk',
    label: 'Auto-approve low-risk proposals',
    description: 'Any proposal with blast_radius = low AND confidence ≥ min_confidence.',
    default_config: { min_confidence: 0.85 },
  },
  {
    key: 'auto_merge_small_pr',
    label: 'Auto-merge small PRs',
    description: 'Merge PRs under max_files files and max_additions lines added.',
    default_config: { max_files: 5, max_additions: 200 },
  },
  {
    key: 'auto_approve_split',
    label: 'Auto-approve issue splits (except high-risk)',
    description: 'Planner proposals that break an issue into sub-issues are usually safe.',
    default_config: {},
  },
  {
    key: 'auto_close_safe',
    label: 'Auto-close low-risk issues',
    description: 'Agent-proposed closes where confidence is high and blast radius is low.',
    default_config: {},
  },
];

module.exports = { maybeAutoApprove, KNOWN_RULES, loadRules };
