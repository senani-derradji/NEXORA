import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User } from '../api/api';
import { authAPI } from '../api/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('nexora_token');
    const storedUser = localStorage.getItem('nexora_user');
    if (storedToken && storedUser) {
      // Check if it's a mock token - if so, require real login
      if (storedToken.startsWith('mock-token-')) {
        console.warn('Found mock token, clearing it');
        localStorage.removeItem('nexora_token');
        localStorage.removeItem('nexora_user');
        setIsLoading(false);
        return;
      }
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    console.log('[AuthContext.login] Starting login for:', username);
    // ALWAYS try real API - no mock fallback
    const data = await authAPI.login(username, password);
    console.log('[AuthContext.login] API success, user:', data.user);
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    authAPI.logout();
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
