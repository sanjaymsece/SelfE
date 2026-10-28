import React, { useEffect, useRef, useState } from 'react';
import { Bot, Check, Copy, Send, Volume2, X } from 'lucide-react';
import { api } from '../api/client';
import { Logo3D } from './Logo3D';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  isStreaming?: boolean;
}

interface AIChatDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSpeak: (text: string) => void;
  voiceGender: 'female' | 'male';
}

export const AIChatDialog: React.FC<AIChatDialogProps> = ({
  isOpen,
  onClose,
  onSpeak,
  voiceGender,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello Sophia! I am your autonomous Instagram manager. I can diagnose your Reels analytics, draft viral 3-second hooks, write full video scripts, or help negotiate brand deals. What are we creating today?',
      timestamp: 'Just now',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll on new message
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      inputRef.current?.focus();
    }
  }, [messages, isOpen, isTyping]);

  if (!isOpen) return null;

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputValue;
    if (!text.trim() || isTyping) return;

    const userMsgId = `user-${Date.now()}`;
    const newMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, newMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Call real backend Gemini AI endpoint
      const res = await api.chatWithCoPilot(text.trim());

      let fullResponse = res.reply;
      if (res.hook) {
        fullResponse += `\n\nViral Hook:\n“${res.hook}”`;
      }
      if (res.why_it_works) {
        fullResponse += `\n\nWhy it works:\n${res.why_it_works}`;
      }

      // Stream the response smoothly with typewriter effect
      streamAIResponse(fullResponse, res.reply);
    } catch (err: any) {
      const errorMsg =
        typeof err === 'string'
          ? err
          : err?.message || 'Unable to connect to Gemini API servers.';
      const cleanMsg = String(errorMsg).replace(/\[object Object\]/gi, 'Service notification').trim();
      streamAIResponse(`Gemini Co-pilot notice: ${cleanMsg}`);
    }
  };

  const streamAIResponse = (fullText: string, spokenText?: string) => {
    const aiMsgId = `ai-${Date.now()}`;
    const initialAiMsg: ChatMessage = {
      id: aiMsgId,
      sender: 'assistant',
      text: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, initialAiMsg]);
    setIsTyping(false);

    let charIndex = 0;
    const chunkSize = 3; // stream 3 characters per tick for smooth, natural reading flow
    const interval = setInterval(() => {
      charIndex += chunkSize;
      if (charIndex >= fullText.length) {
        clearInterval(interval);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId ? { ...m, text: fullText, isStreaming: false } : m
          )
        );
        if (spokenText) {
          onSpeak(spokenText);
        }
      } else {
        const currentSlice = fullText.slice(0, charIndex);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId ? { ...m, text: currentSlice } : m
          )
        );
      }
    }, 25);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/45 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-[#FAF7F4] text-[#382A37] rounded-[28px] shadow-2xl border border-[#8E7A8A]/30 flex flex-col h-[620px] max-h-[90vh] overflow-hidden relative animate-in zoom-in-95 duration-200">
        {/* Chat Header */}
        <div className="px-5 py-4 border-b border-[#8E7A8A]/20 bg-[#E5DCE0]/70 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo3D size="w-5 h-5" />
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-display font-bold text-sm text-[#382A37]">
                  SocioSync AI Co-pilot
                </h3>
                <span className="px-2 py-0.5 rounded-full bg-[#523B50] text-[#FAF7F4] font-mono text-[9px] font-bold">
                  Gemini 3.5 Flash
                </span>
              </div>
              <p className="text-[11px] text-[#756573]">
                {voiceGender === 'female' ? 'Sophia Voice' : 'Marcus Voice'} Active &bull; Zero Salary Retainer
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-[#FAF7F4] border border-[#8E7A8A]/30 flex items-center justify-center text-[#523B50] hover:bg-[#523B50] hover:text-[#FAF7F4] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-[#523B50] text-[#FAF7F4] flex items-center justify-center shrink-0 border border-[#8E7A8A]/40 mt-0.5">
                  <Bot className="w-4 h-4 text-[#E8B259]" />
                </div>
              )}

              <div
                className={`max-w-[82%] sm:max-w-[75%] rounded-[20px] p-3.5 text-xs sm:text-sm leading-relaxed relative ${
                  msg.sender === 'user'
                    ? 'bg-[#523B50] text-[#FAF7F4] rounded-tr-xs shadow-sm'
                    : 'bg-[#E5DCE0]/60 border border-[#8E7A8A]/25 text-[#382A37] rounded-tl-xs shadow-2xs'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.text}</div>
                {msg.isStreaming && (
                  <span className="inline-block w-2 h-4 ml-1 bg-[#D66882] animate-pulse align-middle" />
                )}

                {msg.sender === 'assistant' && !msg.isStreaming && (
                  <div className="mt-2.5 pt-2 border-t border-[#8E7A8A]/15 flex items-center justify-between text-[10px] text-[#756573]">
                    <span>{msg.timestamp}</span>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => onSpeak(msg.text)}
                        title="Read aloud"
                        className="p-1 rounded-md hover:bg-[#FAF7F4] text-[#523B50] cursor-pointer"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleCopy(msg.text, msg.id)}
                        title="Copy text"
                        className="p-1 rounded-md hover:bg-[#FAF7F4] text-[#523B50] cursor-pointer"
                      >
                        {copiedId === msg.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#E8B259] to-[#D66882] p-0.5 shrink-0 mt-0.5">
                  <img
                    src="/unnamed.jpg"
                    alt="Sophia"
                    className="w-full h-full rounded-full object-cover border border-[#FAF7F4]"
                  />
                </div>
              )}
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex gap-3 justify-start items-center">
              <div className="w-8 h-8 rounded-full bg-[#523B50] text-[#FAF7F4] flex items-center justify-center shrink-0 border border-[#8E7A8A]/40">
                <Bot className="w-4 h-4 text-[#E8B259]" />
              </div>
              <div className="px-4 py-2.5 rounded-full bg-[#E5DCE0]/60 border border-[#8E7A8A]/25 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#D66882] animate-bounce"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#D66882] animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#D66882] animate-bounce [animation-delay:0.4s]"></span>
                <span className="text-[11px] font-mono text-[#756573] ml-1">Gemini Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="px-4 py-1.5 bg-[#E5DCE0]/30 border-t border-[#8E7A8A]/15 flex items-center gap-2 overflow-x-auto">
          {[
            'Hook for high-end matcha routine',
            'Why is Sunday 6PM best to post?',
            'Draft counter-offer for Oatly ($2,500)',
            'Script a 30s desk setup reel',
          ].map((suggestion, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(suggestion)}
              className="px-2.5 py-1 rounded-full bg-[#FAF7F4] hover:bg-[#523B50] hover:text-[#FAF7F4] text-[10px] font-medium border border-[#8E7A8A]/25 whitespace-nowrap transition-colors cursor-pointer text-[#523B50]"
            >
              &bull; {suggestion}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-3 sm:p-4 bg-[#E5DCE0]/50 border-t border-[#8E7A8A]/20">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2 bg-[#FAF7F4] border border-[#8E7A8A]/35 rounded-2xl p-1.5 shadow-2xs focus-within:ring-2 focus-within:ring-[#523B50]/30 transition-all"
          >
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask anything about Instagram Reels, hooks, or analytics..."
              className="flex-1 bg-transparent px-3 py-1.5 text-xs sm:text-sm text-[#382A37] placeholder:text-[#756573] focus:outline-none"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isTyping}
              className="px-3 py-2 rounded-xl bg-[#523B50] hover:bg-[#664A64] text-[#FAF7F4] font-bold text-xs flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-40"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
