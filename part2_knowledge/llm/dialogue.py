"""Local LLM dialogue via Ollama, with a context-driven Socratic fallback."""
from __future__ import annotations

import os
import re

MODEL_NAME = os.getenv("OLLAMA_MODEL", "phi3.5")


def _section(prompt: str, label: str) -> str:
    pattern = rf"{re.escape(label)}\s*:?\s*(.+?)(?:\n[A-Z][^\n]{{0,40}}:|\Z)"
    match = re.search(pattern, prompt, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def socratic_fallback(prompt: str) -> str:
    """Build one guiding question from retrieved context — no canned topic switch."""
    topic = _section(prompt, "Topic") or "this idea"
    topic = topic.splitlines()[0].strip()
    student = _section(prompt, "Student said") or _section(prompt, "Student")
    context = _section(prompt, "Retrieved Syllabus & GraphRAG Context") or _section(prompt, "Context")
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", context) if len(s.strip()) > 24]
    seed = sentences[0] if sentences else f"{topic} is built from smaller parts you can name."
    seed = seed[:180]
    student_l = student.lower()
    if any(word in student_l for word in ("wrong", "idk", "don't know", "dont know", "confused", "stuck")):
        return (
            f"Let's slow down on {topic}. Using this clue — {seed} — "
            f"which single word in that sentence feels least clear to you?"
        )
    if "?" in student:
        return (
            f"Good question. Before we jump ahead, what would change in {topic} "
            f"if this were true: {seed.rstrip('. ')}?"
        )
    return (
        f"You mentioned {topic}. From the notes: {seed} "
        f"What happens if you try to explain that idea in your own words, one step at a time?"
    )


def ask(prompt: str, model: str = MODEL_NAME) -> str:
    try:
        import ollama

        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]
    except Exception:
        return socratic_fallback(prompt)


if __name__ == "__main__":
    print(ask("Topic: Calculus Integrals\nStudent said: Why do we integrate?\nRetrieved Syllabus & GraphRAG Context: Integrals measure area under a curve."))
