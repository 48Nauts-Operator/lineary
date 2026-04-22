// ABOUTME: Recent activity feed — vertical list, clickable rows, not a carousel.
// ABOUTME: Shows the "did anything happen since I last looked?" glance.

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
  icon: React.ReactNode;
};

function shapeFor(e: PulseEvent): Shape {
  const at = e.activity_type || '';
  if (at === 'pr_merged') return { label: 'merged', color: '#F59E0B', icon: <PRIcon color="#F59E0B" /> };
  if (at === 'pr_opened') return { label: 'opened PR', color: '#4ADE80', icon: <PRIcon color="#4ADE80" /> };
  if (at === 'pr_closed') return { label: 'closed PR', color: '#F87171', icon: <PRIcon color="#F87171" /> };
  if (at === 'commit_linked') return { label: 'committed', color: '#878A98', icon: <CommitIcon /> };
  if (at === 'comment') return { label: 'commented', color: '#878A98', icon: <CommentIcon /> };
  if (at === 'created') return { label: 'opened', color: '#6EA0F5', icon: <Dot color="#6EA0F5" /> };
  if (at.startsWith('status_')) return { label: 'moved', color: '#6EA0F5', icon: <Dot color="#6EA0F5" /> };
  return { label: 'event', color: '#878A98', icon: <Dot /> };
}

function eventTitle(e: PulseEvent): string {
  const meta = (e.metadata || {}) as any;
  if (e.activity_type === 'commit_linked') {
    const sha = (meta.commit_sha as string)?.slice(0, 7) || '';
    const msg = (e.description || '').replace(/^Commit linked:\s*\w+\s*-\s*/, '');
    return `${sha} — ${msg}`;
  }
  if (e.activity_type === 'comment') {
    return `"${e.description.length > 90 ? e.description.slice(0, 90) + '…' : e.description}"`;
  }
  if (e.activity_type?.startsWith('pr_')) {
    const n = meta.pr_number;
    const title = (e.description || '').replace(/^Pull Request #\d+ \S+:\s*/, '');
    return `${n ? `#${n} ` : ''}${title}`;
  }
  return e.description;
}

function eventActor(e: PulseEvent): string {
  const meta = (e.metadata || {}) as any;
  if (e.kind === 'comment' && e.user_id) return e.user_id;
  if (e.activity_type === 'commit_linked' && meta.author) return meta.author;
  if (e.activity_type?.startsWith('pr_') && (meta.merged_by || meta.author))
    return meta.merged_by || meta.author;
  return '';
}

interface Props {
  projectId: string;
  onOpenIssue?: (issueId: string) => void;
  compact?: boolean; // small-variant for tight layouts
}

export function ProjectPulse({ projectId, onOpenIssue, compact = false }: Props) {
  const [events, setEvents] = useState<PulseEvent[]>([]);
  const [filter, setFilter] = useState<'all' | 'issues' | 'prs' | 'commits' | 'comments'>('all');
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () =>
      axios
        .get(`${API_URL}/projects/${projectId}/pulse?limit=30`)
        .then((r) => alive && setEvents(r.data.events || []))
        .catch(() => alive && setEvents([]))
        .finally(() => alive && setLoading(false));
    load();
    const t = setInterval(load, 30_000);
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

  const visible = expanded ? filtered : filtered.slice(0, compact ? 5 : 6);

  return (
    <div className="mb-8 flex flex-col gap-2.5">
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

      <div className="overflow-hidden rounded-lg border border-gray-800 bg-[#272931]">
        {loading && events.length === 0 ? (
          <div className="py-6 text-center text-sm text-gray-500">Loading…</div>
        ) : visible.length === 0 ? (
          <div className="py-6 text-center text-sm text-gray-500">Nothing happening yet.</div>
        ) : (
          visible.map((e, i) => (
            <PulseRow
              key={e.id}
              event={e}
              last={i === visible.length - 1}
              onClick={() => onOpenIssue?.(e.issue_id)}
            />
          ))
        )}
      </div>

      {filtered.length > visible.length && !expanded ? (
        <button
          onClick={() => setExpanded(true)}
          className="self-start text-[11px] font-medium text-gray-500 hover:text-gray-300"
        >
          Show {filtered.length - visible.length} more events →
        </button>
      ) : expanded && filtered.length > 6 ? (
        <button
          onClick={() => setExpanded(false)}
          className="self-start text-[11px] font-medium text-gray-500 hover:text-gray-300"
        >
          Collapse
        </button>
      ) : null}
    </div>
  );
}

function PulseRow({
  event,
  last,
  onClick,
}: {
  event: PulseEvent;
  last: boolean;
  onClick: () => void;
}) {
  const s = shapeFor(event);
  const actor = eventActor(event);
  return (
    <button
      onClick={onClick}
      className={`group flex w-full items-center gap-3 px-4 py-2.5 text-left hover:bg-[#151823] ${
        last ? '' : 'border-b border-gray-800/60'
      }`}
    >
      <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center">{s.icon}</div>
      <span
        className="w-[78px] flex-shrink-0 text-[11px] font-semibold uppercase tracking-wider"
        style={{ color: s.color }}
      >
        {s.label}
      </span>
      <span className="min-w-0 flex-1 truncate text-[13px] text-gray-200 group-hover:text-white">
        {eventTitle(event)}
      </span>
      {actor ? (
        <span className="flex-shrink-0 text-[11px] text-gray-500">@{actor}</span>
      ) : null}
      <span className="flex-shrink-0 font-mono text-[11px] text-gray-600">{relative(event.created_at)}</span>
    </button>
  );
}

function PRIcon({ color }: { color: string }) {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5">
      <circle cx="18" cy="18" r="3" />
      <circle cx="6" cy="6" r="3" />
      <path d="M6 21V9a9 9 0 009 9" />
    </svg>
  );
}

function CommitIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#878A98" strokeWidth="2">
      <circle cx="12" cy="12" r="4" />
      <path d="M1.05 12H8m8 0h7" strokeLinecap="round" />
    </svg>
  );
}

function CommentIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#878A98" strokeWidth="2">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  );
}

function Dot({ color = '#878A98' }: { color?: string }) {
  return <span className="inline-block h-2 w-2 rounded-full" style={{ background: color }} />;
}
