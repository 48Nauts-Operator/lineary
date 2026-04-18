import { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface Props {
  projectId: string;
  projectName: string;
  onClose: () => void;
  onSelected: (mode: 'mcp_only' | 'github') => void;
}

export function ProjectModeDialog({ projectId, projectName, onClose, onSelected }: Props) {
  const [busy, setBusy] = useState(false);

  const pick = async (mode: 'mcp_only' | 'github') => {
    setBusy(true);
    try {
      await axios.patch(`/api/projects/${projectId}`, { mode });
      onSelected(mode);
      if (mode === 'github') {
        // Open the GitHub App install flow in a new tab.
        const r = await axios.get(`/api/github/install-url`, { params: { projectId } });
        if (r.data?.url) window.open(r.data.url, '_blank', 'noopener');
      } else {
        toast.success('Project configured for MCP-only workflow');
        onClose();
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'Failed to set project mode');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-xl border border-gray-800 bg-gray-950 p-6 text-gray-100 shadow-xl">
        <h2 className="mb-1 text-xl font-semibold">How do you want to use {projectName}?</h2>
        <p className="mb-6 text-sm text-gray-400">
          Choose once. You can reconfigure in project settings later.
        </p>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => pick('mcp_only')}
            className="group rounded-lg border border-gray-800 bg-gray-900 p-5 text-left transition-colors hover:border-purple-500 hover:bg-gray-900/80 disabled:opacity-50"
          >
            <div className="mb-3 flex items-center gap-2">
              <svg className="h-5 w-5 text-purple-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span className="font-medium">MCP only</span>
            </div>
            <p className="text-sm text-gray-400">
              Agents create and manage issues directly via MCP. No external sync. Best for AI-first workflows.
            </p>
          </button>

          <button
            type="button"
            disabled={busy}
            onClick={() => pick('github')}
            className="group rounded-lg border border-gray-800 bg-gray-900 p-5 text-left transition-colors hover:border-blue-500 hover:bg-gray-900/80 disabled:opacity-50"
          >
            <div className="mb-3 flex items-center gap-2">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 .297C5.373.297 0 5.67 0 12.297c0 5.302 3.438 9.8 8.207 11.387.6.113.82-.258.82-.577 0-.285-.011-1.04-.017-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.744.083-.729.083-.729 1.205.084 1.838 1.237 1.838 1.237 1.07 1.834 2.809 1.304 3.495.997.108-.775.419-1.305.762-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.468-2.382 1.236-3.222-.124-.303-.535-1.523.117-3.176 0 0 1.008-.322 3.3 1.23a11.5 11.5 0 013.003-.404c1.018.005 2.045.138 3.003.404 2.29-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.873.118 3.176.77.84 1.235 1.912 1.235 3.222 0 4.61-2.804 5.625-5.475 5.92.43.37.814 1.102.814 2.222 0 1.604-.015 2.896-.015 3.286 0 .322.218.697.825.577C20.565 22.093 24 17.595 24 12.297 24 5.67 18.627.297 12 .297" />
              </svg>
              <span className="font-medium">GitHub-connected</span>
            </div>
            <p className="text-sm text-gray-400">
              Install the Lineary GitHub App on a repo. Issues, PRs, and comments sync both ways. Agents, humans, and GitHub all see the same state.
            </p>
          </button>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 disabled:opacity-50"
          >
            Decide later
          </button>
        </div>
      </div>
    </div>
  );
}
