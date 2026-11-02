export type EmotionState =
  | 'idle'
  | 'watching'
  | 'listening'
  | 'thinking'
  | 'curious'
  | 'happy'
  | 'concerned'
  | 'alert';

export type PostureStatus = 'UPRIGHT' | 'SLOUCHING';

export type InterventionLevel = 'IDLE' | 'GENTLE' | 'MODERATE' | 'HIGH';

export type ExamRisk = 'low' | 'medium' | 'high';

export type LearningStyle = 'Intuitive & Analogy' | 'Mathematical & Rigorous' | 'Applied & Hands-on';

export interface StudentProfile {
  student_id: string;
  name: string;
  major: string;
  year: string;
  preferredStyle: LearningStyle;
  targetGoal: string;
  isFirstTime: boolean;
  createdAt: string;
}

export interface LearnerCharacterisation {
  cognitivePace: 'deliberate' | 'balanced' | 'fast-paced';
  conceptualStrength: string[];
  growthAreas: string[];
  postureFatigueIndex: number; // 0 to 100
  focusResilience: number; // 0 to 100
  preferredTone: 'encouraging' | 'analytical' | 'direct';
  sessionsCount: number;
  totalQuestionsAnswered: number;
  averageMastery: number;
  graphRAGSummary: string;
  personalityTags: string[];
}

export interface StudentContext {
  student_id: string;
  student_name?: string;
  active_topic: string;
  p_mastery: number;
  nearest_exam: string;
  days_left: number;
}

export interface ServoAngles {
  0: number; // Head Pan (-90° to +90°)
  1: number; // Head Tilt (-30° to +45°)
  2: number; // Left Arm (0° to 120°)
  3: number; // Right Arm (0° to 120°)
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'tutor' | 'robot';
  text: string;
  grounded?: boolean;
  topic?: string;
  timestamp: string;
  ssml_hint?: string;
  emotion?: EmotionState;
}

export interface StudyMaterialItem {
  id: string;
  title: string;
  sourceType: 'file' | 'url' | 'manual';
  chunksCount: number;
  addedAt: string;
  summary: string;
}

export interface ConceptNode {
  id: string;
  name: string;
  category: string;
  mastery: number;
  connections: string[];
  isStudentPersona?: boolean;
}

export interface ConceptEdge {
  from: string;
  to: string;
  relation: string;
  weight?: number;
}

export interface QuizItem {
  id: string;
  topic: string;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  concept: string;
}

export interface TelemetryState {
  student_id: string;
  E_t: number;
  emotion: EmotionState;
  posture: PostureStatus;
  neckAngle: number;
  isSlouching: boolean;
  interventionLevel: InterventionLevel;
  active_topic: string;
  p_mastery: number;
  days_left: number;
  nearest_exam: string;
  exam_risk: ExamRisk;
  servo_angles: ServoAngles;
}
