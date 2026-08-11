"""
Phase 2 task (not day 1 priority): wire up TTS. Left as a stub with a clear interface so
Part 2's tutor.response events have somewhere to go once this is implemented.

TODO(Part 1 team):
  - Pick a TTS provider: cloud (ElevenLabs) for expressiveness, or local (Piper) for offline demos.
  - Map emotion/intervention level -> SSML (rate, pitch) per SRS Section 5.5.
"""
from integration.schemas import TutorResponse


def speak(response: TutorResponse):
    """
    TODO: replace with a real TTS call. For now, just prints what would be spoken.
    """
    tone = response.ssml_hint or "neutral"
    print(f"[TTS - {tone}] {response.text}")
