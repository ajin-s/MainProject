import React from 'react';
import { ServoAngles } from '../types';
import { Cpu, RotateCcw, Play } from 'lucide-react';

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
    <div className="bg-[#121a2b]/80 backdrop-blur-md border border-white/10 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
            PCA9685 Servo Angles (I2C 0x40)
          </span>
        </div>
        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
          MG90S 4-AXIS
        </span>
      </div>

      {/* 2x2 Grid matching web_dashboard.py */}
      <div className="grid grid-cols-2 gap-2.5">
        {servosMeta.map((s) => {
          const val = servoAngles[s.channel] ?? 0;
          return (
            <div
              key={s.channel}
              className="bg-black/30 border border-white/5 rounded-xl p-3 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                <span>{s.name}</span>
                <span className="font-mono text-[10px] text-gray-400">CH{s.channel}</span>
              </div>
              <div className="text-xl font-bold font-mono text-cyan-400">
                {val.toFixed(1)}{s.unit}
              </div>
              <input
                type="range"
                min={s.min}
                max={s.max}
                step="1"
                value={val}
                onChange={(e) => onSetAngle(s.channel, parseFloat(e.target.value))}
                className="mt-2 w-full h-1 bg-white/10 rounded appearance-none cursor-pointer accent-cyan-400"
              />
            </div>
          );
        })}
      </div>

      {/* Preset Choreography Actions */}
      <div className="pt-2 border-t border-white/5">
        <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block mb-2">
          Choreography Presets
        </span>
        <div className="grid grid-cols-3 gap-1.5 text-xs">
          <button
            onClick={() => onRunChoreography('nod')}
            className="py-1 px-2 rounded bg-white/5 hover:bg-white/10 text-gray-300 font-medium transition-colors text-center"
          >
            Nod Yes
          </button>
          <button
            onClick={() => onRunChoreography('shake')}
            className="py-1 px-2 rounded bg-white/5 hover:bg-white/10 text-gray-300 font-medium transition-colors text-center"
          >
            Shake No
          </button>
          <button
            onClick={() => onRunChoreography('wave')}
            className="py-1 px-2 rounded bg-white/5 hover:bg-white/10 text-gray-300 font-medium transition-colors text-center"
          >
            Celebration
          </button>
          <button
            onClick={() => onRunChoreography('alert')}
            className="py-1 px-2 rounded bg-red-500/10 hover:bg-red-500/20 text-red-300 font-medium transition-colors text-center border border-red-500/20"
          >
            Alert Pose
          </button>
          <button
            onClick={() => onRunChoreography('curious')}
            className="py-1 px-2 rounded bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-300 font-medium transition-colors text-center border border-yellow-500/20"
          >
            Curious Tilt
          </button>
          <button
            onClick={() => onRunChoreography('neutral')}
            className="py-1 px-2 rounded bg-white/5 hover:bg-white/10 text-gray-400 font-medium transition-colors text-center flex items-center justify-center gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};
