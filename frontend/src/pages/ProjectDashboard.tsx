// ABOUTME: Single-project dashboard — Artboard 2 layout.
// ABOUTME: Header (name/repo/stats/spark) + pulse bar + filterable issues list.

import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Project, Issue, API_URL } from '../App';
import { ProjectPulse } from '../components/ProjectPulse';
import { GitHubSyncBadge } from '../components/GitHubSyncBadge';

interface Props {
  project: Project;
  issues: Issue[];
  onOpenIssue: (issue: Issue) => void;
  onBack: () => void;
}

type StatusFilter = 'all' | 'open' | 'in_progress' | 'done';

function rel(iso?: string) {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.max(1, Math.round(diff / 60_000));
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}

const STATUS_LANES: Record<string, { bg: string; fg: string; border: string; dot: string; label: string }> = {
  backlog: { bg: 'transparent', fg: '#878A98', border: '#5A5D6E', dot: 'transparent', label: 'Backlog' },
  todo: { bg: 'transparent', fg: '#878A98', border: '#5A5D6E', dot: 'transparent', label: 'To do' },
  in_progress: { bg: '#1F2A3A', fg: '#9FBCE8', border: '#253446', dot: '#6EA0F5', label: 'In progress' },
  in_review: { bg: '#3A2F1E', fg: '#FBBF24', border: '#4A3A1E', dot: '#F59E0B', label: 'In review' },
  done: { bg: '#1F2E1F', fg: '#7FD38E', border: '#2F4A2F', dot: '#34D399', label: 'Done' },
  cancelled: { bg: '#2A1F1F', fg: '#E88888', border: '#3A2828', dot: '#F87171', label: 'Cancelled' },
};

export function ProjectDashboard({ project, issues, onOpenIssue, onBack }: Props) {
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');
  const [spark, setSpark] = useState<number[]>([]);
  const [counts, setCounts] = useState({ open: 0, inProgress: 0, done: 0, events24h: 0, openPRs: 0 });

  useEffect(() => {
    // Fetch pulse events to derive stats + a 14-bucket sparkline of the last 7 days.
    axios
      .get(`${API_URL}/projects/${project.id}/pulse?limit=200`)
      .then((r) => {
        const events = r.data.events || [];
        const buckets = new Array(14).fill(0);
        const now = Date.now();
        const span = 7 * 24 * 60 * 60 * 1000;
        const bucketMs = span / 14;
        let events24 = 0;
        let openPRs = 0;
        events.forEach((e: { created_at: string; activity_type?: string }) => {
          const t = new Date(e.created_at).getTime();
          const age = now - t;
          if (age < 24 * 60 * 60 * 1000) events24++;
          if (age < span) {
            const idx = Math.min(13, Math.max(0, 13 - Math.floor(age / bucketMs)));
            buckets[idx]++;
          }
          if (e.activity_type === 'pr_opened') openPRs++;
        });
        setSpark(buckets);
        setCounts((c) => ({ ...c, events24h: events24, openPRs }));
      })
      .catch(() => {});
  }, [project.id]);

  useEffect(() => {
    const open = issues.filter((i) => i.status !== 'done' && i.status !== 'cancelled').length;
    const inProgress = issues.filter((i) => i.status === 'in_progress' || i.status === 'in_review').length;
    const done = issues.filter((i) => i.status === 'done').length;
    setCounts((c) => ({ ...c, open, inProgress, done }));
  }, [issues]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return issues
      .filter((i) => {
        if (filter === 'open') return i.status !== 'done' && i.status !== 'cancelled';
        if (filter === 'in_progress') return i.status === 'in_progress' || i.status === 'in_review';
        if (filter === 'done') return i.status === 'done';
        return true;
      })
      .filter((i) => !q || i.title.toLowerCase().includes(q) || (i.description || '').toLowerCase().includes(q))
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 100);
  }, [issues, filter, search]);

  const maxSpark = Math.max(1, ...spark);

  return (
    <div className="mx-auto max-w-[1200px] px-4">
      <button
        onClick={onBack}
        className="mb-4 inline-flex items-center gap-1.5 text-[12px] text-gray-500 hover:text-gray-300"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M15 18l-6-6 6-6" strokeLinecap="round" />
        </svg>
        All projects
      </button>

      {/* Header */}
      <div className="mb-6 flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div
            className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-[16px] font-bold text-[#23252C]"
            style={{ background: project.color || '#C2410C' }}
          >
            {project.name.slice(0, 1).toUpperCase()}
          </div>
          <h1 className="text-[26px] font-semibold tracking-tight text-gray-50">{project.name}</h1>
          {project.mode === 'github' ? <GitHubSyncBadge projectId={project.id} /> : null}
          {project.mode === 'mcp_only' ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-gray-800 bg-[#2B2D36] px-2.5 py-1 text-[11px] text-gray-400">
              <span className="h-1.5 w-1.5 rounded-full bg-[#F59E0B]" />
              MCP only — no repo sync
            </span>
          ) : null}
        </div>

        <div className="flex flex-wrap items-center gap-8">
          <Stat value={counts.open} label="open issues" />
          <Stat value={counts.openPRs} label="open PRs" />
          <Stat value={counts.events24h} label="events last 24h" />
          <div className="flex-1" />
          <Sparkline values={spark} max={maxSpark} />
        </div>
      </div>

      {/* Pulse */}
      <ProjectPulse
        projectId={project.id}
        onOpenIssue={(issueId) => {
          const match = issues.find((i) => i.id === issueId);
          if (match) onOpenIssue(match);
        }}
      />

      {/* Issues list */}
      <div className="mt-2 flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-5 border-b border-[#C2410C]/20 pb-3">
          <TabBtn label="All issues" count={issues.length} active={filter === 'all'} onClick={() => setFilter('all')} />
          <TabBtn label="Open" count={counts.open} active={filter === 'open'} onClick={() => setFilter('open')} />
          <TabBtn
            label="In progress"
            count={counts.inProgress}
            active={filter === 'in_progress'}
            onClick={() => setFilter('in_progress')}
          />
          <TabBtn label="Done" count={counts.done} active={filter === 'done'} onClick={() => setFilter('done')} />
          <div className="flex-1" />
          <label className="flex items-center gap-2 rounded-md border border-[#C2410C]/40 bg-[#2B2D36]/60 px-3 py-1.5 text-[12px] text-[#FDBA74] focus-within:border-[#C2410C] focus-within:ring-1 focus-within:ring-[#C2410C]/40">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4-4" />
            </svg>
            <input
              className="w-[180px] bg-transparent text-gray-100 placeholder-[#FDBA74]/50 focus:outline-none"
              placeholder="Search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
        </div>

        {filtered.length === 0 ? (
          <div className="py-14 text-center text-sm text-gray-500">
            No issues match. Agents will create issues here as they work.
          </div>
        ) : (
          filtered.map((issue) => <IssueRow key={issue.id} issue={issue} onClick={() => onOpenIssue(issue)} />)
        )}
      </div>

      <ReleasesPanel projectId={project.id} />
      <AutonomyPanel projectId={project.id} />
    </div>
  );
}

interface Release {
  id: string;
  name: string;
  tag: string | null;
  status: 'draft' | 'published';
  body: string | null;
  pr_numbers: number[] | null;
  published_at: string | null;
  created_at: string;
}

function ReleasesPanel({ projectId }: { projectId: string }) {
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [drafting, setDrafting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API_URL}/projects/${projectId}/releases`);
      setReleases(r.data.releases || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const autoDraft = async () => {
    setDrafting(true);
    try {
      const r = await axios.post(`${API_URL}/projects/${projectId}/releases/auto-draft`);
      if (r.data.release) {
        setReleases((prev) => [r.data.release, ...prev]);
        setExpanded(r.data.release.id);
      }
    } finally {
      setDrafting(false);
    }
  };

  const publish = async (id: string) => {
    try {
      const r = await axios.post(`${API_URL}/projects/${projectId}/releases/${id}/publish`);
      setReleases((prev) => prev.map((x) => (x.id === id ? r.data : x)));
    } catch {
      // noop
    }
  };

  return (
    <div className="mt-12 border-t border-gray-800 pt-8">
      <div className="mb-4 flex items-baseline justify-between">
        <div className="flex items-baseline gap-3">
          <h2 className="text-[16px] font-semibold text-gray-200">Releases</h2>
          <span className="text-[12px] text-gray-500">
            Bundles of merged work. Auto-drafted from merged PRs; edit, then publish.
          </span>
        </div>
        <button
          onClick={autoDraft}
          disabled={drafting}
          className="rounded-md border border-gray-800 px-3 py-1.5 text-[12px] font-medium text-gray-300 hover:bg-gray-800 disabled:opacity-50"
        >
          {drafting ? 'Drafting…' : 'Auto-draft from recent merges'}
        </button>
      </div>

      {loading ? (
        <div className="py-6 text-center text-sm text-gray-500">Loading…</div>
      ) : releases.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-800 bg-[#272931] p-6 text-center text-[12px] text-gray-500">
          No releases yet. Click Auto-draft when you want to stamp a slice of merged work as a release.
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {releases.map((rel) => (
            <div key={rel.id} className="rounded-lg border border-gray-800 bg-[#2B2D36]">
              <button
                onClick={() => setExpanded(expanded === rel.id ? null : rel.id)}
                className="flex w-full items-center gap-3 px-4 py-3 text-left"
              >
                <span
                  className={`inline-block rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                    rel.status === 'published'
                      ? 'border-[#2F4A2F] bg-[#1F2E1F] text-[#7FD38E]'
                      : 'border-gray-800 bg-[#32343E] text-gray-400'
                  }`}
                >
                  {rel.status}
                </span>
                <span className="text-[13px] font-medium text-gray-200">{rel.name}</span>
                {rel.tag ? <span className="font-mono text-[12px] text-[#F59E0B]">{rel.tag}</span> : null}
                <span className="ml-auto flex items-center gap-3 text-[11px] text-gray-500">
                  {rel.pr_numbers && rel.pr_numbers.length > 0 ? (
                    <span>
                      {rel.pr_numbers.length} PR{rel.pr_numbers.length === 1 ? '' : 's'}
                    </span>
                  ) : null}
                  <span className="font-mono">
                    {rel.published_at
                      ? `published ${new Date(rel.published_at).toLocaleDateString()}`
                      : `drafted ${new Date(rel.created_at).toLocaleDateString()}`}
                  </span>
                </span>
              </button>
              {expanded === rel.id ? (
                <div className="border-t border-gray-800 p-4">
                  <pre className="whitespace-pre-wrap text-[13px] leading-[20px] text-gray-300">{rel.body || ''}</pre>
                  {rel.status === 'draft' ? (
                    <div className="mt-3 flex justify-end">
                      <button
                        onClick={() => publish(rel.id)}
                        className="rounded-md border border-[#2F4A2F] bg-[#1F2E1F] px-3 py-1.5 text-[12px] font-semibold text-[#8AD896]"
                      >
                        Publish release
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface AutonomyRule {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
  config: Record<string, unknown>;
  default_config: Record<string, unknown>;
}

function AutonomyPanel({ projectId }: { projectId: string }) {
  const [rules, setRules] = useState<AutonomyRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    axios
      .get(`${API_URL}/projects/${projectId}/autonomy`)
      .then((r) => alive && setRules(r.data.rules || []))
      .catch(() => alive && setRules([]))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [projectId]);

  const toggle = async (rule: AutonomyRule) => {
    const next = !rule.enabled;
    setSaving(rule.key);
    try {
      await axios.put(`${API_URL}/projects/${projectId}/autonomy/${rule.key}`, {
        enabled: next,
        config: rule.config ?? rule.default_config,
      });
      setRules((prev) => prev.map((r) => (r.key === rule.key ? { ...r, enabled: next } : r)));
    } catch {
      // noop; UI will stay as-is
    } finally {
      setSaving(null);
    }
  };

  if (loading) return null;

  return (
    <div className="mt-12 border-t border-gray-800 pt-8">
      <div className="mb-4 flex items-baseline gap-3">
        <h2 className="text-[16px] font-semibold text-gray-200">Autonomy</h2>
        <span className="text-[12px] text-gray-500">
          When a rule matches, the proposal is applied immediately without a human click.
        </span>
      </div>
      <div className="flex flex-col gap-2">
        {rules.map((rule) => (
          <div
            key={rule.key}
            className="flex items-center gap-4 rounded-lg border border-gray-800 bg-[#2B2D36] px-4 py-3"
          >
            <div className="flex flex-1 flex-col gap-0.5">
              <span className="text-[13px] font-medium text-gray-200">{rule.label}</span>
              <span className="text-[12px] text-gray-500">{rule.description}</span>
            </div>
            <button
              onClick={() => toggle(rule)}
              disabled={saving === rule.key}
              className={`flex h-[22px] w-[38px] flex-shrink-0 items-center rounded-full p-[2px] transition-colors ${
                rule.enabled ? 'bg-[#34D399]/70' : 'bg-gray-800'
              } ${saving === rule.key ? 'opacity-60' : ''}`}
              aria-pressed={rule.enabled}
              aria-label={rule.label}
            >
              <span
                className={`h-[18px] w-[18px] rounded-full bg-gray-50 transition-transform ${
                  rule.enabled ? 'translate-x-[16px]' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-[22px] font-semibold tracking-tight text-gray-50">{value}</span>
      <span className="text-[12px] text-gray-500">{label}</span>
    </div>
  );
}

function Sparkline({ values, max }: { values: number[]; max: number }) {
  const colors = ['#5A5D6E', '#393E54', '#393E54', '#6EA0F5', '#393E54', '#F59E0B', '#393E54', '#4ADE80', '#393E54', '#F59E0B', '#393E54', '#6EA0F5', '#393E54', '#5A5D6E'];
  return (
    <div className="flex items-end gap-[2px]" title="Activity — last 7 days">
      {values.map((v, i) => (
        <div
          key={i}
          className="w-[3px] rounded-[1px]"
          style={{
            height: `${Math.max(4, (v / max) * 30)}px`,
            background: v === 0 ? '#3A3D47' : colors[i % colors.length],
          }}
        />
      ))}
    </div>
  );
}

function TabBtn({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count?: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`text-[13px] font-medium ${active ? 'text-gray-50' : 'text-gray-400 hover:text-gray-200'}`}
    >
      {label}
      {typeof count === 'number' ? (
        <span className={`ml-1.5 font-mono text-[12px] ${active ? 'text-[#FDBA74]' : 'text-[#FDBA74]/50'}`}>{count}</span>
      ) : null}
    </button>
  );
}

function IssueRow({ issue, onClick }: { issue: Issue; onClick: () => void }) {
  const s = STATUS_LANES[issue.status] || STATUS_LANES.todo;
  const key = issue.id.slice(0, 7);
  const gh = (issue as any).github_issue_number as number | undefined;
  const source = (issue as any).source as string | undefined;
  const isMcpOnly = !gh && source !== 'github';
  const strike = issue.status === 'done' || issue.status === 'cancelled';

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3.5 border-b border-[#C2410C]/15 py-3 text-left hover:bg-[#C2410C]/5"
    >
      <div className="flex w-6 flex-shrink-0 justify-center">
        <StatusDot status={issue.status} />
      </div>
      <div
        className={`w-[80px] flex-shrink-0 font-mono text-[12px] font-medium ${strike ? 'text-gray-600 line-through' : 'text-gray-500'}`}
      >
        LIN-{key}
      </div>
      <div className={`flex flex-1 items-center gap-2 overflow-hidden ${strike ? 'text-gray-500 line-through' : 'text-gray-200'}`}>
        <span className="truncate text-[14px] font-medium">{issue.title}</span>
        {(issue as any).source === 'agent' || (issue as any).created_by_agent ? (
          <span className="inline-block flex-shrink-0 rounded border border-gray-800 bg-[#32343E] px-1.5 py-[1px] text-[10px] font-semibold uppercase tracking-wider text-[#F59E0B]">
            Agent
          </span>
        ) : null}
      </div>
      <div className="w-[92px] flex-shrink-0">
        {gh ? (
          <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-gray-500">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="#5A5D6E">
              <path d="M12 .297C5.373.297 0 5.67 0 12.297c0 5.302 3.438 9.8 8.207 11.387.6.113.82-.258.82-.577 0-.285-.011-1.04-.017-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.744.083-.729.083-.729 1.205.084 1.838 1.237 1.838 1.237 1.07 1.834 2.809 1.304 3.495.997.108-.775.419-1.305.762-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.468-2.382 1.236-3.222-.124-.303-.535-1.523.117-3.176 0 0 1.008-.322 3.3 1.23a11.5 11.5 0 013.003-.404c1.018.005 2.045.138 3.003.404 2.29-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.873.118 3.176.77.84 1.235 1.912 1.235 3.222 0 4.61-2.804 5.625-5.475 5.92.43.37.814 1.102.814 2.222 0 1.604-.015 2.896-.015 3.286 0 .322.218.697.825.577C20.565 22.093 24 17.595 24 12.297 24 5.67 18.627.297 12 .297" />
            </svg>
            GH#{gh}
          </span>
        ) : isMcpOnly ? (
          <span className="text-[11px] italic text-[#FDBA74]/80">MCP only</span>
        ) : null}
      </div>
      <div className="w-[60px] flex-shrink-0 text-right font-mono text-[11px] text-[#FDBA74]/60">{rel(issue.created_at)}</div>
    </button>
  );
}

function StatusDot({ status }: { status: string }) {
  const s = STATUS_LANES[status] || STATUS_LANES.todo;
  if (s.dot === 'transparent') {
    return <div className="h-2.5 w-2.5 rounded-full border-2" style={{ borderColor: s.border }} />;
  }
  return <div className="h-2.5 w-2.5 rounded-full" style={{ background: s.dot }} />;
}
