import React, { useState, createContext, useContext } from 'react';
import { createBrowserRouter, Navigate } from 'react-router';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { DevicesPage } from './pages/DevicesPage';

import { TopologyPage } from './pages/TopologyPage';
import { MetricsPage } from './pages/MetricsPage';
import { SettingsPage } from './pages/SettingsPage';

import { useAuth } from './context/AuthContext';

// ─── Theme Context ────────────────────────────────────────────────────────────

interface ThemeCtx { theme: 'dark' | 'light'; toggleTheme: () => void; }
const ThemeContext = createContext<ThemeCtx>({ theme: 'dark', toggleTheme: () => {} });
export const useTheme = () => useContext(ThemeContext);

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'dark' | 'light'>(() =>
    (localStorage.getItem('nexora_theme') as 'dark' | 'light') || 'dark'
  );
  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('nexora_theme', next);
  };
  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>;
}

// ─── Guards ───────────────────────────────────────────────────────────────────

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#080d1a' }}>
      <div className="text-center space-y-4">
        <div className="w-10 h-10 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 text-sm">Loading NEXORA...</p>
      </div>
    </div>
  );
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}



// ─── Wrappers ─────────────────────────────────────────────────────────────────

function AppLayout() {
  const { theme, toggleTheme } = useTheme();
  return (
    <RequireAuth>
      <Layout theme={theme} onToggleTheme={toggleTheme} />
    </RequireAuth>
  );
}

function SettingsWrapper() {
  const { theme, toggleTheme } = useTheme();
  return <SettingsPage theme={theme} onToggleTheme={toggleTheme} />;
}

// Root wraps everything with ThemeProvider so AppLayout + all Outlet children share one theme context
function Root() {
  return (
    <ThemeProvider>
      <AppLayout />
    </ThemeProvider>
  );
}

// ─── Router ───────────────────────────────────────────────────────────────────

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <Root />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'devices', element: <DevicesPage /> },

      { path: 'topology', element: <TopologyPage /> },
      { path: 'metrics', element: <MetricsPage /> },
      { path: 'settings', element: <SettingsWrapper /> },

      { path: '*', element: <Navigate to="/dashboard" replace /> },
    ],
  },
]);
