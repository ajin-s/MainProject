import React from 'react';
import { ExamRisk } from '../types';
import { Award, Calendar, HelpCircle, TrendingUp } from 'lucide-react';

interface BktTrackerProps {
  topic: string;
  pMastery: number;
  nearestExam: string;
  daysLeft: number;
  examRisk: ExamRisk;
  onOpenQuiz: () => void;
  onSimulateAnswer: (correct: boolean) => void;
}

const RISK_BADGES: Record<ExamRisk, { text: string; bg: string; border: string }> = {
  high: { text: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/30' },
  medium: { text: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/30' },
  low: { text: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30' },
};

export const BktTracker: React.FC<BktTrackerProps> = ({
  topic,
  pMastery,
  nearestExam,
  daysLeft,
  examRisk,
  onOpenQuiz,
  onSimulateAnswer,
}) => {
  const masteryPct = Math.round(pMastery * 100);
  const badge = RISK_BADGES[examRisk] || RISK_BADGES.low;

  return (
    <div className="bg-[#121a2b]/80 backdrop-blur-md border border-white/10 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Award className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
            BKT Mastery Tracker
          </span>
        </div>
        <span
          className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded border uppercase ${badge.bg} ${badge.text} ${badge.border}`}
        >
          {examRisk.toUpperCase()} RISK
        </span>
      </div>

      <div>
        <div className="text-sm font-semibold text-white tracking-wide truncate">{topic}</div>
        <div className="flex items-baseline justify-between mt-1">
          <div className="text-4xl font-bold font-mono tracking-tight text-white">
            {masteryPct}%
          </div>
          <span className="text-xs font-mono text-purple-300">
            P(L_t) = {pMastery.toFixed(3)}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-white/10 h-2.5 rounded-full overflow-hidden p-0.5 mt-2">
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-500 via-indigo-500 to-cyan-400 transition-all duration-500 shadow-[0_0_12px_rgba(59,130,246,0.5)]"
            style={{ width: `${masteryPct}%` }}
          ></div>
        </div>
      </div>

      {/* Exam Countdown */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-black/30 border border-white/5">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-cyan-400" />
          <div>
            <div className="text-xs font-semibold text-white">Nearest Exam: {nearestExam}</div>
            <div className="text-[11px] text-gray-400">
              {daysLeft} days remaining {daysLeft <= 3 ? '⚠️ Urgent' : ''}
            </div>
          </div>
        </div>
        <span
          className={`text-xs font-bold font-mono px-2 py-1 rounded ${
            daysLeft <= 3 ? 'bg-red-500/20 text-red-300' : 'bg-white/10 text-gray-300'
          }`}
        >
          {daysLeft}d left
        </span>
      </div>

      {/* Interactive Quiz & Simulation controls */}
      <div className="pt-2 border-t border-white/5 space-y-2">
        <button
          onClick={onOpenQuiz}
          className="w-full py-2.5 px-3 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white shadow-lg shadow-purple-600/20 transition-all flex items-center justify-center gap-2"
        >
          <HelpCircle className="w-4 h-4" />
          Test Knowledge (Interactive Quiz)
        </button>

        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <button
            onClick={() => onSimulateAnswer(true)}
            className="py-1.5 px-2 rounded-lg font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/25 transition-all text-center"
          >
            + Correct Ans (BKT ↑)
          </button>
          <button
            onClick={() => onSimulateAnswer(false)}
            className="py-1.5 px-2 rounded-lg font-semibold bg-red-500/15 text-red-300 border border-red-500/30 hover:bg-red-500/25 transition-all text-center"
          >
            - Wrong Ans (BKT ↓)
          </button>
        </div>
      </div>

      <div className="text-[10px] text-gray-400 flex items-center justify-between pt-1">
        <span>BKT: p_transit=0.1, p_slip=0.1, p_guess=0.2</span>
        <span className="text-purple-300/80">SRS §5.4</span>
      </div>
    </div>
  );
};
