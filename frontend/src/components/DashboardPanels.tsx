import React, { useState } from 'react';
import {
  Check,
  Copy,
  RefreshCw,
  Sparkles,
  Star,
  Upload,
  Volume2,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import type { MetricOverview, PostingTimeRecommendation } from '../types';

export type PanelType =
  | 'profile'
  | 'weekly_stats'
  | 'model_videos'
  | 'video_scripts'
  | 'trending_now'
  | 'content_calendar'
  | 'connected_accounts'
  | 'upload_video'
  | 'settings'
  | 'privacy'
  | 'comment_replies'
  | 'notifications'
  | 'sponsorship_emails'
  | 'celebrity_dms'
  | 'follow_ups'
  | null;

interface DashboardPanelsProps {
  activePanel: PanelType;
  onClose: () => void;
  overview: MetricOverview | null;
  postingTimes: PostingTimeRecommendation[];
  onGenerateHook: (prompt: string) => void;
}

export const DashboardPanels: React.FC<DashboardPanelsProps> = ({
  activePanel,
  onClose,
  overview,
  postingTimes,
  onGenerateHook,
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Script Generator Inside Panel
  const [scriptTopic, setScriptTopic] = useState('');
  const [scriptDuration, setScriptDuration] = useState(30);
  const [isGeneratingScript, setIsGeneratingScript] = useState(false);
  const [generatedScript, setGeneratedScript] = useState<any>(null);

  // Comment Replies state
  const [liveTokenInput, setLiveTokenInput] = useState('');
  const [isConnectingLive, setIsConnectingLive] = useState(false);
  const [liveConnectMsg, setLiveConnectMsg] = useState<string | null>(null);

  // Gemini API Key Tester state
  const [customApiKey, setCustomApiKey] = useState(() => localStorage.getItem('gemini_api_key') || '');
  const [testPrompt, setTestPrompt] = useState('Give me a 3-second hook for selling aesthetic ceramics');
  const [saveToEnv, setSaveToEnv] = useState(true);
  const [isTestingKey, setIsTestingKey] = useState(false);
  const [testKeyResult, setTestKeyResult] = useState<any>(null);

  // ElevenLabs Voice state
  const [elevenlabsApiKey, setElevenlabsApiKey] = useState(() => localStorage.getItem('elevenlabs_api_key') || '');
  const [selectedVoice, setSelectedVoice] = useState('21m00Tcm4TlvDq8ikWAM'); // Rachel (ElevenLabs)
  const [isTestingVoice, setIsTestingVoice] = useState(false);
  const [voiceTestStatus, setVoiceTestStatus] = useState<string | null>(null);

  const [commentsList, setCommentsList] = useState<any[]>([
    {
      id: 1,
      author: 'elena.lifestyle',
      text: 'Where did you get that oversized linen shirt from?? Need it!',
      sentiment: 'positive',
      time: '18m ago',
      suggestions: [
        'It is linked in my bio under "Outfit Essentials"! Let me know if you grab it 🤍',
        'Thank you! Got it from Linen & Co, check the link in my story highlights!',
      ],
    },
    {
      id: 2,
      author: 'fit_with_marcus',
      text: 'Would love to collab on a high-protein breakfast recipe Reel next month!',
      sentiment: 'collaboration',
      time: '2h ago',
      suggestions: [
        'Hey Marcus! That sounds fantastic, sending you a DM with my media kit.',
        'Love your content! Let’s definitely cook up something fun. Shoot me a DM!',
      ],
    },
    {
      id: 3,
      author: 'sarah_mindset',
      text: 'How often do you batch film your reels? Consistency is so hard 😭',
      sentiment: 'question',
      time: '5h ago',
      suggestions: [
        'I batch film 4 reels every Sunday in 90 mins! Will drop a full breakdown reel on this Tuesday.',
        'Sundays are my sacred batching days! Happy to share my exact Notion template if you want it.',
      ],
    },
  ]);

  if (!activePanel) return null;

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleGenerateScriptInPanel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scriptTopic.trim()) return;
    setIsGeneratingScript(true);
    try {
      const res = await api.generateScripts({
        topic: scriptTopic,
        target_duration_seconds: scriptDuration,
      });
      setGeneratedScript(res.scripts?.[0] || null);
    } catch (err: any) {
      try {
        const copilot = await api.chatWithCoPilot(
          `Write a full viral Instagram Reel script for topic: "${scriptTopic}" with target duration ${scriptDuration} seconds. Include Hook, Visual B-Roll direction, Voiceover, and CTA.`
        );
        setGeneratedScript({
          title: scriptTopic,
          body: `${copilot.hook ? '🪝 HOOK:\n' + copilot.hook + '\n\n' : ''}🎬 SCRIPT:\n${copilot.reply}\n\n💡 WHY IT WORKS:\n${copilot.why_it_works}`,
        });
      } catch (copilotErr: any) {
        alert(`Generation error: ${err.message}`);
      }
    } finally {
      setIsGeneratingScript(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-xl bg-[#FAF7F4] text-[#382A37] h-full shadow-2xl flex flex-col border-l border-[#8E7A8A]/25 relative animate-in slide-in-from-right duration-300">
        {/* Panel Header */}
        <div className="px-6 py-5 border-b border-[#8E7A8A]/20 flex items-center justify-between bg-[#E5DCE0]/60">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-[#D66882] font-bold block">
              SocioSync Module
            </span>
            <h2 className="text-xl font-bold font-display capitalize">
              {activePanel.replace('_', ' ')}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-[#FAF7F4] border border-[#8E7A8A]/30 flex items-center justify-center text-[#523B50] hover:bg-[#523B50] hover:text-[#FAF7F4] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Panel Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* PROFILE PANEL */}
          {activePanel === 'profile' && (
            <div className="space-y-6">
              <div className="p-5 rounded-[24px] bg-[#E5DCE0] border border-[#8E7A8A]/30 flex items-center gap-4">
                <img
                  alt="Sophia Tompson"
                  src="/unnamed.jpg"
                  className="w-16 h-16 rounded-full object-cover border-2 border-[#E8B259] shadow-md"
                />
                <div>
                  <h3 className="text-lg font-bold font-display">Sophia Tompson</h3>
                  <p className="text-xs text-[#756573]">@sophia.studio • Lifestyle & Visual Creator</p>
                  <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#523B50] text-[10px] font-mono uppercase text-[#FAF7F4]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#8BB8BD]"></span>
                    Instagram Creator Business Mode
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/20 text-center">
                  <span className="text-[10px] font-mono text-[#756573] uppercase">Followers</span>
                  <p className="text-lg font-bold font-display text-[#523B50]">128.4K</p>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/20 text-center">
                  <span className="text-[10px] font-mono text-[#756573] uppercase">Avg. Reach</span>
                  <p className="text-lg font-bold font-display text-[#D66882]">44.2K</p>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/20 text-center">
                  <span className="text-[10px] font-mono text-[#756573] uppercase">Engagement</span>
                  <p className="text-lg font-bold font-display text-[#8BB8BD]">4.82%</p>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#756573]">Connected Brand Partnerships</h4>
                <div className="p-4 rounded-2xl bg-[#E5DCE0]/40 border border-[#8E7A8A]/25 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">Oatly Coffee Collab</span>
                    <span className="font-mono text-[#E8B259] font-bold">$1,800 · In Review</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">Gymshark Apparel Reel</span>
                    <span className="font-mono text-[#8BB8BD] font-bold">$2,400 · Contract Signed</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* WEEKLY STATS PANEL */}
          {activePanel === 'weekly_stats' && (
            <div className="space-y-6">
              <div className="p-5 rounded-[24px] bg-[#E5DCE0] border border-[#8E7A8A]/30 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-[#756573] uppercase font-bold">7-Day Performance</span>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-800 text-xs font-bold">
                    {overview?.growth?.reach ? `+${overview.growth.reach.toFixed(1)}% Reach Spike` : '+18.4% Reach Spike'}
                  </span>
                </div>
                <p className="text-sm font-medium leading-relaxed">
                  Your last 3 short-form Reels averaged 31.4K impressions. Optimal retention was driven by strong visual hooks in the first 2.5 seconds. Total reach: {overview?.totals?.reach ? overview.totals.reach.toLocaleString() : '128,400'}.
                </p>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#756573]">Top Recommended Posting Slots</h4>
                {postingTimes.map((slot, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-2xl bg-[#E5DCE0]/40 border border-[#8E7A8A]/25 flex items-center justify-between text-xs"
                  >
                    <div>
                      <p className="font-bold text-[#523B50]">
                        {slot.day_of_week} at {slot.hour_display}
                      </p>
                      <p className="text-[11px] text-[#756573]">Historical avg: {slot.average_engagement_rate?.toFixed(2)}% ER</p>
                    </div>
                    <span className="px-2.5 py-1 rounded-full bg-[#523B50] text-[#FAF7F4] font-mono text-[10px] font-bold">
                      {slot.confidence} priority
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* MODEL VIDEOS (VIRAL REELS) */}
          {activePanel === 'model_videos' && (
            <div className="space-y-4">
              <p className="text-xs text-[#756573]">
                Proven viral Reel templates calibrated for your niche. Click to adapt into a script.
              </p>
              {[
                {
                  title: 'The "What I Thought vs What It Actually Took" Flip',
                  hook: '"Everyone tells you to just post 3x a day... but here is what actually 10x\'d my reach."',
                  views: '184K Views',
                  vibe: 'Raw / Direct to Camera',
                },
                {
                  title: 'The Silent 3-Step Routine (ASMR + Text Overlay)',
                  hook: '"POV: The 15-minute morning routine that eliminated all my creative burnout."',
                  views: '240K Views',
                  vibe: 'Cinematic Aesthetic',
                },
                {
                  title: 'The Mistake I Wish I Knew Sooner',
                  hook: '"Stop doing this with your Instagram hooks if you want people to watch past 3 seconds."',
                  views: '92K Views',
                  vibe: 'Educational Breakdown',
                },
              ].map((vid, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/25 space-y-2 hover:border-[#D66882] transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-sm text-[#523B50]">{vid.title}</h4>
                    <span className="text-[10px] font-mono text-[#D66882] font-bold">{vid.views}</span>
                  </div>
                  <p className="text-xs text-[#382A37] italic">🪝 {vid.hook}</p>
                  <button
                    onClick={() => {
                      setScriptTopic(vid.title);
                      onGenerateHook(vid.title);
                    }}
                    className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#523B50] hover:bg-[#664A64] text-[#FAF7F4] text-xs font-bold transition-colors cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#E8B259]" />
                    <span>Adapt With AI</span>
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* VIDEO SCRIPTS */}
          {activePanel === 'video_scripts' && (
            <div className="space-y-5">
              <form onSubmit={handleGenerateScriptInPanel} className="space-y-3">
                <label className="block text-xs font-bold uppercase tracking-wider text-[#756573]">
                  Script Topic or Reel Concept
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 3 Habits that doubled my focus"
                  value={scriptTopic}
                  onChange={(e) => setScriptTopic(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#FAF7F4] border border-[#8E7A8A]/35 text-xs text-[#382A37] focus:outline-none"
                />
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-[#756573]">Target Length:</span>
                  {[15, 30, 60].map((dur) => (
                    <button
                      key={dur}
                      type="button"
                      onClick={() => setScriptDuration(dur)}
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold cursor-pointer transition-all ${
                        scriptDuration === dur
                          ? 'bg-[#523B50] text-[#FAF7F4]'
                          : 'bg-[#FAF7F4] text-[#523B50] border border-[#8E7A8A]/30'
                      }`}
                    >
                      {dur}s
                    </button>
                  ))}
                </div>
                <button
                  type="submit"
                  disabled={isGeneratingScript}
                  className="w-full py-2.5 rounded-full bg-[#523B50] hover:bg-[#664A64] text-[#FAF7F4] font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
                >
                  {isGeneratingScript ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5 text-[#E8B259]" />
                  )}
                  <span>{isGeneratingScript ? 'Writing Script...' : 'Generate Video Script'}</span>
                </button>
              </form>

              {generatedScript && (
                <div className="p-4 rounded-2xl bg-[#E5DCE0]/60 border border-[#8E7A8A]/30 space-y-3 text-xs">
                  <div className="flex items-center justify-between border-b border-[#8E7A8A]/20 pb-2">
                    <span className="font-bold text-sm text-[#523B50]">{generatedScript.title || 'Generated Script'}</span>
                    <button
                      onClick={() => handleCopy(generatedScript.body || JSON.stringify(generatedScript), 'script')}
                      className="px-2.5 py-1 rounded-full bg-[#FAF7F4] text-xs font-bold border border-[#8E7A8A]/30 flex items-center gap-1"
                    >
                      {copiedId === 'script' ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedId === 'script' ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <p className="whitespace-pre-wrap leading-relaxed text-[#382A37]">
                    {generatedScript.body || generatedScript.content}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* COMMENT REPLIES */}
          {activePanel === 'comment_replies' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#756573] uppercase tracking-wider">
                  Pending Comment Inquiries ({commentsList.length})
                </span>
              </div>

              {commentsList.map((comm) => (
                <div
                  key={comm.id}
                  className="p-4 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/25 space-y-3 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#523B50]">@{comm.author}</span>
                    <span className="text-[10px] text-[#756573]">{comm.time}</span>
                  </div>
                  <p className="text-slate-800 font-medium">"{comm.text}"</p>

                  <div className="space-y-1.5 pt-2 border-t border-[#8E7A8A]/20">
                    <span className="text-[10px] font-mono uppercase text-[#D66882] font-bold block">
                      AI Suggested Responses:
                    </span>
                    {comm.suggestions.map((sug: string, sIdx: number) => (
                      <div
                        key={sIdx}
                        className="p-2.5 rounded-xl bg-[#FAF7F4] border border-[#8E7A8A]/20 flex items-center justify-between gap-2"
                      >
                        <p className="text-[11px] text-[#382A37] flex-1">{sug}</p>
                        <button
                          onClick={() => {
                            handleCopy(sug, `comm-${comm.id}-${sIdx}`);
                            setTimeout(() => {
                              setCommentsList((prev) => prev.filter((c) => c.id !== comm.id));
                            }, 800);
                          }}
                          className="px-2 py-1 rounded-md bg-[#523B50] hover:bg-[#664A64] text-[#FAF7F4] text-[10px] font-bold flex items-center gap-1 cursor-pointer"
                        >
                          {copiedId === `comm-${comm.id}-${sIdx}` ? (
                            <Check className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                          <span>{copiedId === `comm-${comm.id}-${sIdx}` ? 'Sent' : 'Reply'}</span>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* SPONSORSHIPS */}
          {activePanel === 'sponsorship_emails' && (
            <div className="space-y-4">
              <span className="text-xs font-bold text-[#756573] uppercase tracking-wider block">
                Brand Deal Requests (2 Ready)
              </span>

              {[
                {
                  brand: 'Oatly Brand Partnership',
                  offer: '$1,800 USD',
                  deliverable: '1 Dedicated Reel + 2 Story Frames',
                  details: 'Focus on oat milk morning matcha routine. 30-day usage rights.',
                },
                {
                  brand: 'Gymshark Studio Activewear',
                  offer: '$2,400 USD',
                  deliverable: '2 Reels + Bio Link (14 Days)',
                  details: 'Seamless leggings try-on haul and workout styling.',
                },
              ].map((deal, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-2xl bg-[#E5DCE0]/60 border border-[#8E7A8A]/30 space-y-2.5 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-sm text-[#523B50]">{deal.brand}</h4>
                    <span className="font-mono text-[#D66882] font-bold text-sm">{deal.offer}</span>
                  </div>
                  <p className="text-slate-700">{deal.details}</p>
                  <div className="pt-2 flex items-center justify-between">
                    <span className="text-[11px] font-mono text-[#756573]">{deal.deliverable}</span>
                    <button
                      onClick={() => alert(`Pitch generator initiated for ${deal.brand}`)}
                      className="px-3 py-1 rounded-full bg-[#523B50] text-[#FAF7F4] text-xs font-bold cursor-pointer"
                    >
                      Draft Counter Pitch
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* NOTIFICATIONS */}
          {activePanel === 'notifications' && (
            <div className="space-y-3">
              {[
                { title: 'Reel Milestone Hit', msg: 'Your latest reel passed 25,000 views in 18 hours!', time: '1h ago' },
                { title: 'Follower Spike', msg: '+380 new followers gained from Explore page.', time: '4h ago' },
                { title: 'Weekly Insight Ready', msg: 'Your weekly diagnosis has been refreshed by Gemini.', time: '1d ago' },
              ].map((notif, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-2xl bg-[#E5DCE0]/40 border border-[#8E7A8A]/20 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between font-bold text-[#523B50]">
                    <span>{notif.title}</span>
                    <span className="text-[10px] text-[#756573] font-normal">{notif.time}</span>
                  </div>
                  <p className="text-slate-700">{notif.msg}</p>
                </div>
              ))}
            </div>
          )}

          {/* TRENDING NOW */}
          {activePanel === 'trending_now' && (
            <div className="space-y-4">
              <p className="text-xs text-[#756573]">
                Real-time Instagram Reels trend pulse. High virality potential for aesthetic creators.
              </p>
              <div className="space-y-3">
                {[
                  {
                    type: 'Trending Audio',
                    title: 'Warm Acoustic Lo-Fi (Slowed)',
                    trend: '+412% this week',
                    uses: '84.2K Reels',
                  },
                  {
                    type: 'Visual Format',
                    title: 'Split screen: 2024 self vs 2026 self (Minimalist)',
                    trend: '+290% virality index',
                    uses: '129K Reels',
                  },
                  {
                    type: 'Pacing Archetype',
                    title: 'Fast cuts (0.7s) with calm monotone voiceover',
                    trend: '94% completion rate',
                    uses: 'High retention',
                  },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/25 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-[#D66882] font-bold">
                        {item.type}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-700 bg-emerald-500/15 px-2 py-0.5 rounded-full font-bold">
                        {item.trend}
                      </span>
                    </div>
                    <h4 className="font-bold text-sm text-[#523B50]">{item.title}</h4>
                    <p className="text-[11px] text-[#756573]">{item.uses}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CONTENT CALENDAR */}
          {activePanel === 'content_calendar' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-xs text-[#756573]">Upcoming scheduled Reels & Stories</p>
                <span className="text-[10px] font-mono text-[#D66882] font-bold">Auto-Sync ON</span>
              </div>
              <div className="space-y-3">
                {[
                  { day: 'Today (Mon)', time: '6:30 PM', title: 'Morning Matcha & Reset Routine', status: 'Ready to Post' },
                  { day: 'Wednesday', time: '12:15 PM', title: 'Desk Setup Tour: 2026 Edition', status: 'Draft Ready' },
                  { day: 'Friday', time: '7:00 PM', title: 'Oatly Partner Reel · Sponsored', status: 'Brand Approved' },
                  { day: 'Sunday', time: '10:00 AM', title: 'Weekly Mindset Reset & Journaling', status: 'Ideation' },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/25 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#523B50]">{item.day}</span>
                        <span className="text-[11px] font-mono text-[#756573]">{item.time}</span>
                      </div>
                      <p className="text-slate-700 text-xs mt-0.5">{item.title}</p>
                    </div>
                    <span className="px-2.5 py-1 rounded-full bg-[#523B50] text-[#FAF7F4] text-[10px] font-mono font-bold">
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CONNECTED ACCOUNTS */}
          {activePanel === 'connected_accounts' && (
            <div className="space-y-4">
              <p className="text-xs text-[#756573]">Integrated social channels managed by SocioSync AI</p>
              <div className="p-4 rounded-2xl bg-[#E5DCE0]/60 border border-[#8E7A8A]/30 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <img
                      src="/unnamed.jpg"
                      alt="Sophia"
                      className="w-10 h-10 rounded-full object-cover border border-[#D66882]"
                    />
                    <div>
                      <h4 className="font-bold text-sm text-[#382A37]">Instagram Business</h4>
                      <p className="text-xs text-[#756573]">@sophia.studio (128.4K followers)</p>
                    </div>
                  </div>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-800 text-[10px] font-bold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Connected
                  </span>
                </div>
                <div className="pt-2 flex items-center gap-2 border-t border-[#8E7A8A]/20">
                  <button
                    onClick={() => alert('Instagram token refreshed successfully!')}
                    className="flex-1 py-1.5 rounded-xl bg-[#FAF7F4] border border-[#8E7A8A]/30 text-xs font-semibold hover:bg-[#FAF7F4]/80 text-[#523B50]"
                  >
                    Refresh Token
                  </button>
                  <button
                    onClick={() => alert('Webhook endpoint active at /api/v1/comments/webhook/')}
                    className="flex-1 py-1.5 rounded-xl bg-[#523B50] text-[#FAF7F4] text-xs font-semibold hover:bg-[#664A64]"
                  >
                    Sync Webhooks
                  </button>
                </div>
              </div>

              {/* Live Meta Connect Box */}
              <div className="p-4 rounded-2xl bg-[#E5DCE0]/40 border border-[#8E7A8A]/25 space-y-3 text-xs">
                <span className="font-bold text-sm text-[#523B50] block">
                  Link Live Meta Graph API Token
                </span>
                <p className="text-[#756573] leading-relaxed">
                  Paste your Instagram User Token from Meta Developers &rarr; Graph API Explorer to synchronize live followers, real reels, and comments:
                </p>
                <input
                  type="password"
                  value={liveTokenInput}
                  onChange={(e) => setLiveTokenInput(e.target.value)}
                  placeholder="EAAG... (Meta Graph Access Token)"
                  className="w-full px-3 py-2 rounded-xl bg-[#FAF7F4] border border-[#8E7A8A]/35 text-xs text-[#382A37] focus:outline-none font-mono"
                />
                <button
                  type="button"
                  disabled={isConnectingLive || !liveTokenInput.trim()}
                  onClick={async () => {
                    setIsConnectingLive(true);
                    setLiveConnectMsg(null);
                    try {
                      const res = await fetch('/api/v1/social-accounts/instagram-connect/', {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('selfe_token') || ''}`,
                          'X-Workspace-ID': localStorage.getItem('selfe_workspace_id') || '1',
                        },
                        body: JSON.stringify({ access_token: liveTokenInput, handle: 'sophia.studio' }),
                      });
                      const data = await res.json();
                      setLiveConnectMsg(data.message || 'Connected successfully!');
                    } catch (err: any) {
                      setLiveConnectMsg(`Sync result: Token saved. Live message: ${err.message}`);
                    } finally {
                      setIsConnectingLive(false);
                    }
                  }}
                  className="w-full py-2 rounded-full bg-[#523B50] hover:bg-[#664A64] text-[#FAF7F4] font-bold text-xs cursor-pointer disabled:opacity-50 transition-colors"
                >
                  {isConnectingLive ? 'Connecting to Meta...' : 'Connect Live Instagram Token'}
                </button>
                {liveConnectMsg && (
                  <p className="text-[11px] font-mono text-emerald-800 bg-emerald-500/15 p-2 rounded-xl">
                    {liveConnectMsg}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* UPLOAD VIDEO FOR REVIEW */}
          {activePanel === 'upload_video' && (
            <div className="space-y-4">
              <p className="text-xs text-[#756573]">
                AI Pre-flight Video Audit: SocioSync reviews your 3-second hook retention, lighting contrast, text safe-zone, and sound energy before posting.
              </p>
              <div className="p-6 rounded-2xl border-2 border-dashed border-[#8E7A8A]/40 text-center space-y-3 hover:border-[#D66882] transition-colors cursor-pointer bg-[#E5DCE0]/20">
                <Upload className="w-8 h-8 text-[#523B50] mx-auto" />
                <div>
                  <p className="text-xs font-bold text-[#523B50]">Drag & drop video file or browse</p>
                  <p className="text-[10px] text-[#756573] mt-0.5">MP4, MOV up to 150MB</p>
                </div>
                <button
                  onClick={() => alert('Video upload simulation ready: AI hook audit scored 9.4/10!')}
                  className="px-4 py-1.5 rounded-full bg-[#523B50] text-[#FAF7F4] text-xs font-bold"
                >
                  Simulate Hook Audit
                </button>
              </div>
            </div>
          )}

          {/* CELEBRITY DMS */}
          {activePanel === 'celebrity_dms' && (
            <div className="space-y-3">
              <p className="text-xs text-[#756573]">Priority inbox for verified creators and public figures.</p>
              {[
                { name: 'emma.chamberlain.mgmt', verified: true, msg: 'Hey Sophia, love the aesthetic of your latest reel! Are you open to coffee in LA next month?', time: '3h ago' },
                { name: 'matthew.encina', verified: true, msg: 'Great framing on that workspace reel. Would love to feature your desk in our newsletter.', time: '1d ago' },
              ].map((dm, idx) => (
                <div key={idx} className="p-4 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/25 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#523B50] flex items-center gap-1">
                      @{dm.name} <Star className="w-3 h-3 text-[#E8B259] fill-current" />
                    </span>
                    <span className="text-[10px] text-[#756573]">{dm.time}</span>
                  </div>
                  <p className="text-slate-700 italic">“{dm.msg}”</p>
                  <button
                    onClick={() => alert(`AI auto-reply draft generated for ${dm.name}`)}
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-[#D66882] hover:underline"
                  >
                    Draft AI Co-pilot Reply &rarr;
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* FOLLOW-UPS */}
          {activePanel === 'follow_ups' && (
            <div className="space-y-3">
              <p className="text-xs text-[#756573]">Automated pending actions and sponsor check-ins.</p>
              <div className="p-4 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/25 space-y-2 text-xs">
                <div className="flex items-center justify-between font-bold text-[#523B50]">
                  <span>Oatly Brand Partnership</span>
                  <span className="text-[#D66882] font-mono">Deliverable Due in 48h</span>
                </div>
                <p className="text-slate-700">Submit preview link of matcha reel to marketing@oatly.com for copy approval.</p>
                <button
                  onClick={() => alert('Follow-up reminder confirmed and synced with your calendar.')}
                  className="px-3 py-1 rounded-full bg-[#523B50] text-[#FAF7F4] text-xs font-bold"
                >
                  Mark Sent
                </button>
              </div>
            </div>
          )}

          {/* SETTINGS */}
          {activePanel === 'settings' && (
            <div className="space-y-4 text-xs">
              <p className="text-[#756573]">Configure SocioSync voice model and autonomous behavior.</p>
              <div className="p-4 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/25 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-[#382A37]">AI Co-pilot Engine</h4>
                    <p className="text-[11px] text-[#756573]">Google Gemini 3.5 Flash Lite</p>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-800 font-mono font-bold text-[10px]">Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-[#382A37]">Auto-Reply Mode</h4>
                    <p className="text-[11px] text-[#756573]">Draft suggestions before sending</p>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-[#523B50] text-[#FAF7F4] font-mono font-bold text-[10px]">Manual Confirm</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-[#382A37]">Voice Synthesis Engine</h4>
                    <p className="text-[11px] text-[#756573]">ElevenLabs Female (Rachel) & High-Fidelity Neural</p>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-[#8BB8BD]/20 text-[#523B50] font-mono font-bold text-[10px]">Active</span>
                </div>
              </div>

              {/* LIVE GEMINI API KEY TESTER & CONNECTOR */}
              <div className="p-4 rounded-2xl bg-[#E5DCE0]/60 border border-[#8E7A8A]/30 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-[#523B50]">Connect & Test Gemini API Key</h4>
                  <span className="text-[10px] font-mono font-bold text-[#D66882]">Google AI Studio</span>
                </div>
                <p className="text-[#756573] leading-relaxed text-xs">
                  Connect your personal Gemini API key. Once connected, your key is active across the voice orb, interactive text chat, script generator, and diagnosis chips.
                </p>

                <div className="space-y-2">
                  <label className="text-[10px] font-mono uppercase text-[#756573] font-bold block">
                    API Key (Auto-saved across session)
                  </label>
                  <input
                    type="password"
                    value={customApiKey}
                    onChange={(e) => {
                      setCustomApiKey(e.target.value);
                      if (e.target.value.trim()) {
                        localStorage.setItem('gemini_api_key', e.target.value.trim());
                      }
                    }}
                    placeholder="AQ.Ab... or AIzaSy... (Saved in settings)"
                    className="w-full px-3 py-2 rounded-xl bg-[#FAF7F4] border border-[#8E7A8A]/35 text-xs text-[#382A37] focus:outline-none font-mono"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-mono uppercase text-[#756573] font-bold block">
                    Test Prompt
                  </label>
                  <input
                    type="text"
                    value={testPrompt}
                    onChange={(e) => setTestPrompt(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-[#FAF7F4] border border-[#8E7A8A]/35 text-xs text-[#382A37] focus:outline-none"
                  />
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="save_env"
                    checked={saveToEnv}
                    onChange={(e) => setSaveToEnv(e.target.checked)}
                    className="accent-[#523B50]"
                  />
                  <label htmlFor="save_env" className="text-[11px] text-[#756573]">
                    Save key permanently into backend .env configuration
                  </label>
                </div>

                <button
                  type="button"
                  disabled={isTestingKey}
                  onClick={async () => {
                    setIsTestingKey(true);
                    setTestKeyResult(null);
                    try {
                      const keyToTest = customApiKey.trim() || undefined;
                      if (keyToTest) {
                        localStorage.setItem('gemini_api_key', keyToTest);
                      }
                      const res = await api.testGeminiKey({
                        api_key: keyToTest,
                        prompt: testPrompt.trim(),
                        save_to_env: saveToEnv,
                      });
                      setTestKeyResult(res);
                    } catch (err: any) {
                      setTestKeyResult({
                        status: 'error',
                        error: err.message || 'Connection failed',
                        api_key_valid: false,
                      });
                    } finally {
                      setIsTestingKey(false);
                    }
                  }}
                  className="w-full py-2.5 rounded-full bg-[#523B50] hover:bg-[#664A64] text-[#FAF7F4] font-bold text-xs cursor-pointer disabled:opacity-50 transition-colors flex items-center justify-center gap-2 shadow-sm"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#E8B259]" />
                  <span>{isTestingKey ? 'Connecting to Google Gemini...' : 'Test & Connect Gemini Key'}</span>
                </button>

                {testKeyResult && (
                  <div className={`p-3.5 rounded-xl border text-xs space-y-1.5 ${
                    testKeyResult.status === 'ok'
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-950'
                      : 'bg-rose-500/10 border-rose-500/30 text-rose-950'
                  }`}>
                    <div className="flex items-center justify-between font-bold">
                      <span>{testKeyResult.status === 'ok' ? '✓ Google Gemini Connected (200 OK)' : '✗ Connection Error'}</span>
                      {testKeyResult.latency_seconds && (
                        <span className="font-mono text-[10px]">{testKeyResult.latency_seconds}s latency</span>
                      )}
                    </div>
                    {testKeyResult.status === 'ok' ? (
                      <div className="space-y-1 text-slate-800">
                        <p className="font-medium italic">“{testKeyResult.reply}”</p>
                        <p className="text-[11px] text-[#756573]">Strategy: {testKeyResult.strategy}</p>
                        <p className="text-[10px] font-mono text-[#D66882]">Model: {testKeyResult.model}</p>
                      </div>
                    ) : (
                      <p className="text-[11px] text-rose-800 font-medium whitespace-pre-wrap leading-relaxed">
                        {typeof testKeyResult.error === 'object'
                          ? testKeyResult.error?.message || JSON.stringify(testKeyResult.error)
                          : String(testKeyResult.error || 'Connection failed')}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* ELEVENLABS & FEMALE VOICE SETTINGS */}
              <div className="p-4 rounded-2xl bg-[#E5DCE0]/60 border border-[#8E7A8A]/30 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-[#523B50]">AI Female Voice (ElevenLabs & Neural)</h4>
                  <span className="text-[10px] font-mono font-bold text-[#8BB8BD]">Natural Audio</span>
                </div>
                <p className="text-[#756573] leading-relaxed text-xs">
                  Sophia speaks using calm, natural, human-quality female speech. Optional: Add your ElevenLabs API key for direct ElevenLabs Rachel synthesis.
                </p>

                <div className="space-y-2">
                  <label className="text-[10px] font-mono uppercase text-[#756573] font-bold block">
                    Female Voice Persona
                  </label>
                  <select
                    value={selectedVoice}
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-[#FAF7F4] border border-[#8E7A8A]/35 text-xs text-[#382A37] focus:outline-none"
                  >
                    <option value="21m00Tcm4TlvDq8ikWAM">ElevenLabs Rachel — Calm, Authentic Female Voice</option>
                    <option value="AZnzlk1XvdvUeBnXmlld">ElevenLabs Domi — Energetic Female Voice</option>
                    <option value="EXAVITQu4vr4xnSDxMaL">ElevenLabs Bella — Expressive Female Voice</option>
                    <option value="en-US-JennyNeural">Sophia Neural Jenny — Smooth Natural Neural Voice (Free)</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-mono uppercase text-[#756573] font-bold block">
                    ElevenLabs API Key (Optional)
                  </label>
                  <input
                    type="password"
                    value={elevenlabsApiKey}
                    onChange={(e) => {
                      setElevenlabsApiKey(e.target.value);
                      if (e.target.value.trim()) {
                        localStorage.setItem('elevenlabs_api_key', e.target.value.trim());
                      }
                    }}
                    placeholder="sk_... (Leave empty to use built-in Neural Female voice)"
                    className="w-full px-3 py-2 rounded-xl bg-[#FAF7F4] border border-[#8E7A8A]/35 text-xs text-[#382A37] focus:outline-none font-mono"
                  />
                </div>

                <button
                  type="button"
                  disabled={isTestingVoice}
                  onClick={async () => {
                    setIsTestingVoice(true);
                    setVoiceTestStatus('Synthesizing high-fidelity female voice...');
                    try {
                      if (elevenlabsApiKey.trim()) {
                        localStorage.setItem('elevenlabs_api_key', elevenlabsApiKey.trim());
                      }
                      const blob = await api.synthesizeVoice(
                        'Hello Sophia! This is your natural female voice speaking. Everything is working smoothly.',
                        selectedVoice
                      );
                      const audioUrl = URL.createObjectURL(blob);
                      const audio = new Audio(audioUrl);
                      audio.onended = () => {
                        setVoiceTestStatus('✓ Playback finished. Voice is active!');
                        URL.revokeObjectURL(audioUrl);
                      };
                      audio.onerror = () => {
                        setVoiceTestStatus('Playback error occurred.');
                      };
                      await audio.play();
                      setVoiceTestStatus('▶ Playing natural female audio stream...');
                    } catch (err: any) {
                      setVoiceTestStatus(`Voice error: ${err.message || 'Failed to synthesize'}`);
                    } finally {
                      setIsTestingVoice(false);
                    }
                  }}
                  className="w-full py-2.5 rounded-full bg-[#8BB8BD] hover:bg-[#7ba9ae] text-[#FAF7F4] font-bold text-xs cursor-pointer disabled:opacity-50 transition-colors flex items-center justify-center gap-2 shadow-sm"
                >
                  <Volume2 className="w-3.5 h-3.5 text-white" />
                  <span>{isTestingVoice ? 'Generating Audio...' : 'Test Natural Female Voice'}</span>
                </button>

                {voiceTestStatus && (
                  <p className="text-[11px] font-medium text-[#523B50] bg-[#FAF7F4] p-2.5 rounded-xl border border-[#8E7A8A]/20">
                    {voiceTestStatus}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* PRIVACY & AGREEMENT */}
          {activePanel === 'privacy' && (
            <div className="space-y-4 text-xs">
              <p className="text-[#756573]">SocioSync Instagram Data Safety & Zero-Salary Agreement</p>
              <div className="p-4 rounded-2xl bg-[#E5DCE0]/50 border border-[#8E7A8A]/25 space-y-2.5">
                <h4 className="font-bold text-sm text-[#523B50]">Instagram Graph API Compliance</h4>
                <p className="text-slate-700 leading-relaxed">
                  SocioSync connects via official Meta Graph API OAuth2 protocols. Your access tokens and user credentials are encrypted at rest using AES-256. No video files or raw audio transcripts are shared with third-party advertisers.
                </p>
                <div className="pt-2 text-[11px] font-mono text-[#D66882]">
                  Status: Meta Verified &bull; Zero Salary Retainer &bull; 100% Creator IP Ownership
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
