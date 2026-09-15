"""
Response Verification & Student Answer Evaluation Engine.
Checks LLM response factual grounding and evaluates student quiz answers against reference context.
"""
from typing import List, Tuple


def is_grounded(answer_text: str, retrieved_chunks: List[str], min_overlap: float = 0.15) -> bool:
    """
    Checks if answer text has sufficient factual grounding in retrieved RAG chunks.
    """
    if not answer_text or not retrieved_chunks:
        return True

    answer_words = set(answer_text.lower().split())
    context_words = set(" ".join(retrieved_chunks).lower().split())

    if not answer_words:
        return False

    # Ignore tiny stop words
    stop_words = {"a", "an", "the", "is", "are", "to", "of", "and", "in", "for", "on", "with"}
    meaningful_words = answer_words - stop_words

    if not meaningful_words:
        return True

    overlap = len(meaningful_words & context_words) / len(meaningful_words)
    return overlap >= min_overlap


def evaluate_student_answer(
    question: str, expected_keywords: List[str], student_text: str
) -> Tuple[bool, float]:
    """
    Evaluates student answer correctness based on key concepts.
    Returns: (is_correct, score)
    """
    if not student_text:
        return False, 0.0

    student_lower = student_text.lower()
    matches = sum(1 for kw in expected_keywords if kw.lower() in student_lower)

    score = matches / max(1, len(expected_keywords))
    is_correct = score >= 0.50
    return is_correct, round(score, 2)


if __name__ == "__main__":
    answer = "Integrals calculate the area under a mathematical function curve."
    context = ["Bayesian Knowledge Tracing models mastery.", "Integrals represent area under curve."]
    print("Is Grounded:", is_grounded(answer, context))

    correct, score = evaluate_student_answer("What is an integral?", ["area", "curve", "limit"], "It finds area under curve.")
    print(f"Student Answer Evaluation: Correct={correct}, Score={score}")

