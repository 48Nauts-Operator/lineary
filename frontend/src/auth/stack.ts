import { StackClientApp } from '@stackframe/react';

const projectId = import.meta.env.VITE_STACK_PROJECT_ID as string | undefined;

if (!projectId) {
  // eslint-disable-next-line no-console
  console.error('[stack-auth] Missing VITE_STACK_PROJECT_ID — auth will not work. Create frontend/.env.');
}

export const stackApp = new StackClientApp({
  projectId: projectId ?? 'missing',
  tokenStore: 'cookie',
  urls: {
    signIn: '/handler/sign-in',
    signUp: '/handler/sign-up',
    afterSignIn: '/',
    afterSignUp: '/',
    afterSignOut: '/handler/sign-in',
  },
});
