import React, { useState } from 'react';
import { StudentProfile, LearnerCharacterisation, LearningStyle } from '../types';
import {
  User,
  Sparkles,
  BookOpen,
  Award,
  Zap,
  CheckCircle,
  Activity,
  Layers,
  X,
  Target,
} from 'lucide-react';

interface StudentProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: StudentProfile;
  characterisation: LearnerCharacterisation;
  onSaveProfile: (profile: StudentProfile) => void;
  availableTopics: string[];
}

export const StudentProfileModal: React.FC<StudentProfileModalProps> = ({
  isOpen,
  onClose,
  profile,
  characterisation,
  onSaveProfile,
  availableTopics,
}) => {
  if (!isOpen) return null;

  const [name, setName] = useState(profile.name || '');
  const [major, setMajor] = useState(profile.major || 'Computer Science & AI');
  const [year, setYear] = useState(profile.year || 'Year 4 (Senior)');
  const [preferredStyle, setPreferredStyle] = useState<LearningStyle>(profile.preferredStyle);
  const [targetGoal, setTargetGoal] = useState(profile.targetGoal || 'Artificial Intelligence');

  const [activeTab, setActiveTab] = useState<'edit' | 'characterisation'>('edit');

  const handleSave = () => {
    onSaveProfile({
      ...profile,
      name: name.trim() || 'Student',
      major,
      year,
      preferredStyle,
      targetGoal,
      isFirstTime: false,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative text-slate-800">
        {!profile.isFirstTime && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
            <User className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-900">
                {profile.isFirstTime ? 'Welcome! Set Up Your Student Profile' : 'Student Learner Profile'}
              </h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                GraphRAG Persona
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              SmartEduSync adapts Socratic tutoring, voice pitch, and concept recommendations to your personal learning habits.
            </p>
          </div>
        </div>

        {/* Tabs */}
        {!profile.isFirstTime && (
          <div className="flex bg-slate-100 p-1 rounded-xl mb-5 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('edit')}
              className={`flex-1 py-1.5 rounded-lg transition-all ${
                activeTab === 'edit'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Profile Settings
            </button>
            <button
              onClick={() => setActiveTab('characterisation')}
              className={`flex-1 py-1.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                activeTab === 'characterisation'
                  ? 'bg-white text-indigo-600 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
              Dynamic GraphRAG Characterisation
            </button>
          </div>
        )}

        {activeTab === 'edit' ? (
          <div className="space-y-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Your Full Name:</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Alex Chen"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Academic Major:</label>
                <input
                  type="text"
                  value={major}
                  onChange={(e) => setMajor(e.target.value)}
                  placeholder="e.g. Computer Science & AI"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Academic Year:</label>
                <select
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:border-indigo-500 font-medium"
                >
                  <option value="Year 1 (Freshman)">Year 1 (Freshman)</option>
                  <option value="Year 2 (Sophomore)">Year 2 (Sophomore)</option>
                  <option value="Year 3 (Junior)">Year 3 (Junior)</option>
                  <option value="Year 4 (Senior)">Year 4 (Senior)</option>
                  <option value="Graduate / Master">Graduate / Master</option>
                </select>
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1.5">
                Preferred Learning &amp; Explanation Style:
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(
                  [
                    'Intuitive & Analogy',
                    'Mathematical & Rigorous',
                    'Applied & Hands-on',
                  ] as LearningStyle[]
                ).map((style) => (
                  <button
                    key={style}
                    type="button"
                    onClick={() => setPreferredStyle(style)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      preferredStyle === style
                        ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold shadow-sm'
                        : 'border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    <div className="text-[11px] font-semibold">{style.split('&')[0]}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5 font-normal">
                      {style.includes('Intuitive')
                        ? 'Metaphors & intuition'
                        : style.includes('Mathematical')
                        ? 'Proofs & derivations'
                        : 'Real code & robotics'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Target Priority Subject / Exam:
              </label>
              <select
                value={targetGoal}
                onChange={(e) => setTargetGoal(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:border-indigo-500 font-medium"
              >
                {availableTopics.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={handleSave}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-sm transition-all"
              >
                {profile.isFirstTime ? 'Complete Onboarding & Start' : 'Save Profile Changes'}
              </button>
            </div>
          </div>
        ) : (
          /* Dynamic GraphRAG Characterisation View */
          <div className="space-y-4 text-xs">
            <div className="p-3.5 bg-indigo-50/60 border border-indigo-100 rounded-xl">
              <div className="flex items-center gap-1.5 text-indigo-900 font-semibold mb-1">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                Live GraphRAG Personality Node Summary
              </div>
              <p className="text-slate-600 leading-relaxed text-[11px]">
                {characterisation.graphRAGSummary}
              </p>
            </div>

            {/* Cognitive & Focus Metrics */}
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[10px] text-slate-500 uppercase font-mono block">
                  Focus Resilience
                </span>
                <span className="text-base font-bold text-emerald-600 font-mono">
                  {characterisation.focusResilience}%
                </span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[10px] text-slate-500 uppercase font-mono block">
                  Fatigue Index
                </span>
                <span className="text-base font-bold text-amber-600 font-mono">
                  {characterisation.postureFatigueIndex}%
                </span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[10px] text-slate-500 uppercase font-mono block">
                  Cognitive Pace
                </span>
                <span className="text-xs font-bold text-indigo-600 uppercase">
                  {characterisation.cognitivePace}
                </span>
              </div>
            </div>

            {/* Strengths & Growth Nodes */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-xl">
                <span className="text-[10px] font-bold text-emerald-800 uppercase block mb-1">
                  Mastered Concept Anchors
                </span>
                <div className="space-y-1">
                  {characterisation.conceptualStrength.map((s, i) => (
                    <div key={i} className="flex items-center gap-1 text-[11px] text-emerald-900 font-medium">
                      <CheckCircle className="w-3 h-3 text-emerald-600 shrink-0" />
                      <span className="truncate">{s}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-amber-50/50 border border-amber-100 rounded-xl">
                <span className="text-[10px] font-bold text-amber-800 uppercase block mb-1">
                  Active Growth Nodes
                </span>
                <div className="space-y-1">
                  {characterisation.growthAreas.map((w, i) => (
                    <div key={i} className="flex items-center gap-1 text-[11px] text-amber-900 font-medium">
                      <Target className="w-3 h-3 text-amber-600 shrink-0" />
                      <span className="truncate">{w}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Personality Tags */}
            <div>
              <span className="text-[11px] font-semibold text-slate-700 block mb-1.5">
                Dynamic Behavioral Badges:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {characterisation.personalityTags.map((tag, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-[10px] font-medium"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
