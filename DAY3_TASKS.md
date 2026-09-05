# Day 3 Tasks

Day 2's goal was a full end-to-end console demo, no hardware. Day 3's goal: turn that demo
into a **session you can sit with** — one always-on loop where the robot remembers you from
yesterday, answers *and* quizzes you in a real voice, and only ever speaks lines that are
safe, verified, and grounded in real data. Same rule as before: everything still runs on a
laptop, no hardware. This is finishing SRS Phase 2 (voice, service layer, memory) so that
Day 4+ can bolt on the Pi, servos, and display without re-architecting anything.

## Standup first (10 min)
Confirm yesterday's demo still runs end-to-end (engagement.update → intervention.trigger →
grounded Socratic reply → verifier pass → "spoken") and `scripts/smoke_test.py` passes. If
yesterday isn't green yet, that is the morning's priority — today's demo *is* yesterday's
demo plus memory and voice, so it only works if the loop already works. Also confirm who has
Ollama + the model pulled and who has audio output (headphones count).

---

## Part 1 — Companion & Emotion

### 1. Perception: make E_t trustworthy
File: `part1_companion/perception/engagement.py`
- Publish a **smoothed** E_t: keep a ~2 s ring buffer and publish the rolling mean at 5 Hz
  instead of the raw instantaneous value (SRS §10: don't nag on a one-frame blip).
- Decide what "no face in frame" means: treat it as *unknown*, not E_t = 0 — skip publishing
  while lost rather than firing an intervention because the student stood up.
- Add a `--sim` mode that replays a synthetic E_t trace, so behavior is testable with no
  camera and no face.
- Definition of done: a scripted trace with three sub-second dips never leaves `watching`,
  but one sustained low stretch does (thresholds still compressed via env var/flag as in Day 2).

### 2. Intervention: nudge text grounded in real data
Files: `part1_companion/mastery/bkt.py`, `part1_companion/intervention/state_machine.py`
- Add a minimal exam calendar to the BKT SQLite DB (`exams` table: subject, date) and seed a
  few entries. Write `get_student_context(student_id) -> {active_topic, p_mastery,
  nearest_exam, days_left}` that joins mastery + calendar (SRS 5.4 grounds nag text in
  specifics — topic name, days remaining, mastery %).
- When `InterventionManager` leaves `IDLE`, attach that context to the trigger path so the
  downstream nudge can cite real numbers instead of the generic "engagement low" reason.
- Definition of done: a simulated low-engagement run hands downstream a topic, days-left, and
  mastery % that were actually read from the DB — no fabricated values anywhere.

### 3. Persona & safety guardrail: nothing nasty gets spoken
File: `part1_companion/persona/guardrail.py` (new module, SRS 5.1)
- Rule-based `check(text, facts) -> {verdict, reason}` that flags (a) toxic/demotivating
  phrasing ("hopeless", "why can't you even", "this is easy"), (b) give-up instructions, and
  (c) any numeric/factual claim not present in the `facts` dict handed in alongside the text.
- Add `rewrite(text, facts)` that maps common violations to approved encouragement templates.
- Definition of done: a deliberately nasty nudge and a made-up-statistic nudge are both
  denied/rewritten; a genuine grounded nudge passes unchanged.

### 4. Voice: actually speak (with tone), offline-safe
File: `part1_companion/voice/tts.py`
- Replace the day-2 print-stub with a real provider behind one switch: **ElevenLabs** when
  `ELEVENLABS_API_KEY` is set, otherwise **local Piper** (`pip install piper-tts`) so the demo
  never depends on the network. Write audio to the speaker when available; keep `--silent`
  mode that prints `[TTS - tone] text` for machines with no audio.
- Turn the day-2 tone lookup into actual speech parameters per SRS 5.5: `gentle` → slower,
  softer, more spacing; `escalated` → faster, sharper — driven by the `ssml_hint` field on
  `TutorResponse`.
- Definition of done: playing one gentle and one escalated response audibly differs in
  rate/pitch, and `--silent` still behaves like yesterday for the no-audio demo.

---

## Part 2 — Knowledge & Intelligence

### 1. Dialogue as a service: FastAPI with real session state
File: `part2_knowledge/server.py` (new, SRS 6.1)
- FastAPI app exposing `POST /chat` taking `{message, session_id, topic?}` and returning
  `{text, ssml_hint, topic, confidence, grounded}`. Pipeline per request: RAG retrieve →
  graph 1-hop expansion (Day 2) → Socratic ask on the real LLM → verifier gate.
- Hold per-session message history so follow-up questions have context; load the FAISS index,
  graph, and DB once at startup; if the LLM is down, return a clear error instead of crashing.
- Definition of done: two back-to-back `curl` calls in one session — the second referring to
  the first — each return grounded replies with their retrieved source/page printed.

### 2. Verifier: check answers *and* check the answerer
File: `part2_knowledge/verify/verifier.py`
- Replace the word-overlap placeholder in `is_grounded()` with an LLM self-check via
  `dialogue.ask()` ("Is this answer fully supported by the given chunks? Reply YES/NO and one
  reason"). Keep word-overlap as an automatic fallback when Ollama is unavailable, logging
  which path ran (SRS 6.5).
- Add `evaluate_answer(question, expected_points, student_text) -> (correct, missing_points)`
  so Part 1 can run real BKT updates on actual student answers instead of the fake quiz.
- Definition of done: a hallucinated date in a model reply is rejected; the grounded reply
  passes; one wrong student answer moves `p_mastery` down in `mastery.db`.

### 3. Learning memory that survives a restart
File: `part2_knowledge/memory/store.py` (new, SRS 6.5)
- SQLite tables: `conversation_log(session_id, role, text, ts)`, `doubts(topic, note, ts)`,
  and `answer_outcomes(topic, correct, ts)`. Keep it a separate DB from Part 1's `mastery.db`
  so each team owns its store; they join on `(student_id, topic)`.
- When the active topic has recorded doubts, load them into the Socratic prompt
  ("you found X tricky last session — let's start there").
- Definition of done: restart the server, ask about the same topic, and the response
  reflects the recorded doubt; a `SELECT` on conversation_log shows the earlier session.

---

## Integration (both teams, together, end of day)

- Build `integration/session.py`: one always-on asyncio process that starts the perception
  loop (~5 Hz; real camera or `--sim`), keeps the intervention manager subscribed to the bus,
  and runs a stdin chat loop that sends typed messages through the Part 2 pipeline and speaks
  the replies.
- Add the **speech choke point**: every line headed to `speak()` — nudges *and* answers —
  passes guardrail → verifier → TTS, so nothing is spoken that isn't safe and grounded
  (SRS 5.1 + 6.5). On `intervention.trigger`, compose the nudge as: student context from
  BKT + topic → Socratic nudge → choke point → spoken in the escalated/gentle tone.
- 15-min end-of-day call, then run the full session demo together:
  greet with recall of yesterday's doubt → typed question gets a grounded Socratic response
  that is *actually spoken* (or `--silent`-printed) → a wrong answer visibly drops mastery →
  a 10 s look-away (or `--sim` dip) fires a gentle nudge citing the real exam date and
  mastery % → Ctrl+C, restart, and it remembers. That is today's definition of done.

## Parking lot (don't start today, just note it)
- Hardware bring-up: servos + PCA9685, head display + animated face (parts in SRS §3.2) — this
  is the natural Day 4, but only once today's session demo is solid.
- Barge-in / interrupt-mid-speech (the core hear path — mic → STT — is a Day 4 task, not parking lot)
- Automated (Uptrain-style) tone audit; RL-based escalation; Neo4j swap for NetworkX
- A small hallucination eval set; threshold tuning with real users (SRS Phase 4)
