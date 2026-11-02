"""Speak real Socratic tutor lines with intervention- and emotion-mapped prosody.

Usage:
    python -m demo.simulate_tts
    python -m demo.simulate_tts --silent
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from part1_companion.mastery.bkt import get_student_context
from part1_companion.voice.tts import speak, tone_for_emotion, tone_for_intervention_level
from part2_knowledge.tutor.pipeline import run_tutor_turn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", action="store_true")
    args = parser.parse_args()

    context = get_student_context("student_1")
    topic = context.get("active_topic", "Calculus Integrals")
    mastery = float(context.get("p_mastery", 0.5))
    response, _ = run_tutor_turn(
        "student_1",
        f"Why does {topic} matter?",
        topic,
        mastery,
        context,
        session_id="tts_demo",
    )

    print("By intervention level (same grounded tutor line):")
    for level in ("gentle", "firm", "escalated"):
        response.ssml_hint = tone_for_intervention_level(level)
        speak(response, silent=args.silent)

    print("\nBy detected emotion:")
    for emotion in ("engaged", "frustrated", "bored", "confused"):
        response.ssml_hint = tone_for_emotion(emotion)
        speak(response, silent=args.silent)


if __name__ == "__main__":
    main()
