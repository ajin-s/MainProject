import { StudentProfile, LearnerCharacterisation } from '../types';

const PROFILE_STORAGE_KEY = 'smartedusync_student_profile';
const CHARACTERISATION_STORAGE_KEY = 'smartedusync_learner_characterisation';

export const DEFAULT_STUDENT_PROFILE: StudentProfile = {
  student_id: 'student_1',
  name: 'Alex Chen',
  major: 'Computer Science & AI',
  year: 'Year 4 (Senior)',
  preferredStyle: 'Intuitive & Analogy',
  targetGoal: 'Artificial Intelligence',
  isFirstTime: true,
  createdAt: new Date().toISOString(),
};

export const DEFAULT_CHARACTERISATION: LearnerCharacterisation = {
  cognitivePace: 'balanced',
  conceptualStrength: ['Supervised Learning', 'Matrix Multiplication'],
  growthAreas: ['Backpropagation & Neural Networks', 'Calculus Integrals'],
  postureFatigueIndex: 35, // low/moderate fatigue
  focusResilience: 82, // good focus endurance
  preferredTone: 'encouraging',
  sessionsCount: 3,
  totalQuestionsAnswered: 8,
  averageMastery: 0.54,
  graphRAGSummary:
    'Alex exhibits high conceptual retention when taught through intuitive real-world analogies. Demonstrates solid grounding in Supervised Learning and Linear Algebra, but requires step-by-step scaffolding on Backpropagation gradient chain rules. Posture monitoring shows slight afternoon slouch tendencies when tackling high-difficulty proofs.',
  personalityTags: [
    'Intuitive Thinker',
    'Goal-Oriented',
    'AI & ML Track',
    'Responds well to Playful Nudges',
  ],
};

export function loadStoredStudentProfile(): StudentProfile {
  if (typeof window === 'undefined') return DEFAULT_STUDENT_PROFILE;
  try {
    const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.warn('Could not read stored profile:', e);
  }
  return DEFAULT_STUDENT_PROFILE;
}

export function saveStoredStudentProfile(profile: StudentProfile) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
  } catch (e) {
    console.warn('Could not save profile:', e);
  }
}

export function loadStoredCharacterisation(): LearnerCharacterisation {
  if (typeof window === 'undefined') return DEFAULT_CHARACTERISATION;
  try {
    const raw = localStorage.getItem(CHARACTERISATION_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.warn('Could not read characterisation:', e);
  }
  return DEFAULT_CHARACTERISATION;
}

export function saveStoredCharacterisation(char: LearnerCharacterisation) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(CHARACTERISATION_STORAGE_KEY, JSON.stringify(char));
  } catch (e) {
    console.warn('Could not save characterisation:', e);
  }
}

/**
 * Dynamically updates the learner characterisation in GraphRAG
 * as interactions occur (quiz answers, slouching events, chat queries, mastery shifts).
 */
export function updateLearnerCharacterisation(
  current: LearnerCharacterisation,
  action: {
    type: 'quiz_answer' | 'slouch_event' | 'chat_message' | 'mastery_shift';
    topic?: string;
    isCorrect?: boolean;
    slouchAngle?: number;
    masteryVal?: number;
  }
): LearnerCharacterisation {
  const updated = { ...current };

  if (action.type === 'quiz_answer') {
    updated.totalQuestionsAnswered += 1;
    if (action.topic) {
      if (action.isCorrect) {
        if (!updated.conceptualStrength.includes(action.topic)) {
          updated.conceptualStrength = [...updated.conceptualStrength.slice(-3), action.topic];
        }
        updated.growthAreas = updated.growthAreas.filter((g) => g !== action.topic);
      } else {
        if (!updated.growthAreas.includes(action.topic)) {
          updated.growthAreas = [...updated.growthAreas.slice(-3), action.topic];
        }
      }
    }
  }

  if (action.type === 'slouch_event') {
    // Increase fatigue index slightly
    updated.postureFatigueIndex = Math.min(100, updated.postureFatigueIndex + 5);
    updated.focusResilience = Math.max(30, updated.focusResilience - 2);
    if (!updated.personalityTags.includes('Slouch Sensitive')) {
      updated.personalityTags.push('Slouch Sensitive');
    }
  }

  if (action.type === 'mastery_shift' && action.masteryVal !== undefined) {
    updated.averageMastery = Number(action.masteryVal.toFixed(2));
  }

  if (action.type === 'chat_message') {
    updated.sessionsCount += 1;
  }

  // Synthesize updated GraphRAG personality summary
  const strengthStr =
    updated.conceptualStrength.length > 0 ? updated.conceptualStrength.join(', ') : 'Foundations';
  const growthStr =
    updated.growthAreas.length > 0 ? updated.growthAreas.join(', ') : 'Advanced Synthesis';

  updated.graphRAGSummary = `GraphRAG learner node profile: Exhibits ${updated.cognitivePace} pacing with a preference for ${updated.preferredTone} feedback. Core mastery anchors in [${strengthStr}]. Currently requires scaffolded Socratic hints on [${growthStr}]. Posture resilience rating: ${updated.focusResilience}%, with fatigue index at ${updated.postureFatigueIndex}%.`;

  saveStoredCharacterisation(updated);
  return updated;
}
