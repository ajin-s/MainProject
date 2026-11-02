import React, { useState } from 'react';
import {
  EduGraphData,
  GeneratedStudyPlan,
  StudyPlanItem,
  buildEduGraphFromMaterial,
  generateStudyPlan,
} from '../logic/studyPlanEngine';
import {
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  FileText,
  Network,
  PlayCircle,
  Sparkles,
  Upload,
} from 'lucide-react';

interface StudyPlanStudioProps {
  onSelectConceptForStudy: (conceptTitle: string) => void;
  onMasteryUpdated: (newMastery: number) => void;
  activeTopic: string;
}

const DEFAULT_AI_MATERIAL = `
Module 1: Foundations of Artificial Intelligence & Search
- Problem Formulation, State Spaces, and Uninformed vs Informed Search
- Heuristic Functions, Admissibility, and Consistency in A* Search
- Adversarial Search: Game Trees, Minimax Algorithm, and Alpha-Beta Pruning
- Constraint Satisfaction Problems (CSP) and Backtracking Search

Module 2: Machine Learning & Statistical Models
- Supervised Learning: Linear Regression, Logistic Regression, and Loss Functions
- Optimization Dynamics: Gradient Descent, Learning Rate Pacing, and Momentum
- Neural Networks & Deep Learning: Multi-Layer Perceptrons, Activations, and Backpropagation
- Overfitting Defenses: L1 (Lasso) and L2 (Ridge) Regularization, Dropout, Cross-Validation

Module 3: Knowledge Representation & Logical Reasoning
- Propositional Logic, Truth Tables, and Horn Clauses
- First-Order Logic (FOL): Quantifiers, Unification, and Forward/Backward Chaining
- Automated Theorem Proving with Resolution Refutation
`;

export const StudyPlanStudio: React.FC<StudyPlanStudioProps> = ({
  onSelectConceptForStudy,
  onMasteryUpdated,
  activeTopic,
}) => {
  const [materialTitle, setMaterialTitle] = useState(
    activeTopic === 'Machine Learning'
      ? 'Machine Learning & Statistical Optimization'
      : activeTopic === 'Artificial Intelligence'
      ? 'Artificial Intelligence: Search, Logic & Optimization'
      : `${activeTopic} Core Curriculum`
  );
  const [rawText, setRawText] = useState(DEFAULT_AI_MATERIAL);
  const [daysAvailable, setDaysAvailable] = useState<number>(5);
  const [dailyHours, setDailyHours] = useState<number>(2);

  // Generated results
  const [eduGraph, setEduGraph] = useState<EduGraphData>(() =>
    buildEduGraphFromMaterial(materialTitle, DEFAULT_AI_MATERIAL)
  );

  const [studyPlan, setStudyPlan] = useState<GeneratedStudyPlan>(() =>
    generateStudyPlan(
      buildEduGraphFromMaterial(materialTitle, DEFAULT_AI_MATERIAL),
      materialTitle,
      5,
      2
    )
  );

  const [activeTab, setActiveTab] = useState<'plan' | 'edugraph' | 'syllabus'>('plan');

  const handleGenerate = () => {
    const graph = buildEduGraphFromMaterial(materialTitle, rawText);
    setEduGraph(graph);
    const plan = generateStudyPlan(graph, materialTitle, daysAvailable, dailyHours);
    setStudyPlan(plan);
    onMasteryUpdated(plan.overallMastery / 100);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setMaterialTitle(file.name.replace(/\.[^/.]+$/, ''));
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content) {
        setRawText(content);
      }
    };
    reader.readAsText(file);
  };

  const toggleItemCompleted = (itemId: string) => {
    setStudyPlan((prev) => {
      const updatedItems = prev.items.map((item) => {
        if (item.id === itemId) {
          const nextStatus = item.status === 'completed' ? 'in_progress' : 'completed';
          return { ...item, status: nextStatus as any };
        }
        return item;
      });

      const completedCount = updatedItems.filter((i) => i.status === 'completed').length;
      const newMastery = Math.round((completedCount / updatedItems.length) * 100);
      onMasteryUpdated(newMastery / 100);

      return {
        ...prev,
        items: updatedItems,
        overallMastery: newMastery,
      };
    });
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Compass className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">
              Adaptive Study Plan &amp; EduGraph Generator
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Ingest study notes, construct prerequisite EduGraphs, and generate a personalized day-by-day exam roadmap.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setActiveTab('plan')}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'plan'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Study Plan ({studyPlan.items.length} Days)
            </button>
            <button
              onClick={() => setActiveTab('edugraph')}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'edugraph'
                  ? 'bg-white text-indigo-600 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              EduGraph ({eduGraph.nodes.length} Nodes)
            </button>
            <button
              onClick={() => setActiveTab('syllabus')}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'syllabus'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Syllabus Outline
            </button>
          </div>
        </div>
      </div>

      {/* Input / Ingestion Controls */}
      <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-3.5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex-1 min-w-[240px]">
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Course / Exam Subject Title:
            </label>
            <input
              type="text"
              value={materialTitle}
              onChange={(e) => setMaterialTitle(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 font-medium"
              placeholder="e.g. Artificial Intelligence: Search, Logic & Optimization"
            />
          </div>

          <div className="flex items-center gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Days Until Exam:
              </label>
              <select
                value={daysAvailable}
                onChange={(e) => setDaysAvailable(parseInt(e.target.value))}
                className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 font-bold focus:outline-none"
              >
                <option value={3}>3 Days (Crash Course)</option>
                <option value={5}>5 Days (Intensive)</option>
                <option value={7}>7 Days (Standard 1-Week)</option>
                <option value={14}>14 Days (Comprehensive)</option>
                <option value={30}>30 Days (Full Semester)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Daily Study Hours:
              </label>
              <select
                value={dailyHours}
                onChange={(e) => setDailyHours(parseFloat(e.target.value))}
                className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 font-bold focus:outline-none"
              >
                <option value={1}>1 Hour / Day</option>
                <option value={2}>2 Hours / Day</option>
                <option value={3}>3 Hours / Day</option>
                <option value={4}>4 Hours / Day</option>
              </select>
            </div>

            <div className="pt-5">
              <label className="cursor-pointer px-3.5 py-2 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-xs text-slate-700 font-semibold flex items-center gap-1.5 transition-colors shadow-sm">
                <Upload className="w-3.5 h-3.5 text-indigo-600" />
                <span>Upload Syllabus Notes</span>
                <input
                  type="file"
                  accept=".txt,.md,.pdf,.csv"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1">
            Raw Study Materials / Syllabus Topics:
          </label>
          <textarea
            rows={3}
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-xs text-slate-800 font-mono focus:outline-none focus:border-indigo-500"
            placeholder="Paste syllabus modules, lecture slides, formulas, or topic outlines..."
          />
        </div>

        <button
          onClick={handleGenerate}
          className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm transition-all flex items-center justify-center gap-2"
        >
          <Sparkles className="w-4 h-4 text-white" />
          <span>Build EduGraph &amp; Re-generate Adaptive Study Plan</span>
        </button>
      </div>

      {/* Main Content Viewport */}
      {activeTab === 'plan' && (
        <div className="space-y-4">
          {/* Plan Summary Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 text-xs">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-mono">Exam Target</span>
              <span className="font-bold text-slate-900 truncate block">{studyPlan.targetExam}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-mono">Exam Target Date</span>
              <span className="font-bold text-indigo-600">{studyPlan.examDate}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-mono">Pacing</span>
              <span className="font-bold text-slate-900">
                {studyPlan.totalDays} Days • {studyPlan.dailyHours} hrs/day
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-mono">
                Curriculum Progress
              </span>
              <span className="font-bold text-emerald-600">
                {studyPlan.overallMastery}% Completed
              </span>
            </div>
          </div>

          {/* Day-by-Day Plan Timeline Cards */}
          <div className="space-y-3">
            {studyPlan.items.map((item) => {
              const isDone = item.status === 'completed';
              return (
                <div
                  key={item.id}
                  className={`border rounded-xl p-4 transition-all ${
                    isDone
                      ? 'bg-slate-50 border-emerald-200'
                      : 'bg-white border-slate-200 hover:border-indigo-300 shadow-sm'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => toggleItemCompleted(item.id)}
                        className={`w-6 h-6 rounded-full border flex items-center justify-center transition-colors ${
                          isDone
                            ? 'bg-emerald-600 border-emerald-600 text-white'
                            : 'border-slate-300 hover:border-indigo-600 text-transparent'
                        }`}
                        title="Toggle completed"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                            Day {item.day} • {item.dateStr}
                          </span>
                          <span className="text-xs text-slate-500 font-mono">
                            {item.durationMinutes} mins
                          </span>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                              item.difficulty === 'Beginner'
                                ? 'bg-emerald-50 text-emerald-700'
                                : item.difficulty === 'Intermediate'
                                ? 'bg-indigo-50 text-indigo-700'
                                : 'bg-amber-50 text-amber-800'
                            }`}
                          >
                            {item.difficulty}
                          </span>
                        </div>
                        <h4
                          className={`text-sm font-bold mt-1 ${
                            isDone ? 'line-through text-slate-400' : 'text-slate-900'
                          }`}
                        >
                          {item.conceptTitle}
                        </h4>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      <button
                        onClick={() => onSelectConceptForStudy(item.conceptTitle)}
                        className="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
                      >
                        <PlayCircle className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Study with Robot</span>
                      </button>
                    </div>
                  </div>

                  {/* Objectives list */}
                  <div className="mt-2.5 pl-9 text-xs text-slate-600 space-y-1">
                    {item.keyObjectives.map((obj, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                        <span>{obj}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* EduGraph Tab */}
      {activeTab === 'edugraph' && (
        <div className="space-y-4">
          <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl text-xs text-indigo-800 font-medium">
            {eduGraph.summary}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {eduGraph.nodes.map((node, i) => (
              <div
                key={node.id}
                className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2 hover:border-indigo-300 transition-colors shadow-sm"
              >
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Node #{i + 1}</span>
                  <span className="text-indigo-600 font-bold">
                    Mastery: {Math.round(node.mastery * 100)}%
                  </span>
                </div>
                <div className="text-xs font-bold text-slate-900">{node.name}</div>
                <div className="text-[11px] text-slate-500">
                  Prerequisites:{' '}
                  <span className="text-slate-700 font-medium">
                    {node.connections.length > 0 ? node.connections.join(', ') : 'Root Foundation'}
                  </span>
                </div>
                <button
                  onClick={() => onSelectConceptForStudy(node.name)}
                  className="w-full py-1.5 text-center rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-[11px] text-indigo-600 font-semibold transition-colors shadow-sm"
                >
                  Query in Socratic Console &rarr;
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extracted Syllabus Tab */}
      {activeTab === 'syllabus' && (
        <div className="space-y-4">
          {eduGraph.extractedSyllabus.map((unit, uIdx) => (
            <div
              key={uIdx}
              className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2 shadow-sm"
            >
              <h4 className="text-xs font-bold font-mono text-indigo-700 uppercase">
                {unit.unitTitle}
              </h4>
              <ul className="space-y-1.5 pl-4 list-disc text-xs text-slate-700">
                {unit.topics.map((top, tIdx) => (
                  <li
                    key={tIdx}
                    className="hover:text-indigo-600 cursor-pointer"
                    onClick={() => onSelectConceptForStudy(top)}
                  >
                    {top}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
