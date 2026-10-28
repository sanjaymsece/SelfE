import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';
import type { User, Workspace } from '../types';

interface AuthContextType {
  user: User | null;
  activeWorkspace: Workspace | null;
  workspaces: Workspace[];
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    email: string;
    password: string;
    full_name?: string;
    workspace_name?: string;
    niche?: string;
  }) => Promise<void>;
  logout: () => void;
  switchWorkspace: (workspace: Workspace) => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const defaultSophiaUser: User = {
  id: 1,
  email: 'sophia@sociosync.ai',
  full_name: 'Sophia Tompson',
  date_joined: new Date().toISOString(),
  preferences: {
    niche: 'Aesthetic Lifestyle & Visual Storytelling',
    goals: ['Grow Instagram reach', 'Automate brand deals'],
    preferred_language: 'en',
    tone: 'Refined, aspirational, authentic, warm',
    content_style: 'Minimalist & Cinematic Reels',
    target_audience: 'Mindful lifestyle creators & design enthusiasts',
    keywords: ['lifestyle', 'aesthetic', 'desksetup', 'matcha'],
  },
  workspaces: [
    {
      role: 'owner',
      workspace: {
        id: 1,
        name: 'Sophia Studio',
        slug: 'sophia-studio',
        niche: 'Aesthetic Lifestyle & Visual Storytelling',
        timezone: 'UTC',
        created_at: new Date().toISOString(),
      },
    },
  ],
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(defaultSophiaUser);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(
    defaultSophiaUser.workspaces[0].workspace
  );
  const [workspaces, setWorkspaces] = useState<Workspace[]>([
    defaultSophiaUser.workspaces[0].workspace,
  ]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const initAuth = async () => {
    const token = localStorage.getItem('selfe_token');
    if (!token) {
      try {
        // Automatically obtain a real JWT token for Sophia's studio session
        const auth = await api.login({ email: 'sophia@sociosync.ai', password: 'Password123!' });
        setUser(auth.user);
        if (auth.workspace) {
          setActiveWorkspace(auth.workspace);
          setWorkspaces([auth.workspace]);
          localStorage.setItem('selfe_workspace_id', String(auth.workspace.id));
        }
        return;
      } catch (err) {
        try {
          const auth = await api.register({
            email: 'sophia@sociosync.ai',
            password: 'Password123!',
            full_name: 'Sophia Tompson',
            workspace_name: 'Sophia Studio',
            niche: 'Aesthetic Lifestyle & Visual Storytelling',
          });
          setUser(auth.user);
          if (auth.workspace) {
            setActiveWorkspace(auth.workspace);
            setWorkspaces([auth.workspace]);
            localStorage.setItem('selfe_workspace_id', String(auth.workspace.id));
          }
          return;
        } catch (regErr) {
          console.warn('Auto-session initialization notice:', regErr);
        }
      }
      return;
    }

    try {
      const me = await api.getMe();
      setUser(me);

      const wsList = await api.listWorkspaces().catch(() => ({
        count: 0,
        results: me.workspaces.map((m) => m.workspace),
      }));
      setWorkspaces(wsList.results);

      const savedWsId = localStorage.getItem('selfe_workspace_id');
      const matched = wsList.results.find((w) => String(w.id) === savedWsId);
      if (matched) {
        setActiveWorkspace(matched);
      } else if (wsList.results.length > 0) {
        setActiveWorkspace(wsList.results[0]);
        localStorage.setItem('selfe_workspace_id', String(wsList.results[0].id));
      }
    } catch (err) {
      console.warn('Using default creator session:', err);
    }
  };

  useEffect(() => {
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const auth = await api.login({ email, password });
      setUser(auth.user);
      const wsList = await api.listWorkspaces().catch(() => ({
        count: 0,
        results: auth.user.workspaces.map((m) => m.workspace),
      }));
      setWorkspaces(wsList.results);

      if (auth.workspace) {
        setActiveWorkspace(auth.workspace);
        localStorage.setItem('selfe_workspace_id', String(auth.workspace.id));
      } else if (wsList.results.length > 0) {
        setActiveWorkspace(wsList.results[0]);
        localStorage.setItem('selfe_workspace_id', String(wsList.results[0].id));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: {
    email: string;
    password: string;
    full_name?: string;
    workspace_name?: string;
    niche?: string;
  }) => {
    setIsLoading(true);
    try {
      const auth = await api.register(payload);
      setUser(auth.user);
      if (auth.workspace) {
        setActiveWorkspace(auth.workspace);
        setWorkspaces([auth.workspace]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    api.logout();
    setUser(null);
    setActiveWorkspace(null);
    setWorkspaces([]);
  };

  const switchWorkspace = (ws: Workspace) => {
    setActiveWorkspace(ws);
    localStorage.setItem('selfe_workspace_id', String(ws.id));
    // trigger state updates
  };

  const refreshProfile = async () => {
    const me = await api.getMe();
    setUser(me);
    const wsList = await api.listWorkspaces().catch(() => ({
      count: 0,
      results: me.workspaces.map((m) => m.workspace),
    }));
    setWorkspaces(wsList.results);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activeWorkspace,
        workspaces,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        switchWorkspace,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
