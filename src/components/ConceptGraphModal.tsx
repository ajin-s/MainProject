import React, { useState } from 'react';
import { BASE_CONCEPT_NODES, BASE_KNOWLEDGE_GRAPH_EDGES } from '../logic/graphrag';
import { ConceptNode, ConceptEdge, StudentProfile, LearnerCharacterisation } from '../types';
import { Network, Sparkles, X, User, ArrowRight } from 'lucide-react';

interface ConceptGraphModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeTopic: string;
  onSelectTopic: (topic: string) => void;
  studentProfile?: StudentProfile;
  characterisation?: LearnerCharacterisation;
  nodes?: ConceptNode[];
  edges?: ConceptEdge[];
}

export const ConceptGraphModal: React.FC<ConceptGraphModalProps> = ({
  isOpen,
  onClose,
  activeTopic,
  onSelectTopic,
  studentProfile,
  characterisation,
  nodes = BASE_CONCEPT_NODES,
  edges = BASE_KNOWLEDGE_GRAPH_EDGES,
}) => {
  if (!isOpen) return null;

  const [selectedNode, setSelectedNode] = useState<string>(activeTopic);

  const selectedNodeData = nodes.find(
    (n) => n.id.toLowerCase() === selectedNode.toLowerCase()
  );

  const connectedEdges = edges.filter(
    (e) =>
      e.from.toLowerCase() === selectedNode.toLowerCase() ||
      e.to.toLowerCase() === selectedNode.toLowerCase()
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative text-slate-800">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-1.5 text-indigo-600 text-xs font-mono font-semibold uppercase">
          <Network className="w-4 h-4" />
          <span>GraphRAG • Concept Topology &amp; Student Persona Network</span>
        </div>

        <h3 className="text-lg font-bold text-slate-900 mb-1">
          Knowledge Graph &amp; Learner Characterisation
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Select concepts or the Student Persona node to inspect prerequisite relations, weak spots, and 1-hop expansions.
        </p>

        {/* Dynamic Persona Node Pill if present */}
        {studentProfile && (
          <div className="p-3 mb-4 bg-indigo-50/70 border border-indigo-100 rounded-xl flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-indigo-600" />
              <div>
                <span className="font-bold text-indigo-900">
                  Learner Node: {studentProfile.name}
                </span>
                <span className="text-slate-500 block text-[11px]">
                  Style: {studentProfile.preferredStyle} • Goal: {studentProfile.targetGoal}
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedNode(`Learner: ${studentProfile.name}`)}
              className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-[11px] transition-colors"
            >
              Inspect Persona Node
            </button>
          </div>
        )}

        {/* Nodes Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-4 max-h-52 overflow-y-auto pr-1">
          {nodes.map((node) => {
            const isCurrent = node.id === selectedNode;
            const isActiveTopic = node.id === activeTopic;
            const isPersona = node.isStudentPersona;
            return (
              <button
                key={node.id}
                onClick={() => setSelectedNode(node.id)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isCurrent
                    ? 'bg-indigo-50 border-indigo-600 shadow-sm'
                    : isPersona
                    ? 'bg-purple-50/60 border-purple-200 text-slate-800'
                    : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold ${
                      isPersona
                        ? 'bg-indigo-100 text-indigo-800'
                        : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {node.category}
                  </span>
                  {isActiveTopic && (
                    <span className="text-[9px] font-bold text-indigo-600 font-mono">ACTIVE</span>
                  )}
                </div>
                <div className="text-xs font-bold text-slate-900 truncate">{node.name}</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                  Mastery: {Math.round(node.mastery * 100)}%
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Node Details & Connected Edges */}
        {selectedNodeData && (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-indigo-900 uppercase font-mono">
                  Inspecting: {selectedNodeData.name}
                </span>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  1-Hop Neighbors expand the Socratic LLM context prompt and track student strengths.
                </p>
              </div>
              {!selectedNodeData.isStudentPersona && selectedNodeData.name !== activeTopic && (
                <button
                  onClick={() => {
                    onSelectTopic(selectedNodeData.name);
                    onClose();
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shadow-sm"
                >
                  Set as Active Subject
                </button>
              )}
            </div>

            <div className="text-xs text-slate-700">
              <span className="font-semibold text-slate-600 block mb-1.5">
                Connected Semantic Graph Edges:
              </span>
              <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                {connectedEdges.map((edge, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between bg-white border border-slate-200 px-3 py-1.5 rounded-lg text-[11px] font-mono shadow-sm"
                  >
                    <span className="text-slate-800 font-medium truncate max-w-[150px]">{edge.from}</span>
                    <span className="text-indigo-600 px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-100 text-[10px] font-semibold">
                      -- [{edge.relation}] --&gt;
                    </span>
                    <span className="text-slate-800 font-medium truncate max-w-[150px]">{edge.to}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
