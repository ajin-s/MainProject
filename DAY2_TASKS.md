# Day 2 Tasks

Day 1 goal was: environment running, event schema frozen, one hello-world per module. Day 2 goal:
**a full end-to-end console demo, no hardware** — camera detects low engagement → intervention
fires → tutor generates a grounded Socratic response → verifier checks it → "spoken" (printed).
That demo is the definition of done for today.

## Standup first (10 min)
Confirm everyone's `smoke_test.py` still passes and yesterday's hello-worlds still run. Anyone
still blocked on setup pairs with someone who isn't, instead of debugging solo.

---

## Part 1 — Companion & Emotion

### 1. Perception: real engagement scoring
File: `part1_companion/perception/engagement.py`
- Implement `compute_engagement_score()` for real: start simple — eyes-open ratio + face-forward
  angle (from landmarks) → a 0–1 score. Don't wait for a trained emotion classifier; a heuristic
  is fine for the demo.
- Change the hello-world loop to actually **publish** `EngagementUpdate` events onto the event
  bus (`integration/event_bus.py`) at ~5 Hz instead of just printing.
- Definition of done: running the script for 10 seconds while you look away from the camera
  produces a visibly dropping E_t in whatever subscriber prints it.

### 2. Intervention: connect to the real event stream
File: `part1_companion/intervention/state_machine.py`
- Subscribe `InterventionManager.on_engagement_update` to the `engagement.update` topic on the
  shared bus (it currently takes a message directly — wrap it in a `bus.subscribe(...)` call).
- Write a small script that simulates a stream of low-E_t events (no camera needed) to test the
  escalation timing without waiting 10 real minutes — e.g. compress the thresholds for testing.
- Definition of done: feeding 5 fake low-engagement events in a row produces a `gentle` →
  `firm` trigger, and one high-E_t event resets it to idle.

### 3. BKT: connect to a fake quiz + exam alerts
File: `part1_companion/mastery/bkt.py`
- Add a tiny CLI or script that simulates "answer this question" (correct/incorrect input) and
  calls `update_mastery()`, so mastery actually changes over a few fake interactions.
- Add `check_exam_risk(topic, days_left, p_mastery) -> risk` per SRS Section 5.4 (simple
  thresholds: `risk = "high"` if `days_left < 3 and p_mastery < 0.5`, etc.) and publish
  `ExamAlert` when risk crosses into medium/high.
- Definition of done: a fake exam 2 days away + low mastery produces one `ExamAlert` event.

### 4. Voice: define the SSML mapping (no real TTS yet)
File: `part1_companion/voice/tts.py`
- Add a lookup table mapping intervention level / emotion → tone hint (`gentle`→soft/slow,
  `escalated`→urgent/fast). You don't need a real TTS API today — just make `speak()` print the
  tone it *would* use, so Part 2's `tutor.response` events have something meaningful to react to.

---

## Part 2 — Knowledge & Intelligence

### 1. LLM: go from mock to real
File: `part2_knowledge/llm/dialogue.py`
- If Ollama isn't installed yet, do that first (`ollama pull phi3.5`).
- Replace the mock `ask()` body with the real `ollama.chat(...)` call from the TODO comment.
- Definition of done: `python part2_knowledge/llm/dialogue.py` prints a real model response, and
  you've noted roughly how long one response takes (this matters for the Pi later).

### 2. RAG: ingest real syllabus content
File: `part2_knowledge/rag/ingest.py`
- Swap `SAMPLE_CHUNKS` for text extracted from one real syllabus PDF via PyMuPDF (`fitz`).
  Chunk it (a few hundred words per chunk is a reasonable start) and keep the source/page as
  metadata alongside each chunk, not just the raw index.
- Definition of done: a real query about a syllabus topic returns real, correctly-ranked chunks
  from that PDF.

### 3. GraphRAG: connect retrieval to the graph
File: `part2_knowledge/graphrag/graph_build.py`
- Replace the 3-node sample graph with 8–10 real topics/subtopics from the same syllabus.
- Write one function that takes a RAG hit's topic, looks up 1-hop related topics in the graph,
  and returns them alongside the retrieved text — this is the "Graph" part of GraphRAG.
- Definition of done: querying about one topic also surfaces its related topics, not just the
  matching chunk.

### 4. Socratic tutor: wire it to real RAG + real LLM
File: `part2_knowledge/tutor/socratic.py`
- Call it with real retrieved context (from #2 above) and the real `ask()` function (from #1)
  instead of placeholders.
- Definition of done: asking about a real syllabus topic produces a guiding question (not a
  direct answer) that references the actual retrieved content.

### 5. Verification: hook it into the response path
File: `part2_knowledge/verify/verifier.py`
- Before "speaking" a `TutorResponse`, run `is_grounded()` against the chunks that were
  retrieved for it. If not grounded, log a warning instead of sending it to voice — don't block
  on making this perfect today, just get it in the pipeline.

---

## Integration (both teams, together, end of day)

- Publish a `tutor.response` event from the Socratic tutor once it's wired up, and confirm
  `voice/tts.py`'s subscriber prints it with the right tone.
- Run the full loop by hand: simulate a low-engagement event stream → intervention fires →
  Part 2 generates a grounded Socratic nudge for a real syllabus topic → verifier passes it →
  console prints it as "spoken." This is today's demo — get it working even if every piece is
  still rough.
- 15-min end-of-day call: each person demos their piece, then run the full loop together once.

## Parking lot (don't start today, just note it)
- Real TTS API integration
- Servo/display hardware
- RL-based escalation (state machine is enough for now)
