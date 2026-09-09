def _speak_piper(self, text: str, params: dict) -> None:
        """Local TTS implementation using pyttsx3 fallback for Windows."""
        try:
            import pyttsx3
            engine = pyttsx3.init()

            # Adjust speed rate dynamically based on tone
            base_rate = engine.getProperty('rate')
            if params['label'] == 'gentle':
                engine.setProperty('rate', base_rate - 40)
            elif params['label'] == 'escalated':
                engine.setProperty('rate', base_rate + 40)

            print(f"[Local Audio - {params['label']}] Speaking...")
            engine.say(text)
            engine.runAndWait()
        except Exception:
            print(f"[TTS - {params['label']}] {text}")