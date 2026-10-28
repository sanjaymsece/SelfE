import React, { useEffect, useState } from 'react';
import {
  Check,
  Copy,
  Heart,
  MessageCircle,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  UserCheck,
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { CommentItem } from '../types';

export const CommentIntelligencePage: React.FC = () => {
  const { activeWorkspace } = useAuth();
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Filters
  const [sentimentFilter, setSentimentFilter] = useState('');
  const [intentFilter, setIntentFilter] = useState('');
  const [isQuestionOnly, setIsQuestionOnly] = useState(false);
  const [search, setSearch] = useState('');

  // Suggest Reply Modal State
  const [replyModalComment, setReplyModalComment] = useState<CommentItem | null>(null);
  const [replyTone, setReplyTone] = useState('friendly');
  const [replySuggestions, setReplySuggestions] = useState<string[]>([]);
  const [isGeneratingReply, setIsGeneratingReply] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const loadComments = async () => {
    if (!activeWorkspace) return;
    setIsLoading(true);
    try {
      const res = await api.listComments({
        sentiment: sentimentFilter || undefined,
        intent: intentFilter || undefined,
        is_question: isQuestionOnly ? true : undefined,
        search: search || undefined,
      });
      setComments(res.results || []);
    } catch (err) {
      console.error('Failed to load comments', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadComments();
  }, [activeWorkspace?.id, sentimentFilter, intentFilter, isQuestionOnly]);

  const handleBatchAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const unanalyzedIds = comments.filter((c) => !c.analyzed_at).map((c) => c.id);
      const res = await api.analyzeComments(unanalyzedIds.slice(0, 50));
      alert(`Analyzed ${res.count} comments with Gemini!`);
      loadComments();
    } catch (err: any) {
      alert(`Comment analysis failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleOpenReplyModal = (comment: CommentItem) => {
    setReplyModalComment(comment);
    setReplySuggestions([]);
    setCopiedIndex(null);
  };

  const handleGenerateReply = async () => {
    if (!replyModalComment) return;
    setIsGeneratingReply(true);
    try {
      const res = await api.suggestReply(replyModalComment.id, {
        tone: replyTone,
      });
      setReplySuggestions(res.suggestions || []);
    } catch (err: any) {
      alert(`Failed to suggest replies: ${err.message}`);
    } finally {
      setIsGeneratingReply(false);
    }
  };

  const handleDeleteComment = async (id: number) => {
    if (!confirm('Are you sure you want to delete this comment?')) return;
    try {
      await api.deleteComment(id);
      setComments((prev) => prev.filter((c) => c.id !== id));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const copyReply = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Sentiment counts
  const positiveCount = comments.filter((c) => c.sentiment === 'positive').length;
  const neutralCount = comments.filter((c) => c.sentiment === 'neutral').length;
  const negativeCount = comments.filter((c) => c.sentiment === 'negative').length;
  const questionCount = comments.filter((c) => c.is_question).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Comment Intelligence & CRM</h1>
          <p className="text-sm text-slate-400">
            Batch sentiment classification, intent detection, and context-aware AI reply generation
          </p>
        </div>

        <button
          onClick={handleBatchAnalyze}
          disabled={isAnalyzing || isLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 via-violet-600 to-pink-500 hover:from-indigo-500 hover:to-pink-400 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
        >
          {isAnalyzing ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
          )}
          <span>{isAnalyzing ? 'Classifying Comments with Gemini...' : 'Analyze All Comments'}</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400">Positive Sentiment</span>
          <p className="text-xl font-bold text-emerald-400">{positiveCount}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400">Questions Asked</span>
          <p className="text-xl font-bold text-indigo-400">{questionCount}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400">Neutral Feedback</span>
          <p className="text-xl font-bold text-slate-300">{neutralCount}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400">Critiques / Complaints</span>
          <p className="text-xl font-bold text-rose-400">{negativeCount}</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={sentimentFilter}
            onChange={(e) => setSentimentFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Sentiments</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
            <option value="unknown">Unanalyzed / Unknown</option>
          </select>

          <select
            value={intentFilter}
            onChange={(e) => setIntentFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Intents</option>
            <option value="question">Question</option>
            <option value="collaboration">Collaboration Opportunity</option>
            <option value="praise">Praise</option>
            <option value="complaint">Complaint</option>
            <option value="feedback">Feedback</option>
            <option value="spam">Spam</option>
          </select>

          <button
            onClick={() => setIsQuestionOnly(!isQuestionOnly)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              isQuestionOnly
                ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            ❓ Questions Only
          </button>
        </div>

        <div className="relative min-w-[200px]">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search author or comment..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadComments()}
            className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Comments List */}
      {isLoading ? (
        <div className="h-48 flex items-center justify-center text-slate-500 text-xs gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-indigo-500" />
          <span>Loading comments...</span>
        </div>
      ) : comments.length > 0 ? (
        <div className="space-y-3">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm text-indigo-300">@{comment.author_username}</span>
                  <span className="text-[10px] text-slate-500">
                    {comment.commented_at ? new Date(comment.commented_at).toLocaleDateString() : '—'}
                  </span>
                  {comment.is_simulated && (
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-500">
                      Simulated
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5 flex-wrap">
                  {/* Sentiment tag */}
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                      comment.sentiment === 'positive'
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : comment.sentiment === 'negative'
                        ? 'bg-rose-500/10 text-rose-400'
                        : comment.sentiment === 'neutral'
                        ? 'bg-slate-800 text-slate-300'
                        : 'bg-amber-500/10 text-amber-400'
                    }`}
                  >
                    {comment.sentiment}
                  </span>

                  {/* Intent tag */}
                  {comment.intent && comment.intent !== 'unknown' && (
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-300 capitalize">
                      {comment.intent}
                    </span>
                  )}

                  {comment.is_collaboration_opportunity && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-pink-500/10 text-pink-400 flex items-center gap-1">
                      <UserCheck className="w-3 h-3" /> Collab Opportunity
                    </span>
                  )}
                </div>
              </div>

              {/* Text */}
              <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">{comment.text}</p>

              {/* Post reference if available */}
              {comment.post_caption && (
                <p className="text-[11px] text-slate-500 truncate">
                  On post: "{comment.post_caption}"
                </p>
              )}

              {/* Actions Footer */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3 text-slate-400">
                  <span className="flex items-center gap-1">
                    <Heart className="w-3.5 h-3.5 text-pink-400" />
                    <span>{comment.like_count}</span>
                  </span>
                  {comment.analysis_summary && (
                    <span className="text-[11px] text-slate-500 italic hidden sm:inline">
                      "{comment.analysis_summary}"
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleOpenReplyModal(comment)}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-semibold border border-indigo-500/30 transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Suggest AI Reply</span>
                  </button>

                  <button
                    onClick={() => handleDeleteComment(comment.id)}
                    className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-500 hover:text-rose-400 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="h-48 rounded-2xl bg-slate-900/30 border border-dashed border-slate-800 flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
          <MessageCircle className="w-6 h-6 text-slate-600" />
          <p>No comments match your filter criteria.</p>
        </div>
      )}

      {/* Suggest Reply Modal */}
      {replyModalComment && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-xl rounded-2xl shadow-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <h3 className="font-semibold text-white text-sm">Gemini AI Reply Assistant</h3>
              </div>
              <button
                onClick={() => setReplyModalComment(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* Comment preview */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <p className="text-xs font-semibold text-indigo-300">@{replyModalComment.author_username}</p>
              <p className="text-xs text-slate-200">"{replyModalComment.text}"</p>
            </div>

            {/* Tone selector */}
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-slate-300">Reply Tone</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'friendly', label: 'Warm & Friendly' },
                  { id: 'professional', label: 'Professional' },
                  { id: 'humorous', label: 'Witty & Fun' },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setReplyTone(t.id)}
                    className={`py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                      replyTone === t.id
                        ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleGenerateReply}
              disabled={isGeneratingReply}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              {isGeneratingReply ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>{isGeneratingReply ? 'Generating Suggestions...' : 'Generate 3 Reply Options'}</span>
            </button>

            {/* Suggestions list */}
            {replySuggestions.length > 0 && (
              <div className="space-y-2.5 pt-2 border-t border-slate-800">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                  Select a Suggested Reply:
                </span>
                {replySuggestions.map((suggestion, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 flex items-center justify-between gap-3 text-xs text-slate-200 transition-colors"
                  >
                    <p className="flex-1 leading-relaxed">{suggestion}</p>
                    <button
                      onClick={() => copyReply(suggestion, i)}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-colors shrink-0"
                    >
                      {copiedIndex === i ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-emerald-400">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
