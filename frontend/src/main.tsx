import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { StackProvider, StackHandler, StackTheme } from '@stackframe/react'
import App from './App.tsx'
import { stackApp } from './auth/stack'
import { RequireAuth } from './auth/RequireAuth'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 30000,
    },
  },
})

function HandlerRoutes() {
  return (
    <Suspense fallback={<div className="p-6 text-gray-300">Loading...</div>}>
      <StackHandler app={stackApp} location={window.location.pathname} fullPage />
    </Suspense>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <StackProvider app={stackApp}>
          <StackTheme>
            <Routes>
              <Route path="/handler/*" element={<HandlerRoutes />} />
              <Route
                path="*"
                element={
                  <RequireAuth>
                    <App />
                  </RequireAuth>
                }
              />
            </Routes>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: 'rgba(17, 24, 39, 0.9)',
                  color: '#f9fafb',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                },
              }}
            />
          </StackTheme>
        </StackProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
