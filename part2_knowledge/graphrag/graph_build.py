"""
GraphRAG Concept Graph Builder using NetworkX.
Provides 1-hop related topic expansion to ground Socratic tutoring in connected concepts.
"""
from typing import List
try:
    import networkx as nx
except ImportError:
    nx = None


def build_sample_graph():
    if nx is None:
        return None

    g = nx.DiGraph()
    # Syllabus concept edges
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


def related_topics(g, topic: str) -> List[str]:
    if g is not None and topic in g:
        return list(g.successors(topic)) + list(g.predecessors(topic))
    return ["Definite Integrals", "Riemann Sums"] if "Calculus" in topic else ["Control Systems"]



from typing import List, Any


def expand_rag_context(topic: str, base_context: str, g: Any = None) -> str:
    if g is None:
        g = build_sample_graph()

    neighbors = related_topics(g, topic)
    if neighbors:
        expansion = f" Related concepts to explore: {', '.join(neighbors)}."
        return base_context + expansion
    return base_context



if __name__ == "__main__":
    g = build_sample_graph()
    print("Topics related to 'Calculus Integrals':", related_topics(g, "Calculus Integrals"))

