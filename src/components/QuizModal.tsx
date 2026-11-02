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
    SAMPLE_QUIZZES[topic] || SAMPLE_QUIZZES['Calculus Integrals'];

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-[#121a2b] border border-white/15 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-2 text-purple-400 text-xs font-mono font-semibold uppercase">
          <HelpCircle className="w-4 h-4" />
          <span>Interactive BKT Knowledge Check • Question {currentIndex + 1} of {questions.length}</span>
        </div>

        <h3 className="text-lg font-bold text-white mb-1">{topic}</h3>
        <p className="text-xs text-gray-400 mb-4 font-mono">
          Concept: <span className="text-cyan-400 font-semibold">{currentQ.concept}</span> • Current Mastery: {Math.round(currentMastery * 100)}%
        </p>

        {/* Question Text */}
        <div className="bg-black/40 border border-white/5 rounded-xl p-4 text-sm font-medium text-gray-200 mb-4">
          {currentQ.question}
        </div>

        {/* Options */}
        <div className="space-y-2 mb-5">
          {currentQ.options.map((opt, idx) => {
            let itemStyle = 'border-white/10 bg-black/20 hover:bg-white/5 text-gray-300';
            if (hasSubmitted) {
              if (idx === currentQ.correctIndex) {
                itemStyle = 'border-emerald-500 bg-emerald-500/20 text-emerald-200';
              } else if (idx === selectedOption) {
                itemStyle = 'border-red-500 bg-red-500/20 text-red-200';
              }
            } else if (selectedOption === idx) {
              itemStyle = 'border-cyan-500 bg-cyan-500/20 text-cyan-200';
            }

            return (
              <button
                key={idx}
                onClick={() => handleSelect(idx)}
                className={`w-full text-left p-3 rounded-xl border text-xs md:text-sm transition-all flex items-start gap-3 ${itemStyle}`}
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
            className={`p-3 rounded-xl mb-4 text-xs ${
              isCorrect
                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
                : 'bg-red-500/10 border border-red-500/30 text-red-300'
            }`}
          >
            <div className="font-bold flex items-center gap-1.5 mb-1">
              {isCorrect ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Correct! BKT mastery increased.
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4 text-red-400" />
                  Incorrect. BKT mastery adjusted.
                </>
              )}
            </div>
            <p className="text-gray-300">{currentQ.explanation}</p>
          </div>
        )}

        {/* Action button */}
        <div className="flex justify-end gap-2">
          {!hasSubmitted ? (
            <button
              onClick={handleSubmit}
              disabled={selectedOption === null}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-white shadow-lg transition-all"
            >
              Submit Answer
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-white/10 hover:bg-white/20 text-white flex items-center gap-1.5 transition-all"
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
