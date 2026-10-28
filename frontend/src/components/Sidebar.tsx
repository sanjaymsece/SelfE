import React from 'react';
import {
  BarChart3,
  Film,
  MessageSquareCode,
  Share2,
  Sliders,
  Sparkles,
} from 'lucide-react';

export type TabType = 'analytics' | 'content' | 'reels' | 'comments' | 'accounts' | 'settings';

interface SidebarProps {
  currentTab: TabType;
  onSelectTab: (tab: TabType) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems = [
    {
      id: 'analytics' as TabType,
      label: 'Analytics & Overview',
      icon: BarChart3,
      badge: 'Live',
    },
    {
      id: 'content' as TabType,
      label: 'Content Studio',
      icon: Sparkles,
      badge: 'AI',
    },
    {
      id: 'reels' as TabType,
      label: 'Reel Generator',
      icon: Film,
      badge: 'AI Plan',
    },
    {
      id: 'comments' as TabType,
      label: 'Comment Intelligence',
      icon: MessageSquareCode,
      badge: 'AI CRM',
    },
    {
      id: 'accounts' as TabType,
      label: 'Social Accounts',
      icon: Share2,
    },
    {
      id: 'settings' as TabType,
      label: 'Brand & Preferences',
      icon: Sliders,
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/40 p-4 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <p className="px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Navigation
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-600/20 to-violet-600/10 text-white border border-indigo-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded-md font-semibold ${
                        isActive
                          ? 'bg-indigo-500 text-white'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Simulation Info Card */}
      <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800 text-xs text-slate-400 space-y-1.5">
        <div className="flex items-center gap-2 text-indigo-400 font-medium">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Simulation Active</span>
        </div>
        <p className="leading-relaxed text-[11px] text-slate-500">
          Instagram & social metrics are simulated safely for rapid testing and experimentation.
        </p>
      </div>
    </aside>
  );
};
