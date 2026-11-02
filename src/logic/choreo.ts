import { EmotionState, ServoAngles } from '../types';
import { getFaceArt } from './faceBitmaps';

export interface ChoreographyResult {
  emotion: EmotionState;
  faceArt: string;
  pose: ServoAngles;
  tone: 'neutral' | 'soft' | 'urgent' | 'warm';
}

export function expressEvent(
  eventType: string,
  data: { level?: string; emotion?: string } = {}
): ChoreographyResult {
  const eventLower = eventType.toLowerCase();
  const level = data.level || 'gentle';
  const emotion = (data.emotion || 'watching') as EmotionState;

  let emo: EmotionState = 'watching';
  let pose: ServoAngles = { 0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0 };
  let tone: 'neutral' | 'soft' | 'urgent' | 'warm' = 'neutral';

  if (eventLower.includes('intervention')) {
    if (level === 'escalated') {
      emo = 'alert';
      pose = { 0: 0.0, 1: 15.0, 2: 45.0, 3: 45.0 }; // Head tilt up, hands raised
      tone = 'urgent';
    } else if (level === 'firm') {
      emo = 'concerned';
      pose = { 0: -15.0, 1: -10.0, 2: 20.0, 3: 20.0 }; // Head tilt side
      tone = 'soft';
    } else {
      emo = 'curious';
      pose = { 0: 15.0, 1: 5.0, 2: 0.0, 3: 0.0 };
      tone = 'soft';
    }
  } else if (eventLower.includes('tutor') || eventLower.includes('success')) {
    emo = 'happy';
    pose = { 0: 0.0, 1: 0.0, 2: 10.0, 3: 10.0 };
    tone = 'warm';
  } else if (eventLower.includes('exam')) {
    emo = 'alert';
    pose = { 0: 0.0, 1: 20.0, 2: 30.0, 3: 30.0 };
    tone = 'urgent';
  } else if (eventLower.includes('thinking')) {
    emo = 'thinking';
    pose = { 0: 10.0, 1: -10.0, 2: 0.0, 3: 0.0 };
    tone = 'neutral';
  } else if (eventLower.includes('listening')) {
    emo = 'listening';
    pose = { 0: 0.0, 1: 5.0, 2: 5.0, 3: 5.0 };
    tone = 'neutral';
  } else {
    emo = ['watching', 'listening', 'thinking'].includes(emotion) ? emotion : 'watching';
    pose = { 0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0 };
    tone = 'neutral';
  }

  const faceArt = getFaceArt(emo);
  return { emotion: emo, faceArt, pose, tone };
}
