import React, { useEffect, useState } from 'react';
import { Check, RefreshCw, Save, Sliders, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { user, activeWorkspace, refreshProfile } = useAuth();

  // Preferences state
  const [niche, setNiche] = useState('');
  const [tone, setTone] = useState('friendly');
  const [contentStyle, setContentStyle] = useState('educational');
  const [targetAudience, setTargetAudience] = useState('');
  const [goalsInput, setGoalsInput] = useState('');
  const [keywordsInput, setKeywordsInput] = useState('');

  // Workspace settings state
  const [wsName, setWsName] = useState('');
  const [wsNiche, setWsNiche] = useState('');
  const [wsTimezone, setWsTimezone] = useState('UTC');

  const [isSavingPref, setIsSavingPref] = useState(false);
  const [isSavingWs, setIsSavingWs] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (user?.preferences) {
      setNiche(user.preferences.niche || '');
      setTone(user.preferences.tone || 'friendly');
      setContentStyle(user.preferences.content_style || 'educational');
      setTargetAudience(user.preferences.target_audience || '');
      setGoalsInput((user.preferences.goals || []).join(', '));
      setKeywordsInput((user.preferences.keywords || []).join(', '));
    }

    if (activeWorkspace) {
      setWsName(activeWorkspace.name);
      setWsNiche(activeWorkspace.niche || '');
      setWsTimezone(activeWorkspace.timezone || 'UTC');
    }
  }, [user, activeWorkspace]);

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingPref(true);
    setSavedSuccess(false);
    try {
      const goals = goalsInput
        .split(',')
        .map((g) => g.trim())
        .filter(Boolean);
      const keywords = keywordsInput
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean);

      await api.updatePreferences({
        niche,
        tone,
        content_style: contentStyle,
        target_audience: targetAudience,
        goals,
        keywords,
      });
      await refreshProfile();
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      alert(`Failed to save preferences: ${err.message}`);
    } finally {
      setIsSavingPref(false);
    }
  };

  const handleSaveWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace) return;
    setIsSavingWs(true);
    try {
      await api.updateWorkspace(activeWorkspace.id, {
        name: wsName,
        niche: wsNiche,
        timezone: wsTimezone,
      });
      await refreshProfile();
      alert('Workspace settings updated successfully!');
    } catch (err: any) {
      alert(`Failed to update workspace: ${err.message}`);
    } finally {
      setIsSavingWs(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl font-bold text-white tracking-tight">Brand & Workspace Settings</h1>
        <p className="text-sm text-slate-400">
          Personalize AI generation tone, target audience, and workspace parameters
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>Brand preferences saved successfully! All AI generators will now use this context.</span>
        </div>
      )}

      {/* Brand Identity / AI Context Card */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
          <Sparkles className="w-4 h-4" />
          <span>Brand Voice & AI Context</span>
        </div>
        <p className="text-xs text-slate-400">
          These preferences are automatically injected into Gemini prompts across the Content Studio and Reel Generator.
        </p>

        <form onSubmit={handleSavePreferences} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Primary Niche / Sector</label>
              <input
                type="text"
                placeholder="e.g. Plant-Based Cooking, Fitness"
                value={niche}
                onChange={(e) => setNiche(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Default Tone</label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none"
              >
                <option value="friendly">Friendly & Approachable</option>
                <option value="authoritative">Expert & Authoritative</option>
                <option value="educational">Educational & Structured</option>
                <option value="humorous">Witty & Humorous</option>
                <option value="inspirational">Inspirational & Bold</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Content Style</label>
              <select
                value={contentStyle}
                onChange={(e) => setContentStyle(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none"
              >
                <option value="educational">Educational / Tutorials</option>
                <option value="storytelling">Storytelling & Vlogs</option>
                <option value="behind-the-scenes">Behind the Scenes</option>
                <option value="promotional">Product & Promotional</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Target Audience</label>
              <input
                type="text"
                placeholder="e.g. Health-conscious families, busy professionals"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Content Goals (Comma-separated)</label>
            <input
              type="text"
              placeholder="e.g. Increase saves, grow followers, drive comments"
              value={goalsInput}
              onChange={(e) => setGoalsInput(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Brand Keywords (Comma-separated)</label>
            <input
              type="text"
              placeholder="e.g. vegan, quick recipes, easy dinner, high protein"
              value={keywordsInput}
              onChange={(e) => setKeywordsInput(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isSavingPref}
              className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              {isSavingPref ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              <span>{isSavingPref ? 'Saving...' : 'Save Brand Preferences'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Workspace Settings Card */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
          <Sliders className="w-4 h-4 text-slate-400" />
          <span>Active Workspace Parameters</span>
        </div>

        <form onSubmit={handleSaveWorkspace} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Workspace Name</label>
              <input
                type="text"
                required
                value={wsName}
                onChange={(e) => setWsName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Niche</label>
              <input
                type="text"
                value={wsNiche}
                onChange={(e) => setWsNiche(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Timezone (IANA)</label>
              <input
                type="text"
                required
                value={wsTimezone}
                onChange={(e) => setWsTimezone(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSavingWs}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            {isSavingWs ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>Update Workspace</span>
          </button>
        </form>
      </div>
    </div>
  );
};
