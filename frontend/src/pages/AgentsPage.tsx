// ABOUTME: Agents list — registered agents, live session, pending proposal counts.

import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL } from '../App';

interface Agent {
  id: string;
  slug: string;
  display_name: string;
  model: string | null;
  specialty: string | null;
  color: string | null;
  is_active: boolean;
  last_seen_at: string | null;
}

interface Session {
  id: string;
  status: string;
  current_task: string | null;
  current_target: string | null;
  last_seen_at: string;
  agent_slug: string;
  color: string | null;
}

interface PendingProposal {
  id: string;
  agent_slug: string | null;
  urgency: string;
}

function rel(iso: string | null) {
  if (!iso) return 'never';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.max(1, Math.round(diff / 60_000));
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}

export function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [pending, setPending] = useState<PendingProposal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    const load = () =>
      Promise.all([
        axios.get(`${API_URL}/agents`).then((r) => r.data.agents || []),
        axios.get(`${API_URL}/agents/presence`).then((r) => r.data.sessions || []),
        axios.get(`${API_URL}/proposals/pending`).then((r) => r.data.proposals || []),
      ]).then(([a, s, p]) => {
        if (!alive) return;
        setAgents(a);
        setSessions(s);
        setPending(p);
        setLoading(false);
      });
    load();
    const t = setInterval(load, 20_000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  return (
    <div className="mx-auto max-w-[960px] px-4">
      <header className="mb-8">
        <h1 className="mb-1 text-[28px] font-semibold tracking-tight text-gray-50">Agents</h1>
        <p className="text-sm text-gray-500">
          Everyone working with you. Agents register themselves when they first propose an action — you don't add them manually.
        </p>
      </header>

      {loading ? (
        <div className="py-14 text-center text-sm text-gray-500">Loading…</div>
      ) : agents.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-800 bg-[#272931] p-14 text-center">
          <div className="mb-2 text-sm text-gray-300">No agents yet.</div>
          <div className="text-[12px] text-gray-500">
            Point an agent's <span className="font-mono text-gray-400">LINEARY_API_KEY</span> at this instance and have it call{' '}
            <span className="font-mono text-gray-400">POST /api/proposals</span> — it'll show up here on its first request.
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {agents.map((a) => {
            const session = sessions.find((s) => s.agent_slug === a.slug);
            const count = pending.filter((p) => p.agent_slug === a.slug).length;
            const urgent = pending.filter((p) => p.agent_slug === a.slug && p.urgency === 'urgent').length;
            return <AgentRow key={a.id} agent={a} session={session} pending={count} urgent={urgent} />;
          })}
        </div>
      )}
    </div>
  );
}

function AgentRow({
  agent,
  session,
  pending,
  urgent,
}: {
  agent: Agent;
  session: Session | undefined;
  pending: number;
  urgent: number;
}) {
  const color = agent.color || '#6EA0F5';
  return (
    <div className="flex items-center gap-4 rounded-xl border border-gray-800 bg-[#2B2D36] px-5 py-4">
      <div
        className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg"
        style={{ background: `${color}22`, border: `1px solid ${color}55` }}
      >
        <AgentGlyph specialty={agent.specialty} color={color} />
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <div className="flex flex-wrap items-baseline gap-2">
          <span className="text-[14px] font-semibold text-gray-100">{agent.display_name}</span>
          <span className="font-mono text-[11px]" style={{ color }}>
            {agent.model || 'unknown'}
          </span>
          {agent.specialty ? (
            <span className="rounded border border-gray-800 px-1.5 py-[1px] text-[10px] uppercase tracking-wider text-gray-400">
              {agent.specialty}
            </span>
          ) : null}
        </div>
        <div className="flex items-center gap-2 text-[12px] text-gray-500">
          {session ? (
            <>
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: color, boxShadow: `0 0 5px ${color}80` }} />
              <span>{session.current_task || session.status}</span>
              {session.current_target ? (
                <span className="font-mono text-[#F59E0B]">{session.current_target}</span>
              ) : null}
            </>
          ) : (
            <>
              <span className="h-1.5 w-1.5 rounded-full bg-gray-700" />
              <span>idle</span>
              <span>· last seen {rel(agent.last_seen_at)}</span>
            </>
          )}
        </div>
      </div>

      <div className="flex flex-shrink-0 items-center gap-5">
        <div className="flex flex-col items-end leading-tight">
          <span className="font-mono text-[15px] font-medium text-gray-200">{pending}</span>
          <span className="text-[10px] uppercase tracking-[0.05em] text-gray-600">proposals</span>
        </div>
        {urgent > 0 ? (
          <div className="flex flex-col items-end leading-tight">
            <span className="font-mono text-[15px] font-medium text-[#F87171]">{urgent}</span>
            <span className="text-[10px] uppercase tracking-[0.05em] text-[#F87171]">urgent</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function AgentGlyph({ specialty, color }: { specialty: string | null; color: string }) {
  if (specialty === 'qa')
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    );
  if (specialty === 'planner' || specialty === 'docs')
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
        <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" />
        <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
      </svg>
    );
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
      <rect x="4" y="8" width="16" height="12" rx="2" />
      <path d="M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2M12 14v2" />
    </svg>
  );
}
