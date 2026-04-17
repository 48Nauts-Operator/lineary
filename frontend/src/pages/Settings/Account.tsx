import { useUser } from '@stackframe/react';
import { ApiKeysPage } from './ApiKeys';

export function AccountPage() {
  const user = useUser();
  if (!user) return null;

  return (
    <div>
      <div className="mx-auto max-w-3xl p-6 text-gray-100">
        <h2 className="mb-2 text-xl font-semibold">Account</h2>
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
      <ApiKeysPage />
    </div>
  );
}
