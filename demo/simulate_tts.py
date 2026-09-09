"""
demo/simulate_tts.py

Shows the intervention-level/emotion -> tone -> speak() pipeline working,
using fake TutorResponse objects (no real TTS API, no Part 2 needed).

Usage:
    python -m demo.simulate_tts
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.schemas import TutorResponse  # noqa: E402
from part1_companion.voice.tts import (  # noqa: E402
    speak,
    tone_for_emotion,
    tone_for_intervention_level,
)


def main() -> None:
    print("By intervention level:")
    for level in ("gentle", "firm", "escalated"):
        tone = tone_for_intervention_level(level)
        response = TutorResponse(
            text=f"(example nudge for a {level!r} intervention)",
            ssml_hint=tone,
            confidence=0.8,
        )
        speak(response)

    print("\nBy detected emotion:")
    for emotion in ("engaged", "frustrated", "bored", "confused"):
        tone = tone_for_emotion(emotion)
        response = TutorResponse(
            text=f"(example line for a student who seems {emotion})",
            ssml_hint=tone,
            confidence=0.8,
        )
        speak(response)


if __name__ == "__main__":
    main()
