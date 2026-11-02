"""GraphRAG: 1-hop concept expansion over a NetworkX syllabus graph."""
from __future__ import annotations

from typing import Any, List, Optional

from part2_knowledge.graphrag.graph_mapper import DynamicGraphMapper

try:
    import networkx as nx
except ImportError:
    nx = None


def build_sample_graph():
    mapper = DynamicGraphMapper()
    mapper.map_document_to_graph(
        [
            {
                "source": "syllabus",
                "text": (
                    "Calculus Integrals include Definite Integrals, Riemann Sums, "
                    "and the Fundamental Theorem of Calculus. Linear Algebra covers "
                    "Matrix Multiplication, Eigenvalues, and Vector Spaces. Robotics "
                    "includes Kinematics and Control Systems. Control Systems include PID Controllers."
                ),
            }
        ]
    )
    if mapper.graph.number_of_edges() == 0 and nx is not None:
        g = nx.DiGraph()
        g.add_edge("Calculus Integrals", "Definite Integrals", relation="subtopic")
        g.add_edge("Calculus Integrals", "Fundamental Theorem of Calculus", relation="prerequisite")
        g.add_edge("Calculus Integrals", "Riemann Sums", relation="method")
        g.add_edge("Linear Algebra", "Matrix Multiplication", relation="subtopic")
        g.add_edge("Linear Algebra", "Eigenvalues", relation="concept")
        g.add_edge("Linear Algebra", "Vector Spaces", relation="foundation")
        g.add_edge("Robotics", "Kinematics", relation="includes")
        g.add_edge("Robotics", "Control Systems", relation="includes")
        g.add_edge("Control Systems", "PID Controllers", relation="includes")
        return g
    return mapper.graph


def _match_node(g, topic: str) -> Optional[str]:
    if g is None:
        return None
    if topic in g:
        return topic
    lowered = topic.lower()
    for node in g.nodes():
        name = str(node)
        if lowered in name.lower() or name.lower() in lowered:
            return name
    return None


def related_topics(g, topic: str) -> List[str]:
    node = _match_node(g, topic)
    if g is not None and node is not None:
        neighbors = list(g.successors(node)) + list(g.predecessors(node))
        return list(dict.fromkeys(str(n) for n in neighbors))
    mapper = DynamicGraphMapper()
    return mapper.extract_concepts_from_text(topic)[:4]


def expand_rag_context(topic: str, base_context: str, g: Any = None) -> str:
    if g is None:
        g = build_sample_graph()
    neighbors = related_topics(g, topic)
    if not neighbors and base_context:
        neighbors = DynamicGraphMapper().extract_concepts_from_text(base_context)[:6]
    if neighbors:
        return f"{base_context} Related concepts to explore: {', '.join(neighbors)}."
    return base_context


if __name__ == "__main__":
    graph = build_sample_graph()
    print("Topics related to 'Calculus Integrals':", related_topics(graph, "Calculus Integrals"))
