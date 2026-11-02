import { ConceptNode } from '../types';

export interface ConceptEdge {
  from: string;
  to: string;
  relation: string;
}

export const KNOWLEDGE_GRAPH_EDGES: ConceptEdge[] = [
  { from: 'Calculus Integrals', to: 'Definite Integrals', relation: 'subtopic' },
  { from: 'Calculus Integrals', to: 'Fundamental Theorem of Calculus', relation: 'prerequisite' },
  { from: 'Calculus Integrals', to: 'Riemann Sums', relation: 'method' },
  { from: 'Definite Integrals', to: 'Area Under Curve', relation: 'geometric meaning' },
  { from: 'Fundamental Theorem of Calculus', to: 'Antiderivatives', relation: 'connection' },
  { from: 'Linear Algebra', to: 'Matrix Multiplication', relation: 'subtopic' },
  { from: 'Linear Algebra', to: 'Eigenvalues', relation: 'concept' },
  { from: 'Linear Algebra', to: 'Vector Spaces', relation: 'foundation' },
  { from: 'Eigenvalues', to: 'Eigenvectors', relation: 'dual' },
  { from: 'Robotics', to: 'Kinematics', relation: 'includes' },
  { from: 'Robotics', to: 'Control Systems', relation: 'includes' },
  { from: 'Control Systems', to: 'PID Controllers', relation: 'includes' },
];

export const INITIAL_CONCEPT_NODES: ConceptNode[] = [
  { id: 'Calculus Integrals', name: 'Calculus Integrals', category: 'Math', mastery: 0.42, connections: ['Definite Integrals', 'Fundamental Theorem of Calculus', 'Riemann Sums'] },
  { id: 'Definite Integrals', name: 'Definite Integrals', category: 'Math', mastery: 0.40, connections: ['Calculus Integrals', 'Area Under Curve'] },
  { id: 'Fundamental Theorem of Calculus', name: 'Fundamental Theorem of Calculus', category: 'Math', mastery: 0.35, connections: ['Calculus Integrals', 'Antiderivatives'] },
  { id: 'Riemann Sums', name: 'Riemann Sums', category: 'Math', mastery: 0.50, connections: ['Calculus Integrals'] },
  { id: 'Linear Algebra', name: 'Linear Algebra', category: 'Math', mastery: 0.78, connections: ['Matrix Multiplication', 'Eigenvalues', 'Vector Spaces'] },
  { id: 'Matrix Multiplication', name: 'Matrix Multiplication', category: 'Math', mastery: 0.85, connections: ['Linear Algebra'] },
  { id: 'Eigenvalues', name: 'Eigenvalues', category: 'Math', mastery: 0.70, connections: ['Linear Algebra', 'Eigenvectors'] },
  { id: 'Robotics', name: 'Robotics', category: 'Engineering', mastery: 0.50, connections: ['Kinematics', 'Control Systems'] },
  { id: 'Control Systems', name: 'Control Systems', category: 'Engineering', mastery: 0.35, connections: ['Robotics', 'PID Controllers'] },
  { id: 'PID Controllers', name: 'PID Controllers', category: 'Engineering', mastery: 0.30, connections: ['Control Systems'] },
];

export function getRelatedConcepts(topic: string): string[] {
  const matches: string[] = [];
  for (const edge of KNOWLEDGE_GRAPH_EDGES) {
    if (edge.from.toLowerCase() === topic.toLowerCase()) {
      matches.push(edge.to);
    } else if (edge.to.toLowerCase() === topic.toLowerCase()) {
      matches.push(edge.from);
    }
  }
  if (matches.length > 0) return matches;
  return topic.includes('Calculus')
    ? ['Definite Integrals', 'Riemann Sums', 'Fundamental Theorem of Calculus']
    : ['Control Systems', 'Kinematics'];
}

export function expandRagContext(topic: string, baseContext: string): string {
  const neighbors = getRelatedConcepts(topic);
  if (neighbors.length > 0) {
    return `${baseContext} Related concepts in student's knowledge graph: ${neighbors.join(', ')}.`;
  }
  return baseContext;
}
