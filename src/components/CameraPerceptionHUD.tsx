import React, { useRef, useState, useEffect } from 'react';
import { VisionMetrics, visionEngine } from '../logic/visionEngine';
import { audioEngine } from '../logic/audioEngine';
import {
  Camera,
  Eye,
  AlertTriangle,
  UserCheck,
  Volume2,
  RefreshCw,
  Sparkles,
  Sliders,
  Info,
} from 'lucide-react';

interface CameraPerceptionHUDProps {
  onMetricsUpdate: (metrics: VisionMetrics) => void;
  onNagTriggered: (phrase: string) => void;
}

export const CameraPerceptionHUD: React.FC<CameraPerceptionHUDProps> = ({
  onMetricsUpdate,
  onNagTriggered,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [cameraSource, setCameraSource] = useState<'webcam' | 'virtual'>('virtual');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [autoNagEnabled, setAutoNagEnabled] = useState<boolean>(true);

  const [currentMetrics, setCurrentMetrics] = useState<VisionMetrics>({
    faceDetected: true,
    eyeOpenness: 0.85,
    neckAngle: 8.5,
    isSlouching: false,
    isDrowsy: false,
    engagementScore: 0.85,
    studentMood: 'focused',
    cameraSource: 'virtual',
  });

  const [lastNagTime, setLastNagTime] = useState<number>(0);
  const [consecutiveBadFrames, setConsecutiveBadFrames] = useState<number>(0);

  // Start perception engine
  const startPerception = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const res = await visionEngine.startCamera(
      videoRef.current,
      canvasRef.current,
      (metrics) => {
        setCurrentMetrics(metrics);
        setCameraSource(metrics.cameraSource);
        if (metrics.errorMessage) {
          setErrorMessage(metrics.errorMessage);
        }
        onMetricsUpdate(metrics);

        // Auto-Nagging Evaluation
        const isDegraded = metrics.isSlouching || metrics.isDrowsy || metrics.engagementScore < 0.40;

        if (isDegraded) {
          setConsecutiveBadFrames((prev) => {
            const next = prev + 1;
            const now = Date.now();
            if (next >= 12 && autoNagEnabled && now - lastNagTime > 12000) {
              const phrase = audioEngine.nagStudent(
                metrics.isSlouching ? 'slouching' : metrics.isDrowsy ? 'drowsy' : 'disengaged'
              );
              onNagTriggered(phrase);
              setLastNagTime(now);
              return 0;
            }
            return next;
          });
        } else {
          setConsecutiveBadFrames(0);
        }
      }
    );

    setCameraSource(res.source);
    if (res.error) setErrorMessage(res.error);
  };

  useEffect(() => {
    startPerception();
    return () => {
      visionEngine.stopCamera();
    };
  }, []);

  const handleTogglePhysicalCamera = async () => {
    setErrorMessage('');
    await startPerception();
  };

  const handleSimulatePosture = (
    angle: number,
    eye: number,
    mood: 'focused' | 'drowsy' | 'distracted' | 'slouching'
  ) => {
    visionEngine.setVirtualPosture(angle, eye, mood);
  };

  const handleManualNag = () => {
    const phrase = audioEngine.nagStudent('manual');
    onNagTriggered(phrase);
  };

  const eyePct = Math.round(currentMetrics.eyeOpenness * 100);

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm space-y-4">
      {/* Top Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
        <div className="flex items-center gap-2.5">
          <Camera className="w-5 h-5 text-indigo-600" />
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Computer Vision &amp; Posture Sensing HUD
            </h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border uppercase ${
                  cameraSource === 'webcam'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-indigo-50 text-indigo-700 border-indigo-200'
                }`}
              >
                ● {cameraSource === 'webcam' ? 'Physical Webcam Live' : 'Virtual AI Perception Stream'}
              </span>
              <span className="text-[11px] text-slate-400 font-mono">30 FPS Active</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setAutoNagEnabled(!autoNagEnabled)}
            className={`text-xs px-2.5 py-1.5 rounded-lg border font-semibold flex items-center gap-1.5 transition-colors shadow-sm ${
              autoNagEnabled
                ? 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100'
                : 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100'
            }`}
            title="Auto-Nag activates robot voice TTS when posture or eye openness drops"
          >
            <Volume2 className="w-3.5 h-3.5" />
            <span>{autoNagEnabled ? 'Auto-Nag Armed' : 'Auto-Nag Off'}</span>
          </button>

          <button
            onClick={handleTogglePhysicalCamera}
            className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-all flex items-center gap-1.5 shadow-sm"
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Connect Physical Camera</span>
          </button>
        </div>
      </div>

      {/* Info notice if physical webcam is blocked by iframe */}
      {errorMessage && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold text-slate-800 block">Browser/Iframe Policy Notice:</span>
            <span>
              {errorMessage} — The perception engine has automatically engaged the{' '}
              <strong>Virtual AI Sensing Stream</strong> with live animated posture tracking, eye-opening meters, and TTS auto-nagging.
            </span>
          </div>
        </div>
      )}

      {/* Viewport: Live Canvas HUD with real webcam or virtual student avatar */}
      <div className="relative aspect-video bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-md flex items-center justify-center">
        {/* Hidden video element supplying real webcam frames to canvas */}
        <video
          ref={videoRef}
          playsInline
          autoPlay
          muted
          className="hidden"
        />

        {/* Live Canvas Feed */}
        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          className="w-full h-full object-cover"
        />

        {/* Live HUD Floating Indicators */}
        <div className="absolute top-3 right-3 flex items-center gap-2 pointer-events-none">
          <span
            className={`text-[11px] font-mono font-bold px-2.5 py-1 rounded-lg backdrop-blur-md border ${
              currentMetrics.isSlouching
                ? 'bg-amber-500/80 text-white border-amber-400 animate-pulse'
                : currentMetrics.isDrowsy
                ? 'bg-rose-500/80 text-white border-rose-400 animate-pulse'
                : 'bg-black/60 text-emerald-400 border-emerald-500/30'
            }`}
          >
            {currentMetrics.studentMood.toUpperCase()}
          </span>

          <span className="text-[11px] font-mono px-2 py-1 rounded-lg bg-black/60 text-white border border-white/10 backdrop-blur-md">
            E_t: {currentMetrics.engagementScore.toFixed(2)}
          </span>
        </div>

        {/* Bottom Alert Banner */}
        {(currentMetrics.isSlouching || currentMetrics.isDrowsy) && (
          <div className="absolute bottom-3 left-3 right-3 bg-amber-500 text-slate-950 font-bold text-xs py-2 px-3 rounded-lg flex items-center justify-between shadow-xl animate-bounce pointer-events-none">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              <span>
                {currentMetrics.isSlouching
                  ? 'SLOUCH DETECTED: Neck angle θ exceeds 22° threshold!'
                  : 'DROWSINESS ALERT: Eye-opening level dropped below 45%!'}
              </span>
            </div>
            <span className="text-[10px] font-mono bg-black/20 px-2 py-0.5 rounded">
              TTS Nag Armed ({consecutiveBadFrames}/12)
            </span>
          </div>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
        {/* Eye opening */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="flex items-center gap-1.5 font-medium">
              <Eye className="w-4 h-4 text-indigo-600" />
              Eye Opening Level
            </span>
            <span className="font-mono text-xs font-bold text-slate-900">{eyePct}%</span>
          </div>
          <div className="text-base font-bold font-mono">
            {currentMetrics.isDrowsy ? (
              <span className="text-rose-600">Drowsy / Closed Eyelids</span>
            ) : (
              <span className="text-emerald-600">Alert &amp; Attentive</span>
            )}
          </div>
          <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden mt-2">
            <div
              className={`h-full transition-all duration-300 ${
                currentMetrics.isDrowsy ? 'bg-rose-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${eyePct}%` }}
            ></div>
          </div>
        </div>

        {/* Neck Angle */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="flex items-center gap-1.5 font-medium">
              <UserCheck className="w-4 h-4 text-indigo-600" />
              Neck Angle (&theta;)
            </span>
            <span className="font-mono text-[10px] text-slate-400">&gt;22° = Slouch</span>
          </div>
          <div className="text-base font-bold font-mono">
            <span
              className={
                currentMetrics.isSlouching ? 'text-amber-600' : 'text-slate-900'
              }
            >
              {currentMetrics.neckAngle.toFixed(1)}°
            </span>{' '}
            <span className="text-[11px] text-slate-400 font-normal">
              {currentMetrics.isSlouching ? '(Slouching)' : '(Upright)'}
            </span>
          </div>
          <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden mt-2">
            <div
              className={`h-full transition-all duration-300 ${
                currentMetrics.isSlouching ? 'bg-amber-500' : 'bg-indigo-500'
              }`}
              style={{ width: `${Math.min(100, (currentMetrics.neckAngle / 45) * 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Mood & Posture */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="font-medium">Student Mood Status</span>
            <button
              onClick={() => visionEngine.resetBaseline()}
              className="text-[10px] text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1 transition-colors"
            >
              <RefreshCw className="w-3 h-3" /> Calibrate
            </button>
          </div>
          <div className="font-bold text-sm">
            <span
              className={`px-2 py-0.5 rounded-full border text-xs font-mono uppercase ${
                currentMetrics.studentMood === 'focused'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : currentMetrics.studentMood === 'slouching'
                  ? 'bg-amber-50 text-amber-800 border-amber-200'
                  : 'bg-rose-50 text-rose-700 border-rose-200'
              }`}
            >
              {currentMetrics.studentMood}
            </span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1 block">
            MediaPipe Pose &amp; Ocular Contrast Model
          </span>
        </div>
      </div>

      {/* Interactive Posture Scenario Switches */}
      <div className="pt-3 border-t border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-indigo-600" />
            Simulate Posture Scenarios (Triggers Vision &amp; Auto-Nag):
          </span>
          <button
            onClick={handleManualNag}
            className="text-xs px-2.5 py-1 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 transition-colors font-medium flex items-center gap-1 shadow-sm"
          >
            <Sparkles className="w-3 h-3 text-amber-600" />
            <span>Test Voice Nag</span>
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <button
            onClick={() => handleSimulatePosture(8.5, 0.85, 'focused')}
            className="py-2 px-3 rounded-xl text-xs font-semibold bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-all text-center flex flex-col items-center justify-center gap-0.5 shadow-sm"
          >
            <span>Sit Upright (8.5°)</span>
            <span className="text-[10px] text-emerald-600 font-medium">Focused &amp; Alert</span>
          </button>

          <button
            onClick={() => handleSimulatePosture(32.5, 0.80, 'slouching')}
            className="py-2 px-3 rounded-xl text-xs font-semibold bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 transition-all text-center flex flex-col items-center justify-center gap-0.5 shadow-sm"
          >
            <span>Slouch Forward (32.5°)</span>
            <span className="text-[10px] text-amber-600 font-medium">Slouch Nag Alert</span>
          </button>

          <button
            onClick={() => handleSimulatePosture(18.0, 0.22, 'drowsy')}
            className="py-2 px-3 rounded-xl text-xs font-semibold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition-all text-center flex flex-col items-center justify-center gap-0.5 shadow-sm"
          >
            <span>Drowsy Eyes (22%)</span>
            <span className="text-[10px] text-rose-600 font-medium">Sleepiness Alert</span>
          </button>

          <button
            onClick={() => handleSimulatePosture(15.0, 0.65, 'distracted')}
            className="py-2 px-3 rounded-xl text-xs font-semibold bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-all text-center flex flex-col items-center justify-center gap-0.5 shadow-sm"
          >
            <span>Look Away</span>
            <span className="text-[10px] text-slate-500 font-medium">Distraction Alert</span>
          </button>
        </div>
      </div>
    </div>
  );
};
