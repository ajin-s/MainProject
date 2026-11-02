import { StudentContext } from '../types';

export function buildPlayfulNudge(context: StudentContext, hasRecentReply = false): string {
  const topic = context.active_topic || 'Calculus Integrals';
  const mastery = Math.round((context.p_mastery || 0.42) * 100);
  const days = context.days_left ?? 3;
  const exam = context.nearest_exam || topic;

  let opener: string;
  if (hasRecentReply) {
    opener = 'I remember you checked in earlier—excellent, my memory circuits are not just decorative.';
  } else if (mastery < 50) {
    opener = `Your ${mastery}% ${topic} progress is patiently waiting; it refuses to improve by staring dramatically at the ceiling.`;
  } else {
    opener = `Your ${mastery}% ${topic} progress is doing respectable work—let's not make it carry the group project alone.`;
  }

  return `${opener} Your ${exam} exam is in ${days} days. Give me one focused ${topic} question, and we'll make the next small step together.`;
}

export function respondToStudentReply(reply: string, context: StudentContext): string {
  const cleanReply = reply.trim();
  const topic = context.active_topic || 'Calculus Integrals';
  const mastery = Math.round((context.p_mastery || 0.42) * 100);
  const days = context.days_left ?? 3;
  const exam = context.nearest_exam || topic;

  if (!cleanReply) {
    return `No worries—I only caught silence. Your ${exam} exam is in ${days} days, so let's start tiny: name one ${topic} idea you want to review.`;
  }

  const excuses = ['tired', 'later', 'busy', "can't", 'cant', 'dont', "don't", 'sleepy', 'bored'];
  if (excuses.some((w) => cleanReply.toLowerCase().includes(w))) {
    return `Fair enough. Life has excellent plot twists. Let’s make a two-minute deal: tell me one single formula or idea you remember about ${topic}, then you can decide the next step.`;
  }

  return `That’s a solid start! Your ${mastery}% progress can grow from one honest attempt—what specific part of ${topic} should we untangle first?`;
}
