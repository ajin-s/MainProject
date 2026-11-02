# SmartEduSync — Comprehensive Project Specification & Architectural Details

## 1. Executive Summary & Vision

**SmartEduSync** is a privacy-first, emotion-aware tabletop AI tutoring robot designed to assist students through personalized, Socratic learning. Developed by **Group 07 (MBCCET)** as a final-year engineering capstone project, it merges real-time computer vision and posture/engagement monitoring with local LLM intelligence, RAG, BKT, NetworkX knowledge graphs, safety guardrails, and expressive robotic behaviors.

### 🛠️ Technologies and Tools Used

| Category | Technology / Tool Stack |
|---|---|
| **Programming** | Python 3.11+ |
| **Computer Vision** | OpenCV, MediaPipe, NumPy |
| **Event Communication** | Pydantic v2, AsyncIO |
| **LLM** | Ollama, Phi-3.5-mini |
| **RAG** | PyMuPDF, LangChain, FAISS |
| **Knowledge Graph** | NetworkX |
| **Backend** | FastAPI, Uvicorn |
| **Voice** | Piper, SpeechRecognition, Faster-Whisper |
| **Display** | Luma.OLED, Pillow |
| **Hardware** | Raspberry Pi 5, PCA9685, MG90S Servos |
| **Database** | SQLite (`bkt_mastery.db`, `memory.db`) |
| **Testing** | Pytest |

---


The robot operates on two decoupled core engines linked by a shared event bus:
1. **Part 1 — Companion & Emotion Engine** (`part1_companion/`): Performs facial landmark analysis, engagement tracking ($E_t$), BKT mastery tracking, intervention state machine management, safety guardrails, expressiveness (face OLED/servo pose), and Text-to-Speech (TTS).
2. **Part 2 — Knowledge & Intelligence Engine** (`part2_knowledge/`): Manages local LLM dialogue (via Ollama), vector retrieval (FAISS), concept knowledge graphs (GraphRAG), Socratic prompt generation, response verification against hallucinations, and persistent memory.
3. **Integration Layer** (`integration/`): Enforces event schemas, manages an asynchronous Pub/Sub Event Bus, coordinates full interactive sessions (`session.py`), and maps display protocols.

---

## 2. Architecture Overview & Component Breakdown

```
                            +-------------------------------------------------+
                            |              SmartEduSync Main Loop             |
                            |            (integration/session.py)             |
                            +------------------------+------------------------+
                                                     |
                 +-----------------------------------+-----------------------------------+
                 |                                                                       |
                 v                                                                       v
  +------------------------------+                                        +------------------------------+
  |  Part 1: Companion Engine    |                                        |  Part 2: Knowledge Engine    |
  |  (part1_companion/)          |                                        |  (part2_knowledge/)          |
  +------------------------------+                                        +------------------------------+
  | • Perception (MediaPipe E_t) |                                        | • Local LLM (Ollama)         |
  | • Intervention State Machine |                                        | • FAISS Vector RAG           |
  | • BKT Mastery (SQLite)       | <======= [Async Pub/Sub Event Bus] =======> | • GraphRAG (NetworkX)        |
  | • Safety Guardrails          |      (integration/event_bus.py)        | • Socratic Tutor             |
  | • Persona & Tone Prosody     |                                        | • Verifier (Grounding Check) |
  | • Voice (TTS / STT)          |                                        | • Persistent Memory Store    |
  | • Hardware / Mock Drivers    |                                        | • FastAPI Server             |
  +------------------------------+                                        +------------------------------+
```

### 2.1 Part 1 — Companion & Emotion Engine (`part1_companion/`)

- **Perception (`perception/engagement.py`)**:
  - Monitors student presence and facial landmarks using OpenCV and MediaPipe Face Landmarker.
  - Computes raw engagement and maintains a rolling 2-second ring buffer (10 samples at 5 Hz) to compute a smoothed engagement index $E_t \in [0, 1]$.
  - Distinguishes missing faces (classified as `unknown`, skipping nagging) from genuine low engagement.

- **Intervention Manager (`intervention/state_machine.py`)**:
  - Implements a state machine for intervention levels: `IDLE`, `GENTLE`, `FIRM`, `ESCALATED`.
  - Monitors sustained low engagement streams. When engagement remains below `low_threshold` (e.g. $0.40$), it transitions states and attaches student context (active topic, mastery %, days until exam).

- **Bayesian Knowledge Tracing (`mastery/bkt.py`)**:
  - Uses standard BKT parameter updates ($P(L_0), P(T), P(S), P(G)$) stored in SQLite (`bkt_mastery.db`).
  - Tracks per-student topic mastery probabilities and upcoming exam schedules (`exams` table).
  - Calculates exam risk score (`LOW`, `MEDIUM`, `HIGH`) based on proximity (days left) and mastery probability ($p_{mastery}$).

- **Safety & Persona Guardrail (`persona/guardrail.py`)**:
  - Filters generated text for toxic, demotivating language (e.g., "hopeless", "give up").
  - Verifies factual grounding of numerical stats (percentages, days) against true student context facts.
  - Auto-rewrites non-compliant responses into safe, encouraging, grounded templates.

- **Voice & Speech (`voice/tts.py`, `voice/stt.py`)**:
  - Text-to-Speech (TTS): Supports pyttsx3, Piper TTS, and ElevenLabs API. Dynamically adjusts speech rate and pitch based on intervention level (`gentle` vs `escalated`) and emotion (`curious`, `concerned`).
  - Speech-to-Text (STT): Mic capture using SpeechRecognition / sounddevice.

- **Hardware & Expression (`hardware/`, `expression/`)**:
  - `bus.py`: Unified I2C interface supporting physical hardware or `MockBus` register logging for headless/benchtop testing.
  - `servo.py`: PCA9685 16-channel PWM driver managing head pan/tilt and arm motion with joint limits and failsafe parking.
  - `display.py`: SSD1306 OLED (128x64) driver supporting live rendering, window sink, or file PNG capture.
  - `expression/`: Renders 8 expressive facial states (`idle`, `watching`, `listening`, `thinking`, `curious`, `happy`, `concerned`, `alert`) and coordinates bodily pose choreography.

---

### 2.2 Part 2 — Knowledge & Intelligence Engine (`part2_knowledge/`)

- **Local LLM Dialogue (`llm/dialogue.py`)**:
  - Integrates local LLM inference via Ollama (`phi3.5`, `llama3.1`) with fallback mock mode for testing environments without local model binaries.

- **Vector RAG Ingestion & Retrieval (`rag/ingest.py`)**:
  - Ingests syllabus documents (PDFs via PyMuPDF).
  - Chunks text into semantic segments, computes embeddings using `SentenceTransformer('all-MiniLM-L6-v2')`, and builds a normalized inner-product FAISS vector index (`faiss.IndexFlatIP`).

- **GraphRAG Concept Expansion (`graphrag/graph_build.py`)**:
  - Represents topic relationships in a NetworkX directed graph (`DiGraph`).
  - Expands retrieved RAG hits by fetching 1-hop related concept nodes to ground Socratic questions in holistic syllabus contexts.

- **Socratic Tutor (`tutor/socratic.py`, `tutor/flashcards.py`)**:
  - Generates guiding questions that prompt the student to reason toward the solution rather than providing direct answers.
  - Generates multi-line display flashcards derived from top syllabus chunks.

- **Verification Engine (`verify/verifier.py`)**:
  - Ensures response factual grounding before outputting to voice or screen.
  - Evaluates student answers against expected answer points to supply BKT with ground-truth correctness flags.

- **FastAPI Service (`server.py`)**:
  - Exposes RESTful endpoint `POST /chat` with session tracking, auto-retrieval, Socratic generation, and verification gating.

- **Persistent Memory Store (`memory/store.py`)**:
  - SQLite database (`memory.db`) storing `conversation_log`, `doubts` (recorded student struggle topics), and `answer_outcomes`.

---

### 2.3 Integration Layer (`integration/`)

- **Event Schemas (`schemas.py`)**:
  - Freezes standard data exchange models:
    - `EngagementUpdate`: $E_t \in [0, 1]$, `emotion`, timestamp.
    - `InterventionTrigger`: `level` (`gentle`, `firm`, `escalated`), `reason`, `topic`, timestamp.
    - `TutorResponse`: `text`, `ssml_hint`, `topic`, `confidence`, timestamp.
    - `MasteryUpdate`: `topic`, `p_mastery`, timestamp.
    - `ExamAlert`: `subject`, `days_left`, `risk` (`low`, `medium`, `high`), timestamp.

- **Event Bus (`event_bus.py`)**:
  - In-process asynchronous Pub/Sub broker enabling decoupled module communication via `.subscribe(topic, handler)` and `await .publish(topic, message)`.

- **Session Controller (`session.py`)**:
  - Main event loop bringing perception, intervention, Socratic tutoring, guardrails, memory, hardware expression, and voice together into an active learning session.

---

## 3. Data Schemas & Topics

| Topic Name Constant | Topic String | Schema Class | Publisher | Subscribers |
|---|---|---|---|---|
| `TOPIC_ENGAGEMENT` | `engagement.update` | `EngagementUpdate` | Perception Service | Intervention Manager, UI Display |
| `TOPIC_INTERVENTION` | `intervention.trigger` | `InterventionTrigger` | Intervention State Machine | Socratic Tutor, Expression Controller |
| `TOPIC_TUTOR_RESPONSE` | `tutor.response` | `TutorResponse` | Socratic Tutor | Persona Guardrail, Verifier, Voice TTS |
| `TOPIC_MASTERY` | `mastery.update` | `MasteryUpdate` | BKT Tracker | State Machine, Server Memory |
| `TOPIC_EXAM_ALERT` | `exam.alert` | `ExamAlert` | BKT Tracker | UI Display, Voice TTS |

---

## 4. Hardware & Mock Protocol Specification

- **PWM Controller**: PCA9685 I2C @ `0x40`, 50 Hz PWM clock.
  - Channel 0: Head Pan (Yaw) — Range $\pm 90^\circ$ (Pulse $102$ to $491$)
  - Channel 1: Head Tilt (Pitch) — Range $\pm 45^\circ$
  - Channels 2–3: Left / Right Hand Actuators
- **Display**: SSD1306 128x64 OLED display via I2C (`0x3C`) or SPI.
- **Environment Driver Toggle**:
  - `HARDWARE=mock`: Logs register reads/writes to `MockBus` memory without requiring physical I2C device nodes.
  - `HARDWARE=real`: Connects directly to Linux `/dev/i2c-1` via SMBus / Adafruit libraries.

---

## 5. Verification & Testing Strategy

1. **Unit Tests**:
   - `test_engagement.py`: Verify ring-buffer smoothing and missing face handling.
   - `test_intervention.py`: Confirm escalation timing and state resets.
   - `test_bkt.py`: Test BKT updates, database context queries, and exam risk logic.
   - `test_guardrail.py`: Validate toxic phrase rejection and ungrounded stat detection.
   - `test_rag_and_socratic.py`: Test sentence embedding, FAISS index search, and Socratic prompt generation.
   - `test_verifier.py`: Validate grounding verifier and student answer evaluator.
   - `test_hardware.py`: Test PCA9685 mock bus register writes and display bitmap generation.
2. **Integration Soak & Demo Scripts**:
   - `demo/simulate_full_loop.py`: End-to-end event bus execution.
   - `demo/soak_session.py`: Long-running session verification across all subsystems.

---

## 6. Document Summary

This specification serves as the definitive reference manual for **SmartEduSync**. All subsequent code modifications and additions maintain strict adherence to these interfaces, guardrail rules, and architectural boundaries.
