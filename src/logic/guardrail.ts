import { StudentContext } from '../types';

export const BANNED_PHRASES: string[] = [
  'hopeless',
  "why can't you even",
  'this is easy',
  'give up',
  "you're bad at",
  'too late for you',
  'stop trying',
  'fail',
  'stupid',
];

function extractNumbers(text: string): number[] {
  const matches = text.match(/\b\d+(?:\.\d+)?%?/g);
  if (!matches) return [];
  const extracted: number[] = [];
  for (const m of matches) {
    const cleanNum = m.replace('%', '');
    const val = parseFloat(cleanNum);
    if (!isNaN(val)) extracted.push(val);
  }
  return extracted;
}

export function checkGuardrails(
  text: string,
  context: Partial<StudentContext>
): { verdict: 'PASSED' | 'DENIED'; reason?: string } {
  const lower = text.toLowerCase();

  for (const banned of BANNED_PHRASES) {
    if (lower.includes(banned)) {
      return {
        verdict: 'DENIED',
        reason: `Toxic or demotivating phrasing detected: "${banned}"`,
      };
    }
  }

  // Number grounding check
  const extractedNums = extractNumbers(text);
  const validValues = new Set<number>();
  if (context.p_mastery !== undefined) {
    validValues.add(Number((context.p_mastery).toFixed(2)));
    validValues.add(Math.round(context.p_mastery * 100));
  }
  if (context.days_left !== undefined) {
    validValues.add(context.days_left);
  }

  // Allow small counting numbers like 1, 2, 3 questions, 0
  for (const num of extractedNums) {
    if (num <= 5 && Number.isInteger(num)) continue;
    if (!validValues.has(num) && !validValues.has(Math.round(num))) {
      return {
        verdict: 'DENIED',
        reason: `Ungrounded stat detected: number ${num} is not supported by student ground-truth records.`,
      };
    }
  }

  return { verdict: 'PASSED' };
}

export function rewriteGuardrailResponse(text: string, context: Partial<StudentContext>): string {
  const topic = context.active_topic || 'your current topic';
  const masteryPct = Math.round((context.p_mastery ?? 0.5) * 100);
  const daysLeft = context.days_left ?? 3;
  const exam = context.nearest_exam || topic;

  return `Let's focus on ${topic}. You're currently at ${masteryPct}% mastery with ${daysLeft} days left until your ${exam} exam. Let's take it one step at a time!`;
}
