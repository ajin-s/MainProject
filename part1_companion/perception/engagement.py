import argparse
import time
from collections import deque
from typing import Generator, Optional, Tuple


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
        # Treat lost face as unknown (skip publishing) rather than E_t = 0
        if not face_detected or raw_engagement is None:
            return None

        # Clamp raw input to valid bounds [0.0, 1.0]
        clamped_val = max(0.0, min(1.0, float(raw_engagement)))
        self.ring_buffer.append(clamped_val)

        # Calculate smoothed E_t across the sliding window
        smoothed_E_t = sum(self.ring_buffer) / len(self.ring_buffer)
        return round(smoothed_E_t, 3)


def synthetic_trace_generator() -> Generator[Tuple[bool, Optional[float]], None, None]:
    """
    Yields a scripted sequence of (face_detected, raw_engagement) frames.
    """
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
    run_perception(sim_mode=args.sim, low_threshold=args.threshold)