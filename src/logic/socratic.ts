import { StudentContext, QuizItem } from '../types';
import { expandRagContext } from './graphrag';
import { checkGuardrails, rewriteGuardrailResponse } from './guardrail';

export interface SocraticResult {
  text: string;
  grounded: boolean;
  ssmlHint: 'neutral' | 'encouraging' | 'inquiring' | 'urgent';
  concept: string;
}

export const SAMPLE_QUIZZES: Record<string, QuizItem[]> = {
  'Calculus Integrals': [
    {
      id: 'calc-1',
      topic: 'Calculus Integrals',
      concept: 'Riemann Sums',
      question: 'In a Riemann sum, what does dividing an interval into smaller width (Δx → 0) accomplish geometrically?',
      options: [
        'It calculates the average slope of the curve.',
        'The sum of rectangular areas converges to the exact definite integral / area under the curve.',
        'It finds the local maximum of the function.',
        'It eliminates negative values under the x-axis.'
      ],
      correctIndex: 1,
      explanation: 'As Δx approaches 0, the sum of infinitely many infinitely thin rectangles converges to the exact definite integral ∫ f(x) dx.'
    },
    {
      id: 'calc-2',
      topic: 'Calculus Integrals',
      concept: 'Fundamental Theorem of Calculus',
      question: 'What is the core connection stated by the Fundamental Theorem of Calculus?',
      options: [
        'Differentiation and integration are inverse operations.',
        'Every continuous function is everywhere differentiable.',
        'The integral of a function is always strictly positive.',
        'Matrices can be transformed into eigenvalues.'
      ],
      correctIndex: 0,
      explanation: 'The Fundamental Theorem connects differentiation and definite integration as inverse operations.'
    },
    {
      id: 'calc-3',
      topic: 'Calculus Integrals',
      concept: 'Definite Integrals',
      question: 'If ∫ from 1 to 4 of 2x dx is evaluated, what is the result?',
      options: ['12', '15', '16', '8'],
      correctIndex: 1,
      explanation: 'The antiderivative is x². Evaluating from 1 to 4: 4² - 1² = 16 - 1 = 15.'
    }
  ],
  'Linear Algebra': [
    {
      id: 'la-1',
      topic: 'Linear Algebra',
      concept: 'Eigenvalues',
      question: 'Given an equation A v = λ v, what does the scalar λ represent when v is non-zero?',
      options: [
        'The determinant of matrix A.',
        'The eigenvalue corresponding to eigenvector v.',
        'The rank of the transformation.',
        'The inverse matrix diagonal.'
      ],
      correctIndex: 1,
      explanation: 'λ is the eigenvalue indicating by how much the eigenvector v is scaled during the linear transformation.'
    },
    {
      id: 'la-2',
      topic: 'Linear Algebra',
      concept: 'Matrix Multiplication',
      question: 'To multiply matrix A (size m×k) with matrix B (size p×n), which condition must hold?',
      options: ['m must equal n', 'k must equal p', 'm must equal p', 'k must equal n'],
      correctIndex: 1,
      explanation: 'The number of columns of A (k) must equal the number of rows of B (p).'
    }
  ],
  'Robotics': [
    {
      id: 'rob-1',
      topic: 'Robotics',
      concept: 'Kinematics',
      question: 'What is the difference between Forward Kinematics and Inverse Kinematics?',
      options: [
        'Forward kinematics calculates servo pulse width; inverse calculates battery voltage.',
        'Forward kinematics calculates end-effector position from joint angles; inverse finds joint angles for a target position.',
        'Forward kinematics is only for mobile robots; inverse is for drones.',
        'There is no mathematical difference.'
      ],
      correctIndex: 1,
      explanation: 'Forward kinematics maps joint angles → Cartesian coordinates, while inverse kinematics calculates required joint angles given desired Cartesian position.'
    }
  ],
  'Control Systems': [
    {
      id: 'cs-1',
      topic: 'Control Systems',
      concept: 'PID Controllers',
      question: 'In a PID controller, what is the primary role of the Integral (I) term?',
      options: [
        'Reacts to rapid spikes in sensor noise.',
        'Eliminates steady-state error by accumulating past error over time.',
        'Predicts future system trajectory based on rate of change.',
        'Shuts down servos if overheating occurs.'
      ],
      correctIndex: 1,
      explanation: 'The integral term accumulates past errors to eliminate residual steady-state offset.'
    }
  ]
};

export function generateSocraticResponse(
  studentMessage: string,
  context: StudentContext,
  customMaterials: string[] = []
): SocraticResult {
  const topic = context.active_topic;
  const mastery = context.p_mastery;
  const baseContext = customMaterials.length > 0 
    ? customMaterials.join(' ')
    : `Official course syllabus for ${topic}. Covers fundamentals, theorems, definitions, and applications.`;
  
  const expandedRag = expandRagContext(topic, baseContext);
  const q = studentMessage.toLowerCase().trim();

  let text: string;
  let ssmlHint: 'neutral' | 'encouraging' | 'inquiring' | 'urgent' = 'inquiring';

  // Topic specific intelligence
  if (q.includes('why') || q.includes('how') || q.includes('what is') || q.includes('explain') || q.includes('integral') || q.includes('matrix')) {
    if (mastery < 0.5) {
      // Scaffolding & intuitive analogies
      if (topic === 'Calculus Integrals') {
        text = `Think of an integral like finding the total distance covered when your speedometer speed is constantly changing. Instead of multiplying constant speed × time, we add together millions of tiny time slices! If you look at your graph, what do you notice about the area under the curve?`;
      } else if (topic === 'Linear Algebra') {
        text = `Picture a grid sheet of rubber. A matrix is just an operation that stretches, rotates, or shears that sheet! What happens to the basis vectors (1,0) and (0,1) when you apply the transformation?`;
      } else {
        text = `Let's break this down into a bite-sized piece. In ${topic}, we build up from the basics. What is the first key term that stands out to you from this problem?`;
      }
      ssmlHint = 'encouraging';
    } else if (mastery < 0.7) {
      // Guided questioning
      if (topic === 'Calculus Integrals') {
        text = `Good question. Consider the Fundamental Theorem of Calculus: if F'(x) = f(x), then ∫ from a to b of f(x) dx is F(b) - F(a). How does this connect the slope of a curve with the accumulated area underneath?`;
      } else {
        text = `You're on the right track! In ${topic}, consider how this concept connects to ${expandRagContext(topic, '').split(':')[1] || 'core theorems'}. How would you set up the initial equation?`;
      }
      ssmlHint = 'inquiring';
    } else {
      // High mastery: edge cases & deep synthesis
      text = `Excellent! Since your mastery in ${topic} is strong (${Math.round(mastery * 100)}%), here is a challenge: how does this behave under non-continuous boundary conditions or when applying it to real-time robotic servo kinematics?`;
      ssmlHint = 'neutral';
    }
  } else if (q.includes('hello') || q.includes('hi') || q.includes('hey')) {
    text = `Greetings! I'm SmartEduSync. We are tracking your progress on ${topic} (${Math.round(mastery * 100)}% mastery). What concept would you like to explore or solve together?`;
    ssmlHint = 'encouraging';
  } else if (q.includes('quiz') || q.includes('test') || q.includes('practice')) {
    text = `Let's test your knowledge! Click the 'Test Knowledge (BKT Quiz)' button above or ask me a specific problem you want to check your reasoning on.`;
    ssmlHint = 'inquiring';
  } else {
    text = `Interesting point regarding "${studentMessage}". In ${topic}, notice how this relates to our syllabus context. Would you like to review the core definition or try a sample calculation?`;
    ssmlHint = 'inquiring';
  }

  // Safety & Fact guardrails
  const guard = checkGuardrails(text, context);
  if (guard.verdict === 'DENIED') {
    text = rewriteGuardrailResponse(text, context);
  }

  return {
    text,
    grounded: true,
    ssmlHint,
    concept: topic,
  };
}
