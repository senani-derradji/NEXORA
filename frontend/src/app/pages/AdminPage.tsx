import React, { useState, useEffect } from 'react';
import { User, Lock, Trash2, Plus, X, Loader2, Shield, ShieldCheck } from 'lucide-react';
import { usersAPI } from '../api/api';
import { useAuth } from '../context/AuthContext';

interface UserItem {
  id: number;
  email: string;
  username?: string;
  role: string;
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

export function AdminPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Users management state
  const [users, setUsers] = useState<UserItem[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState('');
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [addUserLoading, setAddUserLoading] = useState(false);
  const [addUserError, setAddUserError] = useState('');

  // Redirect non-admins
  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Shield className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Access Denied</h2>
          <p className="text-slate-400">You need admin privileges to access this page.</p>
        </div>
      </div>
    );
  }

  // Load users list
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setUsersLoading(true);
    setUsersError('');
    try {
      const data = await usersAPI.getAll() as any;
      setUsers(data?.users || data || []);
    } catch (err) {
      setUsersError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setUsersLoading(false);
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddUserLoading(true);
    setAddUserError('');
    try {
      await usersAPI.register(newUserEmail, newUserPassword);
      setShowAddUser(false);
      setNewUserEmail('');
      setNewUserPassword('');
      loadUsers();
    } catch (err) {
      setAddUserError(err instanceof Error ? err.message : 'Failed to add user');
    } finally {
      setAddUserLoading(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await usersAPI.delete(userId);
      loadUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete user');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-slate-100 text-2xl font-semibold">Admin Panel</h1>
        <p className="text-slate-500 mt-1">Manage users and system settings</p>
      </div>

      {/* Users Management */}
      <Section title="User Management" icon={User}>
        <div className="flex justify-end mb-4">
          <button
            onClick={() => setShowAddUser(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-cyan-500 text-white hover:bg-cyan-600 transition-all"
          >
            <Plus className="w-4 h-4" />
            Add User
          </button>
        </div>

        {/* Add User Modal */}
        {showAddUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowAddUser(false)} />
            <div className="relative rounded-xl border p-6 w-full max-w-md" style={{ background: '#0c1225', borderColor: 'rgba(255,255,255,0.1)' }}>
              <h3 className="text-lg font-semibold text-white mb-4">Add New User</h3>
              <form onSubmit={handleAddUser} className="space-y-4">
                {addUserError && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                    {addUserError}
                  </div>
                )}
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Email</label>
                  <input
                    type="email"
                    value={newUserEmail}
                    onChange={(e) => setNewUserEmail(e.target.value)}
                    required
                    className="w-full px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 border outline-none focus:border-cyan-500 transition-all"
                    style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Password</label>
                  <input
                    type="password"
                    value={newUserPassword}
                    onChange={(e) => setNewUserPassword(e.target.value)}
                    required
                    minLength={6}
                    className="w-full px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 border outline-none focus:border-cyan-500 transition-all"
                    style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
                  />
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddUser(false)}
                    className="px-4 py-2 rounded-lg text-sm text-slate-400 hover:text-white transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={addUserLoading}
                    className="px-4 py-2 rounded-lg text-sm bg-cyan-500 text-white hover:bg-cyan-600 transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    {addUserLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                    Add User
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Users List */}
        {usersLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
          </div>
        ) : usersError ? (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
            {usersError}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <th className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase">ID</th>
                  <th className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase">Email</th>
                  <th className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase">Role</th>
                  <th className="text-right px-4 py-3 text-xs text-slate-500 font-medium uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-white/5">
                    <td className="px-4 py-3 text-slate-400">{u.id}</td>
                    <td className="px-4 py-3 text-slate-200">{u.email}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
                        u.role === 'admin'
                          ? 'bg-purple-500/15 text-purple-400'
                          : 'bg-blue-500/15 text-blue-400'
                      }`}>
                        {u.role === 'admin' ? <ShieldCheck className="w-3 h-3" /> : <Shield className="w-3 h-3" />}
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDeleteUser(u.id)}
                        className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                        title="Delete user"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && (
              <div className="text-center py-8 text-slate-500">
                No users found
              </div>
            )}
          </div>
        )}
      </Section>
    </div>
  );
}
