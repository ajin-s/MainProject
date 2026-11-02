"""Generate quiz items from retrieved syllabus chunks and score them with BKT."""
from __future__ import annotations

import re
from typing import Dict, List

from part2_knowledge.rag.ingest import retrieve_chunks
from part2_knowledge.verify.verifier import extract_key_concepts


def generate_quiz_item(topic: str, chunks: List[str] | None = None) -> Dict[str, object]:
    corpus = chunks or retrieve_chunks(topic, k=3)
    passage = corpus[0] if corpus else f"{topic} is a core idea in this course."
    sentence = re.split(r"(?<=[.!?])\s+", passage.strip())[0].strip()
    keywords = extract_key_concepts(passage, limit=5)
    focus = keywords[0] if keywords else topic.split()[0]
    question = (
        f"Using the idea of {topic}, explain in your own words what '{focus}' means. "
        f"Hint from your notes: {sentence[:140]}"
    )
    return {
        "topic": topic,
        "question": question,
        "expected_keywords": keywords,
        "source": sentence,
    }


def generate_quiz(topic: str, n: int = 5) -> List[Dict[str, object]]:
    chunks = retrieve_chunks(topic, k=max(n, 3))
    items = []
    for i in range(n):
        window = chunks[i % len(chunks) :] + chunks[: i % len(chunks)]
        items.append(generate_quiz_item(topic, window))
    return items
