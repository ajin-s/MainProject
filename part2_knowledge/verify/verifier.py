"""Grounding check and keyword-overlap evaluation of student answers."""
from __future__ import annotations

import re
from typing import List, Tuple

STOP_WORDS = {
    "a", "an", "the", "is", "are", "to", "of", "and", "in", "for", "on", "with",
    "that", "this", "as", "be", "or", "by", "from", "it", "we", "you", "your",
}


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())


def extract_key_concepts(text: str, limit: int = 8) -> List[str]:
    """Content words from retrieved material used as expected-answer keywords."""
    counts: dict[str, int] = {}
    for token in _tokens(text):
        if token in STOP_WORDS:
            continue
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts, key=lambda word: (-counts[word], -len(word), word))
    return ranked[:limit]


def is_grounded(answer_text: str, retrieved_chunks: List[str], min_overlap: float = 0.15) -> bool:
    if not answer_text or not retrieved_chunks:
        return True
    answer_words = set(_tokens(answer_text)) - STOP_WORDS
    context_words = set(_tokens(" ".join(retrieved_chunks))) - STOP_WORDS
    if not answer_words:
        return False
    overlap = len(answer_words & context_words) / len(answer_words)
    return overlap >= min_overlap


def evaluate_student_answer(
    question: str, expected_keywords: List[str], student_text: str
) -> Tuple[bool, float]:
    if not student_text:
        return False, 0.0
    student_lower = student_text.lower()
    keys = [kw for kw in expected_keywords if kw]
    if not keys:
        keys = extract_key_concepts(question)
    matches = sum(1 for kw in keys if kw.lower() in student_lower)
    score = matches / max(1, len(keys))
    return score >= 0.50, round(score, 2)


def evaluate_against_context(student_text: str, chunks: List[str]) -> Tuple[bool, float, List[str]]:
    keywords = extract_key_concepts(" ".join(chunks))
    correct, score = evaluate_student_answer("", keywords, student_text)
    return correct, score, keywords


if __name__ == "__main__":
    answer = "Integrals calculate the area under a mathematical function curve."
    context = ["Bayesian Knowledge Tracing models mastery.", "Integrals represent area under curve."]
    print("Is Grounded:", is_grounded(answer, context))
    correct, score = evaluate_student_answer("What is an integral?", ["area", "curve", "limit"], "It finds area under curve.")
    print(f"Student Answer Evaluation: Correct={correct}, Score={score}")
