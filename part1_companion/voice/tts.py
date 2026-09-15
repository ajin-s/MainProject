import os
from typing import Optional

from integration.event_bus import bus
from integration.schemas import TOPIC_TUTOR_RESPONSE, TutorResponse

# Tone mapping dictionaries
LEVEL_TONE_MAP = {
    "gentle": "soft",
    "firm": "neutral",
    "escalated": "urgent",
}

EMOTION_TONE_MAP = {
    "engaged": "neutral",
    "confused": "soft",
    "distracted": "soft",
    "frustrated": "soft",
    "bored": "urgent",
}


def tone_for_intervention_level(level: str) -> str:
    return LEVEL_TONE_MAP.get(level.lower(), "neutral")


def tone_for_emotion(emotion: str) -> str:
    return EMOTION_TONE_MAP.get(emotion.lower(), "neutral")


def speak(response: TutorResponse, silent: bool = False) -> None:
    """
    Speaks the given TutorResponse text using local pyttsx3 or console fallback.
    """
    tone = response.ssml_hint or "neutral"

    if silent or os.getenv("TTS_SILENT", "0") == "1":
        print(f"[TTS - {tone}] {response.text}")
        return

    try:
        import pyttsx3
        engine = pyttsx3.init()
        base_rate = engine.getProperty("rate")

        if tone == "soft":
            engine.setProperty("rate", max(100, base_rate - 30))
        elif tone == "urgent":
            engine.setProperty("rate", base_rate + 40)
        else:
            engine.setProperty("rate", base_rate)

        print(f"[TTS Audio - {tone}] \"{response.text}\"")
        engine.say(response.text)
        engine.runAndWait()
    except Exception:
        print(f"[TTS - {tone}] {response.text}")


async def _on_tutor_response(msg: TutorResponse) -> None:
    speak(msg)


def subscribe() -> None:
    """Subscribes the TTS engine to TOPIC_TUTOR_RESPONSE on the event bus."""
    bus.subscribe(TOPIC_TUTOR_RESPONSE, _on_tutor_response)


if __name__ == "__main__":
    sample = TutorResponse(text="Hello! Let's work on Calculus today.", ssml_hint="soft", confidence=0.9)
    speak(sample, silent=True)