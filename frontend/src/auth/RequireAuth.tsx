import { useEffect, useRef } from 'react';
import { useUser } from '@stackframe/react';
import axios from 'axios';

interface Props {
  children: React.ReactNode;
}

export function RequireAuth({ children }: Props) {
  const user = useUser({ or: 'redirect' });
  const claimed = useRef(false);

  useEffect(() => {
    if (!user || claimed.current) return;
    claimed.current = true;
    // Claim any orphaned (pre-auth) projects for this user on first sign-in.
    axios.post('/api/auth/claim-orphans').catch(() => {
      // Non-fatal — projects may already be owned or the user is new.
    });
  }, [user]);

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-gray-100">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 mx-auto animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <p className="text-sm text-gray-400">Signing you in...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
