import { StudentContext, QuizItem, EmotionState } from '../types';
import { expandRagContext } from './graphrag';
import { checkGuardrails, rewriteGuardrailResponse } from './guardrail';

export interface SocraticResult {
  text: string;
  grounded: boolean;
  ssmlHint: 'neutral' | 'encouraging' | 'inquiring' | 'urgent';
  emotion: EmotionState;
  concept: string;
}

export const SAMPLE_QUIZZES: Record<string, QuizItem[]> = {
  'Artificial Intelligence': [
    {
      id: 'ai-1',
      topic: 'Artificial Intelligence',
      concept: 'A* Heuristic Search',
      question: 'For the A* search algorithm to be mathematically guaranteed to find the optimal path on a tree, what property must the heuristic function h(n) satisfy?',
      options: [
        'h(n) must always be equal to zero.',
        'h(n) must be admissible: it never overestimates the true cost to reach the goal (h(n) ≤ h*(n)).',
        'h(n) must be strictly strictly greater than the actual cost g(n).',
        'h(n) must be negative to incentivize fast node expansion.'
      ],
      correctIndex: 1,
      explanation: 'An admissible heuristic never overestimates the true remaining cost, guaranteeing that A* expands the optimal path first.'
    },
    {
      id: 'ai-2',
      topic: 'Artificial Intelligence',
      concept: 'Alpha-Beta Pruning',
      question: 'In adversarial game search, under what condition does Alpha-Beta pruning safely prune a subtree without affecting the minimax outcome?',
      options: [
        'When the search depth reaches an even number.',
        'Whenever alpha becomes greater than or equal to beta (α ≥ β).',
        'When the evaluation score drops to exactly zero.',
        'Only when the opponent is playing sub-optimally.'
      ],
      correctIndex: 1,
      explanation: 'When α ≥ β, the current player or opponent already has a guaranteed better or equal move elsewhere, so exploring this branch cannot change the decision.'
    },
    {
      id: 'ai-3',
      topic: 'Artificial Intelligence',
      concept: 'Knowledge Representation',
      question: 'What is the key principle behind Resolution Refutation in Propositional Logic theorem proving?',
      options: [
        'Assuming the theorem is false, converting to Conjunctive Normal Form (CNF), and deriving a contradiction (empty clause).',
        'Calculating the Euclidean distance between propositions.',
        'Pruning states using depth-first iterative deepening.',
        'Randomly assigning truth values until all clauses evaluate to True.'
      ],
      correctIndex: 0,
      explanation: 'Resolution refutation negates the goal clause, adds it to the knowledge base in CNF, and uses the resolution rule to derive a contradiction (nil/empty clause).'
    }
  ],
  'Machine Learning': [
    {
      id: 'ml-1',
      topic: 'Machine Learning',
      concept: 'Gradient Descent',
      question: 'If the learning rate α in Gradient Descent is set excessively high, what failure mode commonly occurs?',
      options: [
        'The model will underfit by getting stuck immediately at the initial weights.',
        'The loss function will oscillate wildly and diverge away from the local or global minimum.',
        'The gradients will instantly vanish to zero.',
        'The dataset will automatically shuffle.'
      ],
      correctIndex: 1,
      explanation: 'An overly large learning rate causes the updates to overshoot the minimum valley, leading to catastrophic divergence of the loss.'
    },
    {
      id: 'ml-2',
      topic: 'Machine Learning',
      concept: 'Overfitting & Regularization',
      question: 'How does L1 Regularization (Lasso) differ fundamentally from L2 Regularization (Ridge) regarding feature selection?',
      options: [
        'L1 adds an absolute value penalty (|w|), driving non-essential feature weights to exactly zero for sparse feature selection.',
        'L1 squares the weights while L2 takes the square root.',
        'L2 always removes 50% of all features from the neural network.',
        'There is no mathematical difference; both behave identically.'
      ],
      correctIndex: 0,
      explanation: 'The sharp corner of the L1 diamond constraint boundary forces irrelevant parameter weights directly to 0, producing inherent feature sparsity.'
    },
    {
      id: 'ml-3',
      topic: 'Machine Learning',
      concept: 'Backpropagation & Neural Networks',
      question: 'What fundamental calculus rule enables Backpropagation to efficiently compute weight gradients across deep neural network layers?',
      options: [
        'The Chain Rule of multivariable calculus (∂L/∂w = ∂L/∂a · ∂a/∂z · ∂z/∂w).',
        'Integration by Parts.',
        'L\'Hopital\'s Rule.',
        'Taylor Series Expansion only.'
      ],
      correctIndex: 0,
      explanation: 'Backpropagation is an efficient application of the multivariable Chain Rule, propagating error signals backwards from output loss to each parameter.'
    }
  ],
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
  const studentName = context.student_name || 'student';

  const baseContext = customMaterials.length > 0 
    ? customMaterials.join(' ')
    : `Official course syllabus for ${topic}. Covers fundamentals, theorems, definitions, algorithms, and real-world implementations.`;
  
  const expandedRag = expandRagContext(topic, baseContext, studentName);
  const q = studentMessage.toLowerCase().trim();

  let text: string;
  let ssmlHint: 'neutral' | 'encouraging' | 'inquiring' | 'urgent' = 'inquiring';
  let emotion: EmotionState = 'thinking';

  // Topic specific pedagogical intelligence
  if (topic === 'Artificial Intelligence') {
    if (q.includes('a*') || q.includes('heuristic') || q.includes('search')) {
      if (mastery < 0.5) {
        text = `Think of A* search like using GPS navigation on your phone. You have the actual distance you've driven so far, plus a smart estimated straight-line distance to your destination. Why is it vital that this estimate never overestimates the real road distance?`;
        emotion = 'curious';
        ssmlHint = 'encouraging';
      } else {
        text = `Right! In A* search, f(n) = g(n) + h(n). If our heuristic is consistent (monotonic), what mathematical guarantee does that provide regarding re-visiting or reopening already expanded states?`;
        emotion = 'happy';
        ssmlHint = 'inquiring';
      }
    } else if (q.includes('minimax') || q.includes('alpha') || q.includes('beta') || q.includes('game')) {
      text = `In game tree search, imagine Minimax as two grandmasters: you maximize your score while assuming your opponent plays the optimal counter. When we prune with Alpha-Beta, why doesn't ignoring those pruned subtrees risk missing a winning move?`;
      emotion = 'curious';
      ssmlHint = 'inquiring';
    } else {
      text = `Great inquiry about ${topic}. In AI systems, we translate fuzzy real-world reasoning into formal representations. What specific algorithm or problem representation should we break down first?`;
      emotion = 'happy';
      ssmlHint = 'encouraging';
    }
  } else if (topic === 'Machine Learning') {
    if (q.includes('gradient') || q.includes('descent') || q.includes('loss')) {
      if (mastery < 0.5) {
        text = `Picture standing on a foggy hillside blindfolded, trying to reach the lowest lake. You feel the slope with your boots and take a small step downhill. That slope is your gradient, and the lake is your minimal loss! What happens if your steps are way too giant?`;
        emotion = 'curious';
        ssmlHint = 'encouraging';
      } else {
        text = `Spot on. With Gradient Descent, θ ← θ - α ∇L(θ). What happens to convergence when the loss landscape has an ill-conditioned Hessian matrix with steep narrow ravines, and how do momentum optimizers like Adam help?`;
        emotion = 'happy';
        ssmlHint = 'inquiring';
      }
    } else if (q.includes('overfit') || q.includes('regularization') || q.includes('backprop')) {
      text = `Overfitting is like memorizing the exact answers on last year's exam instead of learning the underlying concepts! When we apply L2 regularization, how does penalizing large weights keep the model smooth and generalizable?`;
      emotion = 'curious';
      ssmlHint = 'inquiring';
    } else {
      text = `Machine Learning is all about finding mathematical patterns from data. What part of the learning pipeline—loss function, optimization, or generalization—would you like to explore?`;
      emotion = 'happy';
      ssmlHint = 'encouraging';
    }
  } else if (q.includes('why') || q.includes('how') || q.includes('what is') || q.includes('explain')) {
    if (mastery < 0.5) {
      text = `Let's break this down into an intuitive picture. In ${topic}, we start with the simplest core principle before diving into equations. What is the central goal of this concept in your own words?`;
      emotion = 'curious';
      ssmlHint = 'encouraging';
    } else if (mastery < 0.7) {
      text = `Good question, ${studentName}. In ${topic}, notice how this connects to our syllabus context: ${expandedRag.slice(0, 100)}... How would you set up the initial relationship?`;
      emotion = 'thinking';
      ssmlHint = 'inquiring';
    } else {
      text = `Impressive! Since your mastery in ${topic} is strong (${Math.round(mastery * 100)}%), here is a deeper question: how would this principle hold up under boundary conditions or noisy real-world data?`;
      emotion = 'happy';
      ssmlHint = 'neutral';
    }
  } else if (q.includes('hello') || q.includes('hi') || q.includes('hey')) {
    text = `Hello ${studentName}! I'm SmartEduSync. Your active subject is ${topic} (${Math.round(mastery * 100)}% mastery). What concept or homework problem shall we conquer together?`;
    emotion = 'happy';
    ssmlHint = 'encouraging';
  } else {
    text = `Regarding "${studentMessage}" in ${topic}: let's examine the foundational definition and see how we can apply it. Would you like a step-by-step example or a conceptual analogy?`;
    emotion = 'thinking';
    ssmlHint = 'inquiring';
  }

  // Safety & Fact guardrails
  const guard = checkGuardrails(text, context);
  if (guard.verdict === 'DENIED') {
    text = rewriteGuardrailResponse(text, context);
    emotion = 'concerned';
  }

  return {
    text,
    grounded: true,
    ssmlHint,
    emotion,
    concept: topic,
  };
}
