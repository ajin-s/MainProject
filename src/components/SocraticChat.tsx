import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, StudyMaterialItem } from '../types';
import { audioEngine } from '../logic/audioEngine';
import {
  Bot,
  CheckCircle,
  FileText,
  Globe,
  MessageSquare,
  Mic,
  Send,
  Sparkles,
  Upload,
  Volume2,
} from 'lucide-react';

interface SocraticChatProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  onRequestNudge: () => void;
  onAddFiles: (files: FileList) => void;
  onAddUrl: (url: string) => void;
  onboardingStatus: string;
  isAccountabilityAwaiting: boolean;
  activeTopic: string;
}

export const SocraticChat: React.FC<SocraticChatProps> = ({
  messages,
  onSendMessage,
  onRequestNudge,
  onAddFiles,
  onAddUrl,
  onboardingStatus,
  isAccountabilityAwaiting,
  activeTopic,
}) => {
  const [inputVal, setInputVal] = useState('');
  const [urlVal, setUrlVal] = useState('');
  const [showMaterialOnboarding, setShowMaterialOnboarding] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!inputVal.trim()) return;
    onSendMessage(inputVal.trim());
    setInputVal('');
  };

  const handleAddUrl = () => {
    if (!urlVal.trim()) return;
    onAddUrl(urlVal.trim());
    setUrlVal('');
  };

  // Working Speech Recognition for voice interaction
  const toggleSpeechRecognition = () => {
    if (isListening) {
      audioEngine.stopListening();
      setIsListening(false);
      return;
    }

    if (!audioEngine.isSpeechRecognitionAvailable()) {
      alert('Speech Recognition is not available in this browser. Please type your reply.');
      return;
    }

    audioEngine.startListening(
      (transcript) => {
        setInputVal((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      },
      (listening) => {
        setIsListening(listening);
      },
      (error) => {
        setIsListening(false);
        console.warn('Speech recognition error:', error);
      }
    );
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex flex-col h-[740px]">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-indigo-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Socratic Dialogue &amp; Verifier Console
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            RAG Grounded
          </span>
          <button
            onClick={() => setShowMaterialOnboarding(!showMaterialOnboarding)}
            className="text-xs px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors flex items-center gap-1 shadow-sm"
          >
            <Upload className="w-3 h-3 text-indigo-600" />
            <span>{showMaterialOnboarding ? 'Hide Ingestion' : 'Add Materials'}</span>
          </button>
        </div>
      </div>

      {/* Persistent Playful Accountability Nudge Button */}
      <div className="mb-2">
        <button
          onClick={onRequestNudge}
          className="text-xs font-semibold py-1.5 px-3 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 transition-all flex items-center gap-1.5 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          Ask robot for a study nudge
        </button>
      </div>

      {/* Material Ingestion Box */}
      {showMaterialOnboarding && (
        <div className="p-3.5 mb-3 border border-slate-200 bg-slate-50/70 rounded-xl text-xs space-y-2.5">
          <div className="text-slate-700 font-medium flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-indigo-600" />
            Add lecture notes, PDF, or syllabus text to construct your EduGraph:
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept=".pdf,.txt,.md,.csv"
              className="text-xs text-slate-500 file:mr-2 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-200 file:text-slate-800 hover:file:bg-slate-300"
            />
            <button
              onClick={() => {
                if (fileInputRef.current?.files) {
                  onAddFiles(fileInputRef.current.files);
                }
              }}
              className="px-3 py-1 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-colors shadow-sm"
            >
              Analyze files
            </button>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="https://... study page or syllabus notes"
              value={urlVal}
              onChange={(e) => setUrlVal(e.target.value)}
              className="flex-1 bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={handleAddUrl}
              className="px-3 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold flex items-center gap-1"
            >
              <Globe className="w-3 h-3" />
              Analyze link
            </button>
          </div>

          {onboardingStatus && (
            <div className="text-[11px] text-emerald-700 font-mono flex items-center gap-1 pt-1 border-t border-slate-200">
              <CheckCircle className="w-3 h-3 text-emerald-600" />
              <span>{onboardingStatus}</span>
            </div>
          )}
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-3">
        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={m.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                  isUser
                    ? 'bg-indigo-600 text-white rounded-br-none'
                    : 'bg-slate-50 border border-slate-200/80 text-slate-800 rounded-bl-none'
                }`}
              >
                {!isUser && (
                  <div className="flex items-center gap-2 mb-1.5 pb-1 border-b border-slate-200 text-[11px] font-mono">
                    <span className="text-indigo-600 font-bold flex items-center gap-1">
                      <Bot className="w-3.5 h-3.5" /> SmartEduSync
                    </span>
                    {m.emotion && (
                      <span className="text-[10px] uppercase px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold">
                        [{m.emotion}]
                      </span>
                    )}
                    {m.grounded && (
                      <span className="text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200 text-[10px]">
                        ✓ Syllabus Grounded
                      </span>
                    )}
                  </div>
                )}
                <div className="whitespace-pre-wrap">{m.text}</div>
                <div
                  className={`text-[10px] mt-1.5 text-right font-mono ${
                    isUser ? 'text-indigo-200' : 'text-slate-400'
                  }`}
                >
                  {m.timestamp}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested prompts */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 text-[11px] text-slate-500">
        <span className="text-slate-400 shrink-0 font-medium">Quick prompts:</span>
        <button
          onClick={() => setInputVal(`Explain the core intuition behind ${activeTopic}.`)}
          className="shrink-0 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
        >
          {activeTopic} Intuition
        </button>
        <button
          onClick={() => setInputVal(`Step me through a foundational problem in ${activeTopic}.`)}
          className="shrink-0 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
        >
          Step through problem
        </button>
        <button
          onClick={() => setInputVal(`Give me a practice verification question.`)}
          className="shrink-0 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
        >
          Practice question
        </button>
      </div>

      {/* Input Row */}
      <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
        <button
          onClick={toggleSpeechRecognition}
          className={`p-2.5 rounded-xl border transition-colors shadow-sm ${
            isListening
              ? 'bg-rose-50 text-rose-600 border-rose-300 animate-pulse'
              : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
          }`}
          title="Dictate with microphone (STT Speech to Text)"
        >
          <Mic className="w-4 h-4" />
        </button>

        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSend();
          }}
          placeholder={
            isAccountabilityAwaiting
              ? 'Reply to the robot—typed or speech-transcribed...'
              : `Ask about ${activeTopic} (e.g. How does A* guarantee optimality?)`
          }
          className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-inner"
        />

        <button
          onClick={handleSend}
          className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-sm transition-all flex items-center gap-1.5"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
};
