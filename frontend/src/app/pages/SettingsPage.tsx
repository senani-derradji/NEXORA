import React, { useState, useEffect } from 'react';
import { User, Lock, Save, Check, Eye, EyeOff, Loader2 } from 'lucide-react';
import { usersAPI } from '../api/api';
import { useAuth } from '../context/AuthContext';

interface SettingsPageProps {
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
      <div className="flex items-center gap-2 px-5 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="w-7 h-7 rounded-lg bg-cyan-500/10 flex items-center justify-center">
          <Icon className="w-4 h-4 text-cyan-400" />
        </div>
        <h3 className="text-slate-300">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-start py-3 border-b last:border-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
      <label className="text-sm text-slate-400 md:pt-2.5">{label}</label>
      <div className="md:col-span-2">{children}</div>
    </div>
  );
}

function Input({ value, onChange, type = 'text', placeholder, disabled }: {
  value: string; onChange?: (v: string) => void; type?: string; placeholder?: string; disabled?: boolean;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={e => onChange?.(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      className="w-full px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 border outline-none focus:border-cyan-500 transition-all disabled:opacity-50"
      style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
    />
  );
}

interface UserItem {
  id: number;
  email: string;
  username?: string;
  role: string;
}

export function SettingsPage({ theme, onToggleTheme }: SettingsPageProps) {
  const { user } = useAuth();

  const [profileSaved, setProfileSaved] = useState(false);
  const [pwdSaved, setPwdSaved] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [pwdLoading, setPwdLoading] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [pwdError, setPwdError] = useState('');

  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');
  const [showPwd, setShowPwd] = useState(false);
  const [oldPwd, setOldPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');

  const handleSaveProfile = async () => {
    setProfileLoading(true);
    setProfileError('');
    try {
      await usersAPI.updateMe({ username, email });
      await new Promise(r => setTimeout(r, 600));
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 3000);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!oldPwd) { setPwdError('Please enter your current password.'); return; }
    if (newPwd !== confirmPwd) { setPwdError('Passwords do not match.'); return; }
    if (newPwd.length < 4) { setPwdError('Password must be at least 4 characters.'); return; }
    setPwdLoading(true);
    setPwdError('');
    try {
      await usersAPI.changePassword(oldPwd, newPwd);
      await new Promise(r => setTimeout(r, 600));
      setOldPwd(''); setNewPwd(''); setConfirmPwd('');
      setPwdSaved(true);
      setTimeout(() => setPwdSaved(false), 3000);
    } catch (err) {
      setPwdError(err instanceof Error ? err.message : 'Failed to change password. Check your current password.');
    } finally {
      setPwdLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-slate-100">Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">Manage your account and preferences</p>
      </div>

      {/* Profile */}
      <Section title="Profile" icon={User}>
        <FieldRow label="Username">
          <Input value={username} onChange={setUsername} placeholder="username" />
        </FieldRow>
        <FieldRow label="Email">
          <Input value={email} onChange={setEmail} placeholder="email@nexora" />
        </FieldRow>
        <FieldRow label="Role">
          <Input value={user?.role || '—'} disabled />
        </FieldRow>
        {profileError && <p className="text-sm text-red-400 mt-2">{profileError}</p>}
        <div className="flex justify-end mt-4">
          <button
            onClick={handleSaveProfile}
            disabled={profileLoading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm text-white transition-all disabled:opacity-60"
            style={{ background: 'linear-gradient(135deg, #06b6d4, #3b82f6)' }}
          >
            {profileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : profileSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {profileSaved ? 'Saved!' : 'Save Profile'}
          </button>
        </div>
      </Section>

      {/* Password */}
      <Section title="Change Password" icon={Lock}>
        <FieldRow label="Current Password">
          <div className="relative">
            <Input value={oldPwd} onChange={setOldPwd} type={showPwd ? 'text' : 'password'} placeholder="Enter current password" />
            <button onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
              {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </FieldRow>
        <FieldRow label="New Password">
          <Input value={newPwd} onChange={setNewPwd} type={showPwd ? 'text' : 'password'} placeholder="Enter new password" />
        </FieldRow>
        <FieldRow label="Confirm Password">
          <Input value={confirmPwd} onChange={setConfirmPwd} type={showPwd ? 'text' : 'password'} placeholder="Confirm new password" />
        </FieldRow>
        {pwdError && <p className="text-sm text-red-400 mt-2">{pwdError}</p>}
        <div className="flex justify-end mt-4">
          <button
            onClick={handleChangePassword}
            disabled={pwdLoading || !oldPwd || !newPwd}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm text-white transition-all disabled:opacity-60"
            style={{ background: 'linear-gradient(135deg, #06b6d4, #3b82f6)' }}
          >
            {pwdLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : pwdSaved ? <Check className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
            {pwdSaved ? 'Password Changed!' : 'Change Password'}
          </button>
        </div>
      </Section>
    </div>
  );
}
