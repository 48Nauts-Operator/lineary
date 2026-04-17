import { useEffect, useState } from 'react';
import axios from 'axios';

interface Installation {
  installation_id: number;
  repo_owner: string;
  repo_name: string;
  sync_status: 'idle' | 'initial_syncing' | 'live' | 'error';
  sync_error: string | null;
  last_synced_at: string | null;
}

export function GitHubSyncBadge({ projectId }: { projectId: string }) {
  const [inst, setInst] = useState<Installation | null>(null);

  useEffect(() => {
    let mounted = true;
    axios
      .get(`/api/github/installations/${projectId}`)
      .then((r) => mounted && setInst(r.data))
      .catch(() => mounted && setInst(null));
    return () => {
      mounted = false;
    };
  }, [projectId]);

  if (!inst) return null;

  const color =
    inst.sync_status === 'live'
      ? 'bg-green-500'
      : inst.sync_status === 'error'
      ? 'bg-red-500'
      : 'bg-yellow-500';

  const label =
    inst.sync_status === 'live'
      ? 'Synced'
      : inst.sync_status === 'initial_syncing'
      ? 'Syncing...'
      : inst.sync_status === 'error'
      ? 'Sync error'
      : 'Idle';

  return (
    <span
      title={inst.sync_error || `${inst.repo_owner}/${inst.repo_name}`}
      className="inline-flex items-center gap-1.5 rounded-full border border-gray-700 bg-gray-800/70 px-2 py-0.5 text-xs text-gray-300"
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${color}`} />
      <svg className="h-3 w-3 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 .297C5.373.297 0 5.67 0 12.297c0 5.302 3.438 9.8 8.207 11.387.6.113.82-.258.82-.577 0-.285-.011-1.04-.017-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.744.083-.729.083-.729 1.205.084 1.838 1.237 1.838 1.237 1.07 1.834 2.809 1.304 3.495.997.108-.775.419-1.305.762-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.468-2.382 1.236-3.222-.124-.303-.535-1.523.117-3.176 0 0 1.008-.322 3.3 1.23a11.5 11.5 0 013.003-.404c1.018.005 2.045.138 3.003.404 2.29-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.873.118 3.176.77.84 1.235 1.912 1.235 3.222 0 4.61-2.804 5.625-5.475 5.92.43.37.814 1.102.814 2.222 0 1.604-.015 2.896-.015 3.286 0 .322.218.697.825.577C20.565 22.093 24 17.595 24 12.297 24 5.67 18.627.297 12 .297" />
      </svg>
      <span>
        {inst.repo_owner}/{inst.repo_name}
      </span>
      <span className="text-gray-500">· {label}</span>
    </span>
  );
}
