import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { Activity, Eye, EyeOff, AlertCircle, Loader2, UserPlus, X } from 'lucide-react';
import { authAPI, usersAPI } from '../api/api';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Register modal state
  const [showRegister, setShowRegister] = useState(false);
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [regLoading, setRegLoading] = useState(false);
  const [regError, setRegError] = useState('');
  const [regSuccess, setRegSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) { setError('Please enter both username and password.'); return; }
    setLoading(true);
    setError('');
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regEmail || !regPassword) { setRegError('Please enter email and password.'); return; }
    if (regPassword !== regConfirmPassword) { setRegError('Passwords do not match.'); return; }
    if (regPassword.length < 4) { setRegError('Password must be at least 4 characters.'); return; }

    setRegLoading(true);
    setRegError('');
    try {
      await usersAPI.register(regEmail, regPassword);
      setRegSuccess(true);
      setTimeout(() => {
        setShowRegister(false);
        setRegSuccess(false);
        setRegEmail('');
        setRegPassword('');
        setRegConfirmPassword('');
      }, 2000);
    } catch (err) {
      setRegError(err instanceof Error ? err.message : 'Registration failed. Try a different email.');
    } finally {
      setRegLoading(false);
    }
  };

  const fillDemo = (u: string, p: string) => { setUsername(u); setPassword(p); };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #080d1a 0%, #0c1525 50%, #060b16 100%)' }}>
      {/* Background decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #06b6d4, transparent)' }} />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #3b82f6, transparent)' }} />
        {/* Grid */}
        <div className="absolute inset-0 opacity-5"
          style={{ backgroundImage: 'linear-gradient(rgba(6,182,212,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(6,182,212,0.3) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white tracking-wide">NEXORA</div>
            <div className="text-xs text-cyan-400/80 tracking-widest uppercase">Observability Platform</div>
          </div>
        </div>

        {/* Card */}
        <div className="rounded-2xl border p-8 shadow-2xl"
          style={{ background: 'rgba(12,18,37,0.9)', backdropFilter: 'blur(20px)', borderColor: 'rgba(255,255,255,0.08)' }}>
          <h1 className="text-xl text-white mb-1" style={{ fontWeight: 600 }}>Sign In</h1>
          <p className="text-slate-400 text-sm mb-6">Enter your credentials to access the platform</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-300 mb-1.5">Username / Email</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="admin@nexora"
                className="w-full px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 border outline-none transition-all focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30"
                style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
                autoComplete="username"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 pr-10 rounded-lg text-sm text-white placeholder-slate-500 border outline-none transition-all focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30"
                  style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="remember"
                checked={rememberMe}
                onChange={e => setRememberMe(e.target.checked)}
                className="w-4 h-4 accent-cyan-500"
              />
              <label htmlFor="remember" className="text-sm text-slate-400 cursor-pointer">Remember me</label>
            </div>

            {error && (
              <div className="flex items-start gap-2.5 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20">
                <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg text-sm font-medium text-white transition-all flex items-center justify-center gap-2 disabled:opacity-60"
              style={{ background: 'linear-gradient(135deg, #06b6d4, #3b82f6)' }}
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Signing in...</> : 'Sign In'}
            </button>
          </form>

          {/* Register Button */}
          <div className="mt-4">
            <button
              type="button"
              onClick={() => setShowRegister(true)}
              className="w-full py-2.5 rounded-lg text-sm font-medium text-cyan-400 border border-cyan-500/30 transition-all flex items-center justify-center gap-2 hover:bg-cyan-500/10"
            >
              <UserPlus className="w-4 h-4" />
              Create New Account
            </button>
          </div>

          {/* Demo credentials */}
          <div className="mt-6 pt-5 border-t" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
            <p className="text-xs text-slate-500 mb-3 text-center">Demo credentials (click to fill)</p>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => fillDemo('admin@nexora', 'admin')}
                className="px-3 py-2 rounded-lg text-xs text-slate-300 border transition-all hover:border-cyan-500/50 hover:text-cyan-400"
                style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)' }}
              >
                <div className="font-medium">Admin</div>
                <div className="text-slate-500">admin@nexora</div>
              </button>
              <button
                onClick={() => fillDemo('viewer@nexora', 'viewer')}
                className="px-3 py-2 rounded-lg text-xs text-slate-300 border transition-all hover:border-cyan-500/50 hover:text-cyan-400"
                style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)' }}
              >
                <div className="font-medium">Viewer</div>
                <div className="text-slate-500">viewer@nexora</div>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Register Modal */}
      {showRegister && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border shadow-2xl"
            style={{ background: '#0c1225', borderColor: 'rgba(255,255,255,0.1)' }}>
            <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                  <UserPlus className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h2 className="text-white">Create Account</h2>
                  <p className="text-xs text-slate-500">Register a new user</p>
                </div>
              </div>
              <button onClick={() => setShowRegister(false)} className="text-slate-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleRegister} className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1.5">Email</label>
                <input
                  type="email"
                  value={regEmail}
                  onChange={e => setRegEmail(e.target.value)}
                  placeholder="user@nexora"
                  className="w-full px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 border outline-none focus:border-cyan-500"
                  style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1.5">Password</label>
                <input
                  type="password"
                  value={regPassword}
                  onChange={e => setRegPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 border outline-none focus:border-cyan-500"
                  style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1.5">Confirm Password</label>
                <input
                  type="password"
                  value={regConfirmPassword}
                  onChange={e => setRegConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 border outline-none focus:border-cyan-500"
                  style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
                />
              </div>
              {regError && <p className="text-sm text-red-400">{regError}</p>}
              {regSuccess && <p className="text-sm text-emerald-400">Account created successfully!</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowRegister(false)}
                  className="flex-1 py-2.5 rounded-lg text-sm text-slate-400 border border-white/10 hover:border-white/20 transition-all">
                  Cancel
                </button>
                <button type="submit" disabled={regLoading}
                  className="flex-1 py-2.5 rounded-lg text-sm text-white transition-all flex items-center justify-center gap-2 disabled:opacity-60"
                  style={{ background: 'linear-gradient(135deg, #06b6d4, #3b82f6)' }}>
                  {regLoading ? <><Loader2 className="w-4 h-4 animate-spin" />Creating...</> : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
