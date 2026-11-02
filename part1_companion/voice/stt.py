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
        self._live_device = "unprobed"  # cached index of the input device carrying audio energy

    def _detect_live_microphone(self, sr, recognizer, probe_sec: float = 0.5) -> Optional[int]:
        """
        Pick the input device that actually carries audio energy.

        Laptops with virtual-audio drivers often expose many input endpoints whose
        *default* device is silent (muted array, loopback, etc.). We briefly record
        on the default device first, then on every input-capable device, and return
        the index with the highest RMS. Returns None to keep sr.Microphone's default.
        """
        try:
            import numpy as np
        except ImportError:
            return None

        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            candidates: list = [None]  # None = OS default, probed first so it wins ties
            for i in range(pa.get_device_count()):
                try:
                    if pa.get_device_info_by_index(i).get("maxInputChannels", 0) > 0:
                        candidates.append(i)
                except Exception:
                    continue
            pa.terminate()
        except Exception:
            return None

        best_index, best_rms = None, 0.0
        for idx in candidates:
            try:
                with sr.Microphone(device_index=idx) as source:
                    audio = recognizer.record(source, duration=probe_sec)
                samples = np.frombuffer(audio.get_raw_data(convert_rate=16000, convert_width=2), dtype=np.int16)
                rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))) if samples.size else 0.0
                if rms > best_rms:
                    best_index, best_rms = idx, rms
            except Exception:
                continue

        if best_rms < 50:  # every candidate is effectively silent
            return None
        print(f"[STT] Live microphone auto-selected (device={best_index}, rms={best_rms:.0f})")
        return best_index

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
        if self.mode in ("mic", "auto"):
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                if self._live_device == "unprobed":
                    self._live_device = self._detect_live_microphone(sr, recognizer)
                with sr.Microphone(device_index=self._live_device) as source:
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
