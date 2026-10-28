import React from 'react';

export const Logo3D: React.FC<{ size?: string }> = ({ size = 'w-6 h-6' }) => (
  <div className="relative w-8 h-8 rounded-xl bg-[#523B50] border border-[#8E7A8A]/40 flex items-center justify-center overflow-hidden shadow-[0_8px_20px_rgba(82,59,80,0.18)] group-hover:shadow-[0_10px_26px_rgba(214,104,130,0.32)] transition-all duration-300">
    <div className="absolute inset-0 bg-gradient-to-br from-[#8BB8BD]/20 via-transparent to-[#D66882]/25 pointer-events-none"></div>
    <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" className={`${size} transition-transform duration-300 group-hover:scale-105`}>
      <defs>
        <linearGradient id="bar1Aqua" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#8BB8BD"></stop>
          <stop offset="100%" stopColor="#5D8E94"></stop>
        </linearGradient>
        <linearGradient id="bar2Ochre" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#E8B259"></stop>
          <stop offset="100%" stopColor="#C98A2C"></stop>
        </linearGradient>
        <linearGradient id="bar3Rose" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#F2A6B8"></stop>
          <stop offset="50%" stopColor="#D66882"></stop>
          <stop offset="100%" stopColor="#A8465E"></stop>
        </linearGradient>
      </defs>
      <rect x="6" y="21" width="7" height="13" rx="3.5" fill="url(#bar1Aqua)"></rect>
      <rect x="16.5" y="14" width="7" height="20" rx="3.5" fill="url(#bar2Ochre)"></rect>
      <rect x="27" y="6" width="7" height="28" rx="3.5" fill="url(#bar3Rose)"></rect>
      <circle cx="30.5" cy="9.5" r="1.5" fill="#FAF7F4" fillOpacity="0.9"></circle>
    </svg>
  </div>
);
