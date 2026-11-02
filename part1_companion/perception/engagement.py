"""Face-engagement perception: EAR + yaw → smoothed E_t, fused with posture."""
from __future__ import annotations

import argparse
import asyncio
import math
import time
from collections import deque
from typing import Generator, Optional, Tuple

from integration.event_bus import bus
from integration.schemas import EngagementUpdate, TOPIC_ENGAGEMENT
from part1_companion.perception.posture import PostureDetector, fusion_penalty

# Face Mesh landmark indices (MediaPipe).
LEFT_EYE = (33, 133, 159, 145)   # outer, inner, top, bottom
RIGHT_EYE = (362, 263, 386, 374)
NOSE_TIP = 1


class EngagementPerception:
    """Rolling 2 s mean of per-frame engagement (10 samples at 5 Hz)."""

    def __init__(self, buffer_duration_sec: float = 2.0, publish_rate_hz: float = 5.0):
        self.publish_rate_hz = publish_rate_hz
        self.interval_sec = 1.0 / publish_rate_hz
        self.buffer_capacity = int(buffer_duration_sec * publish_rate_hz)
        self.ring_buffer: deque[float] = deque(maxlen=self.buffer_capacity)

    def process_frame(self, face_detected: bool, raw_engagement: Optional[float]) -> Optional[float]:
        if not face_detected or raw_engagement is None:
            return None
        clamped_val = max(0.0, min(1.0, float(raw_engagement)))
        self.ring_buffer.append(clamped_val)
        return round(sum(self.ring_buffer) / len(self.ring_buffer), 3)

    @staticmethod
    def compute_engagement_score(eye_open_ratio: float, face_yaw_ratio: float) -> float:
        """EAR around 0.20–0.35 and near-zero yaw → high engagement."""
        eye_score = max(0.0, min(1.0, (float(eye_open_ratio) - 0.12) / 0.13))
        forward_score = max(0.0, min(1.0, 1.0 - float(face_yaw_ratio) / 0.45))
        return round(0.60 * eye_score + 0.40 * forward_score, 3)

    def fuse_with_posture(self, face_score: float, posture: Optional[dict]) -> float:
        return round(max(0.0, min(1.0, face_score - fusion_penalty(posture))), 3)

    def classify_emotion(self, e_t: float, is_slouching: bool = False) -> str:
        if is_slouching and e_t < 0.55:
            return "bored"
        if e_t >= 0.70:
            return "engaged"
        if e_t >= 0.45:
            return "confused"
        if e_t >= 0.30:
            return "distracted"
        return "frustrated"


class EngagementTracker(EngagementPerception):
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
        self.posture = PostureDetector()
        self.last_posture: Optional[dict] = None

    async def run(self, duration_s: float = 10.0, sim: bool = True):
        start_time = time.time()
        if sim:
            trace = synthetic_trace_generator()
            for face_detected, raw_val in trace:
                if duration_s > 0 and (time.time() - start_time) > duration_s:
                    break
                smoothed_E_t = self.process_frame(face_detected, raw_val)
                if smoothed_E_t is not None:
                    await bus.publish(
                        TOPIC_ENGAGEMENT,
                        EngagementUpdate(
                            E_t=smoothed_E_t,
                            emotion=self.classify_emotion(smoothed_E_t),
                        ),
                    )
                await asyncio.sleep(self.interval_sec)
        else:
            await self._run_live_camera(duration_s)

    async def _run_live_camera(self, duration_s: float) -> None:
        try:
            import cv2
            import mediapipe as mp
        except Exception as exc:
            raise RuntimeError("Live perception requires opencv-python and mediapipe.") from exc

        camera = cv2.VideoCapture(self.camera_index)
        if not camera.isOpened():
            raise RuntimeError(f"Could not open camera index {self.camera_index}.")

        started = time.monotonic()
        face_mesh_api = mp.solutions.face_mesh
        pose_api = mp.solutions.pose
        try:
            with face_mesh_api.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            ) as detector, pose_api.Pose(
                static_image_mode=False,
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            ) as pose:
                while duration_s <= 0 or time.monotonic() - started < duration_s:
                    ok, frame = camera.read()
                    if not ok:
                        await asyncio.sleep(self.interval_sec)
                        continue
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    face_result = detector.process(rgb)
                    pose_result = pose.process(rgb)
                    posture = None
                    if pose_result.pose_landmarks:
                        posture = self.posture.process_pose_landmarks(pose_result.pose_landmarks.landmark)
                        self.last_posture = posture

                    if not face_result.multi_face_landmarks:
                        await asyncio.sleep(self.interval_sec)
                        continue

                    landmarks = face_result.multi_face_landmarks[0].landmark

                    def distance(a: int, b: int) -> float:
                        return math.hypot(landmarks[a].x - landmarks[b].x, landmarks[a].y - landmarks[b].y)

                    left_ear = distance(LEFT_EYE[2], LEFT_EYE[3]) / max(distance(LEFT_EYE[0], LEFT_EYE[1]), 1e-6)
                    right_ear = distance(RIGHT_EYE[2], RIGHT_EYE[3]) / max(distance(RIGHT_EYE[0], RIGHT_EYE[1]), 1e-6)
                    eye_ratio = (left_ear + right_ear) / 2.0
                    eye_mid_x = (landmarks[LEFT_EYE[0]].x + landmarks[RIGHT_EYE[0]].x) / 2.0
                    eye_width = max(distance(LEFT_EYE[0], RIGHT_EYE[0]), 1e-6)
                    yaw_ratio = abs(landmarks[NOSE_TIP].x - eye_mid_x) / eye_width
                    face_score = self.compute_engagement_score(eye_ratio, yaw_ratio)
                    fused = self.fuse_with_posture(face_score, posture)
                    smoothed = self.process_frame(True, fused)
                    if smoothed is not None:
                        slouching = bool(posture and posture.get("is_slouching"))
                        await bus.publish(
                            TOPIC_ENGAGEMENT,
                            EngagementUpdate(
                                E_t=smoothed,
                                emotion=self.classify_emotion(smoothed, slouching),
                                posture=(posture or {}).get("posture", "UPRIGHT"),
                                neck_angle=(posture or {}).get("neck_angle", 0.0),
                                is_slouching=slouching,
                            ),
                        )
                    await asyncio.sleep(self.interval_sec)
        finally:
            camera.release()


def synthetic_trace_generator() -> Generator[Tuple[bool, Optional[float]], None, None]:
    """Deterministic lab trace used when no camera is attached."""
    for _ in range(10):
        yield True, 0.85
    dip_sequence = [
        (True, 0.20), (True, 0.20),
        (True, 0.85), (True, 0.85),
        (True, 0.15), (True, 0.15),
        (True, 0.80), (True, 0.80),
        (True, 0.25), (True, 0.25),
        (True, 0.85), (True, 0.85),
    ]
    for frame in dip_sequence:
        yield frame
    for _ in range(10):
        yield False, None
    for _ in range(20):
        yield True, 0.20
    for _ in range(10):
        yield True, 0.85


def run_perception(sim_mode: bool = False, low_threshold: float = 0.40):
    perception = EngagementPerception(buffer_duration_sec=2.0, publish_rate_hz=5.0)
    print(f"--- Starting Engagement Perception Node (sim_mode={sim_mode}) ---")
    if sim_mode:
        for tick, (face_detected, raw_val) in enumerate(synthetic_trace_generator(), 1):
            timestamp = tick * perception.interval_sec
            smoothed_E_t = perception.process_frame(face_detected, raw_val)
            if smoothed_E_t is None:
                status = "STATUS: NO FACE (Unknown) -> Skip publishing"
            else:
                flag = "LOW ENGAGEMENT" if smoothed_E_t < low_threshold else "WATCHING"
                status = f"E_t (Smoothed): {smoothed_E_t:.3f} | Raw: {raw_val:.2f} | State: {flag}"
            print(f"[{timestamp:04.1f}s] {status}")
            time.sleep(perception.interval_sec)
    else:
        asyncio.run(EngagementTracker().run(duration_s=0.0, sim=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Engagement Perception Node")
    parser.add_argument("--sim", action="store_true", help="Synthetic trace (no camera)")
    parser.add_argument("--threshold", type=float, default=0.40)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--duration", type=float, default=0.0)
    args = parser.parse_args()
    if args.sim:
        run_perception(sim_mode=True, low_threshold=args.threshold)
    else:
        asyncio.run(
            EngagementTracker(camera_index=args.camera_index).run(duration_s=args.duration, sim=False)
        )
