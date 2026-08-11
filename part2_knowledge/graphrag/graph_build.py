"""
Phase 2 task (not day 1 priority): build a concept graph with NetworkX (or Neo4j later) so
retrieval can traverse related topics, not just return isolated text chunks.

Left minimal for now — get RAG (rag/ingest.py) working first.
"""
import networkx as nx


def build_sample_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_edge("Robotics", "Kinematics", relation="includes")
    g.add_edge("Robotics", "Control Systems", relation="includes")
    g.add_edge("Control Systems", "PID Controllers", relation="includes")
    return g


def related_topics(g: nx.DiGraph, topic: str) -> list[str]:
    return list(g.successors(topic)) if topic in g else []


if __name__ == "__main__":
    g = build_sample_graph()
    print("Topics related to 'Robotics':", related_topics(g, "Robotics"))
