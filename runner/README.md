# Lineary Runner

Autonomous dispatch for Lineary. A runner is a machine you own (laptop, homelab, NAS) that long-polls Lineary for issues flagged `auto_handle=true` and runs **headless Claude Code / Codex / OpenCode** in a git worktree. On success it opens a PR.

No inbound ports. The runner phones home to Lineary; Lineary never calls the runner.

## Architecture

```
          ┌────────────┐                ┌──────────────────┐
          │  Lineary   │◀─── long-poll ─│  lineary-runner  │ (your machine)
          │ dispatcher │                │  ─ git worktree  │
          └─────┬──────┘                │  ─ claude -p     │
                │                       │  ─ gh pr create  │
                │  SSE stdout / PR url  │                  │
                └───────────────────────┘                  │
                   issue gets PR in GitHub ◀───────────────┘
```

Flow:
1. Human (or CI) flips `auto_handle=true` on an issue in Lineary.
2. Dispatcher pairs the issue with a free runner that supports the requested runtime.
3. Runner long-polls, claims the dispatch, `git worktree add`s a new branch.
4. Runner spawns `claude -p` (or `codex exec`, `opencode run`) with the issue body.
5. Stdout streams back to Lineary; the issue detail view shows it live.
6. Runner commits, pushes, `gh pr create`s — reports the PR back.
7. CI runs; success closes the issue via the existing GitHub sync.

## Install

```bash
# Node 18+ required (global fetch, no deps needed).
cd runner/
chmod +x lineary-runner.js

# Create your config (do this once, in Lineary: Account → Runners → Register).
mkdir -p ~/.lineary
cp runner.json.example ~/.lineary/runner.json
$EDITOR ~/.lineary/runner.json

# Run it.
./lineary-runner.js
```

## Config: `~/.lineary/runner.json`

```json
{
  "runner_id": "uuid-from-lineary",
  "token": "lrn_...",
  "api_url": "http://localhost:3134",
  "project_paths": {
    "project-uuid": "/absolute/path/to/local/clone",
    "project-slug": "/absolute/path/to/local/clone"
  }
}
```

`project_paths` maps Lineary project IDs (or slugs) to the absolute path of your local checkout. The runner creates a temporary worktree from each, so your working tree is untouched.

## Requirements on the runner machine

- **Node 18+** (for the daemon itself — global `fetch` is used, no npm deps)
- **git 2.20+** (`git worktree`)
- **gh** authenticated (`gh auth status`) for `gh pr create`
- At least one of:
  - `claude` ([Claude Code](https://claude.com/claude-code))
  - `codex` (OpenAI Codex CLI)
  - `opencode` ([opencode.ai](https://opencode.ai))

Whatever runtime you want to use, that CLI needs to be on `PATH` for the user running the daemon.

## Security model

- The runner authenticates with a runner token (`lrn_*`), shown **once** at creation. Store it in `~/.lineary/runner.json` (owner-readable only: `chmod 600`).
- The runner can **only** act on projects whose paths you explicitly list in `project_paths`. No arbitrary filesystem access.
- All dispatches run in a scratch `git worktree` under `$TMPDIR` — the worktree is removed after each run.
- Runner → Lineary traffic is outbound HTTPS only. No inbound ports opened.
- To revoke: delete the runner in Lineary's Account → Runners tab. The next long-poll returns 401 and the daemon exits.

## Running as a background service

### macOS (launchd)

`~/Library/LaunchAgents/ai.lineary.runner.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>ai.lineary.runner</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/node</string>
    <string>/absolute/path/to/lineary/runner/lineary-runner.js</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/lineary-runner.log</string>
  <key>StandardErrorPath</key><string>/tmp/lineary-runner.err.log</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/ai.lineary.runner.plist
```

### Linux (systemd user unit)

`~/.config/systemd/user/lineary-runner.service`:

```ini
[Unit]
Description=Lineary autonomous dispatch runner
After=network-online.target

[Service]
ExecStart=/usr/bin/node /absolute/path/to/lineary/runner/lineary-runner.js
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now lineary-runner
```

## Live stdout over Tailscale (optional)

If you want sub-second round-trip for live stdout from your phone, put Lineary and your runner on the same tailnet. The runner daemon doesn't need to change — it's outbound either way. Tailscale just shortens the path for the SSE tail your browser uses.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `no config at ~/.lineary/runner.json` | copy the example, paste the runner_id + token from Account → Runners |
| long-poll returns 401 | runner was deleted in Lineary, or token expired. re-register. |
| `git worktree add failed` | your project path is dirty. commit or stash before enabling auto_handle. |
| `gh pr create failed` | run `gh auth login` on the runner machine. |
| agent hangs forever | Claude Code needs `--dangerously-skip-permissions` for headless. Confirm with `claude -p hi`. |
