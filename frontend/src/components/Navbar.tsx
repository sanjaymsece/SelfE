import React, { useState } from 'react';
import {
  Building2,
  ChevronDown,
  LogOut,
  Plus,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Navbar: React.FC<{
  onOpenNewWorkspace: () => void;
}> = ({ onOpenNewWorkspace }) => {
  const { user, activeWorkspace, workspaces, switchWorkspace, logout } = useAuth();
  const [isWsOpen, setIsWsOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg text-white tracking-tight">SelfE</span>
            <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              AI Studio
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">AI-Assisted Social Media Manager</p>
        </div>
      </div>

      {/* Center / Right controls */}
      <div className="flex items-center gap-3">
        {/* Workspace Switcher */}
        <div className="relative">
          <button
            onClick={() => setIsWsOpen(!isWsOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-sm font-medium text-slate-200 transition-all shadow-sm"
          >
            <Building2 className="w-4 h-4 text-indigo-400" />
            <span className="max-w-[140px] truncate">{activeWorkspace?.name || 'Select Workspace'}</span>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </button>

          {isWsOpen && (
            <div className="absolute right-0 mt-2 w-64 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-1.5 border-b border-slate-800">
                <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Your Workspaces</p>
              </div>
              <div className="max-h-60 overflow-y-auto py-1">
                {workspaces.map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => {
                      switchWorkspace(ws);
                      setIsWsOpen(false);
                    }}
                    className={`w-full px-3 py-2 text-left text-sm flex items-center justify-between hover:bg-slate-800/80 transition-colors ${
                      activeWorkspace?.id === ws.id ? 'bg-indigo-600/10 text-indigo-300 font-semibold' : 'text-slate-300'
                    }`}
                  >
                    <div className="truncate">
                      <p className="truncate font-medium">{ws.name}</p>
                      <p className="text-xs text-slate-500">{ws.niche || 'General'} • {ws.timezone}</p>
                    </div>
                    {activeWorkspace?.id === ws.id && (
                      <span className="h-2 w-2 rounded-full bg-indigo-500"></span>
                    )}
                  </button>
                ))}
              </div>
              <div className="border-t border-slate-800 pt-1 mt-1 px-2">
                <button
                  onClick={() => {
                    setIsWsOpen(false);
                    onOpenNewWorkspace();
                  }}
                  className="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create Workspace</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User profile dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-800 transition-colors border border-transparent hover:border-slate-700"
          >
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-slate-700 to-slate-600 flex items-center justify-center text-white font-medium text-sm">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email.charAt(0).toUpperCase()}
            </div>
          </button>

          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl py-2 z-50">
              <div className="px-4 py-2 border-b border-slate-800">
                <p className="text-sm font-semibold text-white truncate">{user?.full_name || 'Creator'}</p>
                <p className="text-xs text-slate-400 truncate">{user?.email}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    setIsProfileOpen(false);
                    logout();
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-rose-400 hover:bg-rose-500/10 flex items-center gap-2 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
