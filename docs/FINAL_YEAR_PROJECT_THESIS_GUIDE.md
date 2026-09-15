# SmartEduSync — Final Year Engineering Capstone Project Thesis & Defense Guide

**Project Title**: SmartEduSync: Privacy-First, Emotion-Aware Tabletop AI Tutoring Robot  
**Group / Team**: Group 07 (MBCCET)  
**Domain**: Artificial Intelligence, Computer Vision, Robotics, Natural Language Processing, Embedded Systems  
**Architecture**: Decoupled Dual-Engine System Linked by Asynchronous Pub/Sub Event Bus  

---

## 🛠️ Technologies and Tools Used

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


## 1. Executive Summary & Abstract

**SmartEduSync** is an autonomous tabletop tutoring robot designed to solve two key challenges in computer-assisted learning: (1) student disengagement during solo study, and (2) inaccurate or ungrounded responses in AI tutoring systems.

Unlike static web chatbots or cloud-dependent AI tools, SmartEduSync runs completely locally to ensure strict privacy protection. It combines real-time facial engagement tracking ($E_t$) with a Bayesian Knowledge Tracing (BKT) student model, a Socratic dialogue generator powered by local Large Language Models (LLM), Retrieval-Augmented Generation (RAG) over syllabus PDFs, NetworkX concept graphs (GraphRAG), safety/persona guardrails, and expressive robotic behaviors (OLED facial bitmaps and 4-axis servo movement).

---

## 2. Dual-Group Division of Work & Responsibilities

The project was engineered through a formal two-team collaborative architecture:

```
+---------------------------------------------------------------------------------------------------+
|                                  SMARTEDUSYNC CAPSTONE ARCHITECTURE                               |
+-----------------------------------+-----------------------------------+---------------------------+
| GROUP 1: COMPANION & EMOTION      | GROUP 2: KNOWLEDGE & INTELLIGENCE | JOINT INTEGRATION LAYER   |
| (part1_companion/)                | (part2_knowledge/)                | (integration/)            |
+-----------------------------------+-----------------------------------+---------------------------+
| • Computer Vision Perception      | • Local Ollama LLM Dialogue       | • Async Pub/Sub Event Bus |
|   (MediaPipe & OpenCV)            |   (phi3.5 / llama3.1)             |   (integration/event_bus) |
| • Engagement Smoothing (E_t)      | • Vector RAG Retrieval Engine     | • Frozen Pydantic Schemas |
| • Intervention State Machine      |   (SentenceTransformers + FAISS)  |   (integration/schemas)   |
|   (IDLE/GENTLE/FIRM/ESCALATED)    | • GraphRAG Concept Graph          | • Display Protocols       |
| • Bayesian Knowledge Tracing DB   |   (NetworkX 1-hop expansion)      |   (integration/display)   |
|   (bkt_mastery.db)                | • Socratic Tutor Generator        | • Master Session Runner   |
| • Safety & Persona Guardrails     |   (Guiding questions)             |   (integration/session)   |
|   (Toxicity & Fact Grounding)     | • Response Grounding Verifier     | • Web Presentation GUI    |
| • Speech Prosody & TTS / STT      |   (Hallucination checker)         |   (integration/web_dashboard)|
| • Hardware Drivers & Expressions  | • Persistent Memory Store         | • Master Test Suite       |
|   (PCA9685, SSD1306, Bitmaps)     |   (memory.db)                     |   (tests/test_all)        |
+-----------------------------------+-----------------------------------+---------------------------+
```

---

## 3. Mathematical Models & Core Algorithms

### 3.1 Rolling Engagement Index Smoothing
Raw frame engagement inputs $e_i \in [0, 1]$ from MediaPipe face landmark angle analysis are filtered using a rolling 2-second ring buffer (10 samples at 5 Hz):

$$E_t = \frac{1}{N} \sum_{i=0}^{N-1} e_i, \quad N=10$$

If no face is detected in frame, the system yields $E_t = \text{None}$ (classified as `unknown`), preventing false nag interventions when a student steps away.

---

### 3.2 Bayesian Knowledge Tracing (BKT) Update Model
BKT models a student's mastery of a skill as a hidden binary variable $L_t \in [0, 1]$.
Given parameters:
- $P(L_0)$: Initial mastery probability
- $P(T)$: Transition probability of learning
- $P(S)$: Slip probability (student knows skill, but makes a mistake)
- $P(G)$: Guess probability (student doesn't know skill, but guesses correctly)

Upon observing a student response:

**If Answer is Correct**:
$$P(L_t \mid \text{Correct}) = \frac{P(L_{t-1}) \cdot (1 - P(S))}{P(L_{t-1}) \cdot (1 - P(S)) + (1 - P(L_{t-1})) \cdot P(G)}$$

**If Answer is Incorrect**:
$$P(L_t \mid \text{Incorrect}) = \frac{P(L_{t-1}) \cdot P(S)}{P(L_{t-1}) \cdot P(S) + (1 - P(L_{t-1})) \cdot (1 - P(G))}$$

**State Transition**:
$$P(L_t) = P(L_t \mid \text{Obs}) + (1 - P(L_t \mid \text{Obs})) \cdot P(T)$$

---

### 3.3 PCA9685 16-Channel PWM Servo Pulse Calculation
At 50 Hz PWM refresh rate ($T = 20\text{ ms}$), 12-bit resolution divides each period into $4096$ counts ($4.88\ \mu\text{s/count}$).

For MG90S servos ($500\ \mu\text{s}$ to $2400\ \mu\text{s}$ pulse range):
$$\text{Counts}_{\text{min}} = \frac{500\ \mu\text{s}}{4.88\ \mu\text{s}} \approx 102, \quad \text{Counts}_{\text{max}} = \frac{2400\ \mu\text{s}}{4.88\ \mu\text{s}} \approx 491$$

Angle mapping function for joint angle $\theta \in [\theta_{\text{min}}, \theta_{\text{max}}]$:
$$\text{Counts}(\theta) = \text{Counts}_{\text{min}} + \left( \frac{\theta - \theta_{\text{min}}}{\theta_{\text{max}} - \theta_{\text{min}}} \right) \cdot (\text{Counts}_{\text{max}} - \text{Counts}_{\text{min}})$$

---

## 4. Verification Test Results Matrix

| Test Suite | File Path | Scope Covered | Status | Result |
|---|---|---|---|---|
| Smoke Test | `scripts/smoke_test.py` | Virtualenv & library import validation | PASS | 100% OK |
| Unit Test Suite | `tests/test_all.py` | All 8 subsystems (Perception, Intervention, BKT, Persona, Hardware, GraphRAG, Verifier, Memory) | PASS | 8/8 Passed |
| Intervention Demo | `demo/simulate_intervention.py` | State machine escalation gentle -> firm -> escalated & reset | PASS | PASSED |
| Exam Alert Demo | `demo/simulate_exam_alert.py` | Proximity + low mastery risk evaluation | PASS | PASSED |
| Quiz Demo | `demo/simulate_quiz.py` | Live BKT mastery updates | PASS | PASSED |
| TTS Demo | `demo/simulate_tts.py` | Speech prosody & tone modulation | PASS | PASSED |
| Full Loop Demo | `demo/simulate_full_loop.py` | Async Pub/Sub event bus pipeline | PASS | PASSED |
| Soak Test | `scripts/soak_session.py` | Long-running multi-turn session execution | PASS | 0 Errors |

---

## 5. Examiner Q&A Defense Guide

### Q1: How does SmartEduSync ensure student privacy?
**Answer**: SmartEduSync performs all computer vision, emotion tracking, BKT modeling, and LLM inference locally on device (using MediaPipe and local Ollama model instances). No camera feeds, voice audio, or student performance metrics leave the device or require cloud upload.

### Q2: How does the system handle hallucinated LLM responses?
**Answer**: Every candidate response generated by the Socratic tutor passes through a dual-stage safety choke point before being spoken or displayed:
1. **Persona Safety Guardrail (`persona/guardrail.py`)**: Validates numerical claims against grounded BKT database facts and screens for demotivating phrases.
2. **Grounding Verifier (`verify/verifier.py`)**: Computes keyword and semantic overlap against retrieved RAG chunks. Unverified claims are auto-rewritten into safe Socratic prompts.

### Q3: How do the two groups interface without breaking each other's code?
**Answer**: Group 1 and Group 2 interface exclusively through frozen Pydantic schemas defined in `integration/schemas.py` and the asynchronous Pub/Sub Event Bus in `integration/event_bus.py`. Neither team modifies the internal state of the other team's module; communication occurs strictly through event messages (`engagement.update`, `intervention.trigger`, `tutor.response`, `mastery.update`, `exam.alert`).

### Q4: How is hardware tested without physical servos connected?
**Answer**: Hardware drivers utilize the `I2CBus` abstraction layer (`hardware/bus.py`). In `HARDWARE=mock` mode, the `MockBus` records all PCA9685 register reads/writes and SSD1306 display bitmaps to memory logs and PNG files, proving 100% driver correctness prior to physical Pi wiring.

---

## 6. How to Run the Presentation Web Dashboard for Defense

To demonstrate the full working product to examiners:

1. Launch the Web Dashboard:
   ```bash
   python -m integration.web_dashboard
   ```
2. Open your web browser to:
   ```text
   http://127.0.0.1:8000
   ```
3. Use the dashboard to demonstrate:
   - **Live OLED Robot Face Display** (8 expressive emotion states).
   - **Real-Time Engagement Telemetry ($E_t$)** and simulated engagement dips.
   - **BKT Mastery & Exam Risk Badges**.
   - **Interactive Socratic Dialogue Console** with RAG and verifier scores.
   - **PCA9685 Servo Motor Angle Telemetry**.
