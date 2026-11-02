import { ConceptNode } from '../types';

export interface StudyPlanItem {
  id: string;
  day: number;
  dateStr: string;
  conceptId: string;
  conceptTitle: string;
  category: string;
  durationMinutes: number;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  status: 'pending' | 'in_progress' | 'completed';
  prerequisites: string[];
  keyObjectives: string[];
  suggestedPrompt: string;
}

export interface EduGraphData {
  nodes: ConceptNode[];
  edges: { from: string; to: string; relation: string }[];
  summary: string;
  extractedSyllabus: {
    unitTitle: string;
    topics: string[];
  }[];
}

export interface GeneratedStudyPlan {
  id: string;
  title: string;
  targetExam: string;
  examDate: string;
  totalDays: number;
  dailyHours: number;
  overallMastery: number;
  items: StudyPlanItem[];
  milestones: { title: string; targetDay: number; achieved: boolean }[];
}

/**
 * Intelligent parser that reads raw study materials / syllabus text,
 * extracts concepts and relations to construct the EduGraph, and compiles
 * a day-by-day study roadmap.
 */
export function buildEduGraphFromMaterial(
  title: string,
  rawText: string
): EduGraphData {
  const clean = rawText.trim();
  const lines = clean.split('\n').filter((l) => l.trim().length > 0);

  // Default syllabus seeds if input is short or custom parsed
  const conceptsFound: { name: string; category: string; difficulty: string }[] = [];

  // Parse lines for topics/bullet points or headings
  for (const line of lines) {
    const trimmed = line.replace(/^[-*•\d.)\]\s]+/, '').trim();
    if (trimmed.length > 3 && trimmed.length < 60) {
      if (!conceptsFound.some((c) => c.name.toLowerCase() === trimmed.toLowerCase())) {
        conceptsFound.push({
          name: trimmed,
          category: title.includes('Calculus') || title.includes('Math') ? 'Calculus & Math' : 'Core Syllabus',
          difficulty: 'Intermediate',
        });
      }
    }
  }

  // Fallback defaults if no structure was parsed
  if (conceptsFound.length < 3) {
    if (title.toLowerCase().includes('calculus') || clean.toLowerCase().includes('integral')) {
      conceptsFound.push(
        { name: 'Limits and Continuity', category: 'Foundation', difficulty: 'Beginner' },
        { name: 'Riemann Sums & Rectangles', category: 'Method', difficulty: 'Beginner' },
        { name: 'Definite Integrals', category: 'Calculus', difficulty: 'Intermediate' },
        { name: 'Fundamental Theorem of Calculus', category: 'Theorem', difficulty: 'Intermediate' },
        { name: 'Integration by Substitution (U-Sub)', category: 'Technique', difficulty: 'Intermediate' },
        { name: 'Integration by Parts (LIATE)', category: 'Technique', difficulty: 'Advanced' },
        { name: 'Area Between Curves & Physics Applications', category: 'Application', difficulty: 'Advanced' }
      );
    } else if (title.toLowerCase().includes('robot') || clean.toLowerCase().includes('servo')) {
      conceptsFound.push(
        { name: 'Forward Kinematics', category: 'Kinematics', difficulty: 'Beginner' },
        { name: 'Inverse Kinematics (IK)', category: 'Kinematics', difficulty: 'Advanced' },
        { name: 'PID Feedback Control', category: 'Control', difficulty: 'Intermediate' },
        { name: 'PWM & PCA9685 Servo Buses', category: 'Hardware', difficulty: 'Beginner' },
        { name: 'Computer Vision Posture Sensing', category: 'Perception', difficulty: 'Intermediate' }
      );
    } else {
      conceptsFound.push(
        { name: `${title} - Core Fundamentals`, category: 'Module 1', difficulty: 'Beginner' },
        { name: `${title} - Key Principles & Formulas`, category: 'Module 2', difficulty: 'Intermediate' },
        { name: `${title} - Problem Solving Methods`, category: 'Module 3', difficulty: 'Intermediate' },
        { name: `${title} - Advanced Edge Cases`, category: 'Module 4', difficulty: 'Advanced' },
        { name: `${title} - Comprehensive Exam Synthesis`, category: 'Module 5', difficulty: 'Advanced' }
      );
    }
  }

  // Construct EduGraph Nodes
  const nodes: ConceptNode[] = conceptsFound.map((c, i) => {
    const prev = i > 0 ? [conceptsFound[i - 1].name] : [];
    const next = i < conceptsFound.length - 1 ? [conceptsFound[i + 1].name] : [];
    return {
      id: c.name,
      name: c.name,
      category: c.category,
      mastery: Math.min(0.9, Math.max(0.2, 0.35 + (i * 0.08))),
      connections: [...prev, ...next],
    };
  });

  // Construct Edges
  const edges: { from: string; to: string; relation: string }[] = [];
  for (let i = 0; i < nodes.length - 1; i++) {
    edges.push({
      from: nodes[i].name,
      to: nodes[i + 1].name,
      relation: i === 0 ? 'foundation' : i === 1 ? 'prerequisite' : 'deepens',
    });
  }

  // Structured syllabus units
  const unitsCount = Math.max(2, Math.ceil(nodes.length / 3));
  const extractedSyllabus: { unitTitle: string; topics: string[] }[] = [];
  for (let u = 0; u < unitsCount; u++) {
    const slice = nodes.slice(u * 3, (u + 1) * 3);
    if (slice.length > 0) {
      extractedSyllabus.push({
        unitTitle: `Unit ${u + 1}: ${slice[0].name} and Concepts`,
        topics: slice.map((n) => n.name),
      });
    }
  }

  return {
    nodes,
    edges,
    summary: `EduGraph successfully constructed with ${nodes.length} interconnected concept nodes and ${edges.length} pedagogical relationship edges.`,
    extractedSyllabus,
  };
}

/**
 * Generates an adaptive day-by-day study plan from the EduGraph
 */
export function generateStudyPlan(
  eduGraph: EduGraphData,
  examName: string,
  daysAvailable: number = 7,
  dailyHours: number = 2
): GeneratedStudyPlan {
  const nodes = eduGraph.nodes;
  const items: StudyPlanItem[] = [];

  const now = new Date();
  const examDate = new Date();
  examDate.setDate(now.getDate() + daysAvailable);

  const totalSessions = Math.min(nodes.length, daysAvailable * 2);

  nodes.forEach((node, idx) => {
    const day = Math.min(daysAvailable, Math.floor((idx / nodes.length) * daysAvailable) + 1);
    const itemDate = new Date();
    itemDate.setDate(now.getDate() + (day - 1));

    const difficulty: 'Beginner' | 'Intermediate' | 'Advanced' =
      idx < 2 ? 'Beginner' : idx < nodes.length - 2 ? 'Intermediate' : 'Advanced';

    items.push({
      id: `plan-item-${idx + 1}`,
      day,
      dateStr: itemDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      conceptId: node.id,
      conceptTitle: node.name,
      category: node.category,
      durationMinutes: Math.round((dailyHours * 60) / 2),
      difficulty,
      status: idx === 0 ? 'in_progress' : 'pending',
      prerequisites: node.connections.slice(0, 1),
      keyObjectives: [
        `Understand core intuition behind ${node.name}`,
        `Derive and calculate standard formulas`,
        `Solve 2 verification questions with Socratic robot`,
      ],
      suggestedPrompt: `Explain the intuition and formula for ${node.name} step by step.`,
    });
  });

  const milestones = [
    {
      title: 'Foundations & Prerequisite Mastery',
      targetDay: Math.max(1, Math.floor(daysAvailable * 0.3)),
      achieved: false,
    },
    {
      title: 'Core Problem Solving & Graph Integration',
      targetDay: Math.max(2, Math.floor(daysAvailable * 0.65)),
      achieved: false,
    },
    {
      title: 'Final High-Risk Exam Drill & Formula Speedrun',
      targetDay: daysAvailable,
      achieved: false,
    },
  ];

  return {
    id: `plan-${Date.now()}`,
    title: `${examName} Adaptive Study Roadmap`,
    targetExam: examName,
    examDate: examDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    totalDays: daysAvailable,
    dailyHours,
    overallMastery: Math.round(
      (nodes.reduce((acc, curr) => acc + curr.mastery, 0) / (nodes.length || 1)) * 100
    ),
    items,
    milestones,
  };
}
