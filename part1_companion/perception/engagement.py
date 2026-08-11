"""
Phase 0 task: get the camera + MediaPipe face landmarker running and print something to console.
Phase 1 task: fuse facial emotion + gaze + posture into a single E_t score at ~5 Hz and publish
              it as an EngagementUpdate event (see integration/schemas.py).

Run directly to sanity-check your webcam + MediaPipe install:
    python part1_companion/perception/engagement.py
"""
import time
import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh


def run_camera_hello_world(max_frames: int = 60):
    """Opens the webcam, runs face mesh, prints whether a face is detected. Ctrl+C to stop early."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam (index 0). Try a different index or check permissions.")

    with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh:
        frame_count = 0
        while frame_count < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)
            detected = results.multi_face_landmarks is not None
            print(f"frame {frame_count:03d} | face detected: {detected}")
            frame_count += 1
            time.sleep(1 / 5)  # ~5 Hz, matching the SRS sampling rate

    cap.release()
    print("Done. If you saw 'face detected: True' while looking at the camera, you're good.")


def compute_engagement_score(face_landmarks, posture_hint=None) -> float:
    """
    TODO(Part 1 team, Phase 1): turn landmarks (+ optional posture signal) into a single
    E_t in [0, 1]. Start simple: e.g. eyes-open + face-forward + not-looking-away = high E_t.
    Refine with a real emotion classifier (TFLite) later.
    """
    raise NotImplementedError("Implement in Phase 1 — see SRS Section 5.2")


if __name__ == "__main__":
    run_camera_hello_world()
