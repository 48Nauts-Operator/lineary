#!/usr/bin/env node
// Lineary runner daemon. Long-polls for dispatches, runs a headless coding
// agent (claude / codex / opencode) in a git worktree, streams stdout back,
// opens a PR on success. No inbound ports required.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, execFileSync } = require('child_process');

const CONFIG_PATH = process.env.LINEARY_RUNNER_CONFIG
  || path.join(os.homedir(), '.lineary', 'runner.json');

function loadConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    console.error(`[runner] no config at ${CONFIG_PATH}. run 'lineary-runner register' or copy runner.json.example`);
    process.exit(1);
  }
  const raw = fs.readFileSync(CONFIG_PATH, 'utf-8');
  const cfg = JSON.parse(raw);
  for (const k of ['runner_id', 'token', 'api_url', 'project_paths']) {
    if (!cfg[k]) {
      console.error(`[runner] config is missing "${k}"`);
      process.exit(1);
    }
  }
  return cfg;
}

// Minimal fetch wrapper — no dependencies. Node 18+ has global fetch.
async function api(cfg, method, path, body) {
  const url = `${cfg.api_url.replace(/\/$/, '')}${path}`;
  const res = await fetch(url, {
    method,
    headers: {
      'X-Runner-Token': cfg.token,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const text = await res.text();
  if (!res.ok) throw new Error(`${method} ${path} → ${res.status} ${text}`);
  return text ? JSON.parse(text) : null;
}

async function longPoll(cfg) {
  while (true) {
    try {
      const result = await api(cfg, 'GET', `/api/runners/${cfg.runner_id}/next-dispatch`);
      if (result) return result;
    } catch (err) {
      console.error(`[runner] poll error: ${err.message}, backing off 5s`);
      await sleep(5000);
    }
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function sh(cmd, args, opts) {
  return execFileSync(cmd, args, { stdio: 'pipe', encoding: 'utf-8', ...opts }).trim();
}

function prompt(runtime, issue) {
  const header = `You are working on Lineary issue ${issue.id}.
Title: ${issue.title}
${issue.github_issue_number ? `GitHub: #${issue.github_issue_number}\n` : ''}
${'='.repeat(60)}
${issue.description || '(no description)'}
${'='.repeat(60)}

Instructions:
- Implement the change on this worktree branch.
- Keep the scope tight — do only what the issue asks for.
- Stage and commit your work with a clear message that references the issue.
- When finished, exit. The runner will open the PR.
`;
  return header;
}

function runtimeCommand(runtime) {
  switch (runtime) {
    case 'claude':
      return { cmd: 'claude', args: ['-p', '--dangerously-skip-permissions'] };
    case 'codex':
      return { cmd: 'codex', args: ['exec', '--no-interactive'] };
    case 'opencode':
      return { cmd: 'opencode', args: ['run'] };
    default:
      throw new Error(`unsupported runtime: ${runtime}`);
  }
}

async function postStdout(cfg, dispatchId, line) {
  try {
    await api(cfg, 'POST', `/api/runners/${cfg.runner_id}/dispatches/${dispatchId}/stdout`, { line });
  } catch (err) {
    // Don't fail the dispatch over a dropped stdout line; just log locally.
    console.error(`[runner] stdout post failed: ${err.message}`);
  }
}

async function runAgent(cfg, dispatch) {
  const { cmd, args } = runtimeCommand(dispatch.runtime);
  const cwd = cfg.project_paths[dispatch.project_id] || cfg.project_paths[dispatch.issue.project_slug];
  if (!cwd) {
    throw new Error(`no project_paths entry for project ${dispatch.project_id}/${dispatch.issue.project_slug}`);
  }
  if (!fs.existsSync(cwd)) throw new Error(`project path does not exist: ${cwd}`);

  const branch = `lineary/${dispatch.issue.project_slug || 'task'}-${String(dispatch.issue.id).slice(0, 8)}`;
  const worktreeDir = path.join(os.tmpdir(), `lineary-wt-${dispatch.dispatch_id.slice(0, 8)}`);
  await postStdout(cfg, dispatch.dispatch_id, `📦 creating worktree: ${worktreeDir} (branch ${branch})`);

  try {
    sh('git', ['worktree', 'add', '-b', branch, worktreeDir], { cwd });
  } catch (err) {
    throw new Error(`git worktree add failed: ${err.message}`);
  }

  const promptText = prompt(dispatch.runtime, dispatch.issue);
  await postStdout(cfg, dispatch.dispatch_id, `🤖 launching ${dispatch.runtime} (${cmd} ${args.join(' ')})`);

  const agent = spawn(cmd, args, { cwd: worktreeDir, stdio: ['pipe', 'pipe', 'pipe'] });
  agent.stdin.write(promptText);
  agent.stdin.end();

  let buffer = '';
  const flushLine = async (line) => {
    const clean = line.replace(/\u001b\[[0-9;]*m/g, '').trim();
    if (clean) await postStdout(cfg, dispatch.dispatch_id, clean);
  };

  agent.stdout.on('data', async (chunk) => {
    buffer += chunk.toString();
    const parts = buffer.split('\n');
    buffer = parts.pop();
    for (const line of parts) await flushLine(line);
  });
  agent.stderr.on('data', async (chunk) => {
    const s = chunk.toString().trim();
    if (s) await postStdout(cfg, dispatch.dispatch_id, `⚠️  ${s}`);
  });

  const exitCode = await new Promise((res) => agent.on('close', res));
  if (buffer) await flushLine(buffer);

  if (exitCode !== 0) {
    await postStdout(cfg, dispatch.dispatch_id, `agent exited with code ${exitCode}`);
    sh('git', ['worktree', 'remove', '--force', worktreeDir], { cwd }).catch?.(() => {});
    return { ok: false, error: `agent exited ${exitCode}` };
  }

  // Commit any outstanding changes the agent left unstaged.
  try {
    const status = sh('git', ['status', '--porcelain'], { cwd: worktreeDir });
    if (status) {
      sh('git', ['add', '-A'], { cwd: worktreeDir });
      sh('git', ['commit', '-m', `lineary: ${dispatch.issue.title}\n\nresolves ${dispatch.issue.id}`], { cwd: worktreeDir });
    }
  } catch (err) {
    await postStdout(cfg, dispatch.dispatch_id, `commit step: ${err.message}`);
  }

  // Push + open PR via gh.
  let prUrl = null;
  let prNumber = null;
  try {
    sh('git', ['push', '-u', 'origin', branch], { cwd: worktreeDir });
    const prJson = sh('gh', ['pr', 'create',
      '--title', `${dispatch.issue.title}`,
      '--body', `Auto-generated by lineary-runner for issue ${dispatch.issue.id}${dispatch.issue.github_issue_number ? ` (closes #${dispatch.issue.github_issue_number})` : ''}.`,
      '--head', branch,
    ], { cwd: worktreeDir });
    const m = prJson.match(/https:\/\/github\.com\/[^\s]+\/pull\/(\d+)/);
    if (m) {
      prUrl = m[0];
      prNumber = parseInt(m[1], 10);
    }
    await postStdout(cfg, dispatch.dispatch_id, `🔗 opened PR: ${prUrl || prJson}`);
  } catch (err) {
    await postStdout(cfg, dispatch.dispatch_id, `gh pr create failed: ${err.message}`);
  }

  try {
    sh('git', ['worktree', 'remove', '--force', worktreeDir], { cwd });
  } catch {
    // leave it; user can reap with `git worktree prune`
  }

  return { ok: true, pr_url: prUrl, pr_number: prNumber };
}

async function main() {
  const cfg = loadConfig();
  console.log(`[runner] started; id=${cfg.runner_id} api=${cfg.api_url}`);

  // Best-effort: bump status to idle by doing a poll once at boot.
  while (true) {
    console.log('[runner] waiting for dispatch…');
    const dispatch = await longPoll(cfg);
    console.log(`[runner] picked dispatch ${dispatch.dispatch_id} (${dispatch.runtime})`);
    try {
      const result = await runAgent(cfg, dispatch);
      await api(cfg, 'POST', `/api/runners/${cfg.runner_id}/dispatches/${dispatch.dispatch_id}/complete`, {
        status: result.ok ? 'completed' : 'failed',
        pr_url: result.pr_url,
        pr_number: result.pr_number,
        error: result.error,
      });
    } catch (err) {
      console.error(`[runner] dispatch failed: ${err.message}`);
      try {
        await api(cfg, 'POST', `/api/runners/${cfg.runner_id}/dispatches/${dispatch.dispatch_id}/complete`, {
          status: 'failed',
          error: err.message,
        });
      } catch (_) {}
    }
  }
}

main().catch((err) => {
  console.error(`[runner] fatal: ${err.message}`);
  process.exit(1);
});
