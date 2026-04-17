// ABOUTME: Linear-style issue detail — single scrollable stream with inline
// ABOUTME: comments, commits, PR cards, status events, and a composer.

import { useEffect, useState } from 'react';
import axios from 'axios';
import { Project, Issue, API_URL } from '../App';
import toast from 'react-hot-toast';

interface Props {
  issue: Issue;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
  projects: Project[];
}

interface Comment {
  id: string;
  content: string;
  user_id?: string;
  user_type?: 'human' | 'ai' | 'system';
  sync_origin?: 'lineary' | 'github' | null;
  github_comment_id?: number | null;
  created_at: string;
}

interface Activity {
  id: string;
  activity_type: string;
  description: string;
  user_type?: 'human' | 'ai' | 'system';
  metadata?: Record<string, unknown>;
  created_at: string;
}

type Entry =
  | ({ kind: 'comment' } & Comment)
  | ({ kind: 'activity' } & Activity);

function initials(name: string) {
  const s = (name || '').trim();
  if (!s) return '??';
  const parts = s.split(/\s+/);
  return (parts[0][0] + (parts[1]?.[0] || '')).toUpperCase();
}

function relativeTime(iso: string) {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diff = Math.max(0, now - then);
  const m = Math.round(diff / 60_000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.round(h / 24);
  return `${d}d ago`;
}

const STATUS_STYLE: Record<string, { bg: string; fg: string; border: string; dot: string; label: string }> = {
  backlog: { bg: '#1A1D28', fg: '#878A98', border: '#262832', dot: '#5A5D6E', label: 'Backlog' },
  todo: { bg: '#1A1D28', fg: '#878A98', border: '#262832', dot: '#878A98', label: 'To do' },
  in_progress: { bg: '#1F2A3A', fg: '#9FBCE8', border: '#253446', dot: '#6EA0F5', label: 'In progress' },
  in_review: { bg: '#2A1F3E', fg: '#C8A8FF', border: '#3A2F4E', dot: '#9B8CFF', label: 'In review' },
  done: { bg: '#1F2E1F', fg: '#7FD38E', border: '#2F4A2F', dot: '#34D399', label: 'Done' },
  cancelled: { bg: '#2A1F1F', fg: '#E88888', border: '#3A2828', dot: '#F87171', label: 'Cancelled' },
};

function statusStyle(status?: string) {
  return STATUS_STYLE[status || 'todo'] || STATUS_STYLE.todo;
}

export default function IssueStream({ issue, isOpen, onClose, onUpdate, projects }: Props) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);
  const [composer, setComposer] = useState('');
  const [posting, setPosting] = useState(false);

  const project = projects.find((p) => p.id === issue.project_id);
  const gitMode = project?.mode === 'github';
  const ghNumber = (issue as any).github_issue_number as number | null | undefined;

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    setLoading(true);
    Promise.all([
      axios.get(`${API_URL}/issues/${issue.id}/comments`).catch(() => ({ data: [] })),
      axios.get(`${API_URL}/issues/${issue.id}/activities`).catch(() => ({ data: [] })),
    ]).then(([cRes, aRes]) => {
      if (cancelled) return;
      const comments: Entry[] = (cRes.data || []).map((c: Comment) => ({ kind: 'comment' as const, ...c }));
      const activities: Entry[] = (aRes.data || []).map((a: Activity) => ({ kind: 'activity' as const, ...a }));
      const all = [...comments, ...activities].sort(
        (x, y) => new Date(x.created_at).getTime() - new Date(y.created_at).getTime()
      );
      setEntries(all);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [isOpen, issue.id]);

  const postComment = async () => {
    const body = composer.trim();
    if (!body) return;
    setPosting(true);
    try {
      await axios.post(`${API_URL}/issues/${issue.id}/comments`, { content: body });
      setComposer('');
      const res = await axios.get(`${API_URL}/issues/${issue.id}/comments`);
      setEntries((prev) => {
        const keptActivities = prev.filter((e) => e.kind === 'activity');
        const newComments: Entry[] = (res.data || []).map((c: Comment) => ({ kind: 'comment' as const, ...c }));
        return [...keptActivities, ...newComments].sort(
          (x, y) => new Date(x.created_at).getTime() - new Date(y.created_at).getTime()
        );
      });
      onUpdate();
    } catch {
      toast.error('Failed to post comment');
    } finally {
      setPosting(false);
    }
  };

  if (!isOpen) return null;

  const s = statusStyle(issue.status);

  return (
    <div className="fixed inset-0 z-50 flex justify-center overflow-auto bg-black/70 backdrop-blur-sm">
      <div className="relative my-10 w-[860px] rounded-xl border border-gray-800 bg-[#0D0E12] shadow-2xl">
        {/* top bar */}
        <div className="flex items-center justify-between border-b border-gray-800 px-8 py-3">
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>{project?.name || 'Project'}</span>
            <span className="text-gray-700">/</span>
            <span className="text-gray-300">Issues</span>
            <span className="text-gray-700">/</span>
            <span className="font-mono font-medium text-gray-200">{(issue as any).key || issue.id.slice(0, 7)}</span>
          </div>
          <button
            onClick={onClose}
            className="rounded-md px-2 py-1 text-gray-500 hover:bg-gray-800 hover:text-gray-300"
          >
            Close
          </button>
        </div>

        {/* header */}
        <div className="flex flex-col gap-4 border-b border-gray-800 px-8 pt-8 pb-5">
          <div className="flex items-center gap-3">
            <span
              className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider"
              style={{ background: s.bg, borderColor: s.border, color: s.fg }}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: s.dot }} />
              {s.label}
            </span>
            {gitMode && ghNumber ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-gray-800 bg-[#1A1D28] px-2.5 py-1 font-mono text-[11px] text-gray-400">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 .297C5.373.297 0 5.67 0 12.297c0 5.302 3.438 9.8 8.207 11.387.6.113.82-.258.82-.577 0-.285-.011-1.04-.017-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.744.083-.729.083-.729 1.205.084 1.838 1.237 1.838 1.237 1.07 1.834 2.809 1.304 3.495.997.108-.775.419-1.305.762-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.468-2.382 1.236-3.222-.124-.303-.535-1.523.117-3.176 0 0 1.008-.322 3.3 1.23a11.5 11.5 0 013.003-.404c1.018.005 2.045.138 3.003.404 2.29-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.873.118 3.176.77.84 1.235 1.912 1.235 3.222 0 4.61-2.804 5.625-5.475 5.92.43.37.814 1.102.814 2.222 0 1.604-.015 2.896-.015 3.286 0 .322.218.697.825.577C20.565 22.093 24 17.595 24 12.297 24 5.67 18.627.297 12 .297" />
                </svg>
                GH#{ghNumber}
              </span>
            ) : null}
            <span className="font-mono text-[11px] text-gray-600">
              Updated {relativeTime((issue as any).updated_at || issue.created_at)}
            </span>
          </div>
          <h1 className="text-[28px] font-semibold leading-9 tracking-tight text-gray-50">{issue.title}</h1>

          {/* meta strip */}
          <div className="flex flex-wrap items-center gap-5 pt-2 text-[13px] text-gray-400">
            <div className="flex items-center gap-2">
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#26283A] text-[9px] font-semibold text-gray-200">
                {initials((issue as any).assignee || 'Un')}
              </div>
              <span className="text-gray-300">{(issue as any).assignee || 'Unassigned'}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#878A98" strokeWidth="2">
                <path d="M12 2v20M5 9l7-7 7 7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="text-gray-300">{['Low', 'Low', 'Medium', 'High', 'Urgent'][(issue.priority || 3) - 1] || 'Medium'}</span>
            </div>
          </div>
        </div>

        {/* description */}
        {issue.description ? (
          <div className="border-b border-gray-800 px-8 py-5 text-[14px] leading-[22px] text-gray-300">
            {issue.description}
          </div>
        ) : null}

        {/* timeline */}
        <div className="relative px-8 py-4">
          <div className="pointer-events-none absolute bottom-6 left-[45px] top-6 w-px bg-gray-800" />
          {loading ? (
            <div className="py-8 text-center text-sm text-gray-500">Loading…</div>
          ) : entries.length === 0 ? (
            <div className="py-8 text-center text-sm text-gray-500">No activity yet.</div>
          ) : (
            entries.map((e) => <StreamEntry key={`${e.kind}:${e.id}`} entry={e} />)
          )}
        </div>

        {/* composer */}
        <div className="mx-8 mb-8 mt-4 rounded-xl border border-gray-800 bg-[#12141B] p-4">
          <div className="mb-2 text-[11px] text-gray-500">
            {gitMode && ghNumber ? (
              <>
                Reply — also posts to{' '}
                <span className="font-mono text-[#9B8CFF]">GH#{ghNumber}</span>
              </>
            ) : (
              <>Reply (agents and you can comment here)</>
            )}
          </div>
          <textarea
            className="w-full min-h-[56px] resize-none bg-transparent text-[14px] leading-[22px] text-gray-200 placeholder-gray-600 focus:outline-none"
            placeholder="Write a comment…"
            value={composer}
            onChange={(e) => setComposer(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') postComment();
            }}
          />
          <div className="mt-2 flex items-center justify-between">
            <span className="text-[11px] text-gray-600">Cmd+Enter to send</span>
            <button
              onClick={postComment}
              disabled={posting || !composer.trim()}
              className="rounded-md bg-[#7B61FF] px-4 py-1.5 text-[12px] font-semibold text-white disabled:opacity-40"
            >
              {posting ? 'Posting…' : 'Comment'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StreamEntry({ entry }: { entry: Entry }) {
  if (entry.kind === 'comment') return <EventComment entry={entry} />;
  const { activity_type } = entry;
  if (activity_type === 'commit_linked') return <EventCommit entry={entry} />;
  if (activity_type?.startsWith('pr_')) return <EventPR entry={entry} />;
  if (activity_type === 'created') return <EventCreated entry={entry} />;
  if (activity_type === 'status_changed') return <EventStatus entry={entry} />;
  return <EventGeneric entry={entry} />;
}

function LaneDot({ color = '#5A5D6E' }: { color?: string }) {
  return (
    <div className="z-10 flex h-[22px] w-[22px] flex-shrink-0 items-center justify-center rounded-full bg-[#0D0E12]">
      <div className="h-2 w-2 rounded-full" style={{ background: color }} />
    </div>
  );
}

function Avatar({ label, github }: { label: string; github?: boolean }) {
  return (
    <div className="relative z-10 flex h-[22px] w-[22px] flex-shrink-0 items-center justify-center rounded-full bg-[#26283A] text-[9px] font-semibold text-gray-200">
      {label.slice(0, 2).toUpperCase()}
      {github ? (
        <div className="absolute -right-0.5 -bottom-0.5 flex h-[12px] w-[12px] items-center justify-center rounded-full bg-[#0D0E12]">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="#878A98">
            <path d="M12 .297C5.373.297 0 5.67 0 12.297c0 5.302 3.438 9.8 8.207 11.387.6.113.82-.258.82-.577 0-.285-.011-1.04-.017-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.744.083-.729.083-.729 1.205.084 1.838 1.237 1.838 1.237 1.07 1.834 2.809 1.304 3.495.997.108-.775.419-1.305.762-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.468-2.382 1.236-3.222-.124-.303-.535-1.523.117-3.176 0 0 1.008-.322 3.3 1.23a11.5 11.5 0 013.003-.404c1.018.005 2.045.138 3.003.404 2.29-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.873.118 3.176.77.84 1.235 1.912 1.235 3.222 0 4.61-2.804 5.625-5.475 5.92.43.37.814 1.102.814 2.222 0 1.604-.015 2.896-.015 3.286 0 .322.218.697.825.577C20.565 22.093 24 17.595 24 12.297 24 5.67 18.627.297 12 .297" />
          </svg>
        </div>
      ) : null}
    </div>
  );
}

function EventCreated({ entry }: { entry: Entry & { kind: 'activity' } }) {
  return (
    <div className="flex items-center gap-3 py-2.5">
      <Avatar label="·" />
      <span className="flex-1 text-[13px] text-gray-400">{entry.description}</span>
      <span className="font-mono text-[11px] text-gray-600">{relativeTime(entry.created_at)}</span>
    </div>
  );
}

function EventStatus({ entry }: { entry: Entry & { kind: 'activity' } }) {
  return (
    <div className="flex items-center gap-3 py-2.5">
      <LaneDot color="#6EA0F5" />
      <span className="flex-1 text-[13px] text-gray-400">{entry.description}</span>
      <span className="font-mono text-[11px] text-gray-600">{relativeTime(entry.created_at)}</span>
    </div>
  );
}

function EventGeneric({ entry }: { entry: Entry & { kind: 'activity' } }) {
  return (
    <div className="flex items-center gap-3 py-2.5">
      <LaneDot />
      <span className="flex-1 text-[13px] text-gray-400">{entry.description}</span>
      <span className="font-mono text-[11px] text-gray-600">{relativeTime(entry.created_at)}</span>
    </div>
  );
}

function EventCommit({ entry }: { entry: Entry & { kind: 'activity' } }) {
  const meta = (entry.metadata as any) || {};
  const sha = (meta.commit_sha as string) || '';
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="z-10 flex h-[22px] w-[22px] flex-shrink-0 items-center justify-center rounded-full bg-[#0D0E12]">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#878A98" strokeWidth="2">
          <circle cx="12" cy="12" r="4" />
          <path d="M1.05 12H8m8 0h7" strokeLinecap="round" />
        </svg>
      </div>
      <span className="flex-shrink-0 font-mono text-[12px] font-medium text-[#9B8CFF]">{sha.slice(0, 7)}</span>
      <span className="flex-1 truncate text-[13px] text-gray-300">{entry.description}</span>
      {meta.author ? <span className="flex-shrink-0 text-[12px] text-gray-400">@{meta.author}</span> : null}
      <span className="flex-shrink-0 font-mono text-[11px] text-gray-600">{relativeTime(entry.created_at)}</span>
    </div>
  );
}

function EventPR({ entry }: { entry: Entry & { kind: 'activity' } }) {
  const meta = (entry.metadata as any) || {};
  const isMerge = entry.activity_type === 'pr_merged' || entry.activity_type === 'pr_closed';
  const accent = isMerge ? '#C084FC' : '#4ADE80';
  const bg = isMerge ? '#2A1F3E' : '#1F2E1F';
  const border = isMerge ? '#4A3970' : '#2F4A2F';
  const label = isMerge ? (entry.activity_type === 'pr_merged' ? 'Merged' : 'Closed') : 'Opened';
  return (
    <div className="flex items-start gap-3 py-3">
      <div
        className="z-10 flex h-[22px] w-[22px] flex-shrink-0 items-center justify-center rounded-full border"
        style={{ background: bg, borderColor: border }}
      >
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={accent} strokeWidth="2.5">
          <circle cx="18" cy="18" r="3" />
          <circle cx="6" cy="6" r="3" />
          <path d="M6 21V9a9 9 0 009 9" />
        </svg>
      </div>
      <div className="flex-1 rounded-lg border border-gray-800 bg-[#12141B] p-3">
        <div className="mb-1 flex items-center gap-2 text-[11px] text-gray-500">
          <span>PR {label.toLowerCase()}</span>
          <span className="font-mono text-[11px] text-gray-500">via GitHub</span>
          <span className="ml-auto font-mono">{relativeTime(entry.created_at)}</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {meta.pr_number ? (
            <a href={meta.pr_url || '#'} target="_blank" rel="noreferrer" className="font-mono text-[13px] font-medium text-[#9B8CFF]">
              #{meta.pr_number}
            </a>
          ) : null}
          <span className="text-[14px] font-medium text-gray-200">{entry.description.replace(/^Pull Request #\d+ \S+:\s*/, '')}</span>
          <span
            className="inline-block rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
            style={{ background: bg, borderColor: border, color: accent }}
          >
            {label}
          </span>
        </div>
      </div>
    </div>
  );
}

function EventComment({ entry }: { entry: Entry & { kind: 'comment' } }) {
  const isGithub = entry.sync_origin === 'github' || !!entry.github_comment_id;
  const author = entry.user_id || (isGithub ? 'github-user' : 'you');
  return (
    <div className="flex items-start gap-3 py-3">
      <Avatar label={initials(author)} github={isGithub} />
      <div className="flex flex-1 flex-col gap-1.5">
        <div className="flex items-baseline gap-2 text-[13px]">
          <span className="font-semibold text-gray-200">{author}</span>
          {isGithub ? <span className="text-[11px] text-gray-500">via GitHub</span> : null}
          <span className="font-mono text-[11px] text-gray-600">{relativeTime(entry.created_at)}</span>
        </div>
        <div className="whitespace-pre-wrap text-[14px] leading-[22px] text-gray-300">{entry.content}</div>
      </div>
    </div>
  );
}
