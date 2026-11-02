import React, { useState } from 'react';
import { INITIAL_CONCEPT_NODES, KNOWLEDGE_GRAPH_EDGES } from '../logic/graphrag';
import { Network, Sparkles, X, GitCommit } from 'lucide-react';

interface ConceptGraphModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeTopic: string;
  onSelectTopic: (topic: string) => void;
}

export const ConceptGraphModal: React.FC<ConceptGraphModalProps> = ({
  isOpen,
  onClose,
  activeTopic,
  onSelectTopic,
}) => {
  if (!isOpen) return null;

  const [selectedNode, setSelectedNode] = useState<string>(activeTopic);

  const selectedNodeData = INITIAL_CONCEPT_NODES.find(
    (n) => n.id.toLowerCase() === selectedNode.toLowerCase()
  );

  const connectedEdges = KNOWLEDGE_GRAPH_EDGES.filter(
    (e) =>
      e.from.toLowerCase() === selectedNode.toLowerCase() ||
      e.to.toLowerCase() === selectedNode.toLowerCase()
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-[#121a2b] border border-white/15 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-2 text-purple-400 text-xs font-mono font-semibold uppercase">
          <Network className="w-4 h-4" />
          <span>GraphRAG • NetworkX Concept Topology & 1-Hop Expansion</span>
        </div>

        <h3 className="text-lg font-bold text-white mb-1">Interactive Syllabus Knowledge Graph</h3>
        <p className="text-xs text-gray-400 mb-5">
          Select concepts to inspect prerequisite relations, subtopics, and RAG context expansions.
        </p>

        {/* Nodes Grid / Visualizer */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-5 max-h-56 overflow-y-auto pr-1">
          {INITIAL_CONCEPT_NODES.map((node) => {
            const isCurrent = node.id === selectedNode;
            const isActiveTopic = node.id === activeTopic;
            return (
              <button
                key={node.id}
                onClick={() => setSelectedNode(node.id)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isCurrent
                    ? 'bg-purple-600/30 border-purple-500 shadow-md shadow-purple-500/20'
                    : 'bg-black/30 border-white/10 hover:border-white/25 text-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/10 text-gray-300">
                    {node.category}
                  </span>
                  {isActiveTopic && (
                    <span className="text-[9px] font-bold text-cyan-400 font-mono">ACTIVE</span>
                  )}
                </div>
                <div className="text-xs font-bold text-white truncate">{node.name}</div>
                <div className="text-[10px] text-gray-400 font-mono mt-1">
                  Mastery: {Math.round(node.mastery * 100)}%
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Node Details & Connected Edges */}
        {selectedNodeData && (
          <div className="p-4 rounded-xl bg-black/40 border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-purple-300 uppercase font-mono">
                  Active Node: {selectedNodeData.name}
                </span>
                <p className="text-[11px] text-gray-400 mt-0.5">
                  1-Hop Neighbors expand the Socratic LLM context prompt during dialogue.
                </p>
              </div>
              {selectedNodeData.name !== activeTopic && (
                <button
                  onClick={() => {
                    onSelectTopic(selectedNodeData.name);
                    onClose();
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white transition-colors"
                >
                  Set as Active Topic
                </button>
              )}
            </div>

            <div className="text-xs text-gray-300">
              <span className="font-semibold text-gray-400 block mb-1.5">Direct Graph Relations:</span>
              <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                {connectedEdges.map((edge, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between bg-white/5 px-2.5 py-1.5 rounded-lg text-[11px] font-mono"
                  >
                    <span className="text-gray-300">{edge.from}</span>
                    <span className="text-purple-400 px-1.5 py-0.5 rounded bg-purple-500/10 border border-purple-500/20 text-[10px]">
                      -- [{edge.relation}] --&gt;
                    </span>
                    <span className="text-gray-300">{edge.to}</span>
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
