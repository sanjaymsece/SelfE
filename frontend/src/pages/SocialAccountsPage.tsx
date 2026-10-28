import React, { useEffect, useState } from 'react';
import {
  Camera,
  Globe,
  Plus,
  RefreshCw,
  Share2,
  Trash2,
  Video,
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { SocialAccount } from '../types';

export const SocialAccountsPage: React.FC = () => {
  const { activeWorkspace } = useAuth();
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);

  // Form state
  const [platform, setPlatform] = useState('instagram');
  const [handle, setHandle] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [followers, setFollowers] = useState<number>(1000);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadAccounts = async () => {
    if (!activeWorkspace) return;
    setIsLoading(true);
    try {
      const res = await api.listSocialAccounts();
      setAccounts(res.results || []);
    } catch (err) {
      console.error('Failed to load accounts', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAccounts();
  }, [activeWorkspace?.id]);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim()) return;
    setIsSubmitting(true);
    try {
      await api.connectSocialAccount({
        platform,
        handle,
        display_name: displayName,
        follower_count: followers,
      });
      setIsConnectModalOpen(false);
      setHandle('');
      setDisplayName('');
      loadAccounts();
    } catch (err: any) {
      alert(`Connect failed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDisconnect = async (id: number) => {
    if (!confirm('Are you sure you want to disconnect this simulated account?')) return;
    try {
      await api.disconnectSocialAccount(id);
      setAccounts((prev) => prev.filter((a) => a.id !== id));
    } catch (err: any) {
      alert(`Failed to disconnect: ${err.message}`);
    }
  };

  const getPlatformIcon = (plt: string) => {
    switch (plt) {
      case 'instagram':
        return <Camera className="w-5 h-5 text-pink-500" />;
      case 'tiktok':
        return <Video className="w-5 h-5 text-teal-400" />;
      case 'youtube':
        return <Video className="w-5 h-5 text-red-500" />;
      case 'linkedin':
        return <Globe className="w-5 h-5 text-blue-400" />;
      default:
        return <Share2 className="w-5 h-5 text-indigo-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Connected Social Accounts</h1>
          <p className="text-sm text-slate-400">
            Simulated channels in <span className="text-indigo-400 font-medium">{activeWorkspace?.name}</span>
          </p>
        </div>

        <button
          onClick={() => setIsConnectModalOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Connect Channel</span>
        </button>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="h-48 flex items-center justify-center text-slate-500 text-xs gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-indigo-500" />
          <span>Loading accounts...</span>
        </div>
      ) : accounts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts.map((acc) => (
            <div
              key={acc.id}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-slate-800 flex items-center justify-center">
                    {getPlatformIcon(acc.platform)}
                  </div>
                  <div>
                    <h4 className="font-semibold text-white text-sm">@{acc.handle}</h4>
                    <p className="text-xs text-slate-400">{acc.display_name || acc.platform_display}</p>
                  </div>
                </div>

                <button
                  onClick={() => handleDisconnect(acc.id)}
                  title="Disconnect"
                  className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Followers</span>
                  <span className="font-bold text-white text-sm">{acc.follower_count.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Published Posts</span>
                  <span className="font-bold text-indigo-300 text-sm">{acc.posts_count}</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                <span>{acc.is_simulated ? 'Simulated API Sandbox' : 'Live Channel'}</span>
                <span className="text-emerald-400 font-medium">● Active</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="h-48 rounded-2xl bg-slate-900/30 border border-dashed border-slate-800 flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
          <Share2 className="w-6 h-6 text-slate-600" />
          <p>No social accounts connected to this workspace yet.</p>
        </div>
      )}

      {/* Connect Modal */}
      {isConnectModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-white">Connect Channel (Simulated)</h3>
              <button onClick={() => setIsConnectModalOpen(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleConnect} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Platform</label>
                <select
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none"
                >
                  <option value="instagram">Instagram</option>
                  <option value="tiktok">TikTok</option>
                  <option value="youtube">YouTube</option>
                  <option value="linkedin">LinkedIn</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Handle / Username</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. greenfork_kitchen"
                  value={handle}
                  onChange={(e) => setHandle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Display Name</label>
                <input
                  type="text"
                  placeholder="e.g. Green Fork Kitchen"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Initial Followers (Simulated)</label>
                <input
                  type="number"
                  min={0}
                  value={followers}
                  onChange={(e) => setFollowers(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsConnectModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {isSubmitting ? 'Connecting...' : 'Connect Channel'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
