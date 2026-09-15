"""
Choreography Engine for SmartEduSync Robot.
Maps incoming events into face emotion bitmaps, servo joint targets, and vocal prosody.
"""
from typing import Any, Dict, Tuple
from part1_companion.expression.face import get_face_art
from part1_companion.hardware.servo import ServoController


class ChoreographyEngine:
    def __init__(self, servo_controller: ServoController):
        self.servos = servo_controller

    def express(self, event_type: str, data: Dict[str, Any]) -> Tuple[str, str, Dict[int, float], str]:
        """
        Calculates expression targets.
        Returns:
            (emotion_name, face_art, {channel: angle}, prosody_tone)
        """
        event_lower = event_type.lower()
        level = data.get("level", "gentle")
        emotion = data.get("emotion", "watching")

        if "intervention" in event_lower:
            if level == "escalated":
                emo = "alert"
                pose = {0: 0.0, 1: 15.0, 2: 45.0, 3: 45.0}  # Head tilt up, hands raised
                tone = "urgent"
            elif level == "firm":
                emo = "concerned"
                pose = {0: -15.0, 1: -10.0, 2: 20.0, 3: 20.0}  # Head tilt side
                tone = "soft"
            else:
                emo = "curious"
                pose = {0: 15.0, 1: 5.0, 2: 0.0, 3: 0.0}
                tone = "soft"
        elif "tutor" in event_lower:
            emo = "happy"
            pose = {0: 0.0, 1: 0.0, 2: 10.0, 3: 10.0}
            tone = "neutral"
        elif "exam" in event_lower:
            emo = "alert"
            pose = {0: 0.0, 1: 20.0, 2: 30.0, 3: 30.0}
            tone = "urgent"
        else:
            emo = emotion if emotion in ("watching", "listening", "thinking") else "watching"
            pose = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
            tone = "neutral"

        face_art = get_face_art(emo)

        # Move physical / mock servos to target pose
        for channel, angle in pose.items():
            self.servos.set_angle(channel, angle)

        return emo, face_art, pose, tone


if __name__ == "__main__":
    servos = ServoController(force_mock=True)
    choreo = ChoreographyEngine(servos)
    emo, face, pose, tone = choreo.express("intervention.trigger", {"level": "firm"})
    print(f"Choreography Output: Emotion={emo}, Tone={tone}, Pose={pose}")
