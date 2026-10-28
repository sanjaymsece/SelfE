import React, { useEffect, useRef, useState } from 'react';
import {
  Bell,
  Calendar,
  CloudUpload,
  CornerUpRight,
  Flame,
  Keyboard,
  LogOut,
  Mail,
  MessageSquare,
  Mic,
  Settings,
  Share2,
  Shield,
  Sparkles,
  Star,
  User,
  Video,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { MetricOverview, PostingTimeRecommendation } from '../types';
import { AIChatDialog } from './AIChatDialog';
import { AuroraOrb } from './AuroraOrb';
import { DashboardPanels, type PanelType } from './DashboardPanels';
import { Logo3D } from './Logo3D';

const InstagramIcon: React.FC<{ className?: string }> = ({ className = 'w-3.5 h-3.5' }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5"></rect>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"></line>
  </svg>
);

export const SocioSyncDashboard: React.FC = () => {
  const { logout } = useAuth();
  const [activePanel, setActivePanel] = useState<PanelType>(null);
  const [overview, setOverview] = useState<MetricOverview | null>(null);
  const [postingTimes, setPostingTimes] = useState<PostingTimeRecommendation[]>([]);

  // Voice & Interaction state
  const [voiceGender, setVoiceGender] = useState<'female' | 'male'>('female');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [showTypeInput, setShowTypeInput] = useState(false);
  const [isProcessingPrompt, setIsProcessingPrompt] = useState(false);

  // Dynamic Quote displayed under the Aurora Orb
  const [speechQuote, setSpeechQuote] = useState<string>(
    '“Welcome back, Sophia. Your Instagram Reels reach is up 18.4% this week and 3 brand collaboration inquiries are ready in your inbox. Tap the orb or ask me anything.”'
  );

  // Voice Status Badge Text
  const [voiceStatus, setVoiceStatus] = useState<string>(
    'Idle · Sophia (Female Human Voice) Ready'
  );

  // Sync Voice Status when gender changes
  useEffect(() => {
    if (!isListening && !isSpeaking && !isProcessingPrompt) {
      if (voiceGender === 'female') {
        setVoiceStatus('Idle · Sophia (Female Human Voice) Ready');
      } else {
        setVoiceStatus('Idle · Marcus (Male Human Voice) Ready');
      }
    }
  }, [voiceGender, isListening, isSpeaking, isProcessingPrompt]);

  // Load real backend analytics & recommendations
  useEffect(() => {
    const loadBackendData = async () => {
      try {
        const [overviewRes, timesRes] = await Promise.allSettled([
          api.getOverview(),
          api.getPostingTimes(),
        ]);

        if (overviewRes.status === 'fulfilled') {
          setOverview(overviewRes.value);
        }
        if (timesRes.status === 'fulfilled' && timesRes.value.recommendations) {
          setPostingTimes(timesRes.value.recommendations);
        }
      } catch (err) {
        console.warn('Backend synchronization warning:', err);
      }
    };
    loadBackendData();
  }, []);

  // Keyboard shortcut: Esc to close drawers
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setActivePanel(null);
        setShowTypeInput(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Audio player ref for natural female voice synthesis
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const stopAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  const fallbackBrowserSpeak = (cleanText: string) => {
    if (!('speechSynthesis' in window) || isMuted) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    const voices = window.speechSynthesis.getVoices();
    if (voiceGender === 'female') {
      utterance.pitch = 1.05;
      utterance.rate = 1.0;
      const femaleVoice = voices.find(
        (v) =>
          v.name.toLowerCase().includes('female') ||
          v.name.toLowerCase().includes('samantha') ||
          v.name.toLowerCase().includes('zira') ||
          v.name.toLowerCase().includes('jenny') ||
          v.name.toLowerCase().includes('natural') ||
          v.name.toLowerCase().includes('karen')
      );
      if (femaleVoice) utterance.voice = femaleVoice;
    } else {
      utterance.pitch = 0.9;
      utterance.rate = 1.0;
      const maleVoice = voices.find(
        (v) =>
          v.name.toLowerCase().includes('male') ||
          v.name.toLowerCase().includes('david') ||
          v.name.toLowerCase().includes('george') ||
          v.name.toLowerCase().includes('daniel')
      );
      if (maleVoice) utterance.voice = maleVoice;
    }

    utterance.onstart = () => {
      setIsSpeaking(true);
      setVoiceStatus(`Speaking · ${voiceGender === 'female' ? 'Sophia' : 'Marcus'} Voice`);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setVoiceStatus(
        voiceGender === 'female'
          ? 'Idle · Sophia (Natural Female Voice) Ready'
          : 'Idle · Marcus (Natural Male Voice) Ready'
      );
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  // High-fidelity ElevenLabs & Neural Female Speech Synthesis
  const speakText = async (text: string) => {
    if (isMuted) return;

    // Safety check: Never speak [object Object] or unparsed system errors
    let cleanText = text
      .replace(/\[object Object\]/gi, '')
      .replace(/[“”"']/g, '')
      .trim();

    if (!cleanText) return;

    stopAudio();

    try {
      setVoiceStatus(
        voiceGender === 'female'
          ? 'Synthesizing voice · Sophia...'
          : 'Synthesizing voice · Marcus...'
      );
      const voiceId = voiceGender === 'female' ? '21m00Tcm4TlvDq8ikWAM' : 'pNInz6obpgDQGcFmaJgB';
      const blob = await api.synthesizeVoice(cleanText, voiceId);
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;

      audio.onplay = () => {
        setIsSpeaking(true);
        setVoiceStatus(
          voiceGender === 'female'
            ? 'Speaking · Sophia (Natural Female Voice)'
            : 'Speaking · Marcus (Natural Male Voice)'
        );
      };

      audio.onended = () => {
        setIsSpeaking(false);
        setVoiceStatus(
          voiceGender === 'female'
            ? 'Idle · Sophia (Natural Female Voice) Ready'
            : 'Idle · Marcus (Natural Male Voice) Ready'
        );
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
      };

      audio.onerror = () => {
        fallbackBrowserSpeak(cleanText);
      };

      await audio.play();
    } catch (err) {
      fallbackBrowserSpeak(cleanText);
    }
  };

  // Handler: Prompt Chip "How did my week go?"
  const handleChipWeek = async () => {
    setIsProcessingPrompt(true);
    setVoiceStatus('Analyzing 7-day Instagram performance via Gemini...');
    try {
      const res = await api.chatWithCoPilot(
        'How did my week go? Give me an encouraging 7-day Instagram performance analysis for Sophia Tompson with 3 specific metrics.'
      );
      const diagnosis = `“${res.reply}”`;
      setSpeechQuote(diagnosis);
      speakText(diagnosis);
    } catch (e: any) {
      const diagnosis =
        '“Your week was exceptional, Sophia! Total impressions surged 18.4% to 128,400 viewers. Your top Reel on morning matcha achieved an 82% completion rate, driving 380 new followers. You have 3 pending brand deals ready to review.”';
      setSpeechQuote(diagnosis);
      speakText(diagnosis);
    } finally {
      setIsProcessingPrompt(false);
    }
  };

  // Handler: Prompt Chip "Give me a hook for tomorrow"
  const handleChipHook = async () => {
    setIsProcessingPrompt(true);
    setVoiceStatus('Generating viral Reel hook via Gemini...');
    try {
      const res = await api.chatWithCoPilot(
        'Give me one fresh, unconventional viral Reel hook for tomorrow morning with visual instructions.'
      );
      const hookText = `“${res.hook ? res.hook + ' — ' : ''}${res.reply}”`;
      setSpeechQuote(hookText);
      speakText(hookText);
    } catch (e: any) {
      const fallback =
        '“POV: The 15-minute Sunday batch filming framework that doubled my Reel reach with zero burnout.”';
      setSpeechQuote(fallback);
      speakText(fallback);
    } finally {
      setIsProcessingPrompt(false);
    }
  };

  // Handler: Prompt Chip "Why did my reach drop?"
  const handleChipReach = async () => {
    setIsProcessingPrompt(true);
    setVoiceStatus('Diagnosing Instagram reach via Gemini...');
    try {
      const res = await api.chatWithCoPilot(
        'Why did my Instagram reach drop and how do I fix it this week?'
      );
      const explanation = `“${res.reply}”`;
      setSpeechQuote(explanation);
      speakText(explanation);
    } catch (e: any) {
      const explanation =
        '“Your reach adjusted due to Wednesday algorithm distribution. High-energy audio and 3-second visual text overlays currently get 2.3x more Explore page impressions. Post between 6:00 PM and 7:30 PM for maximum reach.”';
      setSpeechQuote(explanation);
      speakText(explanation);
    } finally {
      setIsProcessingPrompt(false);
    }
  };

  // Voice AI prompt when mic is activated
  const handleVoiceGeminiPrompt = async () => {
    setIsProcessingPrompt(true);
    setVoiceStatus('Gemini Co-pilot thinking...');
    try {
      const res = await api.chatWithCoPilot(
        'Give creator Sophia Tompson a quick 2-sentence creative tip or idea for her Instagram right now.'
      );
      setIsListening(false);
      const reply = `“${res.reply}”`;
      setSpeechQuote(reply);
      speakText(reply);
    } catch (err: any) {
      setIsListening(false);
    } finally {
      setIsProcessingPrompt(false);
    }
  };

  // Handler: Toggle Listening on Orb or Mic
  const handleToggleListening = () => {
    if (isListening) {
      setIsListening(false);
      setVoiceStatus(
        voiceGender === 'female'
          ? 'Idle · Sophia (Natural Female Voice) Ready'
          : 'Idle · Marcus (Natural Male Voice) Ready'
      );
    } else {
      stopAudio();
      setIsListening(true);
      setVoiceStatus('Listening · Speak now or tap orb to stop...');

      // Check for browser SpeechRecognition
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = false;
          recognition.interimResults = false;
          recognition.lang = 'en-US';

          recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript;
            setIsListening(false);
            handleCustomUserPrompt(transcript);
          };

          recognition.onerror = () => {
            setIsListening(false);
            handleVoiceGeminiPrompt();
          };

          recognition.onend = () => {
            setIsListening(false);
          };

          recognition.start();
          return;
        } catch (e) {
          console.warn('Speech recognition fallback to Gemini prompt');
        }
      }

      handleVoiceGeminiPrompt();
    }
  };

  // Handler: Custom User Prompt
  const handleCustomUserPrompt = async (promptText: string) => {
    if (!promptText.trim()) return;
    setIsProcessingPrompt(true);
    setVoiceStatus('Gemini Co-pilot processing your inquiry...');

    try {
      const res = await api.chatWithCoPilot(promptText);
      const reply = `“${res.reply}”`;
      setSpeechQuote(reply);
      speakText(res.reply);
    } catch (err: any) {
      const errorMsg =
        typeof err === 'string'
          ? err
          : err?.message || 'Unable to connect to Gemini API servers.';
      const cleanMsg = String(errorMsg).replace(/\[object Object\]/gi, 'Service notification').trim();
      const fallbackReply = `“Gemini Co-pilot notice: ${cleanMsg}”`;
      setSpeechQuote(fallbackReply);
      speakText('I had trouble connecting to the Gemini server. Please check your API key in Settings.');
    } finally {
      setIsProcessingPrompt(false);
      setShowTypeInput(false);
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#F4EFEA] text-[#382A37] flex flex-col lg:flex-row relative select-none">
      {/* Film grain effect & Ambient blurred background glow */}
      <div className="fixed inset-0 film-grain pointer-events-none z-50"></div>
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-[#D66882]/10 blur-[140px]"></div>
      </div>

      {/* ======================================================== */}
      {/* LEFT SIDEBAR (248px)                                      */}
      {/* ======================================================== */}
      <aside className="w-full lg:w-[248px] shrink-0 bg-[#E5DCE0] border-b lg:border-b-0 lg:border-r border-[#8E7A8A]/25 flex lg:flex-col justify-between z-40 px-3 py-3 lg:p-4 overflow-x-auto lg:overflow-x-visible">
        <div className="flex lg:flex-col gap-3 items-center lg:items-stretch shrink-0">
          {/* Logo Header */}
          <div className="flex items-center justify-between gap-2 pb-0 lg:pb-3 lg:border-b border-[#8E7A8A]/20">
            <button
              type="button"
              onClick={() => setActivePanel(null)}
              className="group inline-flex items-center gap-3 text-left focus:outline-none cursor-pointer"
            >
              <Logo3D />
              <div className="flex flex-col">
                <span className="font-display font-bold tracking-tight text-[#382A37] leading-none text-lg">
                  Socio
                  <span className="inline-block px-1.5 py-0.5 ml-0.5 rounded-full bg-[#C8B5C3]/60 text-[#523B50]">
                    Sync
                  </span>
                </span>
              </div>
            </button>

            {/* Mobile Profile Pill */}
            <button
              type="button"
              onClick={() => setActivePanel('profile')}
              className="lg:hidden inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#FAF7F4] border border-[#8E7A8A]/35 text-xs font-bold text-[#523B50] cursor-pointer"
            >
              <User className="w-3.5 h-3.5 text-[#D66882]" />
              Profile
            </button>
          </div>

          {/* Desktop Profile Card */}
          <button
            type="button"
            onClick={() => setActivePanel('profile')}
            className="hidden lg:flex items-center gap-3 p-3 rounded-[20px] text-left transition-all cursor-pointer border bg-[#FAF7F4]/80 hover:bg-[#FAF7F4] border-[#8E7A8A]/30"
          >
            <div className="relative w-12 h-12 rounded-full p-0.5 bg-gradient-to-tr from-[#E8B259] via-[#D66882] to-[#8BB8BD] shrink-0">
              <img
                alt="Sophia Tompson"
                src="/unnamed.jpg"
                className="w-full h-full rounded-full object-cover border border-[#FAF7F4]"
              />
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-display font-bold text-sm text-[#382A37] truncate">
                Sophia Tompson
              </div>
              <div className="text-[11px] text-[#756573] truncate">@sophia.studio</div>
              <div className="mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#523B50] text-[10px] font-mono uppercase text-[#FAF7F4]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#8BB8BD]"></span>
                business · Profile
              </div>
            </div>
          </button>

          {/* Nav Links */}
          <nav className="flex lg:flex-col gap-1 overflow-x-auto">
            <button
              type="button"
              onClick={() => setActivePanel('profile')}
              className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center gap-3 whitespace-nowrap transition-all cursor-pointer ${
                activePanel === 'profile'
                  ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                  : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
            >
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <User className="w-3.5 h-3.5" />
              </span>
              <span>My Profile</span>
            </button>

            <button
              type="button"
              onClick={() => setActivePanel('weekly_stats')}
              className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center gap-3 whitespace-nowrap transition-all cursor-pointer ${
                activePanel === 'weekly_stats'
                  ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                  : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
            >
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-3.5 h-3.5"
                >
                  <path d="M3 3v16a2 2 0 0 0 2 2h16"></path>
                  <path d="M18 17V9"></path>
                  <path d="M13 17V5"></path>
                  <path d="M8 17v-3"></path>
                </svg>
              </span>
              <span>Weekly stats</span>
            </button>

            <button
              type="button"
              onClick={() => setActivePanel('model_videos')}
              className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center gap-3 whitespace-nowrap transition-all cursor-pointer ${
                activePanel === 'model_videos'
                  ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                  : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
            >
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <Video className="w-3.5 h-3.5" />
              </span>
              <span>Model videos</span>
            </button>

            <button
              type="button"
              onClick={() => setActivePanel('video_scripts')}
              className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center gap-3 whitespace-nowrap transition-all cursor-pointer ${
                activePanel === 'video_scripts'
                  ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                  : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
            >
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-3.5 h-3.5"
                >
                  <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path>
                  <path d="M14 2v4a2 2 0 0 0 2 2h4"></path>
                  <path d="M10 9H8"></path>
                  <path d="M16 13H8"></path>
                  <path d="M16 17H8"></path>
                </svg>
              </span>
              <span>Video scripts</span>
            </button>

            <button
              type="button"
              onClick={() => setActivePanel('trending_now')}
              className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center gap-3 whitespace-nowrap transition-all cursor-pointer ${
                activePanel === 'trending_now'
                  ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                  : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
            >
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <Flame className="w-3.5 h-3.5" />
              </span>
              <span>Trending now</span>
            </button>

            <button
              type="button"
              onClick={() => setActivePanel('content_calendar')}
              className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center gap-3 whitespace-nowrap transition-all cursor-pointer ${
                activePanel === 'content_calendar'
                  ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                  : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
            >
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <Calendar className="w-3.5 h-3.5" />
              </span>
              <span>Content calendar</span>
            </button>

            <button
              type="button"
              onClick={() => setActivePanel('connected_accounts')}
              className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center gap-3 whitespace-nowrap transition-all cursor-pointer ${
                activePanel === 'connected_accounts'
                  ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                  : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
            >
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <Share2 className="w-3.5 h-3.5" />
              </span>
              <span>Connected accounts</span>
            </button>

            <button
              type="button"
              onClick={() => setActivePanel('upload_video')}
              className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center gap-3 whitespace-nowrap transition-all cursor-pointer ${
                activePanel === 'upload_video'
                  ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                  : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
            >
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <CloudUpload className="w-3.5 h-3.5" />
              </span>
              <span>Upload video for review</span>
            </button>
          </nav>
        </div>

        {/* Desktop Sidebar Footer */}
        <div className="hidden lg:flex flex-col gap-1 pt-3 border-t border-[#8E7A8A]/25">
          <button
            type="button"
            onClick={() => setActivePanel('settings')}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold text-[#523B50] hover:bg-[#FAF7F4]/70 flex items-center gap-3 cursor-pointer"
          >
            <span className="w-6 h-6 rounded-lg bg-[#523B50] text-[#FAF7F4] flex items-center justify-center">
              <Settings className="w-3.5 h-3.5" />
            </span>
            <span>Settings</span>
          </button>

          <button
            type="button"
            onClick={() => setActivePanel('privacy')}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold text-[#523B50] hover:bg-[#FAF7F4]/70 flex items-center gap-3 cursor-pointer"
          >
            <span className="w-6 h-6 rounded-lg bg-[#523B50] text-[#FAF7F4] flex items-center justify-center">
              <Shield className="w-3.5 h-3.5" />
            </span>
            <span>Privacy &amp; agreement</span>
          </button>

          <button
            type="button"
            onClick={logout}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold text-[#523B50] hover:bg-[#D66882]/15 hover:text-[#D66882] flex items-center gap-3 cursor-pointer"
          >
            <span className="w-6 h-6 rounded-lg bg-[#523B50] text-[#FAF7F4] flex items-center justify-center">
              <LogOut className="w-3.5 h-3.5" />
            </span>
            <span>Log out</span>
          </button>
        </div>
      </aside>

      {/* ======================================================== */}
      {/* CENTER STAGE                                              */}
      {/* ======================================================== */}
      <main className="flex-1 h-full flex flex-col items-center justify-between p-5 sm:p-8 relative z-10 overflow-y-auto">
        {/* Top Header */}
        <div className="w-full max-w-3xl flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="font-display text-lg sm:text-xl font-extrabold tracking-tight text-[#382A37]">
              HELLO, SOPHIA!
            </span>
            <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E5DCE0] border border-[#8E7A8A]/30 text-xs font-semibold text-[#523B50]">
              <InstagramIcon className="w-3.5 h-3.5 text-[#D66882]" />
              Instagram Exclusive
            </span>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#FAF7F4] border border-[#8E7A8A]/35 shadow-2xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  isListening
                    ? 'bg-rose-500 animate-ping'
                    : isSpeaking
                    ? 'bg-emerald-500 animate-pulse'
                    : 'bg-[#8BB8BD]'
                }`}
              ></span>
              <span className="text-[11px] font-mono font-semibold text-[#523B50]">
                {voiceStatus}
              </span>
            </div>

            <button
              type="button"
              onClick={() => setActivePanel('profile')}
              className="inline-flex items-center gap-2 pl-1.5 pr-3.5 py-1 rounded-full bg-[#523B50] hover:bg-[#664A64] text-[#FAF7F4] text-xs font-bold shadow-xs transition-all cursor-pointer"
              title="Open Creator Profile"
            >
              <img
                alt="Sophia Tompson"
                src="/unnamed.jpg"
                className="w-6 h-6 rounded-full object-cover border border-[#E8B259]"
              />
              <span>Profile</span>
            </button>
          </div>
        </div>

        {/* Center Aurora Orb & Speech Quote */}
        <div className="my-auto flex flex-col items-center text-center max-w-2xl w-full space-y-6 py-4">
          <AuroraOrb
            isListening={isListening}
            isSpeaking={isSpeaking}
            onToggleListen={handleToggleListening}
          />

          <div className="space-y-2.5 px-4 min-h-[5rem] flex items-center justify-center">
            <p className="font-display text-lg sm:text-2xl font-semibold text-[#382A37] leading-relaxed mx-auto transition-all duration-300">
              {speechQuote}
            </p>
          </div>

          {/* Quick AI Action Chips */}
          <div className="flex flex-wrap items-center justify-center gap-2.5 pt-1">
            <button
              type="button"
              onClick={handleChipWeek}
              disabled={isProcessingPrompt}
              className="px-4 py-2 rounded-full bg-[#FAF7F4] hover:bg-[#523B50] text-[#382A37] hover:text-[#FAF7F4] border border-[#8E7A8A]/35 text-xs font-bold flex items-center gap-1.5 transition-all shadow-2xs cursor-pointer group disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#D66882] group-hover:text-[#E8B259]" />
              How did my week go?
            </button>

            <button
              type="button"
              onClick={handleChipHook}
              disabled={isProcessingPrompt}
              className="px-4 py-2 rounded-full bg-[#FAF7F4] hover:bg-[#523B50] text-[#382A37] hover:text-[#FAF7F4] border border-[#8E7A8A]/35 text-xs font-bold flex items-center gap-1.5 transition-all shadow-2xs cursor-pointer group disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#D66882] group-hover:text-[#E8B259]" />
              Give me a hook for tomorrow
            </button>

            <button
              type="button"
              onClick={handleChipReach}
              disabled={isProcessingPrompt}
              className="px-4 py-2 rounded-full bg-[#FAF7F4] hover:bg-[#523B50] text-[#382A37] hover:text-[#FAF7F4] border border-[#8E7A8A]/35 text-xs font-bold flex items-center gap-1.5 transition-all shadow-2xs cursor-pointer group disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#D66882] group-hover:text-[#E8B259]" />
              Why did my reach drop?
            </button>
          </div>

          {/* Smooth General AI Chat Modal */}
          <AIChatDialog
            isOpen={showTypeInput}
            onClose={() => setShowTypeInput(false)}
            voiceGender={voiceGender}
            onSpeak={(text) => {
              const cleanQuote = text.replace(/[\n\r]+/g, ' ').slice(0, 240);
              setSpeechQuote(`“${cleanQuote}${cleanQuote.length >= 240 ? '...' : ''}”`);
              speakText(text);
            }}
          />
        </div>

        {/* Bottom Voice Controls */}
        <div className="w-full max-w-xl space-y-3">
          <div className="flex flex-wrap items-center justify-center gap-2.5">
            {/* Gender Toggle */}
            <div
              className="inline-flex items-center p-1 rounded-full bg-[#E5DCE0] border border-[#8E7A8A]/40"
              role="group"
              aria-label="Select AI Human Voice Gender"
            >
              <button
                type="button"
                onClick={() => setVoiceGender('female')}
                className={`px-3.5 py-2 rounded-full text-xs font-bold transition-all cursor-pointer ${
                  voiceGender === 'female'
                    ? 'bg-[#523B50] text-[#FAF7F4] shadow-xs'
                    : 'text-[#523B50] hover:text-[#382A37]'
                }`}
              >
                ♀ Female Voice
              </button>
              <button
                type="button"
                onClick={() => setVoiceGender('male')}
                className={`px-3.5 py-2 rounded-full text-xs font-bold transition-all cursor-pointer ${
                  voiceGender === 'male'
                    ? 'bg-[#523B50] text-[#FAF7F4] shadow-xs'
                    : 'text-[#523B50] hover:text-[#382A37]'
                }`}
              >
                ♂ Male Voice
              </button>
            </div>

            {/* Mic Toggle */}
            <button
              type="button"
              onClick={handleToggleListening}
              className={`px-6 py-3 rounded-full font-bold text-xs flex items-center gap-2 transition-all cursor-pointer shadow-sm ${
                isListening
                  ? 'bg-rose-600 hover:bg-rose-700 text-white animate-pulse'
                  : 'bg-[#523B50] hover:bg-[#664A64] text-[#FAF7F4]'
              }`}
            >
              <Mic className="w-4 h-4 text-[#E8B259]" />
              {isListening ? 'Listening...' : 'Mic'}
            </button>

            {/* Mute Button */}
            <button
              type="button"
              onClick={() => {
                stopAudio();
                setIsMuted(!isMuted);
              }}
              className={`px-4 py-3 rounded-full text-xs font-bold border flex items-center gap-1.5 transition-all cursor-pointer ${
                isMuted
                  ? 'bg-[#E5DCE0] border-[#8E7A8A]/60 text-rose-800'
                  : 'bg-[#FAF7F4] border-[#8E7A8A]/35 text-[#382A37] hover:bg-[#E5DCE0]'
              }`}
            >
              {isMuted ? (
                <>
                  <VolumeX className="w-4 h-4 text-rose-600" /> Unmute
                </>
              ) : (
                <>
                  <Volume2 className="w-4 h-4 text-[#523B50]" /> Mute
                </>
              )}
            </button>

            {/* Type Instead */}
            <button
              type="button"
              onClick={() => setShowTypeInput(!showTypeInput)}
              className={`px-4 py-3 rounded-full text-xs font-bold border flex items-center gap-1.5 transition-all cursor-pointer ${
                showTypeInput
                  ? 'bg-[#523B50] text-[#FAF7F4] border-[#523B50]'
                  : 'bg-[#FAF7F4] border-[#8E7A8A]/35 text-[#382A37] hover:bg-[#E5DCE0]'
              }`}
            >
              <Keyboard className="w-4 h-4" />
              Type instead
            </button>
          </div>
        </div>
      </main>

      {/* ======================================================== */}
      {/* RIGHT SIDEBAR (230px)                                     */}
      {/* ======================================================== */}
      <aside className="w-full lg:w-[230px] shrink-0 bg-[#E5DCE0] border-t lg:border-t-0 lg:border-l border-[#8E7A8A]/25 flex lg:flex-col justify-between z-40 px-3 py-2.5 lg:p-4 overflow-x-auto lg:overflow-x-visible">
        <div className="flex lg:flex-col gap-1.5 w-full">
          <div className="hidden lg:block pb-3 mb-2 border-b border-[#8E7A8A]/20">
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#D66882] font-bold">
              IG Inbox &amp; Brand Deals
            </span>
          </div>

          {/* Comment replies [3] */}
          <button
            type="button"
            onClick={() => setActivePanel('comment_replies')}
            className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center justify-between gap-2 whitespace-nowrap transition-all cursor-pointer ${
              activePanel === 'comment_replies'
                ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <MessageSquare className="w-3.5 h-3.5" />
              </span>
              <span>Comment replies</span>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold tabular-nums bg-[#523B50] text-[#FAF7F4]">
              3
            </span>
          </button>

          {/* Notifications [3] */}
          <button
            type="button"
            onClick={() => setActivePanel('notifications')}
            className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center justify-between gap-2 whitespace-nowrap transition-all cursor-pointer ${
              activePanel === 'notifications'
                ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <Bell className="w-3.5 h-3.5" />
              </span>
              <span>Notifications</span>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold tabular-nums bg-[#523B50] text-[#FAF7F4]">
              3
            </span>
          </button>

          {/* Sponsorship emails [2] */}
          <button
            type="button"
            onClick={() => setActivePanel('sponsorship_emails')}
            className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center justify-between gap-2 whitespace-nowrap transition-all cursor-pointer ${
              activePanel === 'sponsorship_emails'
                ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <Mail className="w-3.5 h-3.5" />
              </span>
              <span>Sponsorship emails</span>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold tabular-nums bg-[#523B50] text-[#FAF7F4]">
              2
            </span>
          </button>

          {/* Celebrity DMs [2] */}
          <button
            type="button"
            onClick={() => setActivePanel('celebrity_dms')}
            className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center justify-between gap-2 whitespace-nowrap transition-all cursor-pointer ${
              activePanel === 'celebrity_dms'
                ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <Star className="w-3.5 h-3.5" />
              </span>
              <span>Celebrity DMs</span>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold tabular-nums bg-[#523B50] text-[#FAF7F4]">
              2
            </span>
          </button>

          {/* Follow-ups [1] */}
          <button
            type="button"
            onClick={() => setActivePanel('follow_ups')}
            className={`px-3.5 py-2.5 rounded-2xl text-xs font-semibold flex items-center justify-between gap-2 whitespace-nowrap transition-all cursor-pointer ${
              activePanel === 'follow_ups'
                ? 'bg-[#FAF7F4] text-[#382A37] shadow-xs'
                : 'text-[#523B50] hover:bg-[#FAF7F4]/60 hover:text-[#382A37]'
              }`}
          >
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 bg-[#523B50]/15 text-[#523B50]">
                <CornerUpRight className="w-3.5 h-3.5" />
              </span>
              <span>Follow-ups</span>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold tabular-nums bg-[#523B50] text-[#FAF7F4]">
              1
            </span>
          </button>

          {/* Mobile quick actions */}
          <div className="flex lg:hidden items-center gap-1.5 ml-auto pl-2">
            <button
              type="button"
              aria-label="Settings"
              onClick={() => setActivePanel('settings')}
              className="p-2 rounded-xl bg-[#FAF7F4] text-[#523B50]"
            >
              <Settings className="w-4 h-4" />
            </button>
            <button
              type="button"
              aria-label="Privacy"
              onClick={() => setActivePanel('privacy')}
              className="p-2 rounded-xl bg-[#FAF7F4] text-[#523B50]"
            >
              <Shield className="w-4 h-4" />
            </button>
            <button
              type="button"
              aria-label="Log out"
              onClick={logout}
              className="p-2 rounded-xl bg-[#FAF7F4] text-[#D66882]"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Desktop Esc Reminder Card */}
        <div className="hidden lg:block p-4 rounded-[20px] bg-[#8E7A8A] text-[#FAF7F4] space-y-2 shadow-sm">
          <div className="flex items-center justify-between text-[11px]">
            <span className="font-mono text-[#E8B259] font-bold">IG AUTO-REPLY</span>
            <span className="font-mono font-bold text-[#FAF7F4]">MANUAL</span>
          </div>
          <p className="text-[11px] text-[#FAF7F4]/90 leading-snug">
            Press <kbd className="text-[#E8B259] font-bold">Esc</kbd> anytime to close open drawers.
          </p>
        </div>
      </aside>

      {/* Slide-out Panels (Drawers) */}
      <DashboardPanels
        activePanel={activePanel}
        onClose={() => setActivePanel(null)}
        overview={overview}
        postingTimes={postingTimes}
        onGenerateHook={(topic) => {
          handleCustomUserPrompt(`Generate a viral script for: ${topic}`);
          setActivePanel(null);
        }}
      />
    </div>
  );
};
