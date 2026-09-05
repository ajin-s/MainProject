# Day 4 Tasks

Product spec (confirmed by the owner): SmartEduSync **is a robot** — a small tabletop one
(~25–30 cm) that (1) monitors the student with its camera, (2) teaches in a Socratic way,
(3) hears and responds, (4) has a **movable head and hand movement**, and (5) shows
**curiosity and emotions through its voice and the display set in its face**. It is not a
screen-only box: the moving head and hands are part of the design (this restores SRS §3.2 —
head pan/tilt + servo hands — with expression delivered via voice + face display per §5.5).

Day 3 left you with that brain working headless. Day 4's goal: **put the robot in a
simulation**, since the parts aren't bought yet — a free simulation website runs the robot's
body (head + hands), its face display renders emotions and curiosity, and the laptop provides
the real ears (mic → speech-to-text), eyes (webcam, already working), and voice (TTS). When
the Pi + servos + display arrive, only a driver drops in — nothing upstream changes.

## Standup first (10 min)
Confirm the Day 3 session demo still runs (engagement → intervention → grounded Socratic reply
→ guardrail/verifier → spoken) and `scripts/smoke_test.py` passes. Then decide as a team:
(1) the simulator — recommended **Webots** (free desktop app) streamed/shared in the browser on
**webots.cloud**; Gazebo (gz sim) is the URDF-native alternative and works with the same tasks;
(2) who owns the robot model vs. the HAL + expression vs. the demo; (3) add a `simulation/`
folder to the repo; (4) agree the expression vocabulary so code names match:
`idle · watching · listening · thinking · curious · happy · concerned · alert`.
Install the sim now (free). No physical parts are needed for any of today's tasks.

---

## Part 1 — Companion & Emotion (the robot's body and expression)

### 1. Simulated robot model from the SRS
Files: `simulation/smartedusync.urdf` (+ `simulation/meshes/` if you export STLs)
- Build a URDF matching SRS §3: static tabletop base (~25–30 cm tall), **movable head** with
  pan (yaw, ≈±90°) and tilt (pitch), a **face panel fixed to the head**, and **two hands**
  (shoulder joints, + elbow if time). Primitive visual geometry (boxes/cylinders) is fine;
  use STLs only if you want to practice the `$cad` skill.
- Approximate masses/inertias as if servos were MG90S (≈9 g); give the head and hands safe
  joint limits. Import into the chosen sim (Webots: `pip install urdf2webots` → import;
  Gazebo: native URDF).
- Definition of done: the sim world opens with the whole robot visible; a test script smoothly
  sweeps head yaw/tilt and swings both hands with no instability.

### 2. Hardware abstraction layer (HAL) — sim today, real later
Files: `part1_companion/hardware/servo.py`, `display.py`, `backends/sim.py`,
`backends/pca9685.py`
- Interfaces: `servo.set_angle(channel, degrees, speed)` with per-channel safety limits, and
  `display.show_face(emotion)`, `display.show_card(lines)`, `display.show_progress(...)`.
- `backends/sim.py` maps servo channels to the sim's head/hand joints and renders the face on
  the sim Display node mounted on the head panel; `backends/pca9685.py` validates angles but
  **raises NotConnectedError** unless `HARDWARE=real` — it must fail loudly, never silently.
- Backend chosen via env/config (default `sim`); document channel→joint mapping in the header.
- Definition of done: a 5-line script moves the sim head by angle and shows a face state;
  running the pca9685 backend prints a clear "no hardware" error, not a hang.

### 3. Expression: curiosity and emotions through face + voice + pose
Files: `part1_companion/expression/face.py`, `voice.py`, `choreography.py` (new)
- `face.py`: define the expression vocabulary as drawing states (eyes, brows, mouth — wide
  eyes + raised brows for `curious`, etc.) rendered on the head's display by the HAL backend.
- `voice.py`: extend the Day 3 tone table so emotion reaches the voice — `curious` = brighter,
  rising, slightly slower ("Ooh, good question…"); `happy` = bright; `concerned` = softer and
  slower; `alert` = faster and sharper. Keep the Day 3 gentle/firm/escalated mapping working
  on top (level sets urgency, emotion sets warmth/curiosity).
- `choreography.py`: map events → (face, pose, voice tone):
  novel/"why" question or a confused student → head pans/tilts toward them + `curious` face +
  curious voice; sustained low E_t → head turns slowly to the student + `concerned`; gentle →
  warm slow nod; firm → slight head shake; escalated → `alert` face, head straight, faster
  voice; correct answer → `happy` + nod; `exam.alert` high → `alert`; otherwise `idle`.
- Definition of done: during a scripted sequence an observer can name the robot's emotion or
  curiosity from face + voice + pose alone — no reading logs.

### 4. Perception: unchanged, but re-verified
- No camera changes today — the laptop webcam is the stand-in for the Pi Camera Module 3.
  Re-run the Day 3 checks (smoothing, no false nags) so the demo runs on a trustworthy E_t.
  The face shows `watching` while monitoring, which doubles as a nice "it sees you" cue.

---

## Part 2 — Knowledge & Intelligence (what gets said and shown)

### 1. Study cards for the face display
File: `part2_knowledge/tutor/flashcards.py` (new)
- From the top retrieved chunks for the active topic, generate 3–5 one-line study cards
  (concept → short phrasing, chunk source tagged), sized to fit the face display.
- Definition of done: `cards for <topic>` in the session prints a short grounded card set, each
  card traceable to its source chunk.

### 2. On-screen handoff for answers and alerts
File: `integration/display_protocol.py` (new, both teams agree)
- Agree how spoken text becomes face-display text: `TutorResponse.text` → short bubble on the
  face panel (the robot "says" it while TTS speaks it); `ExamAlert` → alert face + card with
  subject, days_left, and mastery % read from Part 1's BKT DB. Reuse existing topics; if a new
  event is unavoidable, post to the team channel first (schema-freeze rule).
- Definition of done: a spoken syllabus answer also appears on the face display, and a
  simulated near-exam alert shows real days-left + mastery % on the panel.

### 3. Session soak test (voice + body)
File: `scripts/soak_session.py` (new)
- Run a scripted 15-minute session with the sim robot live: typed and **spoken** questions,
  deliberate wrong answers, scripted engagement dips (`--sim` trace), and an exam alert. Log
  event counts and unhandled exceptions per module.
- Definition of done: 15 minutes, zero crashes, every event type exercised, every expression
  state reached at least once, and a readable summary (nudges, mastery deltas, verifier
  pass/reject, STT turns).

---

## Integration (both teams, together, end of day)

- Extend `integration/session.py` (Day 3) with a flag that starts the sim world + HAL sim
  backend so the running session drives the simulated robot. Session logic itself must not
  change — the body and face are passive consumers of the same events.
- The **sim → hardware mapping doc** (shared deliverable, `docs/`): map every sim joint to a
  future PCA9685 channel + servo part (confirm MG90S via the `$step-parts` skill), face states
  to LCD draw calls, mic → mic array, webcam → Pi camera. BOM stays SRS §3.2. This makes
  bring-up a one-day job once parts ship.
- 15-min end-of-day call, then run the full demo together, recorded: the sim robot sits beside
  you on screen → you look away → its head slowly turns toward you, face `concerned`, gentle
  voice nudge fires → you *say* a "why" question → head tilts, `curious` face, curious voice
  reply after `listening` → `thinking` → you answer wrong → hands drop, `concerned` face, and
  mastery visibly falls → near-exam alert flips the face to `alert`. One take, saved to a
  webots.cloud share link or a screen recording. **That is the day's definition of done** — a
  tabletop robot that watches, teaches, hears, moves, and emotes, with zero physical parts.

## Parking lot (don't start today, just note it)
- Order the real parts (BOM in SRS §3.2: Pi 5, Camera Module 3, mic array, speaker, LCD,
  MG90S servos + PCA9685) — bring-up is a drop-in once the HAL exists
- Barge-in / interrupt-mid-speech; pick STT model size vs. Pi latency
- Face/voice persona personalization; RL escalation; Neo4j swap (carried from Day 3)
