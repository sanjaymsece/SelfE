import React, { useEffect, useState } from 'react';
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Clock,
  Eye,
  FileText,
  Heart,
  RefreshCw,
  Sparkles,
  Users,
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { AnalyticsReport, MetricOverview, PostingTimeRecommendation } from '../types';

export const AnalyticsPage: React.FC = () => {
  const { activeWorkspace } = useAuth();
  const [rangeDays, setRangeDays] = useState<number>(30);
  const [overview, setOverview] = useState<MetricOverview | null>(null);
  const [postingTimes, setPostingTimes] = useState<PostingTimeRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // AI Report generation state
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [currentReport, setCurrentReport] = useState<AnalyticsReport | null>(null);
  const [savedReports, setSavedReports] = useState<AnalyticsReport[]>([]);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isReportsListOpen, setIsReportsListOpen] = useState(false);

  const calculateDateRange = (days: number) => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - days);
    return {
      date_from: from.toISOString().split('T')[0],
      date_to: to.toISOString().split('T')[0],
    };
  };

  const loadData = async () => {
    if (!activeWorkspace) return;
    setIsLoading(true);
    setError(null);

    const { date_from, date_to } = calculateDateRange(rangeDays);

    try {
      const [ovData, ptData, reportsData] = await Promise.all([
        api.getOverview({ date_from, date_to }),
        api.getPostingTimes({ limit: 5 }),
        api.listReports().catch(() => ({ count: 0, results: [] })),
      ]);
      setOverview(ovData);
      setPostingTimes(ptData.recommendations || []);
      setSavedReports(reportsData.results || []);
    } catch (err: any) {
      console.error('Failed to load analytics', err);
      setError(err.message || 'Could not load analytics metrics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeWorkspace?.id, rangeDays]);

  const handleGenerateAiReport = async () => {
    if (!overview) return;
    setIsGeneratingAi(true);
    try {
      const rep = await api.generateReport(
        overview.date_range.date_from,
        overview.date_range.date_to
      );
      setCurrentReport(rep);
      setIsReportModalOpen(true);
      setSavedReports((prev) => [rep, ...prev]);
    } catch (err: any) {
      alert(`AI report error: ${err.message}`);
    } finally {
      setIsGeneratingAi(false);
    }
  };

  const renderGrowth = (val: number | null | undefined) => {
    if (val === null || val === undefined) return null;
    const isPositive = val >= 0;
    return (
      <span
        className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${
          isPositive ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
        }`}
      >
        {isPositive ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : <ArrowDownRight className="w-3 h-3 mr-0.5" />}
        {Math.abs(val).toFixed(1)}%
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Performance Analytics</h1>
          <p className="text-sm text-slate-400">
            Deterministic metrics calculated from simulated insights in{' '}
            <span className="text-indigo-400 font-medium">{activeWorkspace?.name}</span>
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Range Selector */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-1 flex items-center">
            {[7, 14, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setRangeDays(d)}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                  rangeDays === d
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>

          {/* AI Explain Button */}
          <button
            onClick={handleGenerateAiReport}
            disabled={isGeneratingAi || isLoading}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 via-violet-600 to-pink-500 hover:from-indigo-500 hover:to-pink-400 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
          >
            {isGeneratingAi ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
            )}
            <span>{isGeneratingAi ? 'Analyzing with Gemini...' : 'Explain with AI'}</span>
          </button>

          {/* Past Reports Button */}
          {savedReports.length > 0 && (
            <button
              onClick={() => setIsReportsListOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              <span>Reports ({savedReports.length})</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="h-64 flex flex-col items-center justify-center gap-3 text-slate-500">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
          <p className="text-sm">Calculating workspace metrics...</p>
        </div>
      ) : overview ? (
        <>
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium">Total Impressions</span>
                <Eye className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="flex items-baseline justify-between">
                <p className="text-2xl font-bold text-white tracking-tight">
                  {overview.totals.impressions.toLocaleString()}
                </p>
                {renderGrowth(overview.growth?.impressions)}
              </div>
              <p className="text-[11px] text-slate-500">Content views across accounts</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium">Unique Reach</span>
                <Users className="w-4 h-4 text-violet-400" />
              </div>
              <div className="flex items-baseline justify-between">
                <p className="text-2xl font-bold text-white tracking-tight">
                  {overview.totals.reach.toLocaleString()}
                </p>
                {renderGrowth(overview.growth?.reach)}
              </div>
              <p className="text-[11px] text-slate-500">Unique accounts reached</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium">Total Engagements</span>
                <Heart className="w-4 h-4 text-pink-400" />
              </div>
              <div className="flex items-baseline justify-between">
                <p className="text-2xl font-bold text-white tracking-tight">
                  {overview.totals.engagements.toLocaleString()}
                </p>
                {renderGrowth(overview.growth?.engagements)}
              </div>
              <p className="text-[11px] text-slate-500">
                {overview.totals.likes} likes • {overview.totals.comments} comments • {overview.totals.shares} shares
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium">Engagement Rate</span>
                <BarChart3 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="flex items-baseline justify-between">
                <p className="text-2xl font-bold text-white tracking-tight">
                  {overview.totals.engagement_rate.toFixed(2)}%
                </p>
                {renderGrowth(overview.growth?.engagement_rate)}
              </div>
              <p className="text-[11px] text-slate-500">Across {overview.totals.posts_count} simulated posts</p>
            </div>
          </div>

          {/* Performance Daily Visualizer & Posting Times */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Daily Trend */}
            <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Daily Performance Breakdown</h3>
                  <p className="text-xs text-slate-400">Impressions vs Reach over time</p>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-indigo-500"></span>
                    <span className="text-slate-300">Impressions</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-violet-400"></span>
                    <span className="text-slate-300">Reach</span>
                  </div>
                </div>
              </div>

              {/* Chart simulation bars */}
              {overview.daily && overview.daily.length > 0 ? (
                <div className="h-48 flex items-end gap-1.5 pt-6 pb-2 border-b border-slate-800/80 overflow-x-auto">
                  {(() => {
                    const maxVal = Math.max(...overview.daily.map((d) => d.impressions), 1);
                    return overview.daily.map((day, idx) => {
                      const impHeight = Math.max((day.impressions / maxVal) * 100, 6);
                      const reachHeight = Math.max((day.reach / maxVal) * 100, 4);
                      return (
                        <div
                          key={idx}
                          className="flex-1 min-w-[14px] flex flex-col items-center gap-1 group relative cursor-pointer"
                        >
                          <div className="w-full flex items-end justify-center gap-0.5 h-36">
                            <div
                              style={{ height: `${impHeight}%` }}
                              className="w-1.5 bg-indigo-500/80 rounded-t-sm group-hover:bg-indigo-400 transition-all"
                            ></div>
                            <div
                              style={{ height: `${reachHeight}%` }}
                              className="w-1.5 bg-violet-400/60 rounded-t-sm group-hover:bg-violet-300 transition-all"
                            ></div>
                          </div>
                          <span className="text-[9px] text-slate-500 rotate-45 sm:rotate-0 truncate">
                            {day.date.slice(5)}
                          </span>

                          {/* Hover Tooltip */}
                          <div className="absolute -top-12 left-1/2 -translate-x-1/2 hidden group-hover:block bg-slate-950 border border-slate-700 px-2 py-1 rounded shadow-xl text-[10px] text-slate-200 z-20 whitespace-nowrap">
                            <p className="font-semibold">{day.date}</p>
                            <p className="text-indigo-400">Impr: {day.impressions}</p>
                            <p className="text-violet-400">Reach: {day.reach}</p>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              ) : (
                <div className="h-44 flex items-center justify-center text-slate-500 text-xs">
                  No daily insights in this range.
                </div>
              )}
            </div>

            {/* Recommended Posting Times */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center gap-2 text-indigo-400">
                <Clock className="w-4 h-4" />
                <h3 className="text-sm font-semibold text-white">Optimal Posting Slots</h3>
              </div>
              <p className="text-xs text-slate-400">
                Calculated from simulated historical engagement in {activeWorkspace?.timezone}
              </p>

              <div className="space-y-2.5 pt-1">
                {postingTimes.length > 0 ? (
                  postingTimes.map((slot, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-800/40 border border-slate-800/80 flex items-center justify-between text-xs hover:border-slate-700 transition-colors"
                    >
                      <div>
                        <p className="font-semibold text-slate-200">
                          {slot.day_of_week} @ {slot.hour_display}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          Sample size: {slot.sample_posts} posts
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="font-bold text-emerald-400">
                          {slot.average_engagement_rate.toFixed(2)}%
                        </span>
                        <p className="text-[10px] text-slate-500 uppercase">{slot.confidence} conf.</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic">No recommendations available yet.</p>
                )}
              </div>
            </div>
          </div>

          {/* Top Performing Posts */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-semibold text-white">Top Performing Posts</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/50 text-slate-400 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="p-3 rounded-l-lg">Post / Caption</th>
                    <th className="p-3">Format</th>
                    <th className="p-3">Published</th>
                    <th className="p-3">Impressions</th>
                    <th className="p-3">Reach</th>
                    <th className="p-3">Engagements</th>
                    <th className="p-3 rounded-r-lg">Engagement Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {overview.top_posts && overview.top_posts.length > 0 ? (
                    overview.top_posts.map((post) => (
                      <tr key={post.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="p-3 max-w-xs font-medium text-slate-200 truncate">
                          {post.caption || 'Simulated Post'}
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 font-medium capitalize">
                            {post.media_type}
                          </span>
                        </td>
                        <td className="p-3 text-slate-400">
                          {post.published_at ? new Date(post.published_at).toLocaleDateString() : '—'}
                        </td>
                        <td className="p-3">{post.impressions?.toLocaleString()}</td>
                        <td className="p-3">{post.reach?.toLocaleString()}</td>
                        <td className="p-3 font-semibold text-indigo-300">{post.engagement?.toLocaleString()}</td>
                        <td className="p-3 font-bold text-emerald-400">
                          {post.engagement_rate?.toFixed(2)}%
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="p-4 text-center text-slate-500">
                        No posts found for this period.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}

      {/* AI Report Modal */}
      {isReportModalOpen && currentReport && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col animate-in fade-in zoom-in-95">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-gradient-to-r from-indigo-900/30 to-purple-900/20">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-lg bg-indigo-600/30 text-indigo-400 flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-semibold text-white text-base">Gemini AI Executive Diagnosis</h3>
                  <p className="text-xs text-slate-400">Model: {currentReport.model_used}</p>
                </div>
              </div>
              <button
                onClick={() => setIsReportModalOpen(false)}
                className="h-8 w-8 rounded-lg bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-5 text-sm">
              <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-800/40 text-indigo-200">
                <p className="font-semibold text-xs text-indigo-400 uppercase tracking-wider mb-1">
                  Executive Summary
                </p>
                <p className="leading-relaxed">{currentReport.summary}</p>
              </div>

              {currentReport.growth_explanation && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Growth Context
                  </h4>
                  <p className="text-slate-300 leading-relaxed text-xs">
                    {currentReport.growth_explanation}
                  </p>
                </div>
              )}

              {currentReport.key_findings && currentReport.key_findings.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Key Performance Findings
                  </h4>
                  <ul className="space-y-1.5">
                    {currentReport.key_findings.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                        <span className="text-indigo-400 font-bold">•</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {currentReport.recommendations && currentReport.recommendations.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                    Strategic Recommendations
                  </h4>
                  <ul className="space-y-2">
                    {currentReport.recommendations.map((r, i) => (
                      <li
                        key={i}
                        className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60 text-xs text-slate-200 flex items-start gap-2"
                      >
                        <span className="h-5 w-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex justify-end">
              <button
                onClick={() => setIsReportModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
              >
                Close Diagnosis
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Past Reports List Modal */}
      {isReportsListOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-xl rounded-2xl shadow-2xl p-6 space-y-4 max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-white">Generated AI Reports History</h3>
              <button
                onClick={() => setIsReportsListOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="overflow-y-auto space-y-3">
              {savedReports.map((rep) => (
                <div
                  key={rep.id}
                  onClick={() => {
                    setCurrentReport(rep);
                    setIsReportsListOpen(false);
                    setIsReportModalOpen(true);
                  }}
                  className="p-3.5 rounded-xl bg-slate-800/40 hover:bg-slate-800 border border-slate-800 cursor-pointer transition-colors space-y-1"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-indigo-400">
                      {rep.date_from} → {rep.date_to}
                    </span>
                    <span className="text-slate-500 text-[10px]">
                      {new Date(rep.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 line-clamp-2">{rep.summary}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
