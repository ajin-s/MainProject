import { ConceptNode, ConceptEdge, StudentProfile, LearnerCharacterisation } from '../types';

export const BASE_KNOWLEDGE_GRAPH_EDGES: ConceptEdge[] = [
  // Artificial Intelligence Edges
  { from: 'Artificial Intelligence', to: 'A* Heuristic Search', relation: 'subtopic' },
  { from: 'Artificial Intelligence', to: 'Minimax & Game Trees', relation: 'subtopic' },
  { from: 'Minimax & Game Trees', to: 'Alpha-Beta Pruning', relation: 'optimization' },
  { from: 'Artificial Intelligence', to: 'Knowledge Representation', relation: 'core' },
  { from: 'Knowledge Representation', to: 'Propositional & First-Order Logic', relation: 'formalism' },
  { from: 'A* Heuristic Search', to: 'Admissible Heuristics', relation: 'prerequisite' },

  // Machine Learning Edges
  { from: 'Machine Learning', to: 'Supervised Learning', relation: 'paradigm' },
  { from: 'Supervised Learning', to: 'Loss Functions', relation: 'objective' },
  { from: 'Loss Functions', to: 'Gradient Descent', relation: 'optimization' },
  { from: 'Gradient Descent', to: 'Backpropagation & Neural Networks', relation: 'engine' },
  { from: 'Supervised Learning', to: 'Overfitting & Regularization', relation: 'defense' },
  { from: 'Overfitting & Regularization', to: 'L1/L2 Regularization (Lasso/Ridge)', relation: 'technique' },
  { from: 'Supervised Learning', to: 'Support Vector Machines (SVM)', relation: 'algorithm' },

  // Calculus Edges
  { from: 'Calculus Integrals', to: 'Definite Integrals', relation: 'subtopic' },
  { from: 'Calculus Integrals', to: 'Fundamental Theorem of Calculus', relation: 'prerequisite' },
  { from: 'Calculus Integrals', to: 'Riemann Sums', relation: 'method' },
  { from: 'Definite Integrals', to: 'Area Under Curve', relation: 'geometric meaning' },
  { from: 'Fundamental Theorem of Calculus', to: 'Antiderivatives', relation: 'connection' },

  // Linear Algebra Edges
  { from: 'Linear Algebra', to: 'Matrix Multiplication', relation: 'subtopic' },
  { from: 'Linear Algebra', to: 'Eigenvalues & Eigenvectors', relation: 'concept' },
  { from: 'Linear Algebra', to: 'Vector Spaces & Span', relation: 'foundation' },

  // Cross-discipline bridge
  { from: 'Linear Algebra', to: 'Machine Learning', relation: 'mathematical foundation' },
  { from: 'Calculus Integrals', to: 'Machine Learning', relation: 'gradient computation' },
  { from: 'Robotics', to: 'Artificial Intelligence', relation: 'autonomous decision making' },
  { from: 'Robotics', to: 'Control Systems', relation: 'includes' },
  { from: 'Control Systems', to: 'PID Controllers', relation: 'includes' },
];

export const BASE_CONCEPT_NODES: ConceptNode[] = [
  // AI Nodes
  { id: 'Artificial Intelligence', name: 'Artificial Intelligence', category: 'AI & CS', mastery: 0.48, connections: ['A* Heuristic Search', 'Minimax & Game Trees', 'Knowledge Representation'] },
  { id: 'A* Heuristic Search', name: 'A* Heuristic Search', category: 'AI & CS', mastery: 0.50, connections: ['Artificial Intelligence', 'Admissible Heuristics'] },
  { id: 'Minimax & Game Trees', name: 'Minimax & Game Trees', category: 'AI & CS', mastery: 0.45, connections: ['Artificial Intelligence', 'Alpha-Beta Pruning'] },
  { id: 'Alpha-Beta Pruning', name: 'Alpha-Beta Pruning', category: 'AI & CS', mastery: 0.38, connections: ['Minimax & Game Trees'] },
  { id: 'Knowledge Representation', name: 'Knowledge Representation', category: 'AI & CS', mastery: 0.55, connections: ['Artificial Intelligence', 'Propositional & First-Order Logic'] },
  { id: 'Propositional & First-Order Logic', name: 'Propositional & First-Order Logic', category: 'AI & CS', mastery: 0.60, connections: ['Knowledge Representation'] },

  // ML Nodes
  { id: 'Machine Learning', name: 'Machine Learning', category: 'AI & CS', mastery: 0.52, connections: ['Supervised Learning', 'Loss Functions', 'Gradient Descent'] },
  { id: 'Supervised Learning', name: 'Supervised Learning', category: 'AI & CS', mastery: 0.65, connections: ['Machine Learning', 'Loss Functions', 'Support Vector Machines (SVM)'] },
  { id: 'Loss Functions', name: 'Loss Functions', category: 'AI & CS', mastery: 0.55, connections: ['Supervised Learning', 'Gradient Descent'] },
  { id: 'Gradient Descent', name: 'Gradient Descent', category: 'AI & CS', mastery: 0.58, connections: ['Loss Functions', 'Backpropagation & Neural Networks'] },
  { id: 'Backpropagation & Neural Networks', name: 'Backpropagation & Neural Networks', category: 'AI & CS', mastery: 0.42, connections: ['Gradient Descent'] },
  { id: 'Overfitting & Regularization', name: 'Overfitting & Regularization', category: 'AI & CS', mastery: 0.60, connections: ['Supervised Learning'] },

  // Math & Robotics
  { id: 'Calculus Integrals', name: 'Calculus Integrals', category: 'Math', mastery: 0.42, connections: ['Definite Integrals', 'Fundamental Theorem of Calculus', 'Riemann Sums'] },
  { id: 'Definite Integrals', name: 'Definite Integrals', category: 'Math', mastery: 0.40, connections: ['Calculus Integrals'] },
  { id: 'Fundamental Theorem of Calculus', name: 'Fundamental Theorem of Calculus', category: 'Math', mastery: 0.35, connections: ['Calculus Integrals'] },
  { id: 'Riemann Sums', name: 'Riemann Sums', category: 'Math', mastery: 0.50, connections: ['Calculus Integrals'] },
  { id: 'Linear Algebra', name: 'Linear Algebra', category: 'Math', mastery: 0.78, connections: ['Matrix Multiplication', 'Eigenvalues & Eigenvectors'] },
  { id: 'Matrix Multiplication', name: 'Matrix Multiplication', category: 'Math', mastery: 0.85, connections: ['Linear Algebra'] },
  { id: 'Eigenvalues & Eigenvectors', name: 'Eigenvalues & Eigenvectors', category: 'Math', mastery: 0.70, connections: ['Linear Algebra'] },
  { id: 'Robotics', name: 'Robotics', category: 'Engineering', mastery: 0.50, connections: ['Control Systems'] },
  { id: 'Control Systems', name: 'Control Systems', category: 'Engineering', mastery: 0.35, connections: ['PID Controllers'] },
  { id: 'PID Controllers', name: 'PID Controllers', category: 'Engineering', mastery: 0.30, connections: ['Control Systems'] },
];

/**
 * Builds the complete GraphRAG topology including the Dynamic Student Persona node
 * and personalized semantic edges created from real interactions.
 */
export function buildGraphWithStudentPersona(
  profile: StudentProfile,
  characterisation: LearnerCharacterisation,
  activeTopic: string
): { nodes: ConceptNode[]; edges: ConceptEdge[] } {
  const nodes = [...BASE_CONCEPT_NODES];
  const edges = [...BASE_KNOWLEDGE_GRAPH_EDGES];

  const studentNodeId = `Learner: ${profile.name || 'Student'}`;
  const studentConnections: string[] = [activeTopic, ...characterisation.conceptualStrength, ...characterisation.growthAreas];

  // Add the dynamic Student Persona Node to GraphRAG
  const studentNode: ConceptNode = {
    id: studentNodeId,
    name: studentNodeId,
    category: 'Student Persona',
    mastery: characterisation.averageMastery,
    connections: studentConnections,
    isStudentPersona: true,
  };
  nodes.unshift(studentNode);

  // Add dynamic semantic edges linking student persona to specific concept clusters
  edges.push({
    from: studentNodeId,
    to: activeTopic,
    relation: 'currently studying',
  });

  characterisation.conceptualStrength.forEach((s) => {
    edges.push({
      from: studentNodeId,
      to: s,
      relation: 'demonstrates mastery in',
    });
  });

  characterisation.growthAreas.forEach((w) => {
    edges.push({
      from: studentNodeId,
      to: w,
      relation: 'needs scaffolding on',
    });
  });

  edges.push({
    from: studentNodeId,
    to: profile.targetGoal || 'Artificial Intelligence',
    relation: 'target exam goal',
  });

  return { nodes, edges };
}

export function getRelatedConcepts(topic: string): string[] {
  const matches: string[] = [];
  for (const edge of BASE_KNOWLEDGE_GRAPH_EDGES) {
    if (edge.from.toLowerCase() === topic.toLowerCase()) {
      matches.push(edge.to);
    } else if (edge.to.toLowerCase() === topic.toLowerCase()) {
      matches.push(edge.from);
    }
  }
  if (matches.length > 0) return matches;
  if (topic.includes('AI') || topic.includes('Artificial')) {
    return ['A* Heuristic Search', 'Minimax & Game Trees', 'Knowledge Representation'];
  }
  if (topic.includes('Learning') || topic.includes('ML')) {
    return ['Gradient Descent', 'Loss Functions', 'Supervised Learning', 'Backpropagation & Neural Networks'];
  }
  return ['Definite Integrals', 'Riemann Sums', 'Fundamental Theorem of Calculus'];
}

export function expandRagContext(topic: string, baseContext: string, studentName?: string): string {
  const neighbors = getRelatedConcepts(topic);
  let expansion = '';
  if (neighbors.length > 0) {
    expansion += ` Related concepts in knowledge graph: ${neighbors.join(', ')}.`;
  }
  if (studentName) {
    expansion += ` Grounded for student ${studentName}.`;
  }
  return baseContext + expansion;
}
