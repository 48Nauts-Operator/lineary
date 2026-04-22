// ABOUTME: Runners tab — register headless agent runners for auto_handle issues.
// ABOUTME: Shows one-time raw token with Copy button + install snippet.

import { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface Runner {
  id: string;
  name: string;
  hostname: string | null;
  runtime_preferences: string[];
  status: 'offline' | 'idle' | 'busy';
  last_seen_at: string | null;
  token_prefix: string | null;
  created_at: string;
}

const RUNTIMES = ['claude', 'codex', 'opencode'] as const;
type Runtime = typeof RUNTIMES[number];

function rel(iso: string | null) {
  if (!iso) return 'never';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.round(diff / 60_000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}

export function RunnersPage() {
  const [runners, setRunners] = useState<Runner[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [selected, setSelected] = useState<Runtime[]>(['claude']);
  const [newRunner, setNewRunner] = useState<{ id: string; token: string; name: string } | null>(null);
  const [copied, setCopied] = useState<'token' | 'config' | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await axios.get('/api/runners');
      setRunners(r.data);
    } catch {
      toast.error('Failed to load runners');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggleRuntime = (r: Runtime) => {
    setSelected((prev) => (prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]));
  };

  const create = async () => {
    if (!name.trim()) return toast.error('Give the runner a name');
    if (selected.length === 0) return toast.error('Pick at least one runtime');
    try {
      const r = await axios.post('/api/runners', { name, runtime_preferences: selected });
      setNewRunner({ id: r.data.id, token: r.data.token, name: r.data.name });
      setName('');
      load();
    } catch {
      toast.error('Failed to create runner');
    }
  };

  const del = async (id: string) => {
    if (!confirm('Delete this runner? In-flight dispatches will be dropped.')) return;
    try {
      await axios.delete(`/api/runners/${id}`);
      load();
    } catch {
      toast.error('Failed to delete');
    }
  };

  const copy = async (text: string, kind: 'token' | 'config') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(kind);
      toast.success('Copied');
      setTimeout(() => setCopied(null), 1500);
    } catch {
      toast.error('Copy failed');
    }
  };

  const apiUrl = typeof window !== 'undefined'
    ? `${window.location.origin.replace(/:3399$/, ':3134')}`
    : 'http://localhost:3134';

  const configJson = newRunner
    ? JSON.stringify(
        {
          runner_id: newRunner.id,
          token: newRunner.token,
          api_url: apiUrl,
          project_paths: {
            'your-project-slug-or-id': '/absolute/path/to/your/repo',
          },
        },
        null,
        2
      )
    : '';

  return (
    <div className="mx-auto max-w-3xl p-6 text-gray-100">
      <h2 className="mb-2 text-xl font-semibold">Runners</h2>
      <p className="mb-6 text-sm text-gray-400">
        A runner is a machine you own (laptop, homelab, NAS) that picks up <code className="rounded bg-gray-800 px-1">auto_handle</code> issues
        and runs headless Claude Code / Codex / OpenCode in a git worktree. No inbound ports required.
      </p>

      {newRunner && (
        <div className="mb-6 rounded border border-[#C2410C]/40 bg-[#1f1814]/60 p-4">
          <div className="mb-2 text-sm font-medium text-[#FDBA74]">
            Copy the token now — it won't be shown again.
          </div>
          <div className="mb-3 flex items-center gap-2">
            <code className="flex-1 break-all rounded bg-black/40 p-2 text-sm text-[#FDBA74]">{newRunner.token}</code>
            <button
              onClick={() => copy(newRunner.token, 'token')}
              className="flex-shrink-0 rounded-md bg-[#C2410C] px-3 py-2 text-xs font-medium text-white hover:bg-[#D97706]"
            >
              {copied === 'token' ? '✓ Copied' : 'Copy'}
            </button>
          </div>

          <div className="mb-1 text-xs text-gray-400">
            Save this as <code className="rounded bg-gray-800 px-1">~/.lineary/runner.json</code>:
          </div>
          <div className="flex items-start gap-2">
            <pre className="flex-1 overflow-auto rounded bg-[#23252C] p-3 font-mono text-[12px] leading-[18px] text-gray-300">
{configJson}
            </pre>
            <button
              onClick={() => copy(configJson, 'config')}
              className="flex-shrink-0 rounded-md border border-gray-700 px-3 py-2 text-xs font-medium text-gray-300 hover:bg-gray-800"
            >
              {copied === 'config' ? '✓' : 'Copy'}
            </button>
          </div>
          <div className="mt-3 text-xs text-gray-500">
            Then run <code className="rounded bg-gray-800 px-1">node /path/to/lineary/runner/lineary-runner.js</code>.
          </div>
          <button
            className="mt-3 text-xs text-gray-400 underline hover:text-gray-200"
            onClick={() => setNewRunner(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="mb-6 rounded-lg border border-gray-800 bg-[#2B2D36] p-4">
        <div className="mb-3 text-sm font-medium text-gray-200">Register a runner</div>
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 placeholder-gray-500"
            placeholder="Runner name (e.g., MacBook Pro, Homelab NAS)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button
            className="rounded bg-[#C2410C] px-4 py-2 text-sm font-semibold text-white hover:bg-[#D97706]"
            onClick={create}
          >
            Generate runner
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-3 text-[12px]">
          <span className="text-gray-500">Runtimes:</span>
          {RUNTIMES.map((r) => (
            <label key={r} className="flex items-center gap-1.5 text-gray-300">
              <input
                type="checkbox"
                checked={selected.includes(r)}
                onChange={() => toggleRuntime(r)}
                className="accent-[#C2410C]"
              />
              {r}
            </label>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-sm text-gray-400">Loading…</div>
      ) : runners.length === 0 ? (
        <div className="rounded border border-dashed border-gray-800 p-6 text-center text-sm text-gray-500">
          No runners yet. Register one above.
        </div>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="border-b border-[#C2410C]/20 text-[11px] uppercase tracking-wider text-gray-400">
            <tr>
              <th className="py-2">Name</th>
              <th>Runtimes</th>
              <th>Status</th>
              <th>Last seen</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {runners.map((r) => (
              <tr key={r.id} className="border-b border-[#C2410C]/10">
                <td className="py-3">
                  <div className="text-gray-100">{r.name}</div>
                  <div className="font-mono text-[11px] text-gray-500">{r.token_prefix || '—'}…</div>
                </td>
                <td className="font-mono text-[12px] text-[#FDBA74]">{(r.runtime_preferences || []).join(', ')}</td>
                <td>
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                      r.status === 'idle'
                        ? 'border-[#2F4A2F] bg-[#1F2E1F] text-[#7FD38E]'
                        : r.status === 'busy'
                        ? 'border-[#4A3A1E] bg-[#3A2F1E] text-[#FBBF24]'
                        : 'border-gray-700 bg-gray-800 text-gray-400'
                    }`}
                  >
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{
                        background:
                          r.status === 'idle' ? '#34D399' : r.status === 'busy' ? '#F59E0B' : '#5A5D6E',
                      }}
                    />
                    {r.status}
                  </span>
                </td>
                <td className="font-mono text-[12px] text-[#FDBA74]/60">{rel(r.last_seen_at)}</td>
                <td className="text-right">
                  <button
                    className="text-xs text-red-400 hover:text-red-300"
                    onClick={() => del(r.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
