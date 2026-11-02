"""
Flashcard Generator for SmartEduSync Robot Display Screen.
Generates multi-line study cards from top RAG syllabus chunks.
"""
from typing import Any, Dict, List


def generate_flashcards(topic: str, chunks: List[str]) -> Dict[str, Any]:
    cards = []
    for i, chunk in enumerate(chunks[:3], 1):
        clean_line = chunk.strip().replace("\n", " ")
        if len(clean_line) > 50:
            clean_line = clean_line[:47] + "..."
        cards.append(f"Card {i}: {clean_line}")

    return {
        "topic": topic,
        "cards": cards if cards else [f"Review basic principles of {topic}."]
    }


if __name__ == "__main__":
    fc = generate_flashcards("Calculus", ["Integrals measure area under curves.", "Definite integrals use limits."])
    print(fc)
