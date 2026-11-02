import React from 'react';
import { ExamRisk } from '../types';
import { Award, Calendar, HelpCircle, Check, Minus } from 'lucide-react';

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
  high: { text: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200' },
  medium: { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' },
  low: { text: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' },
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
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Award className="w-4 h-4 text-indigo-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            BKT Mastery Tracker
          </span>
        </div>
        <span
          className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border uppercase ${badge.bg} ${badge.text} ${badge.border}`}
        >
          {examRisk.toUpperCase()} RISK
        </span>
      </div>

      <div>
        <div className="text-sm font-bold text-slate-900 tracking-tight truncate">{topic}</div>
        <div className="flex items-baseline justify-between mt-1">
          <div className="text-3xl font-bold font-mono tracking-tight text-slate-900">
            {masteryPct}%
          </div>
          <span className="text-xs font-mono text-indigo-600 font-semibold">
            P(L_t) = {pMastery.toFixed(3)}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden p-0.5 mt-2">
          <div
            className="h-full rounded-full bg-indigo-600 transition-all duration-500 shadow-sm"
            style={{ width: `${masteryPct}%` }}
          ></div>
        </div>
      </div>

      {/* Exam Countdown */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/60">
        <div className="flex items-center gap-2.5">
          <Calendar className="w-4 h-4 text-indigo-600" />
          <div>
            <div className="text-xs font-semibold text-slate-900">Nearest Exam: {nearestExam}</div>
            <div className="text-[11px] text-slate-500">
              {daysLeft} days remaining {daysLeft <= 3 ? '⚠️ Urgent' : ''}
            </div>
          </div>
        </div>
        <span
          className={`text-xs font-bold font-mono px-2.5 py-1 rounded-md ${
            daysLeft <= 3
              ? 'bg-rose-100 text-rose-800 border border-rose-200'
              : 'bg-slate-200 text-slate-700'
          }`}
        >
          {daysLeft}d left
        </span>
      </div>

      {/* Interactive Quiz & Simulation controls */}
      <div className="pt-2 border-t border-slate-100 space-y-2">
        <button
          onClick={onOpenQuiz}
          className="w-full py-2.5 px-3 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all flex items-center justify-center gap-2"
        >
          <HelpCircle className="w-4 h-4" />
          Test Knowledge (BKT Quiz)
        </button>

        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <button
            onClick={() => onSimulateAnswer(true)}
            className="py-1.5 px-2 rounded-lg font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-all text-center flex items-center justify-center gap-1 shadow-sm"
          >
            <Check className="w-3 h-3" />
            Correct (+BKT)
          </button>
          <button
            onClick={() => onSimulateAnswer(false)}
            className="py-1.5 px-2 rounded-lg font-semibold bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-all text-center flex items-center justify-center gap-1 shadow-sm"
          >
            <Minus className="w-3 h-3" />
            Incorrect (-BKT)
          </button>
        </div>
      </div>

      <div className="text-[10px] text-slate-400 flex items-center justify-between pt-1 font-mono">
        <span>p_transit=0.1, p_slip=0.1, p_guess=0.2</span>
        <span className="text-indigo-600 font-semibold">SRS §5.4</span>
      </div>
    </div>
  );
};
