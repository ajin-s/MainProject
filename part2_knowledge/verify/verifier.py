"""
Phase 3 task (not day 1 priority): before speaking a generated answer, check it's actually
supported by the retrieved RAG/GraphRAG context to catch hallucinations. See SRS Section 6.5.
"""


def is_grounded(answer_text: str, retrieved_chunks: list[str], min_overlap: float = 0.15) -> bool:
    """
    TODO(Part 2 team): naive placeholder using word overlap. Replace with a real entailment
    check (e.g. a small NLI model, or asking the LLM itself to verify) once RAG is stable.
    """
    answer_words = set(answer_text.lower().split())
    context_words = set(" ".join(retrieved_chunks).lower().split())
    if not answer_words:
        return False
    overlap = len(answer_words & context_words) / len(answer_words)
    return overlap >= min_overlap
