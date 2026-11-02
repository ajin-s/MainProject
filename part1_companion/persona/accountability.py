"""Persistent, playful study-accountability personality.

Humour is aimed at procrastination or the robot itself, never the student's intelligence,
appearance, identity, or worth. Every nudge ends with a small, achievable next action.
"""
from typing import Any, Dict, List

from part2_knowledge.memory.store import get_recent_activities, record_activity


def _facts(context: Dict[str, Any]) -> tuple[str, int, int, str]:
    topic = context.get("active_topic", "your current topic")
    mastery = round(float(context.get("p_mastery", 0.5)) * 100)
    days = int(context.get("days_left", 7))
    exam = context.get("nearest_exam", topic)
    return topic, mastery, days, exam


def build_playful_nudge(context: Dict[str, Any], activities: List[Dict[str, str]] | None = None) -> str:
    """Create a fact-grounded accountability nudge with supportive, light sarcasm."""
    topic, mastery, days, exam = _facts(context)
    activities = activities if activities is not None else []
    recent_reply = next((a for a in activities if a["activity_type"] == "student_reply"), None)

    if recent_reply:
        opener = "I remember you checked in earlier—excellent, my memory circuits are not just decorative."
    elif mastery < 50:
        opener = f"Your {mastery}% {topic} progress is patiently waiting; it refuses to improve by staring dramatically at the ceiling."
    else:
        opener = f"Your {mastery}% {topic} progress is doing respectable work—let's not make it carry the group project alone."

    return (
        f"{opener} Your {exam} exam is in {days} days. "
        f"Give me one focused {topic} question, and we'll make the next small step together."
    )


def nudge_student(student_id: str, context: Dict[str, Any], db_path: str = "memory.db") -> str:
    activities = get_recent_activities(student_id, db_path=db_path)
    message = build_playful_nudge(context, activities)
    record_activity(student_id, "robot_nudge", message, db_path=db_path)
    return message


def respond_to_student_reply(
    student_id: str, reply: str, context: Dict[str, Any], db_path: str = "memory.db"
) -> str:
    """Persist a captured reply and return a motivating, non-judgmental next step."""
    clean_reply = reply.strip()
    record_activity(student_id, "student_reply", clean_reply or "No spoken reply captured", db_path=db_path)
    topic, mastery, days, exam = _facts(context)
    if not clean_reply:
        return f"No worries—I only caught silence. Your {exam} is in {days} days, so let's start tiny: name one {topic} idea you want to review."
    if any(word in clean_reply.lower() for word in ("tired", "later", "busy", "can't", "dont", "don't")):
        return f"Fair. Life has excellent plot twists. Let’s make a two-minute deal: tell me one thing you remember about {topic}, then you can decide the next step."
    return f"That’s a start. Your {mastery}% progress can grow from one honest attempt—what part of {topic} should we untangle first?"
