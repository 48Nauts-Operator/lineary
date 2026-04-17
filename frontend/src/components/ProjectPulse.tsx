// ABOUTME: Horizontal scrollable pulse bar — recent events in a project,
// ABOUTME: color-coded by type. Calm signal that the project is alive.

import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL } from '../App';

interface PulseEvent {
  kind: 'activity' | 'comment';
  id: string;
  issue_id: string;
  issue_title: string;
  issue_key: string;
  activity_type: string;
  description: string;
  user_id?: string | null;
  user_type?: 'human' | 'ai' | 'system' | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

function relative(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.max(1, Math.round(diff / 60_000));
  if (m < 60) return `${m}m`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.round(h / 24)}d`;
}

type Shape = {
  label: string;
  color: string;
  bgGradient?: string;
  icon: React.ReactNode;
};

function shapeFor(e: PulseEvent): Shape {
  const at = e.activity_type || '';
  if (at === 'pr_merged')
    return {
      label: 'Merged',
      color: '#C084FC',
      bgGradient: 'linear-gradient(180deg, #1A132A 0, #12141B 100%)',
      icon: <PRIcon color="#C084FC" />,
    };
  if (at === 'pr_opened')
    return {
      label: 'PR opened',
      color: '#7FD38E',
      bgGradient: 'linear-gradient(180deg, #14231A 0, #12141B 100%)',
      icon: <PRIcon color="#4ADE80" />,
    };
  if (at === 'pr_closed') return { label: 'PR closed', color: '#F87171', icon: <PRIcon color="#F87171" /> };
  if (at === 'commit_linked') return { label: 'Commit', color: '#878A98', icon: <CommitIcon /> };
  if (at === 'comment') return { label: 'Comment', color: '#878A98', icon: <CommentIcon /> };
  if (at === 'created') return { label: 'Created', color: '#6EA0F5', icon: <Dot color="#6EA0F5" /> };
  if (at.startsWith('status_')) return { label: 'Status', color: '#6EA0F5', icon: <Dot color="#6EA0F5" /> };
  return { label: 'Event', color: '#878A98', icon: <Dot /> };
}

function title(e: PulseEvent) {
  const meta = (e.metadata || {}) as any;
  if (e.activity_type === 'commit_linked') {
    const sha = (meta.commit_sha as string)?.slice(0, 7) || '';
    return `${sha} · ${(e.description || '').replace(/^Commit linked:\s*\w+\s*-\s*/, '')}`;
  }
  if (e.activity_type === 'comment') return `"${e.description}"`;
  return e.description;
}

function secondary(e: PulseEvent) {
  const meta = (e.metadata || {}) as any;
  if (e.activity_type === 'commit_linked') return meta.author ? `@${meta.author}` : '';
  if (e.kind === 'comment') return `on LIN-${e.issue_key}`;
  if (e.activity_type?.startsWith('pr_')) return `${meta.pr_number ? '#' + meta.pr_number + ' · ' : ''}LIN-${e.issue_key}`;
  return `LIN-${e.issue_key}`;
}

export function ProjectPulse({ projectId }: { projectId: string }) {
  const [events, setEvents] = useState<PulseEvent[]>([]);
  const [filter, setFilter] = useState<'all' | 'issues' | 'prs' | 'commits' | 'comments'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    axios
      .get(`${API_URL}/projects/${projectId}/pulse?limit=30`)
      .then((r) => {
        if (alive) setEvents(r.data.events || []);
      })
      .catch(() => alive && setEvents([]))
      .finally(() => alive && setLoading(false));
    // Refresh every 30s — cheap.
    const t = setInterval(() => {
      axios
        .get(`${API_URL}/projects/${projectId}/pulse?limit=30`)
        .then((r) => alive && setEvents(r.data.events || []))
        .catch(() => {});
    }, 30_000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [projectId]);

  const filtered = events.filter((e) => {
    if (filter === 'all') return true;
    if (filter === 'prs') return e.activity_type?.startsWith('pr_');
    if (filter === 'commits') return e.activity_type === 'commit_linked';
    if (filter === 'comments') return e.activity_type === 'comment';
    if (filter === 'issues')
      return e.activity_type === 'created' || e.activity_type?.startsWith('status_');
    return true;
  });

  return (
    <div className="mb-8 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-gray-600">Pulse</span>
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.6)]" />
          <span className="text-[11px] text-gray-500">live</span>
        </div>
        <div className="flex items-center gap-4 text-[11px] font-medium">
          {(['all', 'issues', 'prs', 'commits', 'comments'] as const).map((k) => (
            <button
              key={k}
              onClick={() => setFilter(k)}
              className={filter === k ? 'text-gray-200' : 'text-gray-600 hover:text-gray-400'}
            >
              {k === 'all' ? 'All' : k[0].toUpperCase() + k.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-2.5 overflow-x-auto pb-1">
        {loading && !events.length ? (
          <div className="py-6 text-center text-sm text-gray-500">Loading recent events…</div>
        ) : filtered.length === 0 ? (
          <div className="py-6 text-center text-sm text-gray-500">No recent events.</div>
        ) : (
          filtered.slice(0, 12).map((e) => <PulseCard key={e.id} event={e} />)
        )}
      </div>
    </div>
  );
}

function PulseCard({ event }: { event: PulseEvent }) {
  const s = shapeFor(event);
  return (
    <div
      className="flex w-[230px] flex-shrink-0 flex-col gap-1.5 rounded-lg border border-gray-800 p-3"
      style={{ background: s.bgGradient || '#12141B' }}
    >
      <div className="flex items-center gap-1.5">
        {s.icon}
        <span
          className="text-[10px] font-semibold uppercase tracking-[0.05em]"
          style={{ color: s.color }}
        >
          {s.label}
        </span>
        <span className="ml-auto font-mono text-[10px] text-gray-600">{relative(event.created_at)}</span>
      </div>
      <div className="truncate text-[12px] leading-4 text-gray-200">{title(event)}</div>
      <div className="text-[11px] text-gray-500">{secondary(event)}</div>
    </div>
  );
}

function PRIcon({ color }: { color: string }) {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5">
      <circle cx="18" cy="18" r="3" />
      <circle cx="6" cy="6" r="3" />
      <path d="M6 21V9a9 9 0 009 9" />
    </svg>
  );
}

function CommitIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#878A98" strokeWidth="2">
      <circle cx="12" cy="12" r="4" />
      <path d="M1.05 12H8m8 0h7" strokeLinecap="round" />
    </svg>
  );
}

function CommentIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#878A98" strokeWidth="2">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  );
}

function Dot({ color = '#878A98' }: { color?: string }) {
  return <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: color }} />;
}
