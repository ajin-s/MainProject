import React from 'react';
import { Bot, Sparkles, Volume2, VolumeX } from 'lucide-react';

interface HeaderProps {
  activeTopic: string;
  onTopicChange: (topic: string) => void;
  availableTopics: string[];
  ttsEnabled: boolean;
  onToggleTts: () => void;
  onOpenGraph: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTopic,
  onTopicChange,
  availableTopics,
  ttsEnabled,
  onToggleTts,
  onOpenGraph,
}) => {
  return (
    <header className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-white/10 mb-6 gap-4">
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 rounded-xl flex items-center justify-center font-bold text-xl text-white shadow-[0_0_20px_rgba(59,130,246,0.5)] border border-white/20">
          <Bot className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white">SmartEduSync</h1>
            <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-mono">v2.0</span>
          </div>
          <p className="text-xs text-gray-400">Privacy-First Tabletop AI Tutoring Robot & Defense Console</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        <div className="flex items-center gap-2 bg-black/40 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-gray-300">
          <span className="text-gray-400 font-medium">Topic:</span>
          <select
            value={activeTopic}
            onChange={(e) => onTopicChange(e.target.value)}
            className="bg-transparent text-cyan-400 font-semibold focus:outline-none cursor-pointer"
          >
            {availableTopics.map((t) => (
              <option key={t} value={t} className="bg-gray-900 text-white">
                {t}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onOpenGraph}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 hover:bg-purple-500/30 transition-colors"
          title="Inspect GraphRAG Concept Graph"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Concept Graph</span>
        </button>

        <button
          onClick={onToggleTts}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
            ttsEnabled
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
              : 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10'
          }`}
          title="Toggle Robot Voice TTS synthesis"
        >
          {ttsEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
          <span>{ttsEnabled ? 'TTS Voice Active' : 'TTS Muted'}</span>
        </button>

        <div className="hidden lg:flex items-center gap-2">
          <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30">
            Team 1: Perception & Emotion
          </span>
          <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/30">
            Team 2: Socratic LLM & RAG
          </span>
        </div>
      </div>
    </header>
  );
};
