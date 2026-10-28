import React, { useEffect, useState } from 'react';
import {
  Archive,
  Check,
  CheckCircle2,
  Copy,
  FileEdit,
  Hash,
  Lightbulb,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  Video,
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { ContentDraft } from '../types';

export const ContentStudioPage: React.FC = () => {
  const { activeWorkspace } = useAuth();
  const [activeTab, setActiveTab] = useState<'ideas' | 'captions' | 'scripts' | 'drafts'>('ideas');

  // Generator form states
  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState('friendly');
  const [goal, setGoal] = useState('Increase engagement and saves');
  const [duration, setDuration] = useState<number>(30);
  const [count, setCount] = useState<number>(3);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResults, setGeneratedResults] = useState<any>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Drafts state
  const [drafts, setDrafts] = useState<ContentDraft[]>([]);
  const [draftFilterKind, setDraftFilterKind] = useState<string>('');
  const [draftFilterStatus, setDraftFilterStatus] = useState<string>('');
  const [draftSearch, setDraftSearch] = useState<string>('');
  const [isLoadingDrafts, setIsLoadingDrafts] = useState<boolean>(false);

  // Create manual draft modal state
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [manualTitle, setManualTitle] = useState('');
  const [manualKind, setManualKind] = useState('idea');
  const [manualBody, setManualBody] = useState('');

  const loadDrafts = async () => {
    if (!activeWorkspace) return;
    setIsLoadingDrafts(true);
    try {
      const res = await api.listDrafts({
        kind: draftFilterKind || undefined,
        status: draftFilterStatus || undefined,
        search: draftSearch || undefined,
      });
      setDrafts(res.results || []);
    } catch (err) {
      console.error('Failed to load drafts', err);
    } finally {
      setIsLoadingDrafts(false);
    }
  };

  useEffect(() => {
    loadDrafts();
  }, [activeWorkspace?.id, draftFilterKind, draftFilterStatus]);

  const handleGenerateIdeas = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setIsGenerating(true);
    setGeneratedResults(null);
    try {
      const res = await api.generateIdeas({
        topic,
        goal,
        count,
        tone,
      });
      setGeneratedResults({ type: 'ideas', items: res.ideas });
      loadDrafts();
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateCaptions = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setIsGenerating(true);
    setGeneratedResults(null);
    try {
      const res = await api.generateCaptions({
        topic,
        tone,
        count,
      });
      setGeneratedResults({ type: 'captions', items: res.captions });
      loadDrafts();
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateScripts = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setIsGenerating(true);
    setGeneratedResults(null);
    try {
      const res = await api.generateScripts({
        topic,
        target_duration_seconds: duration,
        tone,
      });
      setGeneratedResults({ type: 'scripts', items: res.scripts });
      loadDrafts();
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCreateManualDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createDraft({
        title: manualTitle,
        kind: manualKind,
        body: manualBody,
        status: 'draft',
      });
      setIsManualModalOpen(false);
      setManualTitle('');
      setManualBody('');
      loadDrafts();
    } catch (err: any) {
      alert(`Failed to save draft: ${err.message}`);
    }
  };

  const handleUpdateDraftStatus = async (id: number, status: 'approved' | 'archived' | 'draft') => {
    try {
      await api.updateDraft(id, { status });
      loadDrafts();
    } catch (err: any) {
      alert(`Failed to update draft: ${err.message}`);
    }
  };

  const handleDeleteDraft = async (id: number) => {
    if (!confirm('Are you sure you want to delete this draft?')) return;
    try {
      await api.deleteDraft(id);
      loadDrafts();
    } catch (err: any) {
      alert(`Failed to delete draft: ${err.message}`);
    }
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AI Content Studio</h1>
          <p className="text-sm text-slate-400">
            Generate tailored content ideas, captions, hashtags, and video scripts using Gemini
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsManualModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create Draft</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        <button
          onClick={() => {
            setActiveTab('ideas');
            setGeneratedResults(null);
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'ideas'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <Lightbulb className="w-4 h-4 text-amber-400" />
          <span>Idea Generator</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('captions');
            setGeneratedResults(null);
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'captions'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <Hash className="w-4 h-4 text-pink-400" />
          <span>Captions & Hashtags</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('scripts');
            setGeneratedResults(null);
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'scripts'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <Video className="w-4 h-4 text-violet-400" />
          <span>Short Video Scripts</span>
        </button>

        <button
          onClick={() => setActiveTab('drafts')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ml-auto ${
            activeTab === 'drafts'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <FileEdit className="w-4 h-4 text-emerald-400" />
          <span>Saved Drafts ({drafts.length})</span>
        </button>
      </div>

      {/* Generator Views */}
      {activeTab === 'ideas' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Generate Content Ideas</span>
            </h3>
            <form onSubmit={handleGenerateIdeas} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Topic or Concept</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 5 Common Meal Prep Mistakes to Avoid"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Target Goal</label>
                <input
                  type="text"
                  placeholder="e.g. Educate and drive comments"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Tone</label>
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    className="w-full px-2.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none"
                  >
                    <option value="friendly">Friendly</option>
                    <option value="educational">Educational</option>
                    <option value="authoritative">Authoritative</option>
                    <option value="humorous">Humorous</option>
                    <option value="inspirational">Inspirational</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Quantity</label>
                  <select
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                    className="w-full px-2.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none"
                  >
                    <option value={2}>2 Ideas</option>
                    <option value={3}>3 Ideas</option>
                    <option value={5}>5 Ideas</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={isGenerating}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
              >
                {isGenerating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>{isGenerating ? 'Generating with Gemini...' : 'Generate Ideas'}</span>
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 space-y-4">
            {generatedResults?.type === 'ideas' && generatedResults.items ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">Generated Ideas</h3>
                  <span className="text-xs text-emerald-400 font-medium">✓ Auto-saved to Drafts</span>
                </div>
                {generatedResults.items.map((item: any, i: number) => (
                  <div
                    key={i}
                    className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h4 className="font-semibold text-white text-sm">{item.title}</h4>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 uppercase font-semibold">
                        {item.format || 'Post'}
                      </span>
                    </div>
                    {item.hook && (
                      <p className="text-xs text-indigo-300 font-medium">
                        🪝 Hook: <span className="text-slate-300 font-normal">{item.hook}</span>
                      </p>
                    )}
                    {item.angle && (
                      <p className="text-xs text-slate-400">
                        🎯 Angle: <span className="text-slate-300">{item.angle}</span>
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-64 rounded-2xl bg-slate-900/30 border border-dashed border-slate-800 flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
                <Lightbulb className="w-6 h-6 text-slate-600" />
                <p>Enter a topic on the left to spark tailored content ideas.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'captions' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Hash className="w-4 h-4 text-pink-400" />
              <span>Generate Captions & Hashtags</span>
            </h3>
            <form onSubmit={handleGenerateCaptions} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Post Context / Subject</label>
                <textarea
                  rows={3}
                  required
                  placeholder="What is this post about? Key takeaways or highlights..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                ></textarea>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Tone</label>
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full px-2.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none"
                >
                  <option value="friendly">Friendly & Relatable</option>
                  <option value="educational">Educational & Informative</option>
                  <option value="witty">Witty & Punchy</option>
                  <option value="inspirational">Motivational & Bold</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isGenerating}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-pink-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-pink-600/20 transition-all disabled:opacity-50"
              >
                {isGenerating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>{isGenerating ? 'Drafting Captions...' : 'Generate Captions'}</span>
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 space-y-4">
            {generatedResults?.type === 'captions' && generatedResults.items ? (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-white">Generated Captions</h3>
                {generatedResults.items.map((item: any, i: number) => {
                  const fullText = `${item.caption || item.body || ''}\n\n${(item.hashtags || []).map((h: string) => (h.startsWith('#') ? h : `#${h}`)).join(' ')}`;
                  return (
                    <div
                      key={i}
                      className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3 relative group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                          Variant #{i + 1}
                        </span>
                        <button
                          onClick={() => copyToClipboard(fullText, i)}
                          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
                        >
                          {copiedIndex === i ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy Caption</span>
                            </>
                          )}
                        </button>
                      </div>

                      <p className="text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                        {item.caption || item.body}
                      </p>

                      {item.hashtags && item.hashtags.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-800/80">
                          {item.hashtags.map((h: string, hIdx: number) => (
                            <span
                              key={hIdx}
                              className="text-[11px] px-2 py-0.5 rounded-md bg-slate-800/80 text-pink-400"
                            >
                              {h.startsWith('#') ? h : `#${h}`}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="h-64 rounded-2xl bg-slate-900/30 border border-dashed border-slate-800 flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
                <Hash className="w-6 h-6 text-slate-600" />
                <p>Provide a post summary to generate ready-to-publish captions.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'scripts' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Video className="w-4 h-4 text-violet-400" />
              <span>Generate Short-Form Script</span>
            </h3>
            <form onSubmit={handleGenerateScripts} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Video Topic</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 3 Quick Posture Fixes for Desk Workers"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Target Duration</label>
                <div className="grid grid-cols-3 gap-2">
                  {[15, 30, 60].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setDuration(s)}
                      className={`py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                        duration === s
                          ? 'bg-violet-600/20 text-violet-300 border-violet-500/40'
                          : 'bg-slate-950 border-slate-800 text-slate-400'
                      }`}
                    >
                      {s}s
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Tone</label>
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full px-2.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none"
                >
                  <option value="friendly">Energetic & Friendly</option>
                  <option value="educational">Educational / Step-by-step</option>
                  <option value="direct">Direct & Punchy</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isGenerating}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-violet-600/20 transition-all disabled:opacity-50"
              >
                {isGenerating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>{isGenerating ? 'Writing Script...' : 'Generate Script'}</span>
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 space-y-4">
            {generatedResults?.type === 'scripts' && generatedResults.items ? (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-white">Generated Video Scripts</h3>
                {generatedResults.items.map((script: any, i: number) => (
                  <div
                    key={i}
                    className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3"
                  >
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <h4 className="font-semibold text-white text-sm">
                        {script.title || `Script Plan (${duration}s)`}
                      </h4>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 font-semibold uppercase">
                        {duration} Seconds
                      </span>
                    </div>

                    {script.hook && (
                      <div className="p-3 rounded-xl bg-violet-950/20 border border-violet-800/30">
                        <span className="text-[11px] font-semibold text-violet-400 uppercase tracking-wider block mb-0.5">
                          Opening Hook (First 3s)
                        </span>
                        <p className="text-xs text-slate-200">{script.hook}</p>
                      </div>
                    )}

                    <div className="space-y-2">
                      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                        Body / Delivery
                      </span>
                      <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                        {script.body || script.content || JSON.stringify(script)}
                      </p>
                    </div>

                    {script.call_to_action && (
                      <div className="p-2.5 rounded-xl bg-slate-800/40 text-xs text-emerald-400 font-medium">
                        📣 CTA: <span className="text-slate-300">{script.call_to_action}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-64 rounded-2xl bg-slate-900/30 border border-dashed border-slate-800 flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
                <Video className="w-6 h-6 text-slate-600" />
                <p>Select your video topic and target length to generate a short-form script.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Drafts Tab */}
      {activeTab === 'drafts' && (
        <div className="space-y-4">
          {/* Draft Filters */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <select
                value={draftFilterKind}
                onChange={(e) => setDraftFilterKind(e.target.value)}
                className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none"
              >
                <option value="">All Kinds</option>
                <option value="idea">Idea</option>
                <option value="caption">Caption</option>
                <option value="script">Script</option>
              </select>

              <select
                value={draftFilterStatus}
                onChange={(e) => setDraftFilterStatus(e.target.value)}
                className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none"
              >
                <option value="">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="approved">Approved</option>
                <option value="archived">Archived</option>
              </select>
            </div>

            <div className="relative min-w-[200px]">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search drafts..."
                value={draftSearch}
                onChange={(e) => setDraftSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadDrafts()}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Drafts List */}
          {isLoadingDrafts ? (
            <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
              Loading drafts...
            </div>
          ) : drafts.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {drafts.map((draft) => (
                <div
                  key={draft.id}
                  className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-colors"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400">
                        {draft.kind}
                      </span>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize ${
                          draft.status === 'approved'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : draft.status === 'archived'
                            ? 'bg-slate-800 text-slate-400'
                            : 'bg-amber-500/10 text-amber-400'
                        }`}
                      >
                        {draft.status}
                      </span>
                    </div>
                    <h4 className="font-semibold text-white text-sm line-clamp-1">{draft.title}</h4>
                    <p className="text-xs text-slate-300 line-clamp-4 whitespace-pre-wrap">
                      {draft.body || JSON.stringify(draft.content)}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                    <span className="text-[10px]">
                      {draft.source === 'ai' ? '🤖 AI Generated' : '✍️ Manual'}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {draft.status !== 'approved' && (
                        <button
                          onClick={() => handleUpdateDraftStatus(draft.id, 'approved')}
                          title="Approve Draft"
                          className="p-1.5 rounded-lg hover:bg-emerald-500/10 text-slate-400 hover:text-emerald-400 transition-colors"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </button>
                      )}
                      {draft.status !== 'archived' && (
                        <button
                          onClick={() => handleUpdateDraftStatus(draft.id, 'archived')}
                          title="Archive"
                          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                        >
                          <Archive className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteDraft(draft.id)}
                        title="Delete"
                        className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-48 rounded-2xl bg-slate-900/30 border border-dashed border-slate-800 flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
              <FileEdit className="w-6 h-6 text-slate-600" />
              <p>No drafts found matching your criteria.</p>
            </div>
          )}
        </div>
      )}

      {/* Manual Draft Modal */}
      {isManualModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-lg rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-white">Create New Draft</h3>
              <button onClick={() => setIsManualModalOpen(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateManualDraft} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="Draft title..."
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Content Kind</label>
                <select
                  value={manualKind}
                  onChange={(e) => setManualKind(e.target.value)}
                  className="w-full px-2.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none"
                >
                  <option value="idea">Content Idea</option>
                  <option value="caption">Caption & Hashtags</option>
                  <option value="script">Video Script</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Body / Content</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Draft body content..."
                  value={manualBody}
                  onChange={(e) => setManualBody(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                ></textarea>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsManualModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
                >
                  Save Draft
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
