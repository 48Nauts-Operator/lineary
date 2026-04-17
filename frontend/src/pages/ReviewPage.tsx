// ABOUTME: AI-first Review queue — proposals from agents awaiting human attention.
// ABOUTME: Renders a live-now strip + proposal cards with Approve/Intervene actions.

import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { API_URL } from '../App';

interface Proposal {
  id: string;
  project_id: string;
  project_name: string;
  agent_id: string | null;
  agent_name: string | null;
  agent_slug: string | null;
  agent_model: string | null;
  agent_specialty: string | null;
  agent_color: string | null;
  kind: string;
  target_issue_id: string | null;
  target_label: string | null;
  issue_title: string | null;
  issue_status: string | null;
  issue_key: string | null;
  github_issue_number: number | null;
  payload: Record<string, unknown>;
  reasoning: string | null;
  confidence: number | null;
  blast_radius: 'low' | 'medium' | 'high';
  urgency: 'urgent' | 'normal' | 'low';
  status: string;
  auto_approve_at: string | null;
  created_at: string;
}

interface Session {
  id: string;
  status: 'active' | 'idle' | 'waiting' | 'finished';
  current_task: string | null;
  current_target: string | null;
  started_at: string;
  last_seen_at: string;
  agent_slug: string;
  agent_name: string;
  model: string | null;
  specialty: string | null;
  color: string | null;
  project_id: string | null;
  project_name: string | null;
}

function rel(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.max(1, Math.round(diff / 60_000));
  if (m < 60) return `${m}m`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ${Math.round(m - h * 60)}m`.replace(' 0m', '');
  return `${Math.round(h / 24)}d`;
}

function untilFn(iso: string) {
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return null;
  const m = Math.round(diff / 60_000);
  if (m < 60) return `${m}m`;
  const h = Math.round(m / 60);
  return `${h}h ${Math.max(0, m - h * 60)}m`.replace(' 0m', '');
}

export function ReviewPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'urgent' | 'mine'>('all');

  const refresh = useCallback(async () => {
    try {
      const [pRes, sRes] = await Promise.all([
        axios.get(`${API_URL}/proposals/pending`),
        axios.get(`${API_URL}/agents/presence`),
      ]);
      setProposals(pRes.data.proposals || []);
      setSessions(sRes.data.sessions || []);
    } catch {
      // Errors land through the global response interceptor.
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15_000);
    return () => clearInterval(t);
  }, [refresh]);

  const act = async (id: string, action: 'approve' | 'intervene', response?: string) => {
    try {
      await axios.post(`${API_URL}/proposals/${id}/${action}`, { response });
      setProposals((prev) => prev.filter((p) => p.id !== id));
      toast.success(action === 'approve' ? 'Approved — agent proceeding' : 'Intervention sent');
    } catch {
      toast.error(`Failed to ${action}`);
    }
  };

  const urgentCount = proposals.filter((p) => p.urgency === 'urgent').length;
  const filtered = proposals.filter((p) => {
    if (filter === 'urgent') return p.urgency === 'urgent';
    return true;
  });

  const autoApplied24h = 0; // populated later when we track resolution audit

  return (
    <div className="mx-auto max-w-[960px] px-4">
      <LiveStrip sessions={sessions} autoApplied24h={autoApplied24h} />

      <header className="mb-6 flex items-start justify-between gap-6">
        <div>
          <h1 className="mb-1 text-[28px] font-semibold tracking-tight text-gray-50">Needs your attention</h1>
          <p className="text-sm text-gray-500">
            {proposals.length > 0
              ? `${proposals.length} proposal${proposals.length === 1 ? '' : 's'} · ${urgentCount} urgent. Everything else the agents handled for you.`
              : `All clear. Agents will flag anything that needs your call.`}
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-gray-800 bg-[#12141B] p-1">
          {(['all', 'urgent', 'mine'] as const).map((k) => (
            <button
              key={k}
              onClick={() => setFilter(k)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium ${
                filter === k ? 'bg-[#1D2030] text-gray-100' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {k === 'all' ? 'All' : k[0].toUpperCase() + k.slice(1)}{' '}
              <span className={filter === k ? 'text-gray-500' : 'text-gray-700'}>
                {k === 'all' ? proposals.length : k === 'urgent' ? urgentCount : 0}
              </span>
            </button>
          ))}
        </div>
      </header>

      {loading ? (
        <div className="py-20 text-center text-sm text-gray-500">Loading…</div>
      ) : filtered.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex flex-col gap-3.5">
          {filtered.map((p) => (
            <ProposalCard key={p.id} proposal={p} onAct={act} />
          ))}
        </div>
      )}
    </div>
  );
}

function LiveStrip({ sessions, autoApplied24h }: { sessions: Session[]; autoApplied24h: number }) {
  const active = sessions.filter((s) => s.status !== 'finished');
  return (
    <div className="-mx-4 mb-10 flex items-center gap-5 overflow-hidden border-b border-gray-800 bg-[#0F1117] px-6 py-2.5">
      <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-gray-600">Live</span>
      {active.length === 0 ? (
        <span className="text-[12px] text-gray-600">No agents active right now.</span>
      ) : (
        active.slice(0, 4).map((s, i) => (
          <div key={s.id} className="flex items-center gap-2.5">
            {i > 0 && <div className="h-3.5 w-px bg-gray-800" />}
            <div
              className="flex h-[22px] w-[22px] items-center justify-center rounded-md"
              style={{
                background: s.color ? `${s.color}22` : '#1A2235',
                border: `1px solid ${s.color ? `${s.color}55` : '#2A3A55'}`,
              }}
            >
              <AgentGlyph specialty={s.specialty} color={s.color || '#6EA0F5'} />
            </div>
            <span className="text-[12px] font-medium text-gray-300">{s.agent_name || s.agent_slug}</span>
            <span className="text-[12px] text-gray-500">{s.current_task || s.status}</span>
            {s.current_target ? (
              <span className="font-mono text-[12px] text-[#9B8CFF]">{s.current_target}</span>
            ) : null}
            <span className="font-mono text-[11px] text-gray-600">{rel(s.last_seen_at)}</span>
          </div>
        ))
      )}
      <div className="ml-auto text-[11px] text-gray-600">
        {autoApplied24h > 0 ? `${autoApplied24h} actions auto-applied last 24h` : ''}
      </div>
    </div>
  );
}

function AgentGlyph({ specialty, color }: { specialty: string | null; color: string }) {
  // Simple specialty-driven glyph; all at 11px.
  if (specialty === 'qa')
    return (
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    );
  if (specialty === 'planner' || specialty === 'docs')
    return (
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
        <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" />
        <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
      </svg>
    );
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
      <rect x="4" y="8" width="16" height="12" rx="2" />
      <path d="M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2M12 14v2" />
    </svg>
  );
}

function ProposalCard({
  proposal,
  onAct,
}: {
  proposal: Proposal;
  onAct: (id: string, action: 'approve' | 'intervene', response?: string) => void;
}) {
  const { kind } = proposal;
  if (kind === 'ask_question') return <AskCard p={proposal} onAct={onAct} />;
  if (kind === 'merge_pr') return <MergeCard p={proposal} onAct={onAct} />;
  if (kind === 'split_issue') return <SplitCard p={proposal} onAct={onAct} />;
  return <CompactCard p={proposal} onAct={onAct} />;
}

function Confidence({ value, size = 'md' }: { value: number | null; size?: 'sm' | 'md' | 'lg' }) {
  if (typeof value !== 'number') return null;
  const pct = Math.round(value * 100);
  const color = pct >= 90 ? '#4ADE80' : pct >= 70 ? '#E8C055' : '#F87171';
  const fontSize = size === 'lg' ? '20px' : size === 'md' ? '15px' : '13px';
  return (
    <div className="flex flex-col items-end leading-tight">
      <span className="font-mono font-medium" style={{ fontSize, color }}>
        {pct}%
      </span>
      {size === 'lg' ? (
        <span className="text-[10px] uppercase tracking-[0.05em] text-gray-600">confidence</span>
      ) : null}
    </div>
  );
}

function AgentLine({ p }: { p: Proposal }) {
  return (
    <div className="flex items-center gap-3">
      <div
        className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg"
        style={{
          background: p.agent_color ? `${p.agent_color}22` : '#1A2235',
          border: `1px solid ${p.agent_color ? `${p.agent_color}55` : '#2A3A55'}`,
        }}
      >
        <AgentGlyph specialty={p.agent_specialty} color={p.agent_color || '#6EA0F5'} />
      </div>
      <div className="flex flex-col gap-0.5">
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-semibold text-gray-200">{p.agent_name || p.agent_slug || 'agent'}</span>
          {p.agent_model ? (
            <span className="font-mono text-[11px]" style={{ color: p.agent_color || '#6EA0F5' }}>
              {p.agent_model}
            </span>
          ) : null}
        </div>
        <span className="text-[12px] text-gray-500">{verb(p)}</span>
      </div>
    </div>
  );
}

function verb(p: Proposal) {
  switch (p.kind) {
    case 'merge_pr':
      return 'proposes to merge a pull request';
    case 'close_issue':
      return 'proposes to close';
    case 'split_issue':
      return 'proposes to split this into sub-issues';
    case 'ask_question':
      return 'asks about';
    case 'create_issue':
      return 'proposes to create a new issue';
    case 'update_issue':
      return 'proposes to update';
    default:
      return p.kind;
  }
}

function targetLabel(p: Proposal) {
  if (p.issue_key) return `LIN-${p.issue_key}`;
  if (p.target_label) return p.target_label;
  return '';
}

function MergeCard({
  p,
  onAct,
}: {
  p: Proposal;
  onAct: (id: string, action: 'approve' | 'intervene', response?: string) => void;
}) {
  const urgent = p.urgency === 'urgent';
  const pr = (p.payload as any) || {};
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-[#12141B]">
      <div
        className="flex items-center gap-3 border-b border-gray-800 px-5 py-3"
        style={{ background: urgent ? 'linear-gradient(90deg,#2A1F15 0%,#12141B 60%)' : undefined }}
      >
        <div
          className="h-1.5 w-1.5 rounded-full"
          style={{ background: urgent ? '#F87171' : '#9B8CFF', boxShadow: urgent ? '0 0 6px rgba(248,113,113,0.5)' : undefined }}
        />
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em]" style={{ color: urgent ? '#F87171' : '#9B8CFF' }}>
          {urgent ? 'Urgent · needs approval' : 'Needs approval'}
        </span>
        <span className="text-[12px] text-gray-500">
          {p.blast_radius === 'high' ? 'High blast radius' : p.blast_radius === 'medium' ? 'Medium risk' : 'Low risk'}
        </span>
        <span className="ml-auto font-mono text-[11px] text-gray-500">{rel(p.created_at)} waiting</span>
      </div>

      <div className="flex flex-col gap-3.5 px-5 pt-5 pb-4">
        <div className="flex items-center">
          <AgentLine p={p} />
          <div className="ml-auto">
            <Confidence value={p.confidence} size="lg" />
          </div>
        </div>

        {pr.pr_number || p.issue_title ? (
          <div className="flex items-center gap-2.5 rounded-lg border border-gray-800 bg-[#0F1117] p-3.5">
            {pr.pr_number ? (
              <span className="font-mono text-sm font-medium text-[#9B8CFF]">#{pr.pr_number}</span>
            ) : null}
            <span className="text-sm font-medium text-gray-200">{pr.title || p.issue_title}</span>
            {pr.diff_stats ? (
              <span className="ml-auto font-mono text-[11px] text-gray-500">{pr.diff_stats}</span>
            ) : null}
          </div>
        ) : null}

        {p.reasoning ? <div className="text-[13px] leading-5 text-gray-300">"{p.reasoning}"</div> : null}
      </div>

      <div className="flex items-center gap-2.5 border-t border-gray-800 bg-[#0F1117] px-5 py-3">
        <Btn>Read reasoning</Btn>
        <div className="ml-auto" />
        <Btn onClick={() => onAct(p.id, 'intervene')}>Intervene</Btn>
        <BtnPrimary onClick={() => onAct(p.id, 'approve')} accent="#4ADE80">
          Approve &amp; merge
        </BtnPrimary>
      </div>
    </div>
  );
}

function AskCard({
  p,
  onAct,
}: {
  p: Proposal;
  onAct: (id: string, action: 'approve' | 'intervene', response?: string) => void;
}) {
  const options = ((p.payload as any)?.options as string[]) || [];
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-[#12141B]">
      <div
        className="flex items-center gap-3 border-b border-gray-800 px-5 py-3"
        style={{ background: 'linear-gradient(90deg,#2D1F15 0%,#12141B 60%)' }}
      >
        <div className="h-1.5 w-1.5 rounded-full" style={{ background: '#F97316', boxShadow: '0 0 6px rgba(249,115,22,0.5)' }} />
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#F97316]">
          Agent paused · needs your input
        </span>
        <span className="ml-auto font-mono text-[11px] text-gray-500">{rel(p.created_at)} waiting</span>
      </div>

      <div className="flex flex-col gap-3.5 px-5 pt-5 pb-4">
        <div className="flex items-center gap-3">
          <AgentLine p={p} />
          <span className="text-sm text-gray-500">
            {targetLabel(p)}
            {p.issue_title ? ` · ${p.issue_title}` : ''}
          </span>
        </div>
        {p.reasoning ? (
          <div className="rounded-r-lg border-l-2 border-[#F97316] bg-[#0F1117] p-4 text-[14px] leading-[22px] text-gray-200">
            "{p.reasoning}"
          </div>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-gray-800 bg-[#0F1117] px-5 py-3">
        {options.slice(0, 3).map((opt) => (
          <button
            key={opt}
            onClick={() => onAct(p.id, 'intervene', opt)}
            className="rounded-md border border-gray-700 bg-[#1D1F28] px-3.5 py-1.5 text-[12px] font-medium text-gray-100 hover:bg-[#232636]"
          >
            {opt}
          </button>
        ))}
        <button
          onClick={() => {
            const r = prompt('Your answer to the agent:');
            if (r != null) onAct(p.id, 'intervene', r);
          }}
          className="rounded-md border border-gray-800 px-3.5 py-1.5 text-[12px] font-medium text-gray-400 hover:text-gray-200"
        >
          Write a nuanced answer
        </button>
        <button
          onClick={() => onAct(p.id, 'intervene', '__cancel__')}
          className="ml-auto text-[12px] font-medium text-gray-500 hover:text-gray-300"
        >
          Cancel the issue
        </button>
      </div>
    </div>
  );
}

function SplitCard({
  p,
  onAct,
}: {
  p: Proposal;
  onAct: (id: string, action: 'approve' | 'intervene', response?: string) => void;
}) {
  const subIssues = ((p.payload as any)?.sub_issues as { title: string; hint?: string }[]) || [];
  const auto = p.auto_approve_at ? untilFn(p.auto_approve_at) : null;
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-[#12141B]">
      <div className="flex items-center gap-3 border-b border-gray-800 px-5 py-3">
        <div className="h-1.5 w-1.5 rounded-full bg-[#9B8CFF]" />
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#9B8CFF]">Planning · low risk</span>
        {auto ? <span className="text-[12px] text-gray-500">Will be auto-approved in {auto} unless you intervene</span> : null}
        <span className="ml-auto font-mono text-[11px] text-gray-500">{rel(p.created_at)} waiting</span>
      </div>
      <div className="flex flex-col gap-3 px-5 pt-5 pb-3">
        <div className="flex items-center">
          <AgentLine p={p} />
          <div className="ml-auto">
            <Confidence value={p.confidence} />
          </div>
        </div>
        {p.reasoning ? <div className="text-[13px] leading-5 text-gray-300">"{p.reasoning}"</div> : null}
        {subIssues.length > 0 ? (
          <div className="flex flex-col rounded-lg border border-gray-800 bg-[#0F1117] p-3">
            {subIssues.map((s, i) => (
              <div
                key={i}
                className={`flex items-center gap-3 py-1.5 ${i < subIssues.length - 1 ? 'border-b border-dashed border-gray-800' : ''}`}
              >
                <span className="w-10 font-mono text-[11px] text-gray-600">new</span>
                <span className="flex-1 text-[13px] text-gray-200">{s.title}</span>
                {s.hint ? <span className="text-[11px] text-gray-500">{s.hint}</span> : null}
              </div>
            ))}
          </div>
        ) : null}
      </div>
      <div className="flex items-center gap-2.5 border-t border-gray-800 bg-[#0F1117] px-5 py-3">
        <Btn>Preview full spec</Btn>
        <div className="ml-auto" />
        <Btn onClick={() => onAct(p.id, 'intervene', 'keep_as_one')}>Keep as one</Btn>
        <Btn onClick={() => onAct(p.id, 'intervene')}>Intervene</Btn>
        <BtnPrimary onClick={() => onAct(p.id, 'approve')} accent="#C8A8FF">
          Approve split
        </BtnPrimary>
      </div>
    </div>
  );
}

function CompactCard({
  p,
  onAct,
}: {
  p: Proposal;
  onAct: (id: string, action: 'approve' | 'intervene', response?: string) => void;
}) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-gray-800 bg-[#12141B] px-5 py-4">
      <div
        className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg"
        style={{
          background: p.agent_color ? `${p.agent_color}22` : '#1A2235',
          border: `1px solid ${p.agent_color ? `${p.agent_color}55` : '#2A3A55'}`,
        }}
      >
        <AgentGlyph specialty={p.agent_specialty} color={p.agent_color || '#6EA0F5'} />
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex flex-wrap items-baseline gap-2 text-[13px]">
          <span className="font-semibold text-gray-200">{p.agent_name || p.agent_slug || 'agent'}</span>
          {p.agent_model ? (
            <span className="font-mono text-[11px]" style={{ color: p.agent_color || '#6EA0F5' }}>
              {p.agent_model}
            </span>
          ) : null}
          <span className="text-gray-500">{verb(p)}</span>
          {targetLabel(p) ? <span className="font-mono text-[12px] font-medium text-[#9B8CFF]">{targetLabel(p)}</span> : null}
          {p.issue_title ? <span className="text-gray-300">{p.issue_title}</span> : null}
        </div>
        {p.reasoning ? <div className="text-[12px] leading-[18px] text-gray-500">{p.reasoning}</div> : null}
      </div>
      <div className="flex flex-shrink-0 items-center gap-3">
        <Confidence value={p.confidence} size="sm" />
        <div className="font-mono text-[10px] text-gray-600">{rel(p.created_at)}</div>
        <Btn onClick={() => onAct(p.id, 'intervene')}>Intervene</Btn>
        <BtnPrimary onClick={() => onAct(p.id, 'approve')} accent="#4ADE80">
          Approve
        </BtnPrimary>
      </div>
    </div>
  );
}

function Btn({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="rounded-md border border-gray-800 px-3.5 py-1.5 text-[12px] font-medium text-gray-300 hover:bg-gray-800"
    >
      {children}
    </button>
  );
}

function BtnPrimary({ children, onClick, accent }: { children: React.ReactNode; onClick?: () => void; accent: string }) {
  const dim = accent + '22';
  const br = accent + '66';
  return (
    <button
      onClick={onClick}
      className="rounded-md border px-4 py-1.5 text-[12px] font-semibold"
      style={{ background: dim, borderColor: br, color: accent }}
    >
      {children}
    </button>
  );
}

function EmptyState() {
  return (
    <div className="rounded-xl border border-dashed border-gray-800 bg-[#0F1117] p-14 text-center">
      <div className="mb-2 text-sm text-gray-400">All clear.</div>
      <div className="text-[12px] text-gray-600">
        Agents are working. You'll see a proposal here when they need your call — merges, splits, or questions.
      </div>
    </div>
  );
}
