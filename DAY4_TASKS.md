# Day 4 Tasks

Product spec (confirmed by the owner): SmartEduSync **is a robot** — a small tabletop one
(~25–30 cm) that (1) monitors the student with its camera, (2) teaches in a Socratic way,
(3) hears and responds, (4) has a **movable head and hand movement**, and (5) shows
**curiosity and emotions through its voice and the display set in its face** (SRS §3.2 body +
§5.5 expression).

Day 3 left the brain working headless. Day 4's goal: **write the robot's actual software** —
real drivers, real hearing, real expression. The parts aren't bought, so the *only* thing
faked is the physical wire: drivers talk the real I²C/SPI protocols, and a `MockBus` records
every register write so the code is benchtop-tested today and flips to `HARDWARE=real` when
the Pi arrives. No simulator, no URDF, no browser robot — every module written today is
production code that runs unchanged on the hardware.

## Standup first (10 min)
Confirm the Day 3 session demo still runs and `scripts/smoke_test.py` passes. Then agree:
(1) **no simulator** — drivers target real parts; the mock bus appears only in tests and
`--hardware mock` runs; (2) channel map + pins: head pan/tilt = PCA9685 ch 0–1, hands ch 2–3
(elbows ch 4–5 if time), I²C addr 0x40, face-LCD pins; (3) env convention
`HARDWARE=mock|real` (default `mock`); (4) expression vocabulary so code names match:
`idle · watching · listening · thinking · curious · happy · concerned · alert`;
(5) ownership: drivers vs. expression vs. demo.

## Part 1 — Companion & Emotion (body drivers + expression)

### 1. Servo driver — real PCA9685 protocol, benched on a mock bus
Files: `part1_companion/hardware/bus.py`, `hardware/servo.py` (new)
- `bus.py`: `I2CBus` wrapper + `MockBus` — the mock is a thin class that records every
  register write (address, register, value) to a log and exposes the register map, so tests
  assert *exactly what the driver sends*. Selected by `HARDWARE=mock|real`.
- `servo.py`: real PCA9685 driver — 12-bit PWM at 50 Hz (prescale 0x79), MG90S pulse range
  (~500–2400 µs → counts 102–491), `set_angle(channel, degrees, speed)` mapping angle→pulse
  with per-channel joint limits (head pan ±90°, tilt ±45°, hands), speed-limited ramping via
  incremental writes, and a failsafe that parks all channels at neutral on any error.
- Definition of done: `servo_bench.py --hardware mock` sweeps head yaw/pitch + both hands and
  prints the register-write log; `pytest tests/test_servo.py` asserts exact register values
  for known angles, clamping at limits, and failsafe behavior. This driver is the one that
  runs on the real Pi — only `HARDWARE` changes.

### 2. Face display driver — real LCD protocol + rendered emotions
Files: `part1_companion/hardware/display.py` (new)
- `display.py`: SSD1306-class 128×64 driver via `luma.oled` with `show_face(emotion)`,
  `show_card(lines)`, `show_progress(...)`. A tiny `ScreenSink` abstraction: `LumaScreen`
  (real LCD later), `WindowScreen` (laptop window stands in for the LCD today), `FileSink`
  (PNG capture for tests/CI), and a readable log fallback when no GUI exists.
- Definition of done: `python -m part1_companion.hardware.display --cycle` steps all 8
  vocabulary emotions on the laptop window and writes a PNG per emotion; tests assert each
  emotion renders a distinct bitmap.

### 3. Expression: curiosity and emotions through face + voice + pose
Files: `part1_companion/expression/face.py`, `voice.py`, `choreography.py` (new)
- `face.py`: draws each vocabulary state as a 128×64 bitmap (eyes, brows, mouth — wide eyes +
  raised brows for `curious`, etc.) and hands the frame to the display sink.
- `voice.py`: extends the Day 3 tone table so emotion reaches prosody — `curious` = brighter,
  rising, slightly slower ("Ooh, good question…"); `happy` bright; `concerned` softer/slower;
  `alert` faster/sharper. Day 3's gentle/firm/escalated level mapping stays on top (level sets
  urgency, emotion sets warmth/curiosity).
- `choreography.py`: pure function `express(event, state) -> (emotion, pose, tone)`. A
  novel/"why" question or hesitation → head pans/tilts toward the student + `curious`; low E_t
  → slow turn + `concerned`; gentle → warm nod; firm → slight head shake; escalated → `alert`;
  correct answer → `happy` + nod; `exam.alert` high → `alert`; otherwise `idle`.
- Definition of done: table-driven pytest covers every event × vocabulary state; a `--trace`
  mode replays a session log printing (event → emotion/pose/tone) per line, so an observer
  can name the robot's emotion from face + voice + pose alone — no reading logs.

### 4. Ears — real speech-to-text from the laptop mic
Files: `part1_companion/voice/stt.py` (new)
- Real mic capture (sounddevice) → SpeechRecognition (or faster-whisper if the team picks it)
  with simple VAD (silence = end of turn) → transcript fed into the *same* session entry point
  as typed input (`--listen` flag).
- Definition of done: in the demo, say "why does X happen?" and the session receives exactly
  that; a typed-identical path proves spoken and typed share one pipeline.

### 5. Perception re-verified (unchanged)
- Camera code unchanged — re-run the Day 3 checks (smoothing, no false nags) so the demo runs
  on a trustworthy E_t; the face shows `watching` while monitoring.

## Part 2 — Knowledge & Intelligence

### 1. Study cards for the face display
File: `part2_knowledge/tutor/flashcards.py` (new)
- From the top retrieved chunks for the active topic, generate 3–5 one-line study cards
  (concept → short phrasing, chunk source tagged), sized to fit the display and rendered via
  `display.show_card`.
- Definition of done: `cards for <topic>` prints a grounded card set, each traceable to its
  source chunk; pytest asserts every card fits the display width.

### 2. On-screen handoff for answers and alerts
File: `integration/display_protocol.py` (new, both teams agree)
- Agree how spoken text becomes face text: `TutorResponse.text` → short bubble on the display
  while TTS speaks it; `ExamAlert` → alert face + card with subject, days_left, mastery % read
  from Part 1's BKT DB. Reuse existing topics; post first if a new event is unavoidable
  (schema-freeze rule).
- Definition of done: a spoken syllabus answer also appears on the face window; a simulated
  near-exam alert shows real days-left + mastery % on the panel.

### 3. Session soak test (voice + body, mock hardware)
File: `scripts/soak_session.py` (new)
- 15-minute headless session with `HARDWARE=mock`: typed and **spoken** questions, deliberate
  wrong answers, scripted engagement dips (`--sim` trace), an exam alert. Log event counts,
  unhandled exceptions per module, and the full mock-bus register log.
- Definition of done: 15 minutes, zero crashes, every event type exercised, all 8 expression
  states reached, and a readable summary (nudges, mastery deltas, verifier pass/reject, STT
  turns).

## Integration (both teams, end of day)
- `integration/session.py` (Day 3) gains a `--hardware` flag so a running session drives the
  face window and streams servo/PWM writes to the mock-bus log. Session logic itself does not
  change — the body and face are passive consumers of the same events.
- **Hardware mapping doc** (shared, `docs/`): channel→joint→MG90S, I²C address + LCD pins,
  mic → mic array, webcam → Pi camera; BOM stays SRS §3.2. When parts arrive: `HARDWARE=real`
  makes bring-up a one-day job.
- 15-min end-of-day call, then the full demo together, recorded: you look away → E_t dips →
  face turns `concerned`, head-pan writes stream to the log, gentle voice nudge fires → you
  *say* a "why" question → mic → STT → `listening` → `thinking` → head tilts, `curious` face,
  bright rising reply → you answer wrong → hands-drop writes, `concerned`, mastery visibly
  falls → near-exam alert flips the face to `alert`. One take — screen recording + mock-bus
  log. **That is the day's definition of done** — a tabletop robot that watches, teaches,
  hears, moves (proven by its register log) and emotes, with the physical bus as the only
  stand-in.

## Parking lot (don't start today, just note it)
- Order the parts (BOM SRS §3.2) and flip `HARDWARE=real` — one-day bring-up, drivers already
  written and benched
- Barge-in / interrupt-mid-speech; pick STT model size vs. Pi latency
- Face/voice persona personalization; RL escalation; Neo4j swap (carried from Day 3)