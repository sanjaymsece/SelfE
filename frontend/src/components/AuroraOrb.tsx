import React from 'react';

export interface AuroraOrbProps {
  isListening: boolean;
  isSpeaking: boolean;
  onToggleListen: () => void;
}

export const AuroraOrb: React.FC<AuroraOrbProps> = ({
  isListening,
  isSpeaking,
  onToggleListen,
}) => {
  return (
    <div className="relative flex flex-col items-center justify-center select-none py-2">
      {/* Outer Glow Halo */}
      <div
        className={`absolute rounded-full pointer-events-none blur-3xl w-60 h-60 sm:w-72 sm:h-72 transition-all duration-700 ${
          isListening
            ? 'scale-115 opacity-100'
            : isSpeaking
            ? 'scale-110 opacity-90'
            : 'scale-100 opacity-80'
        }`}
        style={{
          background: isListening
            ? 'radial-gradient(circle, rgba(139, 184, 189, 0.65) 0%, rgba(214, 104, 130, 0.5) 48%, rgba(232, 178, 89, 0.4) 70%, transparent 85%)'
            : 'radial-gradient(circle, rgba(214, 104, 130, 0.5) 0%, rgba(142, 122, 138, 0.48) 48%, rgba(232, 178, 89, 0.3) 70%, rgba(244, 239, 234, 0) 85%)',
        }}
      ></div>

      {/* Main Orb Button */}
      <button
        type="button"
        onClick={onToggleListen}
        aria-label={isListening ? 'Listening... Tap to stop' : 'Tap orb to speak · Idle & breathing'}
        className={`relative w-60 h-60 sm:w-72 sm:h-72 rounded-full overflow-hidden cursor-pointer focus:outline-none group shadow-[0_22px_60px_rgba(82,59,80,0.32),inset_0_0_36px_rgba(250,247,244,0.45)] border-2 border-[#FAF7F4]/80 transition-transform duration-500 hover:scale-[1.02] ${
          isListening ? 'scale-105 ring-4 ring-[#8BB8BD]/40' : isSpeaking ? 'animate-orb-pulse' : ''
        }`}
        style={{
          background: 'radial-gradient(circle at 30% 25%, rgb(142, 122, 138) 0%, rgb(82, 59, 80) 90%)',
        }}
      >
        {/* Layer 1: Conic Gradient swirling colors */}
        <div
          className="absolute -inset-8 opacity-90 animate-orb-rotate"
          style={{
            filter: 'blur(22px)',
            background:
              'conic-gradient(rgb(142, 122, 138) 0deg, rgb(82, 59, 80) 95deg, rgb(214, 104, 130) 185deg, rgb(232, 178, 89) 265deg, rgb(139, 184, 189) 325deg, rgb(142, 122, 138) 360deg)',
          }}
        ></div>

        {/* Layer 2: Screen Blend Light Source */}
        <div
          className="absolute inset-2 rounded-full mix-blend-screen opacity-80"
          style={{
            filter: 'blur(18px)',
            background:
              'radial-gradient(circle at 65% 35%, rgb(214, 104, 130) 0%, rgba(232, 178, 89, 0.85) 36%, rgba(139, 184, 189, 0.65) 68%, transparent 82%)',
          }}
        ></div>

        {/* Layer 3: Overlay Blend Core */}
        <div
          className="absolute inset-8 rounded-full mix-blend-overlay opacity-80 transition-all duration-300"
          style={{
            filter: 'blur(14px)',
            background:
              'radial-gradient(circle at 40% 40%, rgb(250, 247, 244) 0%, rgb(232, 178, 89) 45%, transparent 75%)',
          }}
        ></div>

        {/* Inner Border Ring */}
        <div className="absolute inset-1.5 rounded-full border border-[#FAF7F4]/35 group-hover:border-[#FAF7F4]/80 transition-colors duration-300 pointer-events-none"></div>

        {/* Active Listening Ripple / Wave Effect */}
        {isListening && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="h-16 w-16 rounded-full border-2 border-white/60 animate-ping"></div>
          </div>
        )}
      </button>
    </div>
  );
};
