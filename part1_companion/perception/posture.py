"""
Computer Vision Posture Recognition & Slouch Detection Module for SmartEduSync.
Uses MediaPipe Pose / Facial-Upper Body landmarks and geometric inclination angles / CNN classifier
to detect whether a student is sitting UPRIGHT or SLOUCHING.
"""
import math
import numpy as np
from typing import Dict, Any, Optional, Tuple


class PostureDetector:
    """
    Computes neck inclination angle, ear-to-shoulder vertical ratio, and classifies slouching.
    """

    def __init__(self, neck_angle_threshold: float = 15.0, ratio_threshold: float = 0.50):
        self.neck_angle_threshold = neck_angle_threshold
        self.ratio_threshold = ratio_threshold

    def calculate_angle(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculates inclination angle of line p1-p2 relative to vertical (in degrees)."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        if dy == 0:
            return 90.0
        angle_rad = math.atan2(abs(dx), abs(dy))
        return math.degrees(angle_rad)

    def extract_features(
        self,
        nose: Tuple[float, float],
        l_ear: Tuple[float, float],
        r_ear: Tuple[float, float],
        l_shoulder: Tuple[float, float],
        r_shoulder: Tuple[float, float],
    ) -> np.ndarray:
        """Extracts normalized 10D keypoint feature vector for CNN classification."""
        return np.array([
            nose[0], nose[1],
            l_ear[0], l_ear[1], r_ear[0], r_ear[1],
            l_shoulder[0], l_shoulder[1], r_shoulder[0], r_shoulder[1]
        ], dtype=np.float32)

    def process_landmarks(
        self,
        nose: Tuple[float, float],
        l_ear: Tuple[float, float],
        r_ear: Tuple[float, float],
        l_shoulder: Tuple[float, float],
        r_shoulder: Tuple[float, float],
    ) -> Dict[str, Any]:
        """
        Analyzes upper-body keypoints to compute postural metrics and slouch classification.
        Keypoints expected as normalized (x, y) coordinates in range [0.0, 1.0].
        """
        mid_ear = ((l_ear[0] + r_ear[0]) / 2.0, (l_ear[1] + r_ear[1]) / 2.0)
        mid_shoulder = ((l_shoulder[0] + r_shoulder[0]) / 2.0, (l_shoulder[1] + r_shoulder[1]) / 2.0)

        # 1. Neck Inclination Angle
        neck_angle = self.calculate_angle(mid_shoulder, mid_ear)

        # 2. Ear to Shoulder Vertical Distance Ratio
        vert_dist = abs(mid_shoulder[1] - mid_ear[1])
        shoulder_width = math.hypot(r_shoulder[0] - l_shoulder[0], r_shoulder[1] - l_shoulder[1])
        ratio = vert_dist / max(0.01, shoulder_width)

        # 3. Posture Classification
        is_slouching = neck_angle > self.neck_angle_threshold or ratio < self.ratio_threshold
        confidence = min(1.0, max(0.1, (neck_angle / 30.0) * 0.5 + (1.0 - min(1.0, ratio / 0.6)) * 0.5))
        posture_label = "SLOUCHING" if is_slouching else "UPRIGHT"

        return {
            "posture": posture_label,
            "is_slouching": is_slouching,
            "neck_angle": round(neck_angle, 1),
            "vert_ratio": round(ratio, 2),
            "confidence": round(confidence, 2),
        }


def synthetic_posture_frames():
    """Generates scripted posture keypoints for testing."""
    # 1. Upright posture
    yield (0.5, 0.3), (0.4, 0.3), (0.6, 0.3), (0.35, 0.6), (0.65, 0.6)
    # 2. Slouching posture (head tilts forward 20 deg, ear-shoulder vertical distance drops)
    yield (0.55, 0.52), (0.45, 0.52), (0.65, 0.52), (0.35, 0.6), (0.65, 0.6)



if __name__ == "__main__":
    detector = PostureDetector()
    print("--- Posture Detection Test ---")
    for i, frame in enumerate(synthetic_posture_frames(), 1):
        res = detector.process_landmarks(*frame)
        print(f"Frame {i}: Posture={res['posture']} | Neck Angle={res['neck_angle']} deg | Vert Ratio={res['vert_ratio']} | Conf={res['confidence']}")
