import React from 'react';
import { EmotionState } from '../types';
import { getFaceArt } from '../logic/faceBitmaps';
import { AlertCircle, Eye, RefreshCw } from 'lucide-react';

interface OledFaceProps {
  emotion: EmotionState;
  onSimulateEngagementDip: () => void;
  onSimulateSlouch: () => void;
  onSimulateFocused: () => void;
  onSetEmotion: (emotion: EmotionState) => void;
}

const EMOTION_PILLS: Record<EmotionState, { bg: string; text: string; border: string }> = {
  idle: { bg: 'bg-slate-100', text: 'text-slate-600', border: 'border-slate-200' },
  watching: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  listening: { bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200' },
  thinking: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
  curious: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  happy: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  concerned: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  alert: { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' },
};

export const OledFace: React.FC<OledFaceProps> = ({
  emotion,
  onSimulateEngagementDip,
  onSimulateSlouch,
  onSimulateFocused,
  onSetEmotion,
}) => {
  const art = getFaceArt(emotion);
  const pill = EMOTION_PILLS[emotion] || EMOTION_PILLS.watching;

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-indigo-600" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Robot Face Display (128×64)
            </span>
          </div>
          <span
            className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border uppercase ${pill.bg} ${pill.text} ${pill.border}`}
          >
            {emotion}
          </span>
        </div>

        {/* OLED Simulated Screen with realistic hardware matte bezel */}
        <div className="relative font-mono bg-slate-950 rounded-xl p-4 text-[#00ff66] text-xs text-center leading-relaxed border border-slate-800 shadow-inner overflow-hidden select-none">
          <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.3)_50%)] bg-[length:100%_4px] pointer-events-none opacity-30"></div>
          
          <pre className="relative z-10 font-bold whitespace-pre transition-all duration-300 drop-shadow-[0_0_6px_rgba(0,255,102,0.6)]">
            {art}
          </pre>

          <div className="mt-2 text-[10px] text-emerald-500/80 font-mono tracking-wider flex items-center justify-between border-t border-slate-800 pt-1.5">
            <span>SSD1306 OLED (I2C 0x3C)</span>
            <span className="flex items-center gap-1 text-[10px] text-emerald-400">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              SYNC ACTIVE
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
                className={`text-[10px] py-1 px-1 rounded-md font-mono uppercase transition-colors border ${
                  emotion === emo
                    ? 'bg-slate-900 text-white border-slate-900 font-bold shadow-sm'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                }`}
              >
                {emo}
              </button>
            )
          )}
        </div>
      </div>

      {/* Simulation triggers */}
      <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
        <button
          onClick={onSimulateEngagementDip}
          className="w-full py-2 px-3 rounded-xl text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors flex items-center justify-center gap-1.5 shadow-sm"
        >
          <AlertCircle className="w-3.5 h-3.5" />
          Simulate Engagement Dip (0.20)
        </button>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onSimulateSlouch}
            className="py-1.5 px-2.5 rounded-xl text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 transition-colors shadow-sm"
          >
            Simulate Slouch (32.5°)
          </button>
          <button
            onClick={onSimulateFocused}
            className="py-1.5 px-2.5 rounded-xl text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200 hover:bg-slate-100 transition-colors shadow-sm"
          >
            Reset Normal (0.85)
          </button>
        </div>
      </div>
    </div>
  );
};
