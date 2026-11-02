"""
Dynamic GraphRAG Entity & Concept Mapper for SmartEduSync.
Parses ingested study materials (PDFs, Web links, Images, Notes) and dynamically builds
and updates NetworkX directed concept graphs with source metadata.
"""
import re
from typing import Any, Dict, List, Set, Tuple
import networkx as nx


class DynamicGraphMapper:
    def __init__(self):
        self.graph = nx.DiGraph()

    def extract_concepts_from_text(self, text: str) -> List[str]:
        """Extracts key academic concepts using capitalized phrase pattern & keyword matching."""
        keywords = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        stop = {"The", "A", "An", "In", "For", "To", "On", "Of", "And", "With", "By", "This", "That", "It"}
        concepts = [k for k in keywords if k not in stop and len(k) > 3]

        # Additional domain concepts
        lower = text.lower()
        if "integral" in lower or "calculus" in lower:
            concepts.extend(["Calculus Integrals", "Riemann Sums", "Definite Integrals"])
        if "matrix" in lower or "vector" in lower or "linear algebra" in lower:
            concepts.extend(["Linear Algebra", "Eigenvalues", "Matrix Multiplication"])
        if "robot" in lower or "kinematics" in lower or "control" in lower:
            concepts.extend(["Robotics", "Kinematics", "PID Controllers"])

        return list(dict.fromkeys(concepts))

    def map_document_to_graph(self, chunks: List[Dict[str, Any]]) -> nx.DiGraph:
        """
        Maps ingested chunks to NetworkX Directed Graph.
        Connects sequential concepts with relations ('subtopic', 'prerequisite', 'related_method').
        """
        for chunk in chunks:
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            concepts = self.extract_concepts_from_text(text)

            for i in range(len(concepts)):
                c1 = concepts[i]
                if not self.graph.has_node(c1):
                    self.graph.add_node(c1, source=source)

                if i + 1 < len(concepts):
                    c2 = concepts[i + 1]
                    if not self.graph.has_node(c2):
                        self.graph.add_node(c2, source=source)
                    self.graph.add_edge(c1, c2, relation="subtopic", source=source)

        return self.graph

    def get_graph_summary(self) -> Dict[str, Any]:
        nodes = list(self.graph.nodes())
        edges = [(u, v, d.get("relation", "related")) for u, v, d in self.graph.edges(data=True)]
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges,
        }


if __name__ == "__main__":
    mapper = DynamicGraphMapper()
    mapper.map_document_to_graph([
        {"source": "calculus.pdf", "text": "Calculus Integrals include Definite Integrals and Riemann Sums."}
    ])
    summary = mapper.get_graph_summary()
    print("GraphRAG Dynamic Summary:", summary)
