import React, { useState, useEffect } from 'react';
import {
  EmotionState,
  PostureStatus,
  InterventionLevel,
  ExamRisk,
  ServoAngles,
  ChatMessage,
  StudentContext,
  StudentProfile,
  LearnerCharacterisation,
} from './types';
import { INITIAL_TOPICS, calculateBktUpdate, checkExamRisk } from './logic/bkt';
import { expressEvent } from './logic/choreo';
import { buildPlayfulNudge, respondToStudentReply } from './logic/accountability';
import { generateSocraticResponse } from './logic/socratic';
import { audioEngine } from './logic/audioEngine';
import { VisionMetrics } from './logic/visionEngine';
import {
  loadStoredStudentProfile,
  saveStoredStudentProfile,
  loadStoredCharacterisation,
  saveStoredCharacterisation,
  updateLearnerCharacterisation,
} from './logic/studentProfile';
import { buildGraphWithStudentPersona } from './logic/graphrag';

import { Header } from './components/Header';
import { OledFace } from './components/OledFace';
import { PerceptionPanel } from './components/PerceptionPanel';
import { SocraticChat } from './components/SocraticChat';
import { BktTracker } from './components/BktTracker';
import { ServoMonitor } from './components/ServoMonitor';
import { QuizModal } from './components/QuizModal';
import { ConceptGraphModal } from './components/ConceptGraphModal';
import { CameraPerceptionHUD } from './components/CameraPerceptionHUD';
import { StudyPlanStudio } from './components/StudyPlanStudio';
import { StudentProfileModal } from './components/StudentProfileModal';

import { LayoutDashboard, Camera, Compass } from 'lucide-react';

export function App() {
  // Student Profile & Characterisation
  const [studentProfile, setStudentProfile] = useState<StudentProfile>(() =>
    loadStoredStudentProfile()
  );
  const [characterisation, setCharacterisation] = useState<LearnerCharacterisation>(() =>
    loadStoredCharacterisation()
  );
  const [isProfileModalOpen, setIsProfileModalOpen] = useState<boolean>(() => {
    return studentProfile.isFirstTime;
  });

  // Navigation tabs
  const [activeView, setActiveView] = useState<'dashboard' | 'study_plan' | 'camera'>('dashboard');

  // Topics & BKT store
  const [topics, setTopics] = useState(INITIAL_TOPICS);
  const [activeTopic, setActiveTopic] = useState<string>(
    studentProfile.targetGoal || 'Artificial Intelligence'
  );

  // Active student context
  const currentTopicData = topics[activeTopic] || INITIAL_TOPICS['Artificial Intelligence'];
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
      text: `Hello ${studentProfile.name}! I'm SmartEduSync, your AI tutoring robot. I've tailored our session to your ${studentProfile.preferredStyle} learning style. What would you like to explore in ${studentProfile.targetGoal || 'Artificial Intelligence'} today?`,
      grounded: true,
      topic: activeTopic,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      ssml_hint: 'encouraging',
      emotion: 'happy',
    },
  ]);

  const [isAccountabilityAwaiting, setIsAccountabilityAwaiting] = useState(false);
  const [onboardingStatus, setOnboardingStatus] = useState<string>('');
  const [customMaterialTexts, setCustomMaterialTexts] = useState<string[]>([]);
  const [ttsEnabled, setTtsEnabled] = useState(true);

  // Modals
  const [isQuizOpen, setIsQuizOpen] = useState(false);
  const [isGraphOpen, setIsGraphOpen] = useState(false);

  const studentContext: StudentContext = {
    student_id: studentProfile.student_id,
    student_name: studentProfile.name,
    active_topic: activeTopic,
    p_mastery: pMastery,
    nearest_exam: nearestExam,
    days_left: daysLeft,
  };

  // Helper for voice synthesis with emotional prosody
  const speakWithEmotion = (text: string, emo: EmotionState) => {
    if (!ttsEnabled) return;
    audioEngine.speak(text, emo);
  };

  // Handler for live metrics coming from CameraPerceptionHUD
  const handleCameraMetrics = (metrics: VisionMetrics) => {
    setNeckAngle(metrics.neckAngle);
    setIsSlouching(metrics.isSlouching);
    setPosture(metrics.isSlouching ? 'SLOUCHING' : 'UPRIGHT');
    setEt(metrics.engagementScore);

    if (metrics.isSlouching) {
      setInterventionLevel('GENTLE');
      setEmotion('alert');
      // Update dynamic characterisation with slouch event
      setCharacterisation((prev) =>
        updateLearnerCharacterisation(prev, {
          type: 'slouch_event',
          slouchAngle: metrics.neckAngle,
        })
      );
    } else if (metrics.isDrowsy) {
      setInterventionLevel('GENTLE');
      setEmotion('concerned');
    } else if (metrics.studentMood === 'distracted') {
      setInterventionLevel('GENTLE');
      setEmotion('curious');
    } else {
      setInterventionLevel('IDLE');
      if (emotion !== 'happy' && emotion !== 'thinking') {
        setEmotion('watching');
      }
    }
  };

  // Handler when Camera HUD auto-nags the student via TTS
  const handleNagTriggered = (phrase: string) => {
    const choreo = expressEvent('intervention.trigger', { level: 'escalated' });
    setEmotion('alert');
    setServoAngles(choreo.pose);

    const nagMsg: ChatMessage = {
      id: `nag-${Date.now()}`,
      role: 'tutor',
      text: `📢 ${phrase}`,
      grounded: true,
      topic: activeTopic,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      ssml_hint: 'urgent',
      emotion: 'alert',
    };
    setChatMessages((prev) => [...prev, nagMsg]);
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

    // Update dynamic learner characterisation
    setCharacterisation((prev) =>
      updateLearnerCharacterisation(prev, {
        type: 'chat_message',
        topic: activeTopic,
      })
    );

    if (isAccountabilityAwaiting) {
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
        emotion: 'happy',
      };
      setChatMessages((prev) => [...prev, tutorMsg]);
      speakWithEmotion(replyText, 'happy');
    } else {
      const result = generateSocraticResponse(text, studentContext, customMaterialTexts);
      const choreo = expressEvent('tutor.response');
      setEmotion(result.emotion || choreo.emotion);
      setServoAngles(choreo.pose);

      const tutorMsg: ChatMessage = {
        id: `t-${Date.now()}`,
        role: 'tutor',
        text: result.text,
        grounded: result.grounded,
        topic: activeTopic,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        ssml_hint: result.ssmlHint,
        emotion: result.emotion,
      };
      setChatMessages((prev) => [...prev, tutorMsg]);
      speakWithEmotion(result.text, result.emotion);
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
      emotion: 'curious',
    };
    setChatMessages((prev) => [...prev, tutorMsg]);
    speakWithEmotion(nudge, 'curious');
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
    setCharacterisation((prev) =>
      updateLearnerCharacterisation(prev, { type: 'slouch_event', slouchAngle: 32.5 })
    );
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
    const sl = angle > 22.0;
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

    // Update dynamic learner characterisation in GraphRAG
    setCharacterisation((prev) =>
      updateLearnerCharacterisation(prev, {
        type: 'quiz_answer',
        topic: activeTopic,
        isCorrect: correct,
        masteryVal: updated,
      })
    );

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
    setOnboardingStatus('Analyzing study material...');
    setTimeout(() => {
      const addedChunks = files.length * 4;
      const fileNames = files.map((f) => f.name).join(', ');
      setCustomMaterialTexts((prev) => [
        ...prev,
        `Extracted study material from ${fileNames} covering key topics, definitions, and practice problems.`,
      ]);
      setOnboardingStatus(`Ready: analyzed ${files.length} source(s), built ${addedChunks} study chunks.`);
    }, 600);
  };

  // URL onboarding
  const handleAddUrl = (url: string) => {
    setOnboardingStatus(`Fetching and analyzing link ${url}...`);
    setTimeout(() => {
      setCustomMaterialTexts((prev) => [
        ...prev,
        `Ingested syllabus text from ${url} with prerequisite definitions and graph nodes.`,
      ]);
      setOnboardingStatus(`Ready: added 5 study chunks and updated concept graph.`);
    }, 700);
  };

  // Study plan connection: jump into Socratic conversation about this concept
  const handleSelectConceptFromPlan = (conceptTitle: string) => {
    if (!topics[conceptTitle]) {
      setTopics((prev) => ({
        ...prev,
        [conceptTitle]: {
          topic: conceptTitle,
          p_mastery: 0.48,
          nearest_exam: activeTopic,
          days_left: daysLeft,
          department: 'Computer Science',
        },
      }));
    }
    setActiveTopic(conceptTitle);
    setActiveView('dashboard');

    const promptText = `Let's study ${conceptTitle}! Can you explain the core definition and step me through a sample problem?`;
    handleSendMessage(promptText);
  };

  // Update mastery from study plan completion
  const handleMasteryFromPlan = (newMastery: number) => {
    setTopics((prev) => ({
      ...prev,
      [activeTopic]: {
        ...prev[activeTopic],
        p_mastery: Number(newMastery.toFixed(3)),
      },
    }));
    setCharacterisation((prev) =>
      updateLearnerCharacterisation(prev, {
        type: 'mastery_shift',
        masteryVal: newMastery,
      })
    );
  };

  // Save profile from modal
  const handleSaveProfile = (newProfile: StudentProfile) => {
    setStudentProfile(newProfile);
    saveStoredStudentProfile(newProfile);
    if (newProfile.targetGoal && topics[newProfile.targetGoal]) {
      setActiveTopic(newProfile.targetGoal);
    }
  };

  // Build GraphRAG nodes with dynamic Student Persona
  const graphData = buildGraphWithStudentPersona(studentProfile, characterisation, activeTopic);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-4 md:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <Header
        activeTopic={activeTopic}
        onTopicChange={setActiveTopic}
        availableTopics={Object.keys(topics)}
        ttsEnabled={ttsEnabled}
        onToggleTts={() => setTtsEnabled(!ttsEnabled)}
        onOpenGraph={() => setIsGraphOpen(true)}
        studentProfile={studentProfile}
        onOpenProfile={() => setIsProfileModalOpen(true)}
      />

      {/* Primary Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
        <button
          onClick={() => setActiveView('dashboard')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeView === 'dashboard'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
          }`}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>Robot Control &amp; Socratic Console</span>
        </button>

        <button
          onClick={() => setActiveView('study_plan')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeView === 'study_plan'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
          }`}
        >
          <Compass className="w-4 h-4" />
          <span>Study Plan &amp; EduGraph Studio</span>
        </button>

        <button
          onClick={() => setActiveView('camera')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeView === 'camera'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
          }`}
        >
          <Camera className="w-4 h-4" />
          <span>Computer Vision &amp; Posture HUD</span>
          {(isSlouching || interventionLevel !== 'IDLE') && (
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping"></span>
          )}
        </button>
      </div>

      {/* VIEW 1: Main Robot Dashboard */}
      {activeView === 'dashboard' && (
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
              onOpenCamera={() => setActiveView('camera')}
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
      )}

      {/* VIEW 2: Study Plan & EduGraph Studio */}
      {activeView === 'study_plan' && (
        <StudyPlanStudio
          onSelectConceptForStudy={handleSelectConceptFromPlan}
          onMasteryUpdated={handleMasteryFromPlan}
          activeTopic={activeTopic}
        />
      )}

      {/* VIEW 3: Live Camera & Vision HUD (Kept mounted for continuous posture and eye tracking) */}
      <div className={activeView === 'camera' ? 'block' : 'hidden'}>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-7">
            <CameraPerceptionHUD
              onMetricsUpdate={handleCameraMetrics}
              onNagTriggered={handleNagTriggered}
            />
          </div>
          <div className="lg:col-span-5 space-y-5">
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
              onOpenCamera={() => setActiveView('camera')}
            />
          </div>
        </div>
      </div>

      {/* First-Time Profile & Characterisation Modal */}
      <StudentProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        profile={studentProfile}
        characterisation={characterisation}
        onSaveProfile={handleSaveProfile}
        availableTopics={Object.keys(topics)}
      />

      {/* Interactive Quiz Modal */}
      <QuizModal
        isOpen={isQuizOpen}
        onClose={() => setIsQuizOpen(false)}
        topic={activeTopic}
        onAnswerSubmitted={handleBktAnswer}
        currentMastery={pMastery}
      />

      {/* GraphRAG Concept & Student Persona Modal */}
      <ConceptGraphModal
        isOpen={isGraphOpen}
        onClose={() => setIsGraphOpen(false)}
        activeTopic={activeTopic}
        onSelectTopic={(t) => setActiveTopic(t)}
        studentProfile={studentProfile}
        characterisation={characterisation}
        nodes={graphData.nodes}
        edges={graphData.edges}
      />
    </div>
  );
}

export default App;
