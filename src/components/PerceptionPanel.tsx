import React from 'react';
import { PostureStatus, InterventionLevel } from '../types';
import { Activity, ShieldAlert, UserCheck, ArrowRight } from 'lucide-react';

interface PerceptionPanelProps {
  et: number;
  posture: PostureStatus;
  neckAngle: number;
  isSlouching: boolean;
  interventionLevel: InterventionLevel;
  onEtChange: (val: number) => void;
  onNeckAngleChange: (angle: number) => void;
  onOpenCamera?: () => void;
}

export const PerceptionPanel: React.FC<PerceptionPanelProps> = ({
  et,
  posture,
  neckAngle,
  isSlouching,
  interventionLevel,
  onEtChange,
  onNeckAngleChange,
  onOpenCamera,
}) => {
  return (
    <div className="space-y-4">
      {/* Engagement Card */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-600" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Engagement Telemetry (E_t)
            </span>
          </div>
          <span
            className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border uppercase ${
              interventionLevel === 'IDLE'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : interventionLevel === 'GENTLE'
                ? 'bg-amber-50 text-amber-700 border-amber-200'
                : 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse'
            }`}
          >
            Intervention: {interventionLevel}
          </span>
        </div>

        <div className="flex items-baseline justify-between my-2">
          <div className="text-3xl font-bold font-mono tracking-tight text-slate-900">
            {et.toFixed(2)}
          </div>
          <span className="text-xs font-mono font-medium text-slate-500">
            {et >= 0.75 ? 'HIGH FOCUS' : et >= 0.40 ? 'MODERATE FOCUS' : 'DISENGAGED'}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden p-0.5">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              et >= 0.7
                ? 'bg-emerald-500'
                : et >= 0.4
                ? 'bg-indigo-500'
                : 'bg-rose-500'
            }`}
            style={{ width: `${Math.round(et * 100)}%` }}
          ></div>
        </div>

        {/* Slider for live adjustment */}
        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center gap-2">
          <span className="text-[10px] text-slate-500 uppercase font-mono font-semibold">
            Adjust E_t:
          </span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={et}
            onChange={(e) => onEtChange(parseFloat(e.target.value))}
            className="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
        </div>

        <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400">
          <span>Rolling 2s Ring Buffer (5 Hz)</span>
          <span className="font-mono text-slate-500">w_gaze: 0.45, w_blink: 0.25</span>
        </div>
      </div>

      {/* Posture & Slouch Monitor Card */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {isSlouching ? (
              <ShieldAlert className="w-4 h-4 text-amber-600" />
            ) : (
              <UserCheck className="w-4 h-4 text-emerald-600" />
            )}
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Posture &amp; Slouch Monitor
            </span>
          </div>
          <span
            className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border uppercase ${
              isSlouching
                ? 'bg-amber-50 text-amber-800 border-amber-200 animate-pulse'
                : 'bg-emerald-50 text-emerald-700 border-emerald-200'
            }`}
          >
            {posture}
          </span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/60">
          <span className="text-xs text-slate-600">Neck Angle (&theta;):</span>
          <div className="text-right">
            <span
              className={`text-lg font-bold font-mono ${
                isSlouching ? 'text-amber-600' : 'text-slate-900'
              }`}
            >
              {neckAngle.toFixed(1)}°
            </span>
            <span className="text-[10px] text-slate-400 block">
              {neckAngle > 22 ? 'Slouching (>22°)' : 'Upright Alignment'}
            </span>
          </div>
        </div>

        {/* Neck angle slider */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-[10px] text-slate-500 uppercase font-mono font-semibold">
            Neck &theta;:
          </span>
          <input
            type="range"
            min="0"
            max="45"
            step="0.5"
            value={neckAngle}
            onChange={(e) => onNeckAngleChange(parseFloat(e.target.value))}
            className="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
        </div>

        <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
          <span>Camera Vision Tracking</span>
          {onOpenCamera ? (
            <button
              onClick={onOpenCamera}
              className="text-indigo-600 hover:text-indigo-700 font-semibold flex items-center gap-1 transition-colors"
            >
              <span>Open Camera HUD</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          ) : (
            <span className="font-mono text-slate-400">Threshold: 22.0°</span>
          )}
        </div>
      </div>
    </div>
  );
};
