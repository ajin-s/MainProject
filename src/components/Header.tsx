import React from 'react';
import { Bot, Sparkles, Volume2, VolumeX, User, ChevronDown } from 'lucide-react';
import { StudentProfile } from '../types';

interface HeaderProps {
  activeTopic: string;
  onTopicChange: (topic: string) => void;
  availableTopics: string[];
  ttsEnabled: boolean;
  onToggleTts: () => void;
  onOpenGraph: () => void;
  studentProfile: StudentProfile;
  onOpenProfile: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTopic,
  onTopicChange,
  availableTopics,
  ttsEnabled,
  onToggleTts,
  onOpenGraph,
  studentProfile,
  onOpenProfile,
}) => {
  return (
    <header className="bg-white border border-slate-200/80 rounded-2xl px-5 py-4 mb-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div className="flex items-center gap-3.5">
        <div className="w-10 h-10 bg-slate-900 text-white rounded-xl flex items-center justify-center font-bold text-lg shadow-sm">
          <Bot className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold text-slate-900 tracking-tight">SmartEduSync</h1>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200 font-mono">
              v2.5
            </span>
            <span className="hidden sm:inline-block text-[11px] font-medium text-slate-500">
              AI Tutoring Robot &amp; Defense Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Privacy-first tabletop robot with emotion sensing, BKT mastery &amp; GraphRAG syllabus
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        {/* Student Profile Pill */}
        <button
          onClick={onOpenProfile}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-800 transition-colors shadow-sm"
          title="Manage Student Profile & GraphRAG Learner Persona"
        >
          <div className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-[10px] font-bold">
            {studentProfile.name.charAt(0).toUpperCase()}
          </div>
          <span className="truncate max-w-[100px]">{studentProfile.name}</span>
          <ChevronDown className="w-3 h-3 text-slate-400" />
        </button>

        {/* Topic Selector */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 shadow-sm">
          <span className="text-slate-400 font-medium">Subject:</span>
          <select
            value={activeTopic}
            onChange={(e) => onTopicChange(e.target.value)}
            className="bg-transparent text-slate-900 font-semibold focus:outline-none cursor-pointer"
          >
            {availableTopics.map((t) => (
              <option key={t} value={t} className="bg-white text-slate-900">
                {t}
              </option>
            ))}
          </select>
        </div>

        {/* Concept Graph Button */}
        <button
          onClick={onOpenGraph}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors shadow-sm"
          title="Inspect GraphRAG Concept Graph & Student Persona"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>GraphRAG</span>
        </button>

        {/* Emotional TTS Toggle */}
        <button
          onClick={onToggleTts}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors shadow-sm ${
            ttsEnabled
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
              : 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100'
          }`}
          title="Toggle Robot Emotional Voice Synthesis"
        >
          {ttsEnabled ? <Volume2 className="w-3.5 h-3.5 text-emerald-600" /> : <VolumeX className="w-3.5 h-3.5" />}
          <span>{ttsEnabled ? 'Emotional Voice' : 'Voice Muted'}</span>
        </button>
      </div>
    </header>
  );
};
