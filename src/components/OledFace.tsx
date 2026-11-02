import React from 'react';
import { EmotionState } from '../types';
import { getFaceArt } from '../logic/faceBitmaps';
import { AlertCircle, Eye } from 'lucide-react';

interface OledFaceProps {
  emotion: EmotionState;
  onSimulateEngagementDip: () => void;
  onSimulateSlouch: () => void;
  onSimulateFocused: () => void;
  onSetEmotion: (emotion: EmotionState) => void;
}

const EMOTION_COLORS: Record<EmotionState, { text: string; border: string; glow: string }> = {
  idle: { text: 'text-gray-400', border: 'border-gray-500/30', glow: 'shadow-gray-500/20' },
  watching: { text: 'text-emerald-400', border: 'border-emerald-500/30', glow: 'shadow-emerald-500/20' },
  listening: { text: 'text-cyan-400', border: 'border-cyan-500/30', glow: 'shadow-cyan-500/20' },
  thinking: { text: 'text-indigo-400', border: 'border-indigo-500/30', glow: 'shadow-indigo-500/20' },
  curious: { text: 'text-yellow-400', border: 'border-yellow-500/30', glow: 'shadow-yellow-500/20' },
  happy: { text: 'text-green-400', border: 'border-green-500/30', glow: 'shadow-green-500/20' },
  concerned: { text: 'text-amber-400', border: 'border-amber-500/30', glow: 'shadow-amber-500/20' },
  alert: { text: 'text-red-400', border: 'border-red-500/30', glow: 'shadow-red-500/20' },
};

export const OledFace: React.FC<OledFaceProps> = ({
  emotion,
  onSimulateEngagementDip,
  onSimulateSlouch,
  onSimulateFocused,
  onSetEmotion,
}) => {
  const art = getFaceArt(emotion);
  const color = EMOTION_COLORS[emotion] || EMOTION_COLORS.watching;

  return (
    <div className="bg-[#121a2b]/80 backdrop-blur-md border border-white/10 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
              OLED Display Face (128×64)
            </span>
          </div>
          <span
            className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${color.text} ${color.border} bg-black/40`}
          >
            {emotion}
          </span>
        </div>

        {/* OLED Simulated Screen */}
        <div className="relative font-mono bg-black rounded-xl p-4 text-[#00ff66] text-xs md:text-sm text-center leading-relaxed border border-emerald-500/30 shadow-[0_0_20px_rgba(0,255,102,0.15)] overflow-hidden select-none">
          {/* Scanline CRT overlay */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.4)_50%)] bg-[length:100%_4px] pointer-events-none opacity-40"></div>
          
          <pre className="relative z-10 font-bold whitespace-pre transition-all duration-300 drop-shadow-[0_0_8px_rgba(0,255,102,0.8)]">
            {art}
          </pre>

          <div className="mt-2 text-[10px] text-emerald-500/70 font-mono tracking-widest flex items-center justify-between border-t border-emerald-500/20 pt-1.5">
            <span>SSD1306 OLED</span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              LIVE I2C (0x3C)
            </span>
          </div>
        </div>

        {/* Quick emotion switches */}
        <div className="mt-3 grid grid-cols-4 gap-1.5">
          {(['watching', 'thinking', 'curious', 'happy', 'concerned', 'alert', 'listening', 'idle'] as EmotionState[]).map(
            (emo) => (
              <button
                key={emo}
                onClick={() => onSetEmotion(emo)}
                className={`text-[10px] py-1 px-1 rounded font-mono uppercase transition-colors border ${
                  emotion === emo
                    ? 'bg-white/20 text-white border-white/40 font-bold'
                    : 'bg-black/20 text-gray-400 border-white/5 hover:bg-white/10'
                }`}
              >
                {emo}
              </button>
            )
          )}
        </div>
      </div>

      {/* Simulation triggers matching web_dashboard.py */}
      <div className="mt-4 pt-3 border-t border-white/5 space-y-2">
        <button
          onClick={onSimulateEngagementDip}
          className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-red-500/15 text-red-400 border border-red-500/30 hover:bg-red-500/25 transition-all flex items-center justify-center gap-2"
        >
          <AlertCircle className="w-3.5 h-3.5" />
          Simulate Engagement Dip (0.20)
        </button>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onSimulateSlouch}
            className="py-1.5 px-2.5 rounded-lg text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 hover:bg-amber-500/25 transition-all"
          >
            Simulate Slouch (32.5°)
          </button>
          <button
            onClick={onSimulateFocused}
            className="py-1.5 px-2.5 rounded-lg text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/25 transition-all"
          >
            Reset Focused (0.85)
          </button>
        </div>
      </div>
    </div>
  );
};
