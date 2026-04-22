import { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
}

export function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [name, setName] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  const copyKey = async () => {
    if (!newKey) return;
    try {
      await navigator.clipboard.writeText(newKey);
      setCopied(true);
      toast.success('Copied');
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error('Copy failed');
    }
  };

  const load = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/auth/keys');
      setKeys(res.data);
    } catch {
      toast.error('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const create = async () => {
    if (!name.trim()) return toast.error('Give the key a name');
    try {
      const res = await axios.post('/api/auth/keys', { name });
      setNewKey(res.data.key);
      setName('');
      load();
    } catch {
      toast.error('Failed to create key');
    }
  };

  const revoke = async (id: string) => {
    if (!confirm('Revoke this key? Any MCP client using it will break.')) return;
    try {
      await axios.delete(`/api/auth/keys/${id}`);
      toast.success('Revoked');
      load();
    } catch {
      toast.error('Failed to revoke');
    }
  };

  return (
    <div className="mx-auto max-w-3xl p-6 text-gray-100">
      <h2 className="mb-4 text-xl font-semibold">API Keys</h2>
      <p className="mb-6 text-sm text-gray-400">
        Use API keys to authenticate MCP servers and other agents against Lineary. Send the key as{' '}
        <code className="rounded bg-gray-800 px-1">X-API-Key</code>.
      </p>

      {newKey && (
        <div className="mb-6 rounded border border-green-700 bg-green-900/30 p-4">
          <div className="mb-2 text-sm font-medium text-green-200">Copy this key now — it won't be shown again.</div>
          <div className="flex items-center gap-2">
            <code className="flex-1 break-all rounded bg-black/40 p-2 text-sm text-green-100">{newKey}</code>
            <button
              onClick={copyKey}
              className="flex-shrink-0 rounded-md bg-[#C2410C] px-3 py-2 text-xs font-medium text-white hover:bg-[#D97706]"
            >
              {copied ? '✓ Copied' : 'Copy'}
            </button>
          </div>
          <button className="mt-2 text-xs text-green-200 underline" onClick={() => setNewKey(null)}>
            Dismiss
          </button>
        </div>
      )}

      <div className="mb-6 flex gap-2">
        <input
          className="flex-1 rounded border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
          placeholder="Key name (e.g., My MacBook MCP)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="rounded bg-blue-600 px-4 py-2 text-sm hover:bg-blue-500"
          onClick={create}
        >
          Generate key
        </button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-400">Loading...</div>
      ) : keys.length === 0 ? (
        <div className="rounded border border-gray-800 p-4 text-sm text-gray-400">No API keys yet.</div>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-800 text-gray-400">
            <tr>
              <th className="py-2">Name</th>
              <th>Prefix</th>
              <th>Created</th>
              <th>Last used</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {keys.map((k) => (
              <tr key={k.id} className="border-b border-gray-800/50">
                <td className="py-3">{k.name}</td>
                <td className="font-mono text-xs text-gray-300">{k.key_prefix}...</td>
                <td className="text-gray-400">{new Date(k.created_at).toLocaleDateString()}</td>
                <td className="text-gray-400">
                  {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : '—'}
                </td>
                <td className="text-right">
                  {k.revoked_at ? (
                    <span className="text-xs text-red-400">revoked</span>
                  ) : (
                    <button
                      className="text-xs text-red-400 hover:text-red-300"
                      onClick={() => revoke(k.id)}
                    >
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
