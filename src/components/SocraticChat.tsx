import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, StudyMaterialItem } from '../types';
import { Bot, CheckCircle, FileText, Globe, MessageSquare, Mic, Send, Sparkles, Upload } from 'lucide-react';

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

  // Browser Speech Recognition for voice interaction
  const toggleSpeechRecognition = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition is not supported in this browser window. Please type your reply.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputVal((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch (err) {
      setIsListening(false);
    }
  };

  return (
    <div className="bg-[#121a2b]/80 backdrop-blur-md border border-white/10 rounded-2xl p-5 shadow-xl flex flex-col h-[740px]">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
            Socratic Dialogue & Verifier Console
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
            Ollama / RAG Grounded
          </span>
          <button
            onClick={() => setShowMaterialOnboarding(!showMaterialOnboarding)}
            className="text-xs px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-cyan-300 border border-cyan-500/20 transition-colors flex items-center gap-1"
          >
            <Upload className="w-3 h-3" />
            <span>{showMaterialOnboarding ? 'Hide Materials' : 'Add Materials'}</span>
          </button>
        </div>
      </div>

      {/* Persistent Playful Accountability Nudge Button */}
      <div className="mb-2">
        <button
          onClick={onRequestNudge}
          className="text-xs font-semibold py-1.5 px-3 rounded-lg bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-purple-300 border border-purple-500/30 hover:bg-purple-500/30 transition-all flex items-center gap-1.5 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
          Ask robot for a study nudge
        </button>
      </div>

      {/* Material Ingestion Box (SRS §first-run study material onboarding) */}
      {showMaterialOnboarding && (
        <div className="p-3 mb-3 border border-cyan-500/30 bg-black/40 rounded-xl text-xs space-y-2">
          <div className="text-gray-300 font-medium flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            First time here? Add your study materials to build your personal concept graph:
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept=".pdf,.txt,.md,.csv,.png,.jpg,.jpeg,.webp"
              className="text-xs text-gray-400 file:mr-2 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-cyan-500/20 file:text-cyan-300 hover:file:bg-cyan-500/30"
            />
            <button
              onClick={() => {
                if (fileInputRef.current?.files) {
                  onAddFiles(fileInputRef.current.files);
                }
              }}
              className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition-colors"
            >
              Analyse files
            </button>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="https://... study page or syllabus notes"
              value={urlVal}
              onChange={(e) => setUrlVal(e.target.value)}
              className="flex-1 bg-black/50 border border-white/10 rounded px-2.5 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400"
            />
            <button
              onClick={handleAddUrl}
              className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white font-semibold flex items-center gap-1"
            >
              <Globe className="w-3 h-3" />
              Analyse link
            </button>
          </div>

          {onboardingStatus && (
            <div className="text-[11px] text-cyan-400 font-mono flex items-center gap-1 pt-1 border-t border-white/5">
              <CheckCircle className="w-3 h-3" />
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
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-md ${
                  isUser
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-br-none'
                    : 'bg-black/40 border border-white/10 text-gray-200 rounded-bl-none'
                }`}
              >
                {!isUser && (
                  <div className="flex items-center gap-2 mb-1.5 pb-1 border-b border-white/5 text-[11px] font-mono">
                    <span className="text-cyan-400 font-semibold flex items-center gap-1">
                      <Bot className="w-3 h-3" /> SmartEduSync
                    </span>
                    {m.grounded && (
                      <span className="text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20 text-[10px]">
                        ✓ Grounded in Syllabus
                      </span>
                    )}
                    {m.ssml_hint && (
                      <span className="text-purple-300 text-[10px]">
                        [{m.ssml_hint}]
                      </span>
                    )}
                  </div>
                )}
                <div className="whitespace-pre-wrap">{m.text}</div>
                <div className="text-[10px] text-gray-400 mt-1.5 text-right font-mono">
                  {m.timestamp}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested prompts */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 text-[11px] text-gray-400">
        <span className="text-gray-400 shrink-0">Quick prompts:</span>
        <button
          onClick={() => setInputVal(`Why do we use ${activeTopic} in real life?`)}
          className="shrink-0 px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-gray-300 border border-white/5"
        >
          Why {activeTopic}?
        </button>
        <button
          onClick={() => setInputVal(`Step me through a foundational problem in ${activeTopic}.`)}
          className="shrink-0 px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-gray-300 border border-white/5"
        >
          Step through problem
        </button>
        <button
          onClick={() => setInputVal(`What is the intuition behind the core formula?`)}
          className="shrink-0 px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-gray-300 border border-white/5"
        >
          Formula intuition
        </button>
      </div>

      {/* Input Row */}
      <div className="flex items-center gap-2 pt-2 border-t border-white/10">
        <button
          onClick={toggleSpeechRecognition}
          className={`p-2.5 rounded-xl border transition-colors ${
            isListening
              ? 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse'
              : 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10'
          }`}
          title="Dictate with microphone (STT)"
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
              : 'Ask a question (e.g. Why do we use integrals in physics?)'
          }
          className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
        />

        <button
          onClick={handleSend}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold shadow-lg shadow-blue-500/25 transition-all flex items-center gap-1.5"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
};
