export interface VisionMetrics {
  faceDetected: boolean;
  eyeOpenness: number; // 0.0 to 1.0
  neckAngle: number; // in degrees
  isSlouching: boolean;
  isDrowsy: boolean;
  engagementScore: number; // 0.0 to 1.0
  studentMood: 'focused' | 'drowsy' | 'distracted' | 'slouching' | 'absent';
  cameraSource: 'webcam' | 'virtual';
  errorMessage?: string;
}

export class VisionEngine {
  private videoElement: HTMLVideoElement | null = null;
  private canvasElement: HTMLCanvasElement | null = null;
  private stream: MediaStream | null = null;
  private isRunning: boolean = false;
  private animationFrameId: number | null = null;
  private cameraSource: 'webcam' | 'virtual' = 'virtual';
  private errorMessage: string = '';

  // Simulation state variables
  private simTargetAngle: number = 8.5;
  private simCurrentAngle: number = 8.5;
  private simTargetEye: number = 0.85;
  private simCurrentEye: number = 0.85;
  private simMood: 'focused' | 'drowsy' | 'distracted' | 'slouching' | 'absent' = 'focused';
  private simTime: number = 0;

  // Real camera baseline
  private baselineY: number = 0.40;

  public async startCamera(
    video: HTMLVideoElement,
    canvas: HTMLCanvasElement,
    onMetrics: (metrics: VisionMetrics) => void
  ): Promise<{ success: boolean; source: 'webcam' | 'virtual'; error?: string }> {
    this.videoElement = video;
    this.canvasElement = canvas;
    this.stopCamera();
    this.errorMessage = '';

    // First attempt real webcam
    let realStreamStarted = false;
    try {
      if (typeof navigator !== 'undefined' && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Try user facing camera
        let stream: MediaStream;
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
            audio: false,
          });
        } catch (e1) {
          // Fallback to basic video constraint
          stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }

        this.stream = stream;
        this.videoElement.srcObject = stream;
        this.videoElement.setAttribute('playsinline', 'true');
        this.videoElement.setAttribute('autoplay', 'true');
        this.videoElement.muted = true;

        await new Promise<void>((resolve) => {
          if (!this.videoElement) return resolve();
          this.videoElement.onloadedmetadata = () => {
            this.videoElement?.play().then(() => resolve()).catch(() => resolve());
          };
          // Timeout fallback
          setTimeout(resolve, 1200);
        });

        this.cameraSource = 'webcam';
        realStreamStarted = true;
      } else {
        throw new Error('Webcam API is not accessible in this browser context.');
      }
    } catch (err: any) {
      console.warn('Real webcam access not granted or unavailable:', err.name || err.message);
      this.cameraSource = 'virtual';
      this.errorMessage =
        err.name === 'NotAllowedError'
          ? 'Camera permission denied or blocked by iframe security policy.'
          : err.name === 'NotFoundError'
          ? 'No physical camera device found on this system.'
          : err.message || 'Unable to access physical camera.';
    }

    this.isRunning = true;
    this.renderLoop(onMetrics);

    return {
      success: realStreamStarted,
      source: this.cameraSource,
      error: this.errorMessage || undefined,
    };
  }

  public setVirtualPosture(angle: number, eyeOpenness: number, mood?: 'focused' | 'drowsy' | 'distracted' | 'slouching') {
    this.simTargetAngle = angle;
    this.simTargetEye = eyeOpenness;
    if (mood) this.simMood = mood;
  }

  public setCameraSource(source: 'webcam' | 'virtual', onMetrics: (metrics: VisionMetrics) => void) {
    this.cameraSource = source;
  }

  public getCameraSource(): 'webcam' | 'virtual' {
    return this.cameraSource;
  }

  public stopCamera() {
    this.isRunning = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
    if (this.videoElement) {
      this.videoElement.srcObject = null;
    }
  }

  public resetBaseline() {
    this.baselineY = 0.40;
    this.simTargetAngle = 8.5;
    this.simTargetEye = 0.85;
    this.simMood = 'focused';
  }

  private renderLoop(onMetrics: (metrics: VisionMetrics) => void) {
    if (!this.isRunning || !this.canvasElement) return;

    const canvas = this.canvasElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    let neckAngle = 8.5;
    let eyeOpenness = 0.85;
    let isSlouching = false;
    let isDrowsy = false;
    let engagementScore = 0.85;
    let studentMood: 'focused' | 'drowsy' | 'distracted' | 'slouching' | 'absent' = 'focused';

    if (this.cameraSource === 'webcam' && this.videoElement && this.videoElement.readyState >= 2) {
      // 1. REAL WEBCAM MODE
      ctx.save();
      // Mirror video horizontally
      ctx.translate(width, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(this.videoElement, 0, 0, width, height);
      ctx.restore();

      // Analyze pixel brightness & face position
      try {
        const frame = ctx.getImageData(0, 0, width, height);
        const data = frame.data;
        let skinPixels = 0;
        let sumY = 0;
        let eyeLumSum = 0;
        let eyeSamples = 0;

        for (let y = 0; y < height; y += 6) {
          for (let x = 0; x < width; x += 6) {
            const idx = (y * width + x) * 4;
            const r = data[idx];
            const g = data[idx + 1];
            const b = data[idx + 2];

            if (r > 60 && g > 40 && b > 20 && r > g && r > b) {
              skinPixels++;
              sumY += y;
            }

            if (y > height * 0.3 && y < height * 0.5 && x > width * 0.35 && x < width * 0.65) {
              eyeLumSum += 0.299 * r + 0.587 * g + 0.114 * b;
              eyeSamples++;
            }
          }
        }

        const faceDetected = skinPixels > (width * height) / 36 * 0.04;
        if (faceDetected) {
          const centerY = sumY / skinPixels;
          const normY = centerY / height;
          const diff = normY - this.baselineY;
          neckAngle = Math.max(5, Math.min(45, 8.5 + Math.max(0, diff * 55)));
          isSlouching = neckAngle > 22.0 || normY > 0.62;

          const eyeLum = eyeSamples > 0 ? eyeLumSum / eyeSamples : 120;
          eyeOpenness = Math.max(0.15, Math.min(1.0, 0.35 + (eyeLum / 255) * 0.65));
          isDrowsy = eyeOpenness < 0.42;

          if (isSlouching) {
            studentMood = 'slouching';
            engagementScore = 0.30;
          } else if (isDrowsy) {
            studentMood = 'drowsy';
            engagementScore = 0.25;
          } else {
            studentMood = 'focused';
            engagementScore = Math.min(0.95, 0.75 + eyeOpenness * 0.2);
          }
        } else {
          studentMood = 'absent';
          engagementScore = 0.15;
          neckAngle = 15;
        }
      } catch (e) {
        // Pixel reading might be restricted in some CORS situations
        neckAngle = 8.5;
        eyeOpenness = 0.85;
      }
    } else {
      // 2. VIRTUAL STUDENT CAMERA FEED
      this.simTime += 0.03;
      // Smooth interpolation
      this.simCurrentAngle += (this.simTargetAngle - this.simCurrentAngle) * 0.1;
      this.simCurrentEye += (this.simTargetEye - this.simCurrentEye) * 0.1;

      neckAngle = this.simCurrentAngle;
      eyeOpenness = this.simCurrentEye;
      isSlouching = neckAngle > 22.0;
      isDrowsy = eyeOpenness < 0.45;

      if (isSlouching) {
        studentMood = 'slouching';
        engagementScore = 0.25;
      } else if (isDrowsy) {
        studentMood = 'drowsy';
        engagementScore = 0.30;
      } else {
        studentMood = this.simMood;
        engagementScore = 0.88;
      }

      // Render realistic animated study desk & student avatar
      this.renderVirtualAvatar(ctx, width, height, neckAngle, eyeOpenness, isSlouching, isDrowsy);
    }

    // Render HUD Graphics & Landmark Overlays
    this.renderHUDOverlays(ctx, width, height, neckAngle, eyeOpenness, isSlouching, isDrowsy, studentMood);

    // Emit live metrics
    onMetrics({
      faceDetected: true,
      eyeOpenness,
      neckAngle,
      isSlouching,
      isDrowsy,
      engagementScore,
      studentMood,
      cameraSource: this.cameraSource,
      errorMessage: this.errorMessage,
    });

    this.animationFrameId = requestAnimationFrame(() => this.renderLoop(onMetrics));
  }

  private renderVirtualAvatar(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    angle: number,
    eye: number,
    isSlouching: boolean,
    isDrowsy: boolean
  ) {
    // Cyberpunk room background
    ctx.fillStyle = '#070b14';
    ctx.fillRect(0, 0, w, h);

    // Ambient back wall grid
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.08)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Study desk surface
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, h * 0.72, w, h * 0.28);
    ctx.strokeStyle = 'rgba(6, 182, 212, 0.3)';
    ctx.beginPath();
    ctx.moveTo(0, h * 0.72);
    ctx.lineTo(w, h * 0.72);
    ctx.stroke();

    // Laptop & textbook on desk
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(w * 0.32, h * 0.65, w * 0.36, h * 0.12);
    ctx.fillStyle = '#38bdf8';
    ctx.fillRect(w * 0.34, h * 0.67, w * 0.32, h * 0.08);

    // Compute student head position based on slouch neck angle
    // Higher neck angle drops the head downwards and shifts forward
    const headDrop = Math.max(0, (angle - 8.5) * 4.5);
    const headX = w / 2;
    const headY = h * 0.35 + headDrop;

    // Spine & Shoulders
    ctx.strokeStyle = isSlouching ? '#f59e0b' : '#38bdf8';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(headX, headY + 50); // neck
    ctx.lineTo(headX, h * 0.72); // spine
    ctx.stroke();

    // Shoulders
    ctx.beginPath();
    ctx.moveTo(headX - 70, headY + 70 + (isSlouching ? 15 : 0));
    ctx.lineTo(headX, headY + 50);
    ctx.lineTo(headX + 70, headY + 70 + (isSlouching ? 15 : 0));
    ctx.stroke();

    // Head circle / ellipse
    ctx.fillStyle = isSlouching ? '#451a03' : '#082f49';
    ctx.strokeStyle = isSlouching ? '#f59e0b' : '#38bdf8';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.ellipse(headX, headY, 48, 58, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Eyes
    const eyeY = headY - 8;
    const eyeH = Math.max(2, 10 * eye);
    ctx.fillStyle = isDrowsy ? '#ef4444' : '#22d3ee';

    // Left eye
    ctx.beginPath();
    ctx.ellipse(headX - 18, eyeY, 8, eyeH, 0, 0, Math.PI * 2);
    ctx.fill();

    // Right eye
    ctx.beginPath();
    ctx.ellipse(headX + 18, eyeY, 8, eyeH, 0, 0, Math.PI * 2);
    ctx.fill();

    // Eyebrows / expression
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    if (isSlouching || isDrowsy) {
      // drooping eyebrows
      ctx.beginPath();
      ctx.moveTo(headX - 25, eyeY - 14);
      ctx.lineTo(headX - 10, eyeY - 11);
      ctx.moveTo(headX + 10, eyeY - 11);
      ctx.lineTo(headX + 25, eyeY - 14);
      ctx.stroke();
    } else {
      // focused alert eyebrows
      ctx.beginPath();
      ctx.moveTo(headX - 25, eyeY - 12);
      ctx.lineTo(headX - 10, eyeY - 14);
      ctx.moveTo(headX + 10, eyeY - 14);
      ctx.lineTo(headX + 25, eyeY - 12);
      ctx.stroke();
    }
  }

  private renderHUDOverlays(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    angle: number,
    eye: number,
    isSlouching: boolean,
    isDrowsy: boolean,
    mood: string
  ) {
    // Targeting bracket color
    const color = isSlouching ? '#f59e0b' : isDrowsy ? '#ef4444' : '#06b6d4';

    // Corner brackets
    const boxX = w * 0.32;
    const boxY = h * 0.18 + (isSlouching ? (angle - 8.5) * 3 : 0);
    const boxW = w * 0.36;
    const boxH = h * 0.50;

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;

    const cornerSize = 20;
    // Top-left
    ctx.beginPath();
    ctx.moveTo(boxX, boxY + cornerSize);
    ctx.lineTo(boxX, boxY);
    ctx.lineTo(boxX + cornerSize, boxY);
    ctx.stroke();

    // Top-right
    ctx.beginPath();
    ctx.moveTo(boxX + boxW - cornerSize, boxY);
    ctx.lineTo(boxX + boxW, boxY);
    ctx.lineTo(boxX + boxW, boxY + cornerSize);
    ctx.stroke();

    // Bottom-left
    ctx.beginPath();
    ctx.moveTo(boxX, boxY + boxH - cornerSize);
    ctx.lineTo(boxX, boxY + boxH);
    ctx.lineTo(boxX + cornerSize, boxY + boxH);
    ctx.stroke();

    // Bottom-right
    ctx.beginPath();
    ctx.moveTo(boxX + boxW - cornerSize, boxY + boxH);
    ctx.lineTo(boxX + boxW, boxY + boxH);
    ctx.lineTo(boxX + boxW, boxY + boxH - cornerSize);
    ctx.stroke();

    // Center crosshair
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w / 2 - 12, h / 2);
    ctx.lineTo(w / 2 + 12, h / 2);
    ctx.moveTo(w / 2, h / 2 - 12);
    ctx.lineTo(w / 2, h / 2 + 12);
    ctx.stroke();

    // Posture line indicator
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillText(`θ = ${angle.toFixed(1)}°`, boxX + boxW + 8, boxY + 30);
    ctx.fillText(`EYE: ${Math.round(eye * 100)}%`, boxX + boxW + 8, boxY + 45);
    ctx.fillText(`MOOD: ${mood.toUpperCase()}`, boxX + boxW + 8, boxY + 60);

    // Source watermark
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillText(
      this.cameraSource === 'webcam' ? '● LIVE WEBCAM (640x480 30FPS)' : '● VIRTUAL AI PERCEPTION FEED',
      12,
      20
    );
  }
}

export const visionEngine = new VisionEngine();
