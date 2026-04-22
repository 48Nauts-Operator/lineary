// ABOUTME: AI-era operations metrics — proposal resolution, auto-approve
// ABOUTME: hit rate, human intervention rate, merges, agent activity.

import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL } from '../App';

interface Summary {
  window_days: number;
  proposals: { pending: number; approved: number; intervened: number; expired: number; resolved: number };
  auto_approve_hit_rate: number | null;
  human_intervention_rate: number | null;
  auto_approved_count: number;
  issues_closed: number;
  prs_merged: number;
  agents: { total: number; active_now: number };
}

interface SeriesDay {
  day: string;
  approvals: number;
  interventions: number;
  merges: number;
}

export function OperationsPage() {
  const [days, setDays] = useState<7 | 30>(7);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [series, setSeries] = useState<SeriesDay[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([
      axios.get(`${API_URL}/operations/summary?days=${days}`).then((r) => r.data as Summary),
      axios.get(`${API_URL}/operations/timeseries?days=${days * 2}`).then((r) => r.data.series as SeriesDay[]),
    ])
      .then(([s, t]) => {
        if (!alive) return;
        setSummary(s);
        setSeries(t);
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [days]);

  return (
    <div className="mx-auto max-w-[1000px] px-4">
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="mb-1 text-[28px] font-semibold tracking-tight text-gray-50">Operations</h1>
          <p className="text-sm text-gray-500">
            What the tool has been doing for you. Not team velocity — that was the old world.
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-gray-800 bg-[#2B2D36] p-1">
          {([7, 30] as const).map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium ${
                days === d ? 'bg-[#1D2030] text-gray-100' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              Last {d} days
            </button>
          ))}
        </div>
      </header>

      {loading || !summary ? (
        <div className="py-14 text-center text-sm text-gray-500">Loading…</div>
      ) : (
        <>
          <div className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric
              label="Proposals resolved"
              value={summary.proposals.resolved}
              hint={`${summary.proposals.pending} still pending`}
            />
            <Metric
              label="Auto-approve hit rate"
              value={pct(summary.auto_approve_hit_rate)}
              hint={`${summary.auto_approved_count} auto-applied`}
              tone="good"
            />
            <Metric
              label="Human intervention rate"
              value={pct(summary.human_intervention_rate)}
              hint={`${summary.proposals.intervened} redirected`}
              tone={summary.human_intervention_rate !== null && summary.human_intervention_rate > 0.3 ? 'warn' : 'neutral'}
            />
            <Metric
              label="Agents"
              value={summary.agents.total}
              hint={`${summary.agents.active_now} active now`}
            />
          </div>

          <div className="mb-8 grid grid-cols-2 gap-3">
            <Metric label="Issues closed" value={summary.issues_closed} big />
            <Metric label="PRs merged" value={summary.prs_merged} big />
          </div>

          <section className="rounded-xl border border-gray-800 bg-[#2B2D36] p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-[14px] font-semibold text-gray-200">Activity by day</h2>
              <Legend />
            </div>
            <DailyBars series={series} />
          </section>
        </>
      )}
    </div>
  );
}

function pct(v: number | null): string {
  if (v == null) return '—';
  return `${Math.round(v * 100)}%`;
}

function Metric({
  label,
  value,
  hint,
  tone = 'neutral',
  big = false,
}: {
  label: string;
  value: number | string;
  hint?: string;
  tone?: 'neutral' | 'good' | 'warn';
  big?: boolean;
}) {
  const color =
    tone === 'good' ? '#7FD38E' : tone === 'warn' ? '#C2410C' : '#F3F3F7';
  return (
    <div className="flex flex-col gap-1.5 rounded-xl border border-gray-800 bg-[#2B2D36] p-5">
      <span
        className="font-semibold tracking-tight"
        style={{ color, fontSize: big ? '36px' : '26px' }}
      >
        {value}
      </span>
      <span className="text-[12px] text-gray-400">{label}</span>
      {hint ? <span className="text-[11px] text-gray-600">{hint}</span> : null}
    </div>
  );
}

function Legend() {
  return (
    <div className="flex items-center gap-4 text-[11px] text-gray-500">
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-2 w-2 rounded-sm bg-[#4ADE80]" /> approved
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-2 w-2 rounded-sm bg-[#C2410C]" /> intervened
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-2 w-2 rounded-sm bg-[#F59E0B]" /> merges
      </span>
    </div>
  );
}

function DailyBars({ series }: { series: SeriesDay[] }) {
  if (series.length === 0) {
    return <div className="py-6 text-center text-[12px] text-gray-500">No data yet.</div>;
  }
  const max = Math.max(1, ...series.map((d) => d.approvals + d.interventions + d.merges));
  return (
    <div className="flex items-end gap-[3px]">
      {series.map((d) => {
        const total = d.approvals + d.interventions + d.merges;
        const h = (v: number) => `${Math.round((v / max) * 80)}px`;
        return (
          <div key={d.day} title={`${d.day} — ${total} events`} className="flex w-full flex-1 flex-col items-center gap-1">
            <div className="flex w-full flex-col items-stretch gap-[1px]" style={{ height: '80px', justifyContent: 'flex-end' }}>
              {d.merges > 0 ? <div style={{ height: h(d.merges), background: '#F59E0B', borderRadius: '1px' }} /> : null}
              {d.interventions > 0 ? <div style={{ height: h(d.interventions), background: '#C2410C', borderRadius: '1px' }} /> : null}
              {d.approvals > 0 ? <div style={{ height: h(d.approvals), background: '#4ADE80', borderRadius: '1px' }} /> : null}
              {total === 0 ? <div style={{ height: '2px', background: '#3A3D47' }} /> : null}
            </div>
            <span className="font-mono text-[9px] text-gray-700">{d.day.slice(5)}</span>
          </div>
        );
      })}
    </div>
  );
}
