"""Upper-body posture and slouch detection from geometric landmarks.

Uses MediaPipe Pose when a camera is available. Classification is a transparent
rule on neck inclination and ear-to-shoulder vertical ratio — not a black-box
CNN — so the same function works on live frames and unit tests.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, Iterator, Optional, Tuple

import numpy as np

Landmark = Tuple[float, float]

# MediaPipe Pose landmark indices.
NOSE, LEFT_EAR, RIGHT_EAR = 0, 7, 8
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12


class PostureDetector:
    """Neck inclination + ear–shoulder ratio classifier (UPRIGHT vs SLOUCHING)."""

    def __init__(self, neck_angle_threshold: float = 15.0, ratio_threshold: float = 0.50):
        self.neck_angle_threshold = neck_angle_threshold
        self.ratio_threshold = ratio_threshold

    def calculate_angle(self, p1: Landmark, p2: Landmark) -> float:
        """Inclination of line p1→p2 from vertical, in degrees."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        if dy == 0:
            return 90.0
        return math.degrees(math.atan2(abs(dx), abs(dy)))

    def extract_features(
        self,
        nose: Landmark,
        l_ear: Landmark,
        r_ear: Landmark,
        l_shoulder: Landmark,
        r_shoulder: Landmark,
    ) -> np.ndarray:
        return np.array(
            [
                nose[0], nose[1],
                l_ear[0], l_ear[1], r_ear[0], r_ear[1],
                l_shoulder[0], l_shoulder[1], r_shoulder[0], r_shoulder[1],
            ],
            dtype=np.float32,
        )

    def process_landmarks(
        self,
        nose: Landmark,
        l_ear: Landmark,
        r_ear: Landmark,
        l_shoulder: Landmark,
        r_shoulder: Landmark,
    ) -> Dict[str, Any]:
        mid_ear = ((l_ear[0] + r_ear[0]) / 2.0, (l_ear[1] + r_ear[1]) / 2.0)
        mid_shoulder = (
            (l_shoulder[0] + r_shoulder[0]) / 2.0,
            (l_shoulder[1] + r_shoulder[1]) / 2.0,
        )
        neck_angle = self.calculate_angle(mid_shoulder, mid_ear)
        vert_dist = abs(mid_shoulder[1] - mid_ear[1])
        shoulder_width = math.hypot(r_shoulder[0] - l_shoulder[0], r_shoulder[1] - l_shoulder[1])
        ratio = vert_dist / max(0.01, shoulder_width)
        is_slouching = neck_angle > self.neck_angle_threshold or ratio < self.ratio_threshold
        confidence = min(
            1.0,
            max(0.1, (neck_angle / 30.0) * 0.5 + (1.0 - min(1.0, ratio / 0.6)) * 0.5),
        )
        return {
            "posture": "SLOUCHING" if is_slouching else "UPRIGHT",
            "is_slouching": is_slouching,
            "neck_angle": round(neck_angle, 1),
            "vert_ratio": round(ratio, 2),
            "confidence": round(confidence, 2),
            "features": self.extract_features(nose, l_ear, r_ear, l_shoulder, r_shoulder),
        }

    def process_pose_landmarks(self, landmarks) -> Optional[Dict[str, Any]]:
        """Accept MediaPipe Pose landmark list (normalized x, y)."""
        try:
            def xy(index: int) -> Landmark:
                point = landmarks[index]
                return (float(point.x), float(point.y))

            return self.process_landmarks(
                xy(NOSE), xy(LEFT_EAR), xy(RIGHT_EAR), xy(LEFT_SHOULDER), xy(RIGHT_SHOULDER)
            )
        except (IndexError, AttributeError, TypeError):
            return None


def fusion_penalty(posture: Optional[Dict[str, Any]]) -> float:
    """Subtract from face engagement when the student is slouching (0.0–0.25)."""
    if not posture:
        return 0.0
    if not posture.get("is_slouching"):
        return 0.0
    strength = min(1.0, float(posture.get("neck_angle", 0.0)) / 35.0)
    return round(0.10 + 0.15 * strength, 3)


def synthetic_posture_frames() -> Iterator[Tuple[Landmark, Landmark, Landmark, Landmark, Landmark]]:
    yield (0.5, 0.3), (0.4, 0.3), (0.6, 0.3), (0.35, 0.6), (0.65, 0.6)
    yield (0.55, 0.52), (0.45, 0.52), (0.65, 0.52), (0.35, 0.6), (0.65, 0.6)


def analyze_frame_bgr(frame, detector: Optional[PostureDetector] = None) -> Optional[Dict[str, Any]]:
    """Run MediaPipe Pose on a BGR OpenCV frame. Returns None if pose is missing."""
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        return None

    detector = detector or PostureDetector()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    with mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=0,
        min_detection_confidence=0.5,
    ) as pose:
        result = pose.process(rgb)
    if not result.pose_landmarks:
        return None
    return detector.process_pose_landmarks(result.pose_landmarks.landmark)


if __name__ == "__main__":
    detector = PostureDetector()
    print("--- Posture Detection ---")
    for i, frame in enumerate(synthetic_posture_frames(), 1):
        res = detector.process_landmarks(*frame)
        print(
            f"Frame {i}: Posture={res['posture']} | Neck={res['neck_angle']} deg "
            f"| Vert Ratio={res['vert_ratio']} | Conf={res['confidence']}"
        )
    print(f"(wall time {time.time():.0f})")
