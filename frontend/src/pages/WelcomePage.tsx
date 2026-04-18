// ABOUTME: First-login onboarding — starter project, one-time API key,
// ABOUTME: prefilled Claude Desktop config. Single page, one button out.

import { useState } from 'react';
import toast from 'react-hot-toast';

interface WelcomeKit {
  user: { name: string; email: string };
  project: { id: string; name: string; slug: string };
  api_key: { raw: string; name: string; prefix: string };
}

interface Props {
  kit: WelcomeKit;
  onDone: () => void;
}

export function WelcomePage({ kit, onDone }: Props) {
  const apiUrl =
    typeof window !== 'undefined'
      ? `${window.location.origin.replace(/:3399$/, ':3134')}/api`
      : 'http://localhost:3134/api';

  const mcpConfig = JSON.stringify(
    {
      mcpServers: {
        lineary: {
          command: 'python3',
          args: ['/ABSOLUTE/PATH/TO/lineary-mcp-server.py'],
          env: {
            LINEARY_API_URL: apiUrl,
            LINEARY_API_KEY: kit.api_key.raw,
          },
        },
      },
    },
    null,
    2
  );

  return (
    <div className="min-h-screen bg-[#0D0E12] text-gray-100">
      <div className="mx-auto max-w-[760px] px-6 py-16">
        <header className="mb-12">
          <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-500">
            Welcome to Lineary
          </div>
          <h1 className="mb-2 text-[34px] font-semibold leading-tight tracking-tight text-gray-50">
            Hey {kit.user.name} — you're in.
          </h1>
          <p className="text-[15px] leading-relaxed text-gray-400">
            I've set up a starter project, an API key for your first agent, and the config you need to connect
            Claude Desktop (or any MCP client). Three sections below, then you're done.
          </p>
        </header>

        <Section
          number="1"
          title="Your starter project"
          detail="Empty by design — it's a sandbox. Rename or delete it whenever you like."
        >
          <div className="flex items-center gap-3 rounded-lg border border-gray-800 bg-[#12141B] p-4">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-[#9B8CFF] text-[16px] font-bold text-[#0D0E12]">
              M
            </div>
            <div className="flex flex-1 flex-col">
              <span className="text-[14px] font-medium text-gray-100">{kit.project.name}</span>
              <span className="font-mono text-[11px] text-gray-500">project_id: {kit.project.id}</span>
            </div>
            <CopyBtn value={kit.project.id} label="Copy ID" />
          </div>
        </Section>

        <Section
          number="2"
          title="Your first API key"
          detail="Shown once — never stored in plaintext. Copy it now; you can always mint more in Account later."
        >
          <div className="flex items-center gap-3 rounded-lg border border-[#3A2F4E] bg-[#1A132A] p-4">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C8A8FF" strokeWidth="2" className="flex-shrink-0">
              <circle cx="12" cy="16" r="1" />
              <rect x="3" y="10" width="18" height="12" rx="2" />
              <path d="M7 10V7a5 5 0 0110 0v3" />
            </svg>
            <code className="flex-1 break-all font-mono text-[13px] text-[#C8A8FF]">{kit.api_key.raw}</code>
            <CopyBtn value={kit.api_key.raw} label="Copy key" primary />
          </div>
        </Section>

        <Section
          number="3"
          title="Connect your agent"
          detail={
            <>
              Replace <span className="font-mono text-gray-400">/ABSOLUTE/PATH/TO/lineary-mcp-server.py</span>{' '}
              with where you cloned the Lineary repo on this machine.
            </>
          }
        >
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3 rounded-lg border border-gray-800 bg-[#12141B] p-4">
              <div className="flex-1">
                <div className="mb-1 text-[12px] text-gray-400">
                  <span className="font-mono text-gray-500">~/Library/Application Support/Claude/claude_desktop_config.json</span>
                </div>
                <pre className="overflow-auto rounded bg-[#0D0E12] p-3 font-mono text-[12px] leading-[18px] text-gray-300">
{mcpConfig}
                </pre>
              </div>
            </div>
            <div className="flex items-center justify-between gap-3">
              <div className="text-[12px] text-gray-500">
                After pasting: fully quit Claude Desktop and reopen. Your agent will auto-register on its first
                call.
              </div>
              <CopyBtn value={mcpConfig} label="Copy config" />
            </div>
          </div>
        </Section>

        <footer className="mt-14 flex items-center justify-between border-t border-gray-800 pt-8">
          <div className="text-[12px] text-gray-500">
            You can come back to all of this from <span className="text-gray-300">Account</span>.
          </div>
          <button
            onClick={onDone}
            className="rounded-md bg-[#7B61FF] px-6 py-2.5 text-[13px] font-semibold text-white hover:bg-[#8B71FF]"
          >
            Open Lineary →
          </button>
        </footer>
      </div>
    </div>
  );
}

function Section({
  number,
  title,
  detail,
  children,
}: {
  number: string;
  title: string;
  detail: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-10">
      <div className="mb-3 flex items-baseline gap-3">
        <span className="font-mono text-[12px] text-gray-600">0{number}</span>
        <h2 className="text-[18px] font-semibold text-gray-100">{title}</h2>
      </div>
      <p className="mb-4 text-[13px] leading-relaxed text-gray-500">{detail}</p>
      {children}
    </section>
  );
}

function CopyBtn({ value, label, primary }: { value: string; label: string; primary?: boolean }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
          toast.success('Copied');
          setTimeout(() => setCopied(false), 1500);
        } catch {
          toast.error('Copy failed');
        }
      }}
      className={`flex-shrink-0 rounded-md px-3 py-1.5 text-[12px] font-medium ${
        primary
          ? 'bg-[#7B61FF] text-white hover:bg-[#8B71FF]'
          : 'border border-gray-800 text-gray-300 hover:bg-gray-800'
      }`}
    >
      {copied ? '✓' : label}
    </button>
  );
}
