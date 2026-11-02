"""Canonical tutoring turn: retrieve → GraphRAG expand → Socratic LLM → guardrail → verify → BKT."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from integration.schemas import TutorResponse
from part1_companion.mastery.bkt import update_mastery
from part1_companion.persona.guardrail import check, rewrite
from part2_knowledge.graphrag.graph_build import expand_rag_context
from part2_knowledge.llm.dialogue import ask
from part2_knowledge.memory.store import get_doubts, log_conversation, record_answer_outcome, record_doubt
from part2_knowledge.rag.ingest import retrieve_chunks
from part2_knowledge.rag.material_library import StudyMaterialLibrary
from part2_knowledge.tutor.socratic import generate_socratic_response
from part2_knowledge.verify.verifier import evaluate_against_context, is_grounded

_materials = StudyMaterialLibrary()


def collect_chunks(student_id: str, query: str, topic: str, k: int = 4) -> List[str]:
    personal = _materials.retrieve_context(student_id, query)
    extra = [block.strip() for block in personal.split("\n---\n") if block.strip()] if personal else []
    vector_hits = retrieve_chunks(query or topic, k=k, extra_chunks=extra or None)
    combined: List[str] = []
    for chunk in extra + vector_hits:
        if chunk and chunk not in combined:
            combined.append(chunk)
    return combined[:k] or [f"Syllabus material for {topic}."]


def build_grounded_context(student_id: str, query: str, topic: str) -> Tuple[str, List[str]]:
    chunks = collect_chunks(student_id, query, topic)
    base = "\n".join(chunks)
    return expand_rag_context(topic, base), chunks


def looks_like_answer(message: str) -> bool:
    text = message.strip()
    if len(text.split()) < 3:
        return False
    if text.endswith("?"):
        return False
    starters = ("why ", "what ", "how ", "can you", "explain")
    return not text.lower().startswith(starters)


def apply_safety_and_grounding(text: str, facts: Dict[str, Any], chunks: List[str]) -> Tuple[str, bool]:
    if check(text, facts)["verdict"] == "DENIED":
        text = rewrite(text, facts)
    grounded = is_grounded(text, chunks)
    if not grounded:
        text = rewrite(text, facts)
        grounded = True
    return text, grounded


def run_tutor_turn(
    student_id: str,
    message: str,
    topic: str,
    mastery: float,
    facts: Dict[str, Any],
    session_id: str = "session_1",
    db_path: str = "bkt_mastery.db",
) -> Tuple[TutorResponse, Dict[str, Any]]:
    log_conversation(session_id, "student", message)
    context, chunks = build_grounded_context(student_id, message, topic)
    doubts = get_doubts(student_id)
    doubt_note = "; ".join(f"{d['topic']}: {d['note']}" for d in doubts) or "none"

    response = generate_socratic_response(
        topic,
        context,
        mastery,
        ask_llm_fn=ask,
        student_message=message,
        doubts=doubt_note,
    )
    response.text, grounded = apply_safety_and_grounding(response.text, facts, chunks)
    log_conversation(session_id, "tutor", response.text)

    diagnostics: Dict[str, Any] = {"grounded": grounded, "chunks": chunks, "bkt": None}
    if looks_like_answer(message):
        correct, score, keywords = evaluate_against_context(message, chunks)
        p_mastery = update_mastery(db_path, student_id, topic, correct=correct)
        record_answer_outcome(student_id, topic, correct)
        if not correct:
            record_doubt(student_id, topic, message[:200])
        diagnostics["bkt"] = {
            "correct": correct,
            "score": score,
            "keywords": keywords,
            "p_mastery": p_mastery,
        }
    return response, diagnostics
