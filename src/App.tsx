import React, { useState, useEffect } from 'react';
import {
  EmotionState,
  PostureStatus,
  InterventionLevel,
  ExamRisk,
  ServoAngles,
  ChatMessage,
  StudentContext,
} from './types';
import { INITIAL_TOPICS, calculateBktUpdate, checkExamRisk } from './logic/bkt';
import { expressEvent } from './logic/choreo';
import { buildPlayfulNudge, respondToStudentReply } from './logic/accountability';
import { generateSocraticResponse } from './logic/socratic';
import { Header } from './components/Header';
import { OledFace } from './components/OledFace';
import { PerceptionPanel } from './components/PerceptionPanel';
import { SocraticChat } from './components/SocraticChat';
import { BktTracker } from './components/BktTracker';
import { ServoMonitor } from './components/ServoMonitor';
import { QuizModal } from './components/QuizModal';
import { ConceptGraphModal } from './components/ConceptGraphModal';

export function App() {
  // Topics & BKT store
  const [topics, setTopics] = useState(INITIAL_TOPICS);
  const [activeTopic, setActiveTopic] = useState<string>('Calculus Integrals');

  // Active student context
  const currentTopicData = topics[activeTopic] || INITIAL_TOPICS['Calculus Integrals'];
  const pMastery = currentTopicData.p_mastery;
  const daysLeft = currentTopicData.days_left;
  const nearestExam = currentTopicData.nearest_exam;
  const examRisk: ExamRisk = checkExamRisk(activeTopic, daysLeft, pMastery);

  // Perception telemetry
  const [et, setEt] = useState<number>(0.85);
  const [emotion, setEmotion] = useState<EmotionState>('watching');
  const [posture, setPosture] = useState<PostureStatus>('UPRIGHT');
  const [neckAngle, setNeckAngle] = useState<number>(8.5);
  const [isSlouching, setIsSlouching] = useState<boolean>(false);
  const [interventionLevel, setInterventionLevel] = useState<InterventionLevel>('IDLE');

  // PCA9685 Servos
  const [servoAngles, setServoAngles] = useState<ServoAngles>({
    0: 0.0,
    1: 0.0,
    2: 0.0,
    3: 0.0,
  });

  // Chat & Accountability
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'init-1',
      role: 'tutor',
      text: "Hello! I'm SmartEduSync, your tabletop AI tutoring robot. Let's work on Calculus Integrals today. Ask me any question, explore a derivation, or step through a problem.",
      grounded: true,
      topic: 'Calculus Integrals',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      ssml_hint: 'encouraging',
    },
  ]);

  const [isAccountabilityAwaiting, setIsAccountabilityAwaiting] = useState(false);
  const [onboardingStatus, setOnboardingStatus] = useState<string>('');
  const [customMaterialTexts, setCustomMaterialTexts] = useState<string[]>([]);
  const [ttsEnabled, setTtsEnabled] = useState(false);

  // Modals
  const [isQuizOpen, setIsQuizOpen] = useState(false);
  const [isGraphOpen, setIsGraphOpen] = useState(false);

  const studentContext: StudentContext = {
    student_id: 'student_1',
    active_topic: activeTopic,
    p_mastery: pMastery,
    nearest_exam: nearestExam,
    days_left: daysLeft,
  };

  // Helper for voice synthesis
  const speakText = (text: string) => {
    if (!ttsEnabled || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.05;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('TTS error', e);
    }
  };

  // Chat sender
  const handleSendMessage = (text: string) => {
    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setChatMessages((prev) => [...prev, userMsg]);

    if (isAccountabilityAwaiting) {
      // Process accountability answer
      const replyText = respondToStudentReply(text, studentContext);
      setIsAccountabilityAwaiting(false);

      const choreo = expressEvent('tutor.response');
      setEmotion('happy');
      setServoAngles(choreo.pose);

      const tutorMsg: ChatMessage = {
        id: `t-${Date.now()}`,
        role: 'tutor',
        text: replyText,
        grounded: true,
        topic: activeTopic,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        ssml_hint: 'warm',
      };
      setChatMessages((prev) => [...prev, tutorMsg]);
      speakText(replyText);
    } else {
      // Socratic LLM response
      const result = generateSocraticResponse(text, studentContext, customMaterialTexts);
      const choreo = expressEvent('tutor.response');
      setEmotion(choreo.emotion);
      setServoAngles(choreo.pose);

      const tutorMsg: ChatMessage = {
        id: `t-${Date.now()}`,
        role: 'tutor',
        text: result.text,
        grounded: result.grounded,
        topic: activeTopic,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        ssml_hint: result.ssmlHint,
      };
      setChatMessages((prev) => [...prev, tutorMsg]);
      speakText(result.text);
    }
  };

  // Accountability nudge trigger
  const handleRequestNudge = () => {
    const nudge = buildPlayfulNudge(studentContext);
    setIsAccountabilityAwaiting(true);

    const choreo = expressEvent('intervention.trigger', { level: 'gentle' });
    setEmotion('curious');
    setServoAngles(choreo.pose);

    const tutorMsg: ChatMessage = {
      id: `t-${Date.now()}`,
      role: 'tutor',
      text: nudge,
      grounded: true,
      topic: activeTopic,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      ssml_hint: 'curious',
    };
    setChatMessages((prev) => [...prev, tutorMsg]);
    speakText(nudge);
  };

  // Engagement simulation
  const handleSimulateEngagementDip = () => {
    setEt(0.20);
    setEmotion('alert');
    setInterventionLevel('GENTLE');
    const choreo = expressEvent('intervention.trigger', { level: 'gentle' });
    setServoAngles(choreo.pose);
  };

  const handleSimulateSlouch = () => {
    setNeckAngle(32.5);
    setIsSlouching(true);
    setPosture('SLOUCHING');
    setEmotion('concerned');
    const choreo = expressEvent('intervention.trigger', { level: 'firm' });
    setServoAngles(choreo.pose);
  };

  const handleSimulateFocused = () => {
    setEt(0.85);
    setNeckAngle(8.5);
    setIsSlouching(false);
    setPosture('UPRIGHT');
    setEmotion('watching');
    setInterventionLevel('IDLE');
    setServoAngles({ 0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0 });
  };

  const handleEtChange = (val: number) => {
    setEt(val);
    if (val < 0.25) {
      setInterventionLevel('MODERATE');
      setEmotion('alert');
    } else if (val < 0.40) {
      setInterventionLevel('GENTLE');
      setEmotion('concerned');
    } else {
      setInterventionLevel('IDLE');
      setEmotion('watching');
    }
  };

  const handleNeckAngleChange = (angle: number) => {
    setNeckAngle(angle);
    const sl = angle > 25.0;
    setIsSlouching(sl);
    setPosture(sl ? 'SLOUCHING' : 'UPRIGHT');
    if (sl) setEmotion('concerned');
  };

  // BKT mastery update
  const handleBktAnswer = (correct: boolean) => {
    const updated = calculateBktUpdate(pMastery, correct);
    setTopics((prev) => ({
      ...prev,
      [activeTopic]: {
        ...prev[activeTopic],
        p_mastery: updated,
      },
    }));

    if (correct) {
      setEmotion('happy');
      setServoAngles({ 0: 0.0, 1: 10.0, 2: 25.0, 3: 25.0 });
    } else {
      setEmotion('concerned');
      setServoAngles({ 0: -10.0, 1: -5.0, 2: 0.0, 3: 0.0 });
    }
  };

  // Choreography presets
  const handleRunChoreography = (name: string) => {
    switch (name) {
      case 'nod':
        setEmotion('happy');
        setServoAngles({ 0: 0.0, 1: 25.0, 2: 10.0, 3: 10.0 });
        setTimeout(() => setServoAngles({ 0: 0.0, 1: -10.0, 2: 5.0, 3: 5.0 }), 400);
        setTimeout(() => setServoAngles({ 0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0 }), 800);
        break;
      case 'shake':
        setEmotion('concerned');
        setServoAngles({ 0: -30.0, 1: 0.0, 2: 0.0, 3: 0.0 });
        setTimeout(() => setServoAngles({ 0: 30.0, 1: 0.0, 2: 0.0, 3: 0.0 }), 400);
        setTimeout(() => setServoAngles({ 0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0 }), 800);
        break;
      case 'wave':
        setEmotion('happy');
        setServoAngles({ 0: 0.0, 1: 10.0, 2: 70.0, 3: 70.0 });
        setTimeout(() => setServoAngles({ 0: 0.0, 1: 10.0, 2: 30.0, 3: 90.0 }), 400);
        setTimeout(() => setServoAngles({ 0: 0.0, 1: 0.0, 2: 10.0, 3: 10.0 }), 900);
        break;
      case 'alert':
        setEmotion('alert');
        setServoAngles({ 0: 0.0, 1: 20.0, 2: 45.0, 3: 45.0 });
        break;
      case 'curious':
        setEmotion('curious');
        setServoAngles({ 0: 20.0, 1: 10.0, 2: 0.0, 3: 0.0 });
        break;
      case 'neutral':
      default:
        setEmotion('watching');
        setServoAngles({ 0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0 });
        break;
    }
  };

  // File onboarding
  const handleAddFiles = (fileList: FileList) => {
    const files = Array.from(fileList);
    if (!files.length) return;
    setOnboardingStatus('Analysing study material...');
    setTimeout(() => {
      const addedChunks = files.length * 4;
      const fileNames = files.map((f) => f.name).join(', ');
      setCustomMaterialTexts((prev) => [
        ...prev,
        `Extracted study material from ${fileNames} covering key topics, definitions, and practice problems.`,
      ]);
      setOnboardingStatus(`Ready: analysed ${files.length} source(s), built ${addedChunks} study chunks.`);
    }, 600);
  };

  // URL onboarding
  const handleAddUrl = (url: string) => {
    setOnboardingStatus(`Fetching and analysing link ${url}...`);
    setTimeout(() => {
      setCustomMaterialTexts((prev) => [
        ...prev,
        `Ingested syllabus text from ${url} with prerequisite definitions and graph nodes.`,
      ]);
      setOnboardingStatus(`Ready: added 5 study chunks and updated concept graph.`);
    }, 700);
  };

  return (
    <div className="min-h-screen text-gray-100 p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <Header
        activeTopic={activeTopic}
        onTopicChange={setActiveTopic}
        availableTopics={Object.keys(topics)}
        ttsEnabled={ttsEnabled}
        onToggleTts={() => setTtsEnabled(!ttsEnabled)}
        onOpenGraph={() => setIsGraphOpen(true)}
      />

      {/* 3-Column Glassmorphism Grid matching web_dashboard.py */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: OLED Face & Perception Telemetry */}
        <div className="lg:col-span-3 space-y-5">
          <OledFace
            emotion={emotion}
            onSimulateEngagementDip={handleSimulateEngagementDip}
            onSimulateSlouch={handleSimulateSlouch}
            onSimulateFocused={handleSimulateFocused}
            onSetEmotion={setEmotion}
          />

          <PerceptionPanel
            et={et}
            posture={posture}
            neckAngle={neckAngle}
            isSlouching={isSlouching}
            interventionLevel={interventionLevel}
            onEtChange={handleEtChange}
            onNeckAngleChange={handleNeckAngleChange}
          />
        </div>

        {/* Center Column: Socratic Dialogue Console */}
        <div className="lg:col-span-6">
          <SocraticChat
            messages={chatMessages}
            onSendMessage={handleSendMessage}
            onRequestNudge={handleRequestNudge}
            onAddFiles={handleAddFiles}
            onAddUrl={handleAddUrl}
            onboardingStatus={onboardingStatus}
            isAccountabilityAwaiting={isAccountabilityAwaiting}
            activeTopic={activeTopic}
          />
        </div>

        {/* Right Column: BKT Mastery & PCA9685 Servos */}
        <div className="lg:col-span-3 space-y-5">
          <BktTracker
            topic={activeTopic}
            pMastery={pMastery}
            nearestExam={nearestExam}
            daysLeft={daysLeft}
            examRisk={examRisk}
            onOpenQuiz={() => setIsQuizOpen(true)}
            onSimulateAnswer={handleBktAnswer}
          />

          <ServoMonitor
            servoAngles={servoAngles}
            onSetAngle={(ch, angle) =>
              setServoAngles((prev) => ({ ...prev, [ch]: angle }))
            }
            onRunChoreography={handleRunChoreography}
          />
        </div>
      </div>

      {/* Modals */}
      <QuizModal
        isOpen={isQuizOpen}
        onClose={() => setIsQuizOpen(false)}
        topic={activeTopic}
        onAnswerSubmitted={handleBktAnswer}
        currentMastery={pMastery}
      />

      <ConceptGraphModal
        isOpen={isGraphOpen}
        onClose={() => setIsGraphOpen(false)}
        activeTopic={activeTopic}
        onSelectTopic={(t) => setActiveTopic(t)}
      />
    </div>
  );
}

export default App;
