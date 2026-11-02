import { EmotionState } from '../types';

export interface EmotionalVoiceSettings {
  pitch: number;
  rate: number;
  volume: number;
  prefix?: string;
}

export const EMOTIONAL_PROSODY: Record<EmotionState, EmotionalVoiceSettings> = {
  happy: {
    pitch: 1.20,
    rate: 1.06,
    volume: 1.0,
  },
  alert: {
    pitch: 1.28,
    rate: 1.14,
    volume: 1.0,
  },
  concerned: {
    pitch: 0.94,
    rate: 0.92,
    volume: 0.95,
  },
  curious: {
    pitch: 1.12,
    rate: 1.02,
    volume: 1.0,
  },
  thinking: {
    pitch: 1.02,
    rate: 0.94,
    volume: 0.95,
  },
  listening: {
    pitch: 1.05,
    rate: 1.0,
    volume: 1.0,
  },
  watching: {
    pitch: 1.0,
    rate: 1.0,
    volume: 1.0,
  },
  idle: {
    pitch: 0.98,
    rate: 0.98,
    volume: 0.9,
  },
};

export const NAG_PHRASES = [
  "Hey! I see you slouching and fading away. Straighten your posture, your Artificial Intelligence exam is right around the corner!",
  "Slouch alert! Staring at your desk won't transfer machine learning gradients into your neural weights by osmosis. Sit up tall and let's work on this!",
  "Eye opening level dropping! Are you daydreaming or optimizing loss functions? Let's take a deep breath, sit upright, and conquer this next step.",
  "Wake up! Your neck angle is dipping past 22 degrees. The tabletop robot is watching—let's do one focused problem right now!",
  "Posture breakdown detected! Even my PCA9685 servos maintain better joint alignment than that. Straighten up and show me your focus!"
];

class AudioEngine {
  private synth: SpeechSynthesis | null = null;
  private recognition: any = null;
  private isListening: boolean = false;
  private currentEmotion: EmotionState = 'watching';

  constructor() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      this.synth = window.speechSynthesis;
    }
  }

  public speak(text: string, emotion: EmotionState = 'watching', onEnd?: () => void) {
    if (!this.synth) return;
    try {
      this.synth.cancel(); // Stop any pending utterance
      this.currentEmotion = emotion;

      const utterance = new SpeechSynthesisUtterance(text);
      const prosody = EMOTIONAL_PROSODY[emotion] || EMOTIONAL_PROSODY.watching;

      utterance.pitch = prosody.pitch;
      utterance.rate = prosody.rate;
      utterance.volume = prosody.volume;

      // Select high quality voice if available
      const voices = this.synth.getVoices();
      const preferred = voices.find(
        (v) =>
          v.lang.startsWith('en') &&
          (v.name.includes('Natural') ||
            v.name.includes('Google') ||
            v.name.includes('Samantha') ||
            v.name.includes('Alex') ||
            v.name.includes('Karen'))
      );
      if (preferred) utterance.voice = preferred;

      if (onEnd) utterance.onend = onEnd;
      this.synth.speak(utterance);
    } catch (e) {
      console.warn('TTS playback error:', e);
    }
  }

  public stopSpeaking() {
    if (this.synth) {
      this.synth.cancel();
    }
  }

  public nagStudent(reason: string = 'slouching'): string {
    const randomNag = NAG_PHRASES[Math.floor(Math.random() * NAG_PHRASES.length)];
    this.speak(randomNag, 'alert');
    return randomNag;
  }

  public getCurrentEmotion(): EmotionState {
    return this.currentEmotion;
  }

  public isSpeechRecognitionAvailable(): boolean {
    if (typeof window === 'undefined') return false;
    return !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);
  }

  public startListening(
    onResult: (transcript: string) => void,
    onStatusChange?: (listening: boolean) => void,
    onError?: (error: string) => void
  ) {
    const SpeechClass =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechClass) {
      if (onError) onError('Speech recognition not supported in this browser.');
      return;
    }

    try {
      if (this.recognition) {
        this.recognition.abort();
      }

      this.recognition = new SpeechClass();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'en-US';

      this.recognition.onstart = () => {
        this.isListening = true;
        if (onStatusChange) onStatusChange(true);
      };

      this.recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        onResult(transcript);
        this.isListening = false;
        if (onStatusChange) onStatusChange(false);
      };

      this.recognition.onerror = (e: any) => {
        console.warn('STT Error:', e.error);
        this.isListening = false;
        if (onStatusChange) onStatusChange(false);
        if (onError) onError(e.error);
      };

      this.recognition.onend = () => {
        this.isListening = false;
        if (onStatusChange) onStatusChange(false);
      };

      this.recognition.start();
    } catch (err: any) {
      this.isListening = false;
      if (onStatusChange) onStatusChange(false);
      if (onError) onError(err.message || 'STT failed to start');
    }
  }

  public stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }
}

export const audioEngine = new AudioEngine();
