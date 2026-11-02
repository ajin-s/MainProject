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

export interface StudentContext {
  student_id: string;
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
  neck_angle: number;
  is_slouching: boolean;
  intervention_level: InterventionLevel;
  active_topic: string;
  p_mastery: number;
  days_left: number;
  nearest_exam: string;
  exam_risk: ExamRisk;
  servo_angles: ServoAngles;
}
