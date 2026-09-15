"""
Speech-to-Text (STT) Module for SmartEduSync.
Captures microphone input using speech_recognition / sounddevice when available,
or provides interactive typed fallback.
"""
import os
from typing import Optional


class SpeechToText:
    def __init__(self, mode: str = "auto", engine: str = "whisper"):
        self.mode = mode
        self.engine = engine

    def transcribe_audio_whisper(self, audio_path: str) -> str:
        """Transcribes audio file using Faster-Whisper."""
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_path)
            return " ".join(segment.text for segment in segments).strip()
        except Exception:
            return ""

    def listen(self, prompt: str = "Student Voice Input > ") -> str:
        """
        Listens for spoken audio or prompts for typed input in fallback mode.
        """
        if self.mode == "mic":
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    print("[STT] Listening...")
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5.0)
                    text = recognizer.recognize_google(audio)
                    print(f"[STT Recognized] {text}")
                    return text
            except Exception as e:
                print(f"[STT Fallback: mic unavailable ({e})]")

        # Fallback to stdin prompt
        try:
            return input(prompt).strip()
        except EOFError:
            return ""



if __name__ == "__main__":
    stt = SpeechToText(mode="fallback")
    print("STT Module ready.")
