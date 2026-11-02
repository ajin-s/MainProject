"""Flashcards derived from RAG chunks: prompt on the front, key facts on the back."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from part2_knowledge.verify.verifier import extract_key_concepts


def generate_flashcards(topic: str, chunks: List[str]) -> Dict[str, Any]:
    cards = []
    for i, chunk in enumerate(chunks[:3], 1):
        sentence = re.split(r"(?<=[.!?])\s+", chunk.strip())[0].strip()
        keys = extract_key_concepts(chunk, limit=4)
        prompt = f"Recall: what connects {topic} to {keys[0]}?" if keys else f"Recall a key fact about {topic}."
        answer = sentence[:120]
        cards.append({"front": prompt, "back": answer, "label": f"Card {i}"})
    if not cards:
        cards = [{"front": f"Review {topic}", "back": f"Start with the definition of {topic}.", "label": "Card 1"}]
    return {"topic": topic, "cards": cards}


if __name__ == "__main__":
    print(generate_flashcards("Calculus", ["Integrals measure area under curves.", "Definite integrals use limits."]))
