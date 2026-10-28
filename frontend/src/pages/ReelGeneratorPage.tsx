import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Clapperboard,
  Film,
  Music,
  RefreshCw,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { ReelPlan } from '../types';

export const ReelGeneratorPage: React.FC = () => {
  const { activeWorkspace } = useAuth();
  const [topic, setTopic] = useState('');
  const [audience, setAudience] = useState('');
  const [vibe, setVibe] = useState('Dynamic & Engaging');
  const [duration, setDuration] = useState<number>(30);
  const [platform, setPlatform] = useState('instagram');
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeReel, setActiveReel] = useState<ReelPlan | null>(null);

  const [savedReels, setSavedReels] = useState<ReelPlan[]>([]);
  const [, setIsLoadingReels] = useState(false);

  const loadReels = async () => {
    if (!activeWorkspace) return;
    setIsLoadingReels(true);
    try {
      const res = await api.listReels();
      setSavedReels(res.results || []);
      if (!activeReel && res.results && res.results.length > 0) {
        setActiveReel(res.results[0]);
      }
    } catch (err) {
      console.error('Failed to load reels', err);
    } finally {
      setIsLoadingReels(false);
    }
  };

  useEffect(() => {
    loadReels();
  }, [activeWorkspace?.id]);

  const handleGenerateReel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setIsGenerating(true);
    try {
      const plan = await api.generateReel({
        topic,
        target_audience: audience,
        vibe,
        target_duration_seconds: duration,
        platform,
      });
      setActiveReel(plan);
      setSavedReels((prev) => [plan, ...prev]);
    } catch (err: any) {
      alert(`Reel generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleUpdateStatus = async (id: number, status: 'approved' | 'archived') => {
    try {
      const updated = await api.updateReel(id, { status });
      setActiveReel(updated);
      setSavedReels((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    }
  };

  const handleDeleteReel = async (id: number) => {
    if (!confirm('Are you sure you want to delete this Reel blueprint?')) return;
    try {
      await api.deleteReel(id);
      setSavedReels((prev) => prev.filter((r) => r.id !== id));
      if (activeReel?.id === id) {
        setActiveReel(savedReels.find((r) => r.id !== id) || null);
      }
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Reel Production Studio</h1>
          <p className="text-sm text-slate-400">
            Generate cinematic, scene-by-scene short-form video production plans with Gemini AI
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generator Form */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
            <Clapperboard className="w-4 h-4" />
            <span>Create Reel Blueprint</span>
          </div>

          <form onSubmit={handleGenerateReel} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Reel Topic / Title</label>
              <input
                type="text"
                required
                placeholder="e.g. 3 High-Protein Snacks Under 5 Minutes"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Target Audience</label>
              <input
                type="text"
                placeholder="e.g. Busy young professionals, students"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Duration</label>
                <select
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full px-2.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none"
                >
                  <option value={15}>15 Seconds</option>
                  <option value={30}>30 Seconds</option>
                  <option value={60}>60 Seconds</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Platform</label>
                <select
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                  className="w-full px-2.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none"
                >
                  <option value="instagram">Instagram Reels</option>
                  <option value="tiktok">TikTok</option>
                  <option value="youtube">YouTube Shorts</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Aesthetic / Vibe</label>
              <input
                type="text"
                placeholder="e.g. High energy, moody aesthetic, casual vlog"
                value={vibe}
                onChange={(e) => setVibe(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={isGenerating}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-violet-600 via-indigo-600 to-pink-500 hover:from-violet-500 hover:to-pink-400 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
            >
              {isGenerating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              <span>{isGenerating ? 'Drafting Blueprint...' : 'Generate Reel Plan'}</span>
            </button>
          </form>

          {/* Past Reel Blueprints list */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Saved Plans ({savedReels.length})
            </h4>
            <div className="max-h-56 overflow-y-auto space-y-2">
              {savedReels.map((reel) => (
                <div
                  key={reel.id}
                  onClick={() => setActiveReel(reel)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition-all flex items-center justify-between ${
                    activeReel?.id === reel.id
                      ? 'bg-indigo-600/10 border-indigo-500/40 text-indigo-300'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="truncate pr-2">
                    <p className="font-semibold text-slate-200 truncate">{reel.title}</p>
                    <p className="text-[10px] text-slate-500 capitalize">{reel.platform} • {reel.target_duration_seconds}s</p>
                  </div>
                  <span
                    className={`text-[9px] font-bold px-2 py-0.5 rounded-full capitalize ${
                      reel.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {reel.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Blueprint Visual Storyboard */}
        <div className="lg:col-span-2 space-y-6">
          {activeReel ? (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
              {/* Plan Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-white">{activeReel.title}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 font-semibold uppercase">
                      {activeReel.target_duration_seconds}s {activeReel.platform}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">Topic: {activeReel.topic}</p>
                </div>

                <div className="flex items-center gap-2">
                  {activeReel.status !== 'approved' && (
                    <button
                      onClick={() => handleUpdateStatus(activeReel.id, 'approved')}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 text-xs font-semibold border border-emerald-500/30 transition-colors"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Approve Plan</span>
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteReel(activeReel.id)}
                    className="p-1.5 rounded-xl bg-slate-800 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Hook Spotlight */}
              {activeReel.plan?.hook && (
                <div className="p-4 rounded-xl bg-gradient-to-r from-violet-950/40 via-indigo-950/30 to-purple-950/20 border border-indigo-500/30 space-y-2">
                  <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider">
                    <span className="h-2 w-2 rounded-full bg-indigo-400"></span>
                    <span>Opening Hook (Critical First 3s)</span>
                  </div>
                  <p className="text-xs font-medium text-white">
                    🗣 Spoken: <span className="font-normal text-indigo-200">{activeReel.plan.hook.spoken}</span>
                  </p>
                  <p className="text-xs text-slate-300">
                    👁 Visual Action: <span className="text-slate-400">{activeReel.plan.hook.visual}</span>
                  </p>
                </div>
              )}

              {/* Scene Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Film className="w-4 h-4 text-violet-400" />
                  <span>Scene-by-Scene Production Breakdown</span>
                </h4>

                <div className="space-y-3">
                  {(activeReel.plan?.scenes || []).map((scene, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition-colors space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-white flex items-center gap-2">
                          <span className="h-5 w-5 rounded-md bg-slate-800 text-indigo-400 flex items-center justify-center text-[11px]">
                            {scene.scene_number || i + 1}
                          </span>
                          <span>Scene {scene.scene_number || i + 1}</span>
                        </span>
                        <span className="text-slate-400 text-[11px]">⏱ {scene.duration_seconds}s</span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        <div className="space-y-1">
                          <p className="text-slate-400">
                            🎥 <strong className="text-slate-200">Angle:</strong> {scene.camera_angle}
                          </p>
                          <p className="text-slate-400">
                            💡 <strong className="text-slate-200">Lighting:</strong> {scene.lighting}
                          </p>
                          <p className="text-slate-400">
                            🖼 <strong className="text-slate-200">Background:</strong> {scene.background}
                          </p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-slate-300">
                            🎬 <strong className="text-slate-200">Action:</strong> {scene.visual_description}
                          </p>
                          {scene.dialogue_or_voiceover && (
                            <p className="text-indigo-200 font-medium">
                              🎙 <strong className="text-indigo-400">Audio/VO:</strong> "{scene.dialogue_or_voiceover}"
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Music, Caption & Call to Action */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                {activeReel.plan?.music_recommendation && (
                  <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <Music className="w-3.5 h-3.5 text-pink-400" />
                      <span>Audio / Music Suggestion</span>
                    </span>
                    <p className="text-xs text-slate-200 font-medium">{activeReel.plan.music_recommendation}</p>
                  </div>
                )}

                {activeReel.plan?.call_to_action && (
                  <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
                    <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📣 Call to Action</span>
                    </span>
                    <p className="text-xs text-slate-200 font-medium">{activeReel.plan.call_to_action}</p>
                  </div>
                )}
              </div>

              {/* Caption & Hashtags */}
              {activeReel.plan?.caption && (
                <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Optimized Caption
                  </span>
                  <p className="text-xs text-slate-300 whitespace-pre-wrap">{activeReel.plan.caption}</p>
                  {activeReel.plan.hashtags && activeReel.plan.hashtags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {activeReel.plan.hashtags.map((h, idx) => (
                        <span key={idx} className="text-[10px] text-pink-400 bg-slate-900 px-2 py-0.5 rounded">
                          {h.startsWith('#') ? h : `#${h}`}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="h-96 rounded-2xl bg-slate-900/30 border border-dashed border-slate-800 flex flex-col items-center justify-center text-slate-500 text-xs gap-3">
              <Film className="w-8 h-8 text-slate-600" />
              <p>Configure and generate a Reel plan on the left to see the production storyboard.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
