import { ExamRisk } from '../types';

export interface TopicMastery {
  topic: string;
  p_mastery: number;
  nearest_exam: string;
  days_left: number;
  department: string;
}

export const INITIAL_TOPICS: Record<string, TopicMastery> = {
  'Artificial Intelligence': {
    topic: 'Artificial Intelligence',
    p_mastery: 0.48,
    nearest_exam: 'Artificial Intelligence',
    days_left: 4,
    department: 'Computer Science',
  },
  'Machine Learning': {
    topic: 'Machine Learning',
    p_mastery: 0.52,
    nearest_exam: 'Machine Learning',
    days_left: 6,
    department: 'Computer Science',
  },
  'Calculus Integrals': {
    topic: 'Calculus Integrals',
    p_mastery: 0.42,
    nearest_exam: 'Calculus Integrals',
    days_left: 3,
    department: 'Mathematics',
  },
  'Linear Algebra': {
    topic: 'Linear Algebra',
    p_mastery: 0.78,
    nearest_exam: 'Linear Algebra',
    days_left: 7,
    department: 'Mathematics',
  },
  'Robotics': {
    topic: 'Robotics',
    p_mastery: 0.50,
    nearest_exam: 'Robotics',
    days_left: 12,
    department: 'Engineering',
  },
  'Control Systems': {
    topic: 'Control Systems',
    p_mastery: 0.35,
    nearest_exam: 'Control Systems',
    days_left: 2,
    department: 'Engineering',
  },
};

/**
 * Standard Bayesian Knowledge Tracing formula from part1_companion/mastery/bkt.py
 */
export function calculateBktUpdate(
  pPrev: number,
  correct: boolean,
  pTransit: number = 0.1,
  pSlip: number = 0.1,
  pGuess: number = 0.2
): number {
  let pObs: number;
  if (correct) {
    pObs = (pPrev * (1.0 - pSlip)) / (pPrev * (1.0 - pSlip) + (1.0 - pPrev) * pGuess);
  } else {
    pObs = (pPrev * pSlip) / (pPrev * pSlip + (1.0 - pPrev) * (1.0 - pGuess));
  }

  const pUpdated = pObs + (1.0 - pObs) * pTransit;
  return Number(Math.max(0.0, Math.min(1.0, pUpdated)).toFixed(3));
}

/**
 * Exam risk categorization adhering to SRS §5.4
 */
export function checkExamRisk(topic: string, daysLeft: number, pMastery: number): ExamRisk {
  if (daysLeft <= 3 && pMastery < 0.5) {
    return 'high';
  } else if (daysLeft <= 7 && pMastery < 0.7) {
    return 'medium';
  } else {
    return 'low';
  }
}
