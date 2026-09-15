# SmartEduSync — Complete Technical Documentation

**Group 07 (MBCCET) — Final Year Capstone Project**
**Version:** 1.0 | **Last Updated:** September 2026

This document is the single source of truth for everything needed to understand, reproduce, extend, or defend the SmartEduSync project: every algorithm used, the methodology behind each design decision, how the models are trained/configured, and what datasets/data sources the system consumes.

> **Companion documents:** [`PROJECT_DETAILS.md`](PROJECT_DETAILS.md) (architecture spec), [`FINAL_YEAR_PROJECT_THESIS_GUIDE.md`](FINAL_YEAR_PROJECT_THESIS_GUIDE.md) (defense Q&A), [`UPDATES_AND_NEXT_STEPS.md`](UPDATES_AND_NEXT_STEPS.md) (changelog & hardware roadmap), [`EXECUTION_WALKTHROUGH.md`](EXECUTION_WALKTHROUGH.md) (run guide).

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Algorithms — Deep Dive](#3-algorithms--deep-dive)
   - 3.1 [Engagement Estimation (Computer Vision)](#31-engagement-estimation-computer-vision)
   - 3.2 [Slouch / Posture Detection](#32-slouch--posture-detection)
   - 3.3 [Intervention State Machine](#33-intervention-state-machine)
   - 3.4 [Bayesian Knowledge Tracing (BKT)](#34-bayesian-knowledge-tracing-bkt)
   - 3.5 [Exam Risk Model](#35-exam-risk-model)
   - 3.6 [Vector RAG Pipeline (Embeddings + FAISS)](#36-vector-rag-pipeline-embeddings--faiss)
   - 3.7 [GraphRAG (Knowledge Graph Expansion)](#37-graphrag-knowledge-graph-expansion)
   - 3.8 [Socratic Tutoring Prompt Methodology](#38-socratic-tutoring-prompt-methodology)
   - 3.9 [Grounding Verifier & Answer Evaluation](#39-grounding-verifier--answer-evaluation)
   - 3.10 [Persona Guardrails (Safety Layer)](#310-persona-guardrails-safety-layer)
   - 3.11 [Playful Accountability Engine](#311-playful-accountability-engine)
   - 3.12 [Prosody & Choreography Mapping](#312-prosody--choreography-mapping)
4. [Models & Training](#4-models--training)
5. [Datasets & Data Sources](#5-datasets--data-sources)
6. [Data Storage Schema](#6-data-storage-schema)
7. [Hardware & Embedded Methodology](#7-hardware--embedded-methodology)
8. [Testing & Verification Methodology](#8-testing--verification-methodology)
9. [Privacy & Ethics Methodology](#9-privacy--ethics-methodology)
10. [Limitations & Future Work](#10-limitations--future-work)

---

## 1. Project Overview

SmartEduSync is a **privacy-first, emotion-aware tabletop AI tutoring robot**. A camera watches the student (on-device only), a local LLM tutors Socratically, Bayesian Knowledge Tracing tracks mastery, and a small physical robot (OLED face + 4 servos + voice) expresses engagement, concern, and accountability.

**Core design principles:**

| Principle | How it is realized |
|---|---|
| Privacy-first | All inference is local: MediaPipe on-device landmarks, Ollama local LLM, local SQLite storage. No cloud APIs in the default path; no video ever leaves the machine. |
| Pedagogy over answers | Strict Socratic prompt contract: guide with one question, never reveal answers below 85% mastery. |
| Grounded responses | Every LLM output passes a guardrail (toxicity + ungrounded-stat) check and a grounding verifier before being spoken/shown. |
| Testable everywhere | `HARDWARE=mock` MockBus lets the entire robot run headless on any laptop; identical code paths run on the Raspberry Pi 5. |

---

## 2. System Architecture

Two decoupled engines communicate **only** through an in-process asynchronous Pub/Sub event bus (`integration/event_bus.py`), with schemas frozen in `integration/schemas.py` (Pydantic v2 models — the contract between the two teams).

```
                ┌────────────────────────────────────────────┐
                │        integration/session.py (loop)       │
                └───────────────┬────────────────────────────┘
                                │ async Pub/Sub event bus
        ┌───────────────────────┴────────────────────────┐
        ▼                                                ▼
┌─────────────────────────┐                ┌─────────────────────────────┐
│ Part 1 — Companion      │                │ Part 2 — Knowledge          │
│ (part1_companion/)      │                │ (part2_knowledge/)          │
│ • MediaPipe perception  │                │ • Ollama LLM (phi3.5)       │
│ • Posture/slouch        │                │ • FAISS vector RAG          │
│ • Intervention FSM      │                │ • GraphRAG (NetworkX)       │
│ • BKT mastery (SQLite)  │◄═══ events ═══►│ • Socratic tutor            │
│ • Guardrails + persona  │                │ • Verifier + memory (SQLite)│
│ • TTS/STT voice         │                │ • FastAPI server (:8000)    │
│ • Servos + OLED face    │                │ • Study material library    │
└─────────────────────────┘                └─────────────────────────────┘
```

**Event topics (frozen contract):**

| Topic | Schema | Publisher | Subscribers |
|---|---|---|---|
| `engagement.update` | `EngagementUpdate` | Perception (5 Hz) | Intervention FSM, display |
| `intervention.trigger` | `InterventionTrigger` | Intervention FSM | Tutor, choreography, TTS |
| `tutor.response` | `TutorResponse` | Socratic tutor | Guardrail, verifier, TTS |
| `mastery.update` | `MasteryUpdate` | BKT tracker | FSM, memory store |
| `exam.alert` | `ExamAlert` | BKT tracker | Display, TTS |

---

## 3. Algorithms — Deep Dive

### 3.1 Engagement Estimation (Computer Vision)

**Module:** `part1_companion/perception/engagement.py`

**Methodology — transparent heuristic fusion, deliberately not a black-box classifier:**

1. **Landmark capture.** MediaPipe Face Mesh (478 landmarks, `refine_landmarks=True`, tracking confidence 0.5) runs on each webcam frame. Frames are read with OpenCV at the publish cadence of 5 Hz.
2. **Eye Aspect Ratio (EAR).** For each eye, using landmark indices:
   - Left eye: `(33, 133, 159, 145)`, Right eye: `(362, 263, 386, 374)`
   - `EAR = dist(vertical landmarks) / dist(horizontal corners)` (per-eye), averaged over both eyes.
   - Typical open-eye EAR ≈ 0.20–0.35; closed/drowsy ≈ 0.10–0.15.
3. **Yaw (gaze direction).** Nose tip (landmark 1) horizontal displacement from the eye midpoint, normalized by inter-ocular width: `yaw_ratio = |nose.x − eye_mid.x| / eye_width`. 0 = looking straight at the robot/screen.
4. **Fusion (weighted linear score):**

   ```
   eye_score      = clamp((EAR − 0.12) / 0.13, 0, 1)      # 0.12–0.25 maps to 0→1
   forward_score  = clamp(1 − yaw_ratio / 0.45, 0, 1)     # >0.45 yaw ⇒ 0
   E_raw          = 0.60 · eye_score + 0.40 · forward_score
   ```

   The 60/40 weighting encodes the pedagogical prior that *eyes-on-task* matters more than exact head pose.
5. **Temporal smoothing — 2-second ring buffer.** Raw samples are appended to a `deque(maxlen=10)` (10 samples @ 5 Hz = 2 s window) and the published value is the **rolling mean** `E_t ∈ [0,1]`, rounded to 3 decimals. This is a simple moving average (SMA) filter: it suppresses sub-second attention dips (a glance at a phone) so they never trigger interventions, while sustained disengagement (≥ ~2 s) passes through.
6. **Missing-face semantics.** If no face is detected, the module returns `None` and **publishes nothing** — absence is treated as *unknown*, not as `E_t = 0`. This prevents false "worst engagement" spikes when a student stands up or leans out of frame.
7. **Emotion classification thresholds** (on smoothed `E_t`):

   | `E_t` range | Label |
   |---|---|
   | ≥ 0.70 | `engaged` |
   | 0.45 – 0.70 | `confused` |
   | 0.30 – 0.45 | `distracted` |
   | < 0.30 | `frustrated` |

**Why this methodology:** every constant is explainable in a viva; the whole pipeline runs in real time on a Raspberry Pi-class CPU with no GPU and no model training data collection involving children.

---

### 3.2 Slouch / Posture Detection

**Module:** `part1_companion/perception/posture.py`

**Methodology — geometric posture metrics with an optional CNN feature path:**

1. **Keypoints.** Nose, left/right ear, left/right shoulder, as normalized `(x, y) ∈ [0,1]` coordinates (from MediaPipe Pose / upper-body landmarks).
2. **Neck inclination angle.** Angle of the mid-ear → mid-shoulder line against the vertical axis:

   ```
   θ_neck = atan2(|Δx|, |Δy) in degrees
   ```
3. **Ear-to-shoulder vertical ratio.** `ratio = |Δy(mid-ear, mid-shoulder)| / shoulder_width` — slouching compresses this ratio because the head drops toward shoulder height.
4. **Classification rule (two-condition OR):**

   ```
   SLOUCHING if θ_neck > 15°  OR  ratio < 0.50
   ```
5. **Confidence score:**

   ```
   confidence = clamp(0.5·(θ/30) + 0.5·(1 − clamp(ratio/0.6)), 0.1, 1.0)
   ```
6. **CNN feature vector (forward-looking).** `extract_features()` emits a normalized **10-dimensional keypoint vector** `(nose.x, nose.y, l_ear.x, l_ear.y, r_ear.x, r_ear.y, l_sh.x, l_sh.y, r_sh.x, r_sh.y)` intended as the input tensor for a small CNN posture classifier in future work; the shipped classifier is the deterministic geometric rule above, which is fully testable without training data.

---

### 3.3 Intervention State Machine

**Module:** `part1_companion/intervention/state_machine.py`

**Methodology — duration-gated finite state machine (FSM) on the smoothed engagement stream:**

- **States:** `IDLE → GENTLE → FIRM → ESCALATED` (enum-driven), with immediate reset to `IDLE` on recovery (`E_t ≥ 0.40`).
- **Timing ladder** (configurable in the constructor):

  | Level | Trigger condition | Robot behavior |
  |---|---|---|
  | `gentle` | `E_t < 0.40` sustained ≥ 0.5 s | Curious face, soft spoken nudge |
  | `firm` | sustained ≥ 2.5 s | Concerned face, head tilt, softer/direct tone |
  | `escalated` | sustained ≥ 10.0 s | Alert face, head-tilt-up + raised hands, urgent tone |

- **Hysteresis logic:** each transition fires only once per episode (the state guard `state != X` prevents repeated triggers while already in that level); any recovered frame resets `low_start_ts` and the FSM, so brief dips never cascade.
- **Context attachment:** on every trigger the FSM joins BKT state (`get_student_context`) so the nudge names the *weakest topic*, current mastery %, and days to the nearest exam — the intervention is always fact-grounded, never generic.

**Design rationale:** the ring-buffer smoothing (3.1) plus duration gating gives a two-stage noise filter — transient distractions are absorbed by the SMA, and only sustained disengagement escalates. This avoids nagging, which the pedagogy literature identifies as the fastest way to make a companion robot ignorable.

---

### 3.4 Bayesian Knowledge Tracing (BKT)

**Module:** `part1_companion/mastery/bkt.py` — persistence in `bkt_mastery.db` (SQLite).

**Methodology — the standard Corbett & Anderson (1995) two-parameter Bayesian update per (student, topic) pair:**

**Model parameters (defaults in code):**

| Parameter | Symbol | Default | Meaning |
|---|---|---|---|
| Prior knowledge | `P(L₀)` | 0.50 (row default) | Probability topic is mastered before evidence |
| Transition (learning) | `P(T)` | 0.10 | Probability of learning during one opportunity |
| Slip | `P(S)` | 0.10 | Probability a mastered topic is answered wrong |
| Guess | `P(G)` | 0.20 | Probability an unmastered topic is answered right |

**Update equations:**

1. *Evidence step* (Bayes rule on the observed correctness `c`):

   ```
   correct:   P(L|obs) = P(L)·(1−P(S)) / [ P(L)·(1−P(S)) + (1−P(L))·P(G) ]
   incorrect: P(L|obs) = P(L)·P(S)     / [ P(L)·P(S)     + (1−P(L))·(1−P(G)) ]
   ```
2. *Learning step:*

   ```
   P(L_new) = P(L|obs) + (1 − P(L|obs))·P(T)
   ```
3. Clamped to `[0,1]`, rounded to 3 decimals, and upserted with `ON CONFLICT(student_id, topic)`.

**Worked example** (student at `P(L)=0.42`, answers correctly, defaults):
`P(L|obs) = 0.42·0.9 / (0.42·0.9 + 0.58·0.2) = 0.378/0.494 ≈ 0.765`
`P(L_new) = 0.765 + 0.235·0.1 ≈ 0.769` → mastery jumps 42% → 77% after one correct answer, exactly the BKT behavior of fast early gains.

**Why BKT over alternatives:** BKT is interpretable (4 physical parameters a viva panel can audit), needs **no training data** (parameters are pedagogical priors), runs in microseconds on a Pi, and its output `P(L)` directly parameterizes the Socratic prompt and the exam-risk model. DKT (deep knowledge tracing) would require large per-student interaction datasets unavailable to a capstone team and would be unexplainable to teachers.

**Storage:** `student_mastery(student_id, topic, p_mastery)` with PK `(student_id, topic)`; seeded demo rows: `student_1/Calculus Integrals = 0.42`, `student_1/Linear Algebra = 0.78`, `demo_student/Robotics = 0.50`.

**Event coupling:** after every update the tracker publishes `mastery.update`, then joins the `exams` table — if the topic has an upcoming exam it evaluates the risk model (3.5) and may publish `exam.alert`.

---

### 3.5 Exam Risk Model

**Module:** `part1_companion/mastery/bkt.py::check_exam_risk` (SRS §5.4)

**Methodology — 2-D threshold matrix over (urgency, readiness):**

```
HIGH   : days_left ≤ 3  AND p_mastery < 0.50
MEDIUM : days_left ≤ 7  AND p_mastery < 0.70
LOW    : otherwise
```

Only `MEDIUM` and `HIGH` publish an `ExamAlert` event (LOW stays silent to avoid alarm fatigue). `days_left` is computed from the `exams` table and clamped to ≥ 1 so a same-day exam still reports "1 day left" rather than 0/negative.

---

### 3.6 Vector RAG Pipeline (Embeddings + FAISS)

**Modules:** `part2_knowledge/rag/ingest.py` (syllabus pipeline), `part2_knowledge/rag/material_library.py` (student onboarding library).

**Ingestion methodology:**

1. **Extraction:** PDFs page-by-page via PyMuPDF (`fitz`); `.txt/.md/.csv/.html` decoded as UTF-8; images via Tesseract OCR (`pytesseract`); URLs fetched over http(s) with a 10 s timeout, 5 MB cap, and SSRF guard (localhost/loopback hosts rejected).
2. **Chunking:** LangChain `RecursiveCharacterTextSplitter` with `chunk_size=300, chunk_overlap=50` for the syllabus pipeline; the material library uses an overlap-word window (`110` words, `20` overlap) so retrieval works with zero heavy dependencies.
3. **Embedding:** `SentenceTransformer('all-MiniLM-L6-v2')` — 384-dim sentence embeddings, L2-normalized so inner product ≡ cosine similarity.
4. **Indexing:** `faiss.IndexFlatIP` (exact inner-product search — no approximation error at capstone corpus scale), persisted to `sample.index`.

**Retrieval methodology (with graceful degradation):**

```
retrieve_chunks(query, k)
 ├─ try:   FAISS IndexFlatIP top-k over normalized embeddings  (semantic path)
 └─ except: retrieve_lexical() — token-overlap ranking          (lexical fallback)
```

The lexical fallback guarantees the tutor still retrieves grounded context on a Pi with no embedding model loaded. The student-material library additionally appends the first 12 concept-graph nodes to retrieved excerpts so the LLM sees both passages *and* related concepts (mini GraphRAG inside retrieval).

**Failure semantics:** if nothing was extracted from an upload, `MaterialError` is raised with an actionable message (e.g., "PDF has no selectable text — upload an OCR-enabled PDF or notes"); video uploads are explicitly rejected with instructions to attach the transcript.

---

### 3.7 GraphRAG (Knowledge Graph Expansion)

**Modules:** `part2_knowledge/graphrag/graph_build.py` (curated syllabus graph), `part2_knowledge/graphrag/graph_mapper.py` (dynamic per-student graph).

**Methodology A — curated seed graph (`networkx.DiGraph`):**
Hand-authored syllabus edges with typed relations, e.g.

```
Calculus Integrals ──subtopic──▶ Definite Integrals
Calculus Integrals ──prerequisite──▶ Fundamental Theorem of Calculus
Calculus Integrals ──method──▶ Riemann Sums
Linear Algebra ──subtopic──▶ Matrix Multiplication | concept──▶ Eigenvalues | foundation──▶ Vector Spaces
Robotics ──includes──▶ Kinematics, Control Systems ──includes──▶ PID Controllers
```

**Methodology B — dynamic graph construction from student material (`DynamicGraphMapper`):**
1. **Concept extraction:** capitalized-phrase regex `\b[A-Z][a-z]+(\s+[A-Z][a-z]+)*\b` minus a stop-phrase list, plus domain keyword triggers (mentions of "integral"/"matrix"/"kinematics" inject the corresponding canonical concept nodes).
2. **Sequential linking:** concepts co-occurring in a chunk are joined `c₁ → c₂ → …` with `relation="subtopic"` and a `source` attribute naming the origin document — every node/edge is traceable to its material.
3. **Persistence:** the per-student graph is serialized to JSON and stored in `concept_graphs(student_id PK, graph_json, updated_at)`; every ingest triggers a full `rebuild_graph()` so the graph always reflects all of the student's sources.

**Retrieval-time expansion (`expand_rag_context`):** the tutor takes the RAG base context and appends the **1-hop neighborhood** (successors ∪ predecessors) of the active topic: *" Related concepts to explore: Riemann Sums, Definite Integrals."* This grounds Socratic questions in connected syllabus context — e.g., a question about definite integrals can legitimately pull in Riemann Sums — which measurably reduces off-syllabus hallucination and gives the tutor natural "bridging" material.

---

### 3.8 Socratic Tutoring Prompt Methodology

**Module:** `part2_knowledge/tutor/socratic.py`

**Methodology — mastery-conditioned prompt contract with a strict behavioral rule set:**

```
You are SmartEduSync, a patient AI tutor using the strict Socratic Method.
Topic: {topic}
Student's Current Mastery: {mastery:.0%}
Student said: {student_message}
Prior doubts: {doubts}
Retrieved Syllabus & GraphRAG Context: {context}

STRICT SOCRATIC RULES:
1. Do NOT reveal the direct answer or final formula upfront unless mastery is >= 85%.
2. Ask EXACTLY ONE clear, encouraging guiding question that leads the student toward discovery.
3. If the student makes an error, reframe with an intuitive real-world analogy.
4. Keep response under 3 sentences.
Respond to what the student actually said.
```

Key design points:
- **Mastery-conditioned disclosure:** the BKT probability is injected into the prompt, so the same engine naturally becomes more direct as mastery grows (≥ 85% allows revealing the answer) — differentiation is emergent from the BKT state, not a separate code path.
- **Doubt injection:** recorded student doubts (`memory.db`) are fed back so the tutor re-attacks known weak points.
- **Prosody hint:** `ssml_hint` is chosen from mastery (`soft` below 40%, `neutral` at ≥ 85%) and travels with the response so TTS delivery matches pedagogy.
- **LLM binding:** the generator takes an injected `ask_llm_fn`, keeping it unit-testable with mock generators; production binds `part2_knowledge/llm/dialogue.py::ask` → Ollama `phi3.5` (env `OLLAMA_MODEL` overridable, `llama3.1` supported), with a deterministic mock Socratic fallback per domain when Ollama is absent.

---

### 3.9 Grounding Verifier & Answer Evaluation

**Module:** `part2_knowledge/verify/verifier.py`

**`is_grounded(answer, retrieved_chunks, min_overlap=0.15)` — lexical-overlap hallucination gate:**
1. Tokenize answer and joined context into lowercase word sets; drop a small stop-word list.
2. `overlap = |meaningful_answer_words ∩ context_words| / |meaningful_answer_words|`
3. `grounded = overlap ≥ 0.15`. Empty answer/context short-circuits to `True` (nothing to verify).

If ungrounded, the server/session **replaces the response** with a safe generic Socratic opener ("Let's reason about {topic} together…") — the student never hears an unverifiable claim.

**`evaluate_student_answer(question, expected_keywords, student_text)`:**
- Keyword-recall scoring: `score = matched_keywords / total_keywords`, threshold `correct = score ≥ 0.50`.
- The boolean feeds BKT's `correct` input (3.4), closing the loop: **tutor asks → student answers → verifier scores → BKT updates → next prompt adapts.**

---

### 3.10 Persona Guardrails (Safety Layer)

**Module:** `part1_companion/persona/guardrail.py` (SRS §5.1)

**Methodology — deterministic three-rule filter with automatic rewrite:**

1. **Toxicity/demotivation blocklist** (substring match, case-insensitive): *"hopeless", "why can't you even", "this is easy", "give up", "you're bad at", "too late for you", "stop trying"* → `DENIED`.
2. **Ungrounded-stat detection:** every number/percentage in the candidate text is regex-extracted (`\b\d+(\.\d+)?%?`) and must exist in the ground-truth facts dict (mastery values are checked both as fraction and ×100). Any number the robot cannot prove about the student → `DENIED`. This kills the classic LLM failure of inventing "You're 95% ready!".
3. **Auto-rewrite:** denied text is replaced by a grounded template using real facts:

   > "Let's focus on {topic}. You're currently at {mastery_pct}% mastery with {days_left} days left until your {exam} exam. You've got this!"

The guardrail is a **choke point**: every path that speaks or displays tutor text (session loop, web dashboard, server) passes through `check()` first.

---

### 3.11 Playful Accountability Engine

**Module:** `part1_companion/persona/accountability.py` + `part2_knowledge/memory/store.py` (`student_activity` table).

**Methodology:** every nudge is assembled **from verified facts only** (BKT mastery %, days-left, nearest exam, recent activity history). Rules enforced by design and by tests:
- Sarcasm targets **procrastination or the robot itself**, never the student's intelligence/appearance/identity.
- Every nudge ends with a small, achievable next action ("Give me one focused {topic} question…").
- Student replies are persisted (`student_reply`); the response adapts — fatigue words ("tired", "later", "busy", "can't") trigger a *two-minute deal* micro-commitment; silence gets a zero-pressure starter.
- All outputs re-pass the guardrail (3.10) before speaking.

---

### 3.12 Prosody & Choreography Mapping

**Modules:** `part1_companion/voice/tts.py`, `part1_companion/expression/choreography.py`, `part1_companion/expression/face.py`, `part1_companion/hardware/*`

**Prosody tables (intervention level / emotion → tone):**

| Intervention level | Tone | Emotion | Tone |
|---|---|---|---|
| gentle | soft | engaged | neutral |
| firm | neutral | confused / distracted / frustrated | soft |
| escalated | urgent | bored | urgent |

`pyttsx3` maps tone → speech rate: `soft` = base − 30 wpm, `urgent` = base + 40 wpm. (Piper and ElevenLabs are supported alternates; `TTS_SILENT=1` forces console mode for CI.)

**Choreography engine** maps event classes → `(face emotion, servo pose dict, prosody tone)`:

| Event | Face | Pose (pan°, tilt°, L°, R°) | Tone |
|---|---|---|---|
| intervention `gentle` | curious | (+15, +5, 0, 0) | soft |
| intervention `firm` | concerned | (−15, −10, 20, 20) | soft |
| intervention `escalated` | alert | (0, +15, 45, 45) | urgent |
| tutor response | happy | (0, 0, 10, 10) | neutral |
| exam alert | alert | (0, +20, 30, 30) | urgent |

**Face vocabulary:** 8 bitmap emotional states rendered on the SSD1306 — `idle, watching, listening, thinking, curious, happy, concerned, alert` — with three sink backends: `LumaScreen` (real OLED via I2C `0x3C`), `WindowSink` (console preview), `FileSink` (PNG/text capture for CI artifacts).

---

## 4. Models & Training

SmartEduSync uses **pre-trained, configuration-driven models** — a deliberate methodology choice for a privacy-first capstone (no student data is ever collected to train anything).

| Component | Model | Role | "Training" status |
|---|---|---|---|
| Face landmarks | **MediaPipe Face Mesh** (478-pt, refined) | EAR + yaw features for engagement | Pre-trained by Google; used frozen, on-device |
| Sentence embeddings | **all-MiniLM-L6-v2** (SentenceTransformers, 384-d) | Semantic RAG retrieval | Pre-trained; used frozen, L2-normalized |
| LLM tutor | **Phi-3.5-mini** via Ollama (alt: Llama 3.1) | Socratic dialogue generation | Pre-trained instruct model; *no fine-tuning* — pedagogy is enforced by the prompt contract (3.8) + post-hoc guardrails (3.10) instead |
| STT | **Faster-Whisper `tiny`** (CPU, int8) | Student speech transcription | Pre-trained; quantized for Pi-class CPU |
| Posture | Geometric rule (+ future CNN head over the 10-D feature vector) | Slouch detection | No training required in shipped version |
| Mastery | **BKT** (Bayesian parametric model) | Per-student topic mastery | Not trained from data — the 4 parameters are pedagogical priors updated by Bayes rule per answer |
| OCR | **Tesseract** (optional) | Image notes text extraction | Pre-trained system binary |

**Why prompt-contract instead of fine-tuning:** fine-tuning Phi-3.5 on a tutoring corpus would need (a) a licensed dataset, (b) GPU resources, and (c) would *reduce* auditability. The capstone methodology instead enforces pedagogy at three deterministic layers — prompt rules, guardrail filter, grounding verifier — each individually unit-testable. This is the defensible engineering trade-off for a safety-adjacent educational robot.

**Model sizing on the Raspberry Pi 5:** Whisper-tiny int8 (~75 MB), MiniLM (~90 MB), Phi-3.5-mini 4-bit Q4 via Ollama (~2.3 GB) — all fit the 8 GB Pi with the vision stack at 5 Hz.

---

## 5. Datasets & Data Sources

The system ships with **no external training dataset**; its data sources are runtime and local:

| Data source | Type | Used by | Notes |
|---|---|---|---|
| **Live webcam stream** | Sensor input @ 5 Hz | Engagement + posture perception | Frames processed in-memory; never stored or transmitted |
| **Student study material** | PDF / TXT / MD / CSV / HTML / images (OCR) / http(s) pages & PDFs / VTT transcripts | RAG corpus + dynamic GraphRAG | Stored locally in `study_materials.db`; 20 MB upload cap; video itself rejected (transcript required) |
| **`SAMPLE_CHUNKS`** | Built-in seed corpus (4 chunks: BKT, GraphRAG, Socratic method, calculus) | Fallback RAG index when no material uploaded | Ensures the tutor is grounded out-of-the-box |
| **Curated syllabus concept graph** | Hand-authored edges (3.7A) | GraphRAG expansion | Encodes prerequisite/subtopic pedagogy |
| **`bkt_mastery.db`** | Runtime-generated | BKT mastery + exam calendar | Seeded demo rows; grows through real answer outcomes |
| **`memory.db`** | Runtime-generated | Conversation log, doubts, answer outcomes, activity history | The robot's long-term memory of the student |
| **Synthetic test traces** | Scripted generators (`synthetic_trace_generator`, `synthetic_posture_frames`) | Unit tests + `--sim` mode | Deterministic sequences covering engaged/dip/absent/sustained-low/recovery |

**Dataset methodology note (for the thesis):** the project's evaluation datasets are *behavioral* (unit tests + soak runs + synthetic perception traces), not *statistical*. This is honest to report: the team validates correctness of every algorithm path deterministically, while accuracy of the heuristic engagement score on real populations is flagged as future work (§10).

---

## 6. Data Storage Schema

All persistence is SQLite (files in repo root):

| DB | Tables | Purpose |
|---|---|---|
| `bkt_mastery.db` | `student_mastery(student_id, topic, p_mastery)` PK(student,topic); `exams(subject, exam_date)` | Mastery probabilities + exam calendar |
| `memory.db` | `conversation_log(session_id, role, text, ts)`; `doubts(student_id, topic, note, ts)` PK(student,topic); `answer_outcomes(student_id, topic, correct, ts)`; `student_activity(student_id, activity_type, detail, ts)` | Dialogue memory, doubts, BKT ground-truth outcomes, accountability history |
| `study_materials.db` | `study_sources(id, student_id, source_name, source_type, created_at)`; `study_chunks(id, student_id, source_id, page, text)`; `concept_graphs(student_id PK, graph_json, updated_at)` | Per-student RAG corpus + serialized concept graph |
| `sample.index` | FAISS `IndexFlatIP` (384-d) | Syllabus vector index |

---

## 7. Hardware & Embedded Methodology

**Bill of materials:** Raspberry Pi 5 · PCA9685 16-ch PWM driver (I2C `0x40`, 50 Hz) · 4× MG90S servos · SSD1306 128×64 OLED (I2C `0x3C`) · USB webcam · microphone/speaker.

**Servo control methodology** (`hardware/servo.py`):
- MG90S pulse range 500–2400 µs @ 50 Hz → PCA9685 counts **102–491**.
- Angle→counts linear mapping per joint, **clamped to joint limits**: pan ±90° (ch 0), tilt ±45° (ch 1), hands 0–90° (ch 2–3).
- Optional **speed-limited ramp** (`speed_deg_s`): 20 ms step loop for benchtop-safe motion; on any exception → `park_all()` failsafe to neutral.
- **Mock parity:** `HARDWARE=mock` swaps SMBus for `MockBus` (register map + write log), so `tests/test_all.py` asserts actual register writes without hardware. Same binaries run on the Pi with `HARDWARE=real` (`/dev/i2c-1` via smbus2).

**Display methodology:** `RobotDisplay` strategy pattern over three sinks (Luma OLED / console / file capture) — the face state machine is hardware-independent and CI-testable.

---

## 8. Testing & Verification Methodology

**Master suite:** `tests/test_all.py` — 11 test groups, runnable via `pytest` or the built-in runner:

| Test | Verifies |
|---|---|
| `test_engagement_perception` | Ring-buffer SMA math, missing-face → None, EAR/yaw score bounds |
| `test_posture_detection` | Upright vs slouch classification on synthetic keypoints |
| `test_intervention_state_machine` | Gentle escalation timing, recovery → IDLE reset |
| `test_bkt_mastery` | Correct answer raises P(L); risk matrix (2 days, 0.3 → high) |
| `test_persona_guardrail` | Toxic denial, ungrounded-stat denial, clean pass |
| `test_accountability_personality` | Nudge contains true facts, passes guardrail, fatigue reply → two-minute deal |
| `test_hardware_mock` | MockBus write log, servo angle clamp, display file capture |
| `test_graphrag_context_expansion` | 1-hop expansion injects related concepts |
| `test_verifier` | Grounding overlap gate; keyword-recall answer scoring |
| `test_memory_store` | Doubts upsert + retrieval |
| `test_study_material_onboarding` | End-to-end ingest → chunk → graph build → retrieval |

**Additional verification layers:** `scripts/smoke_test.py` (dependency + module import sanity), `scripts/soak_session.py` (long-running multi-turn session across all subsystems), `demo/simulate_full_loop.py` (end-to-end event-bus exercise), `demo/run_engagement_demo.py` (perception visualization), `demo/simulate_quiz.py` / `simulate_exam_alert.py` / `simulate_tts.py` (per-subsystem demos). Face renders are captured to `artifacts/` for visual regression.

---

## 9. Privacy & Ethics Methodology

1. **Local-only inference:** MediaPipe, MiniLM, Whisper, and Ollama all run on-device; no frame, transcript, or mastery record leaves the machine in the default configuration.
2. **No biometric storage:** landmarks are consumed in-memory and discarded; nothing identifying is persisted.
3. **Fact-grounding as an ethical control:** the guardrail's ungrounded-stat rule means the robot *cannot* tell a student a false mastery percentage or false countdown — verified by test.
4. **Psychological safety:** banned-phrase list + accountability rules (never insult the student; sarcasm at procrastination/robot only; every nudge ends in an achievable action).
5. **SSRF/abuse hardening in ingestion:** loopback URLs rejected, 5 MB fetch cap, 20 MB upload cap, content-type sniffing, actionable errors instead of silent failures.

---

## 10. Limitations & Future Work

| Area | Current limitation | Planned direction |
|---|---|---|
| Engagement scoring | Hand-tuned EAR/yaw thresholds; single-student, front-facing assumption | Collect consented labeled sessions; small supervised calibrator (logistic regression / gradient boosting) over the heuristic features |
| Posture | Geometric rule shipped; CNN head designed (10-D features) but untrained | Train a compact CNN on a labeled posture dataset; fuse posture into `E_t` |
| BKT | Fixed priors; single-skill-per-topic | Fit P(T)/P(S)/P(G) per student via grid search over outcome logs; add multi-skill BKT or BKT+IRT hybrid |
| Retrieval | Material library uses lexical ranking by default; FAISS pipeline is syllabus-scoped | Unify both corpora under the FAISS index; hybrid dense+BM25 reranking |
| Concept graph | Sequential co-occurrence edges; relation typing mostly `subtopic` | LLM-assisted relation extraction (`prerequisite`, `contradicts`, `example-of`) with human review |
| STT | Google Web Speech API in mic mode (network dependency) | Full local Whisper streaming as the default mic path |
| Video material | Transcript-only ingestion | On-device speech extraction via Whisper |
| Evaluation | Deterministic/behavioral testing only | IRB-style consented classroom pilot; pre/post mastery gains vs. control |

---

*This document reflects the codebase as of September 2026. Update the version header when algorithms or schemas change — `integration/schemas.py` is the frozen contract both teams depend on.*
