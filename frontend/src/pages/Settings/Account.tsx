import { useState } from 'react';
import { useUser } from '@stackframe/react';
import { ApiKeysPage } from './ApiKeys';
import { RunnersPage } from './Runners';

type Tab = 'profile' | 'keys' | 'runners';

export function AccountPage() {
  const user = useUser();
  const [tab, setTab] = useState<Tab>('profile');
  if (!user) return null;

  return (
    <div>
      <div className="mx-auto max-w-3xl px-6 pt-6">
        <div className="mb-4 flex items-center gap-5 border-b border-[#C2410C]/20 pb-2 text-[13px]">
          {(['profile', 'keys', 'runners'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`font-medium ${tab === t ? 'text-gray-50' : 'text-gray-400 hover:text-gray-200'}`}
            >
              {t === 'profile' ? 'Profile' : t === 'keys' ? 'API Keys' : 'Runners'}
            </button>
          ))}
        </div>
      </div>

      {tab === 'profile' && (
        <div className="mx-auto max-w-3xl p-6 text-gray-100">
          <div className="mb-6 rounded border border-gray-800 bg-gray-900 p-4 text-sm">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-300">{user.primaryEmail}</div>
                {user.displayName && <div className="text-gray-500">{user.displayName}</div>}
              </div>
              <button
                className="rounded border border-gray-700 px-3 py-1 text-xs hover:bg-gray-800"
                onClick={() => user.signOut()}
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}
      {tab === 'keys' && <ApiKeysPage />}
      {tab === 'runners' && <RunnersPage />}
    </div>
  );
}
