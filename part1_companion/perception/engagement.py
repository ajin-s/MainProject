import argparse
import asyncio
import math
import time
from collections import deque
from typing import Generator, Optional, Tuple

from integration.event_bus import bus
from integration.schemas import EngagementUpdate, TOPIC_ENGAGEMENT


class EngagementPerception:
    """
    Processes raw frame engagement inputs into a smoothed, trustworthy E_t signal.
    
    Maintains a 2-second ring buffer (10 elements at 5 Hz) and publishes the rolling mean.
    If no face is detected, treats state as 'unknown' rather than E_t = 0.
    """

    def __init__(self, buffer_duration_sec: float = 2.0, publish_rate_hz: float = 5.0):
        self.publish_rate_hz = publish_rate_hz
        self.interval_sec = 1.0 / publish_rate_hz
        self.buffer_capacity = int(buffer_duration_sec * publish_rate_hz)
        self.ring_buffer = deque(maxlen=self.buffer_capacity)

    def process_frame(self, face_detected: bool, raw_engagement: Optional[float]) -> Optional[float]:
        """
        Process a single frame.

        Args:
            face_detected: True if a student's face is in frame.
            raw_engagement: Instantaneous engagement value in range [0.0, 1.0] if face is present.

        Returns:
            Smoothed E_t (float) if face is detected, or None if face is missing/unknown.
        """
        if not face_detected or raw_engagement is None:
            return None

        clamped_val = max(0.0, min(1.0, float(raw_engagement)))
        self.ring_buffer.append(clamped_val)

        smoothed_E_t = sum(self.ring_buffer) / len(self.ring_buffer)
        return round(smoothed_E_t, 3)

    @staticmethod
    def compute_engagement_score(eye_open_ratio: float, face_yaw_ratio: float) -> float:
        """Convert face-landmark measurements into a transparent 0–1 engagement score.

        ``eye_open_ratio`` is an Eye Aspect Ratio (EAR); values around 0.20–0.35
        are typical for open eyes. ``face_yaw_ratio`` is nose displacement from the
        midpoint of both eyes, normalized by eye width (0 means face-forward).
        The heuristic is deliberately simple and deterministic for on-device use.
        """
        eye_score = max(0.0, min(1.0, (float(eye_open_ratio) - 0.12) / 0.13))
        forward_score = max(0.0, min(1.0, 1.0 - float(face_yaw_ratio) / 0.45))
        return round(0.60 * eye_score + 0.40 * forward_score, 3)

    def classify_emotion(self, e_t: float) -> str:
        if e_t >= 0.70:
            return "engaged"
        elif e_t >= 0.45:
            return "confused"
        elif e_t >= 0.30:
            return "distracted"
        else:
            return "frustrated"


class EngagementTracker(EngagementPerception):
    """
    Runner wrapper compatible with demo scripts, publishing to EventBus.
    """

    def __init__(
        self,
        camera_index: int = 0,
        model_path: Optional[str] = None,
        buffer_duration_sec: float = 2.0,
        publish_rate_hz: float = 5.0,
    ):
        super().__init__(buffer_duration_sec, publish_rate_hz)
        self.camera_index = camera_index
        self.model_path = model_path

    async def run(self, duration_s: float = 10.0, sim: bool = True):
        start_time = time.time()
        if sim:
            trace = synthetic_trace_generator()
            for face_detected, raw_val in trace:
                if duration_s > 0 and (time.time() - start_time) > duration_s:
                    break

                smoothed_E_t = self.process_frame(face_detected, raw_val)
                if smoothed_E_t is not None:
                    emotion = self.classify_emotion(smoothed_E_t)
                    update = EngagementUpdate(E_t=smoothed_E_t, emotion=emotion)
                    await bus.publish(TOPIC_ENGAGEMENT, update)

                await asyncio.sleep(self.interval_sec)
        else:
            await self._run_live_camera(duration_s)

    async def _run_live_camera(self, duration_s: float) -> None:
        """Read webcam frames with MediaPipe Face Mesh and publish smoothed E_t."""
        try:
            import cv2
            import mediapipe as mp
            face_mesh_api = mp.solutions.face_mesh
        except Exception as exc:
            raise RuntimeError("Live perception requires opencv-python and mediapipe.") from exc

        camera = cv2.VideoCapture(self.camera_index)
        if not camera.isOpened():
            raise RuntimeError(f"Could not open camera index {self.camera_index}.")

        # FaceMesh landmark indices: eye corners/top/bottom and nose tip.
        left = (33, 133, 159, 145)
        right = (362, 263, 386, 374)
        started = time.monotonic()
        try:
            with face_mesh_api.FaceMesh(
                static_image_mode=False, max_num_faces=1, refine_landmarks=True,
                min_detection_confidence=0.5, min_tracking_confidence=0.5,
            ) as detector:
                while duration_s <= 0 or time.monotonic() - started < duration_s:
                    ok, frame = camera.read()
                    if not ok:
                        await asyncio.sleep(self.interval_sec)
                        continue
                    result = detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    if not result.multi_face_landmarks:
                        # Deliberately do not publish a zero: the student may have stepped away.
                        await asyncio.sleep(self.interval_sec)
                        continue
                    landmarks = result.multi_face_landmarks[0].landmark

                    def distance(a: int, b: int) -> float:
                        return math.hypot(landmarks[a].x - landmarks[b].x, landmarks[a].y - landmarks[b].y)

                    left_ear = distance(left[2], left[3]) / max(distance(left[0], left[1]), 1e-6)
                    right_ear = distance(right[2], right[3]) / max(distance(right[0], right[1]), 1e-6)
                    eye_ratio = (left_ear + right_ear) / 2.0
                    eye_mid_x = (landmarks[left[0]].x + landmarks[right[0]].x) / 2.0
                    eye_width = max(distance(left[0], right[0]), 1e-6)
                    yaw_ratio = abs(landmarks[1].x - eye_mid_x) / eye_width
                    smoothed = self.process_frame(True, self.compute_engagement_score(eye_ratio, yaw_ratio))
                    if smoothed is not None:
                        await bus.publish(TOPIC_ENGAGEMENT, EngagementUpdate(
                            E_t=smoothed, emotion=self.classify_emotion(smoothed)
                        ))
                    await asyncio.sleep(self.interval_sec)
        finally:
            camera.release()


def synthetic_trace_generator() -> Generator[Tuple[bool, Optional[float]], None, None]:
    """Yields a scripted sequence of (face_detected, raw_engagement) frames."""
    # 1. Steady engaged state (10 ticks = 2s)
    for _ in range(10):
        yield True, 0.85

    # 2. Three sub-second dips (0.4s each, should NOT trigger intervention when smoothed)
    dip_sequence = [
        (True, 0.20), (True, 0.20),  # Dip 1
        (True, 0.85), (True, 0.85),  # Recovery
        (True, 0.15), (True, 0.15),  # Dip 2
        (True, 0.80), (True, 0.80),  # Recovery
        (True, 0.25), (True, 0.25),  # Dip 3
        (True, 0.85), (True, 0.85),  # Recovery
    ]
    for frame in dip_sequence:
        yield frame

    # 3. Student stands up / steps away ("no face in frame")
    for _ in range(10):
        yield False, None

    # 4. Sustained low engagement stretch (20 ticks = 4s at 0.20 -> SHOULD trigger intervention)
    for _ in range(20):
        yield True, 0.20

    # 5. Recovery back to normal engagement
    for _ in range(10):
        yield True, 0.85


def run_perception(sim_mode: bool = False, low_threshold: float = 0.40):
    perception = EngagementPerception(buffer_duration_sec=2.0, publish_rate_hz=5.0)

    print(f"--- Starting Engagement Perception Node (sim_mode={sim_mode}) ---")
    print("Publishing smoothed E_t at 5 Hz...\n")

    if sim_mode:
        trace = synthetic_trace_generator()
        tick = 0
        for face_detected, raw_val in trace:
            tick += 1
            timestamp = tick * perception.interval_sec
            smoothed_E_t = perception.process_frame(face_detected, raw_val)

            if smoothed_E_t is None:
                status = "STATUS: NO FACE (Unknown) -> Skip publishing"
            else:
                is_low = smoothed_E_t < low_threshold
                state_flag = "LOW ENGAGEMENT" if is_low else "WATCHING"
                status = f"E_t (Smoothed): {smoothed_E_t:.3f} | Raw: {raw_val:.2f} | State: {state_flag}"

            print(f"[{timestamp:04.1f}s] {status}")
            time.sleep(perception.interval_sec)
    else:
        print("Live camera mode selected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Engagement Perception Node")
    parser.add_argument("--sim", action="store_true", help="Run in simulation mode with synthetic trace")
    parser.add_argument("--threshold", type=float, default=0.40, help="Low engagement threshold")
    parser.add_argument("--model-path", type=str, default=None, help="Path to face model")
    parser.add_argument("--camera-index", type=int, default=0, help="Camera index")
    parser.add_argument("--duration", type=float, default=0.0, help="Run duration in seconds")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    if args.sim:
        run_perception(sim_mode=True, low_threshold=args.threshold)
    else:
        asyncio.run(EngagementTracker(camera_index=args.camera_index, model_path=args.model_path).run(
            duration_s=args.duration, sim=False
        ))
