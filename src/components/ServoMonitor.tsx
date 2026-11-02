import React from 'react';
import { ServoAngles } from '../types';
import { Cpu, RotateCcw } from 'lucide-react';

interface ServoMonitorProps {
  servoAngles: ServoAngles;
  onSetAngle: (channel: 0 | 1 | 2 | 3, angle: number) => void;
  onRunChoreography: (name: string) => void;
}

export const ServoMonitor: React.FC<ServoMonitorProps> = ({
  servoAngles,
  onSetAngle,
  onRunChoreography,
}) => {
  const servosMeta = [
    { channel: 0 as const, name: 'Head Pan', min: -90, max: 90, unit: '°' },
    { channel: 1 as const, name: 'Head Tilt', min: -30, max: 45, unit: '°' },
    { channel: 2 as const, name: 'Left Arm', min: 0, max: 120, unit: '°' },
    { channel: 3 as const, name: 'Right Arm', min: 0, max: 120, unit: '°' },
  ];

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            PCA9685 Servo Hardware (I2C)
          </span>
        </div>
        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
          MG90S 4-AXIS
        </span>
      </div>

      {/* 2x2 Grid */}
      <div className="grid grid-cols-2 gap-2.5">
        {servosMeta.map((s) => {
          const val = servoAngles[s.channel] ?? 0;
          return (
            <div
              key={s.channel}
              className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                <span className="font-medium text-slate-700">{s.name}</span>
                <span className="font-mono text-[10px] text-slate-400">CH{s.channel}</span>
              </div>
              <div className="text-lg font-bold font-mono text-slate-900">
                {val.toFixed(1)}{s.unit}
              </div>
              <input
                type="range"
                min={s.min}
                max={s.max}
                step="1"
                value={val}
                onChange={(e) => onSetAngle(s.channel, parseFloat(e.target.value))}
                className="mt-2 w-full h-1.5 bg-slate-200 rounded appearance-none cursor-pointer accent-indigo-600"
              />
            </div>
          );
        })}
      </div>

      {/* Preset Choreography Actions */}
      <div className="pt-2 border-t border-slate-100">
        <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider block mb-2">
          Physical Choreography Presets
        </span>
        <div className="grid grid-cols-3 gap-1.5 text-xs">
          <button
            onClick={() => onRunChoreography('nod')}
            className="py-1.5 px-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium transition-colors border border-slate-200 text-center shadow-sm"
          >
            Nod Yes
          </button>
          <button
            onClick={() => onRunChoreography('shake')}
            className="py-1.5 px-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium transition-colors border border-slate-200 text-center shadow-sm"
          >
            Shake No
          </button>
          <button
            onClick={() => onRunChoreography('wave')}
            className="py-1.5 px-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium transition-colors border border-slate-200 text-center shadow-sm"
          >
            Celebration
          </button>
          <button
            onClick={() => onRunChoreography('alert')}
            className="py-1.5 px-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 font-medium transition-colors text-center border border-rose-200 shadow-sm"
          >
            Alert Pose
          </button>
          <button
            onClick={() => onRunChoreography('curious')}
            className="py-1.5 px-2 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-700 font-medium transition-colors text-center border border-amber-200 shadow-sm"
          >
            Curious Tilt
          </button>
          <button
            onClick={() => onRunChoreography('neutral')}
            className="py-1.5 px-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 font-medium transition-colors text-center flex items-center justify-center gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};
