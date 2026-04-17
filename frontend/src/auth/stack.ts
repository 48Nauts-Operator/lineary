import { StackClientApp } from '@stackframe/react';
import axios from 'axios';

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

// Exported so other axios instances (like `api` in services/api.ts) can attach
// the same logic. Applied to the axios singleton below so every bare
// `axios.get/post` throughout the app carries the Bearer token automatically.
export const attachBearer = async (config: any) => {
  try {
    const user = await stackApp.getUser();
    if (user) {
      const { accessToken } = await user.getAuthJson();
      if (accessToken) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
    }
  } catch {
    // No session yet — the request will 401 and the response interceptor redirects.
  }
  return config;
};

axios.interceptors.request.use(attachBearer);

axios.interceptors.response.use(
  (r) => r,
  (error) => {
    if (
      error?.response?.status === 401 &&
      typeof window !== 'undefined' &&
      !window.location.pathname.startsWith('/handler/')
    ) {
      window.location.href = '/handler/sign-in';
    }
    return Promise.reject(error);
  }
);
