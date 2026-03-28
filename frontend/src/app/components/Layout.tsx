import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Server, Network, BarChart2, Settings, Shield, LogOut, ShieldCheck,
  Menu, X, ChevronRight, Activity, Wifi, Moon, Sun, AlertCircle
} from 'lucide-react';

export function getNavItems(userRole: string | undefined) {
  const items = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/alerts', label: 'Alerts', icon: AlertCircle },
    { path: '/devices', label: 'Devices', icon: Server },
    { path: '/topology', label: 'Topology', icon: Network },
    { path: '/metrics', label: 'Metrics', icon: BarChart2 },
  ];

  if (userRole === 'admin') {
    items.push({ path: '/admin', label: 'Admin', icon: ShieldCheck });
  }

  items.push({ path: '/settings', label: 'Settings', icon: Settings });
  return items;
}



export function Layout({ theme, onToggleTheme }: { theme: 'dark' | 'light'; onToggleTheme: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const NavItem = ({ path, label, icon: Icon }: { path: string; label: string; icon: React.ElementType }) => (
    <NavLink
      to={path}
      onClick={() => setSidebarOpen(false)}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
          isActive
            ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
            : 'text-slate-400 hover:text-slate-100 hover:bg-white/5'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-cyan-400' : ''}`} />
          <span className="text-sm">{label}</span>
          {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto text-cyan-400" />}
        </>
      )}
    </NavLink>
  );

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0">
          <Activity className="w-4.5 h-4.5 text-white" />
        </div>
        <div>
          <div className="text-white font-semibold tracking-wide text-base">NEXORA</div>
          <div className="text-slate-500 text-xs">Observability Platform</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="text-xs text-slate-600 font-medium uppercase tracking-wider px-3 mb-2">Navigation</div>
        {getNavItems(user?.role).map(item => <NavItem key={item.path} {...item} />)}
      </nav>

      {/* User / Bottom */}
      <div className="px-3 py-4 border-t border-white/5 space-y-2">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/3">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-medium">
              {(user?.username || user?.email || 'U').charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm text-slate-200 truncate">{user?.username || user?.email}</div>
            <div className="text-xs text-slate-500 capitalize">{user?.role}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all text-sm"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </div>
  );

  return (
    <div className={`flex h-screen overflow-hidden ${theme === 'dark' ? 'dark' : ''}`} style={{ background: theme === 'dark' ? '#080d1a' : '#f1f5f9' }}>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-56 xl:w-60 flex-col flex-shrink-0" style={{ background: theme === 'dark' ? '#0c1225' : '#1e293b' }}>
        {sidebarContent}
      </aside>

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <aside className="relative w-64 flex flex-col" style={{ background: '#0c1225' }}>
            <button className="absolute top-4 right-4 text-slate-400 hover:text-white" onClick={() => setSidebarOpen(false)}>
              <X className="w-5 h-5" />
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between px-4 md:px-6 py-3 border-b flex-shrink-0"
          style={{ background: theme === 'dark' ? '#0c1225' : '#1e293b', borderColor: 'rgba(255,255,255,0.05)' }}>
          <button className="lg:hidden text-slate-400 hover:text-white" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 lg:gap-0">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-slate-400">System Online</span>
            </div>
          </div>
          <button
            onClick={onToggleTheme}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all"
          >
            {theme === 'dark' ? <Sun className="w-4.5 h-4.5" /> : <Moon className="w-4.5 h-4.5" />}
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
