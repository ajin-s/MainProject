import React, { useState } from 'react';
import { QuizItem } from '../types';
import { SAMPLE_QUIZZES } from '../logic/socratic';
import { CheckCircle2, HelpCircle, X, XCircle, ArrowRight } from 'lucide-react';

interface QuizModalProps {
  isOpen: boolean;
  onClose: () => void;
  topic: string;
  onAnswerSubmitted: (correct: boolean) => void;
  currentMastery: number;
}

export const QuizModal: React.FC<QuizModalProps> = ({
  isOpen,
  onClose,
  topic,
  onAnswerSubmitted,
  currentMastery,
}) => {
  if (!isOpen) return null;

  const questions: QuizItem[] =
    SAMPLE_QUIZZES[topic] || SAMPLE_QUIZZES['Artificial Intelligence'] || SAMPLE_QUIZZES['Calculus Integrals'];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const currentQ = questions[currentIndex % questions.length];

  const handleSelect = (idx: number) => {
    if (hasSubmitted) return;
    setSelectedOption(idx);
  };

  const handleSubmit = () => {
    if (selectedOption === null || hasSubmitted) return;
    setHasSubmitted(true);
    const isCorrect = selectedOption === currentQ.correctIndex;
    onAnswerSubmitted(isCorrect);
  };

  const handleNext = () => {
    setSelectedOption(null);
    setHasSubmitted(false);
    setCurrentIndex((prev) => (prev + 1) % questions.length);
  };

  const isCorrect = selectedOption === currentQ.correctIndex;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative text-slate-800">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-2 text-indigo-600 text-xs font-mono font-semibold uppercase">
          <HelpCircle className="w-4 h-4" />
          <span>BKT Knowledge Check • Question {currentIndex + 1} of {questions.length}</span>
        </div>

        <h3 className="text-lg font-bold text-slate-900 mb-1">{topic}</h3>
        <p className="text-xs text-slate-500 mb-4 font-mono">
          Concept: <span className="text-indigo-600 font-semibold">{currentQ.concept}</span> • Current Mastery: {Math.round(currentMastery * 100)}%
        </p>

        {/* Question Text */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm font-medium text-slate-800 mb-4 leading-relaxed">
          {currentQ.question}
        </div>

        {/* Options */}
        <div className="space-y-2 mb-5">
          {currentQ.options.map((opt, idx) => {
            let itemStyle = 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700';
            if (hasSubmitted) {
              if (idx === currentQ.correctIndex) {
                itemStyle = 'border-emerald-500 bg-emerald-50 text-emerald-900 font-medium';
              } else if (idx === selectedOption) {
                itemStyle = 'border-rose-500 bg-rose-50 text-rose-900';
              }
            } else if (selectedOption === idx) {
              itemStyle = 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-medium';
            }

            return (
              <button
                key={idx}
                onClick={() => handleSelect(idx)}
                className={`w-full text-left p-3 rounded-xl border text-xs md:text-sm transition-all flex items-start gap-3 shadow-sm ${itemStyle}`}
              >
                <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-[10px] font-mono shrink-0 mt-0.5">
                  {String.fromCharCode(65 + idx)}
                </span>
                <span className="flex-1 leading-snug">{opt}</span>
              </button>
            );
          })}
        </div>

        {/* Feedback explanation */}
        {hasSubmitted && (
          <div
            className={`p-3.5 rounded-xl mb-4 text-xs ${
              isCorrect
                ? 'bg-emerald-50 border border-emerald-200 text-emerald-900'
                : 'bg-rose-50 border border-rose-200 text-rose-900'
            }`}
          >
            <div className="font-bold flex items-center gap-1.5 mb-1">
              {isCorrect ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Correct! BKT mastery increased.
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4 text-rose-600" />
                  Incorrect. BKT probability adjusted.
                </>
              )}
            </div>
            <p className="text-slate-600">{currentQ.explanation}</p>
          </div>
        )}

        {/* Action button */}
        <div className="flex justify-end gap-2">
          {!hasSubmitted ? (
            <button
              onClick={handleSubmit}
              disabled={selectedOption === null}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white shadow-sm transition-all"
            >
              Submit Answer
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white flex items-center gap-1.5 transition-all shadow-sm"
            >
              <span>Next Question</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
