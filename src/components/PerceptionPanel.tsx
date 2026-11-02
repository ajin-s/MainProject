import React from 'react';
import { PostureStatus, InterventionLevel } from '../types';
import { Activity, ShieldAlert, Sparkles, UserCheck } from 'lucide-react';

interface PerceptionPanelProps {
  et: number;
  posture: PostureStatus;
  neckAngle: number;
  isSlouching: boolean;
  interventionLevel: InterventionLevel;
  onEtChange: (val: number) => void;
  onNeckAngleChange: (angle: number) => void;
}

export const PerceptionPanel: React.FC<PerceptionPanelProps> = ({
  et,
  posture,
  neckAngle,
  isSlouching,
  interventionLevel,
  onEtChange,
  onNeckAngleChange,
}) => {
  // Determine color based on Et
  const etColor =
    et >= 0.7
      ? 'from-emerald-500 to-cyan-500 text-emerald-400'
      : et >= 0.4
      ? 'from-blue-500 to-indigo-500 text-blue-400'
      : 'from-amber-500 to-red-500 text-red-400';

  return (
    <div className="space-y-4">
      {/* Engagement Card */}
      <div className="bg-[#121a2b]/80 backdrop-blur-md border border-white/10 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
              Engagement Telemetry (E_t)
            </span>
          </div>
          <span
            className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
              interventionLevel === 'IDLE'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : interventionLevel === 'GENTLE'
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                : 'bg-red-500/10 text-red-400 border-red-500/20 animate-pulse'
            }`}
          >
            Intervention: {interventionLevel}
          </span>
        </div>

        <div className="flex items-baseline justify-between my-2">
          <div className="text-4xl font-bold font-mono tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            {et.toFixed(2)}
          </div>
          <span className="text-xs font-mono text-gray-400">
            {et >= 0.75 ? 'HIGH FOCUS' : et >= 0.40 ? 'MODERATE' : 'DISENGAGED'}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-white/10 h-2.5 rounded-full overflow-hidden p-0.5">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${etColor} transition-all duration-300 shadow-[0_0_12px_rgba(6,182,212,0.5)]`}
            style={{ width: `${Math.round(et * 100)}%` }}
          ></div>
        </div>

        {/* Slider for live adjustment */}
        <div className="mt-3 pt-2 border-t border-white/5 flex items-center gap-2">
          <span className="text-[10px] text-gray-400 uppercase font-mono">Simulate E_t:</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={et}
            onChange={(e) => onEtChange(parseFloat(e.target.value))}
            className="flex-1 h-1.5 bg-black/40 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
        </div>

        <div className="flex items-center justify-between mt-2 text-[11px] text-gray-400">
          <span>Rolling 2s Ring Buffer (5 Hz)</span>
          <span className="font-mono text-gray-400">w_gaze: 0.45, w_blink: 0.25, w_pose: 0.30</span>
        </div>
      </div>

      {/* Posture & Slouch Monitor Card */}
      <div className="bg-[#121a2b]/80 backdrop-blur-md border border-white/10 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {isSlouching ? (
              <ShieldAlert className="w-4 h-4 text-amber-400" />
            ) : (
              <UserCheck className="w-4 h-4 text-emerald-400" />
            )}
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
              Posture & Slouch Monitor
            </span>
          </div>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
              isSlouching
                ? 'bg-amber-500/20 text-amber-400 border-amber-500/40 animate-pulse'
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
            }`}
          >
            {posture}
          </span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-xl bg-black/30 border border-white/5">
          <span className="text-xs text-gray-300">Neck Angle (&theta;):</span>
          <div className="text-right">
            <span className="text-lg font-bold font-mono text-cyan-400">
              {neckAngle.toFixed(1)}°
            </span>
            <span className="text-[10px] text-gray-400 block">
              {neckAngle > 25 ? 'Exceeds 25° threshold' : 'Optimal alignment'}
            </span>
          </div>
        </div>

        {/* Neck angle slider */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-[10px] text-gray-400 uppercase font-mono">Neck &theta;:</span>
          <input
            type="range"
            min="0"
            max="45"
            step="0.5"
            value={neckAngle}
            onChange={(e) => onNeckAngleChange(parseFloat(e.target.value))}
            className="flex-1 h-1.5 bg-black/40 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
        </div>

        <div className="mt-3 flex items-center justify-between text-[11px] text-gray-400 pt-2 border-t border-white/5">
          <span>Camera Sensing: MediaPipe Pose</span>
          <span className="font-mono text-cyan-400/80">Threshold: 25.0°</span>
        </div>
      </div>
    </div>
  );
};
