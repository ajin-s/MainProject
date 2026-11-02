# SmartEduSync — Final Year Capstone Project Defense & Presentation Guide
**Group 07 | Department of Computer Science & Engineering | MBCCET**

---

## 1. Executive Summary & Vision

**SmartEduSync** is an edge-first, emotion-aware tabletop AI tutoring robot designed to assist students through personalized, Socratic learning. Unlike passive screen-based chatbots, SmartEduSync merges:
1. **Real-time Computer Vision & Ergonomics**: Face landmark tracking, rolling engagement calculation ($E_t \in [0, 1]$), and geometric neck-inclination slouch detection.
2. **Local Socratic Intelligence**: Retrieval-Augmented Generation (RAG via FAISS) coupled with concept graph expansion (GraphRAG via NetworkX) and hallucination verification.
3. **Adaptive Pedagogy**: Bayesian Knowledge Tracing (BKT) to model dynamic student mastery ($P(L_t)$) and calculate proximity-based exam risk.
4. **Physical Expressiveness**: PCA9685 16-channel PWM servo control (head pan/tilt, dual arm gestures) and SSD1306 128x64 OLED display showing 8 distinct emotional states.

---

## 2. End-to-End Architectural Diagram

```
                              +-------------------------------------------------+
                              |          SmartEduSync Central Session           |
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
    | • MediaPipe Face Landmarker  |                                        | • Socratic Dialogue Engine   |
    | • Rolling 2s Ring Buffer E_t |                                        | • PyMuPDF & Sentence-MiniLM  |
    | • Neck Angle Slouch Monitor  | <======= [Async Pub/Sub Event Bus] =======> | • FAISS Inner-Product Index  |
    | • Intervention State Machine |      (integration/event_bus.py)        | • NetworkX GraphRAG Concepts |
    | • Bayesian Knowledge Tracing |                                        | • Grounding & Fact Verifier  |
    | • PCA9685 Servos (I2C 0x40)  |                                        | • Persistent SQLite Memory   |
    | • 8-Emotion OLED / SVG Face  |                                        | • Web Dashboard (FastAPI)    |
    | • Vocal Prosody & STT Mic    |                                        | • Dynamic Material Onboard   |
    +------------------------------+                                        +------------------------------+
```

---

## 3. How to Launch the Complete Presentation Output

We have provided two foolproof launch methods:

### Method A: One-Click Windows Batch Launcher (Recommended)
Simply double-click:
```bat
launch_presentation.bat
```
*(Or in PowerShell: `.\launch_presentation.bat`)*

### Method B: Python Runner
Run from workspace root:
```bash
python run_presentation.py
```
This automatically:
1. Validates `bkt_mastery.db`, `memory.db`, and `study_materials.db`.
2. Pre-loads syllabus content and builds the NetworkX concept graph.
3. Launches the FastAPI server at `http://127.0.0.1:8000`.
4. Automatically opens the interactive presentation dashboard in your browser.
5. Prints the defense cheat-sheet in the terminal.

---

## 4. 5-Minute Live Presentation Walkthrough Script

| Time | Slide / Screen Action | Spoken Script / Talking Points |
|---|---|---|
| **0:00 - 0:45** | **Title Slide & Executive Summary** | *"Respected evaluators, we are Group 07 presenting SmartEduSync: a privacy-first tabletop AI tutoring robot. Traditional e-learning platforms are passive and don't know if a student is confused, slouching, or losing focus. SmartEduSync monitors student attention and posture in real time, responds Socratically using grounded local knowledge, and expresses emotions through its animated face and robotic head and hand gestures."* |
| **0:45 - 1:45** | **Dashboard Overview & Robot Face** | *(Point to the OLED Face on the screen)* *"SmartEduSync possesses an 8-state emotional vocabulary: idle, watching, listening, thinking, curious, happy, concerned, and alert. It is powered by an SSD1306 OLED hardware driver and PCA9685 servo driver operating over I2C at address 0x40. Notice the live I2C register stream showing 50 Hz PWM writes."* |
| **1:45 - 2:45** | **Perception, Rolling $E_t$, and Posture** | *(Click **Scenario 1: Engagement Dip**)* *"Perception uses MediaPipe to extract eye-aspect ratio (EAR) and head yaw. Rather than reacting to single blinks, we maintain a rolling 2-second ring buffer (10 samples at 5 Hz) to compute a stable engagement index $E_t$. When the student looks away, the intervention manager escalates to GENTLE, the robot turns its head, displays a concerned face, and delivers a fact-grounded Socratic study nudge."*<br>*(Click **Scenario 2: Slouch**)* *"Simultaneously, our posture detector calculates the neck inclination angle $\theta$. If $\theta > 15^\circ$, it flags SLOUCHING and penalizes engagement."* |
| **2:45 - 3:45** | **Socratic Tutor & GraphRAG** | *(Click preset question or use the 🎤 mic button)* *"Notice when the student asks 'Why do we calculate integrals in physics?', SmartEduSync does NOT spoil the direct answer. Using our Socratic engine, it asks guiding questions to help the student derive the answer. Our GraphRAG component queries a NetworkX knowledge graph to link related concepts like Riemann Sums, Area Under Curve, and PID controllers."* |
| **3:45 - 4:30** | **Bayesian Knowledge Tracing (BKT)** | *(Click **Scenario 4: Socratic Quiz** and submit an answer)* *"SmartEduSync models student understanding using Bayesian Knowledge Tracing. After every answer, the verifier evaluates semantic concept overlap, updating the mastery probability $P(L_t)$ in SQLite. It also calculates upcoming exam risk based on proximity and mastery level."* |
| **4:30 - 5:00** | **Conclusion & Q&A** | *"SmartEduSync runs entirely locally, preserving 100% student privacy without sending video or sensitive study habits to third-party cloud servers. We are now open for questions."* |

---

## 5. Examiner Questions & Defense Answers (Cheat Sheet)

### Q1: "Why do you use a 2-second rolling buffer for engagement instead of instantaneous frame classification?"
> **Answer**: *"A single frame classification is noisy—natural blinks, brief yaw movements, or occlusion can cause false negatives. By computing a rolling average across 10 samples at 5 Hz (2 seconds), we smooth out transients while maintaining sub-second responsiveness. If a face disappears completely, the state machine marks it as unknown rather than penalizing the student."*

### Q2: "How does Bayesian Knowledge Tracing (BKT) work in your project?"
> **Answer**: *"BKT models the student's mastery of each topic as a latent binary state with 4 classic parameters:
> - $P(L_0)$: Initial prior knowledge (default 0.50).
> - $P(T)$: Probability of learning transition from unlearned to learned (default 0.10).
> - $P(G)$: Probability of guessing correctly without mastery (default 0.20).
> - $P(S)$: Probability of slipping (making a mistake despite mastery, default 0.10).
> When an answer is evaluated, we compute the posterior probability and apply the learning update $P(L_t) = P(L_{t-1} \mid \text{obs}) + (1 - P(L_{t-1} \mid \text{obs})) \times P(T)$."*

### Q3: "How does GraphRAG prevent LLM hallucinations?"
> **Answer**: *"Standard vector RAG can pull isolated chunks out of context. Our GraphRAG maps syllabus documents into a NetworkX directed graph connecting concepts with semantic edges (e.g. `Calculus Integrals` $\xrightarrow{\text{approximated\_by}}$ `Riemann Sums`). When retrieving context, we expand the 1-hop neighborhood. Furthermore, our Verifier checks that every response shares sufficient concept overlap with the source chunks before speech or display output."*

### Q4: "How does the robot communicate with the physical hardware?"
> **Answer**: *"We implemented a decoupled hardware abstraction layer:
> - For servos: PCA9685 16-channel PWM controller via I2C at address `0x40` at 50 Hz. Channel 0 controls Head Yaw ($\pm 90^\circ$), Channel 1 controls Head Pitch ($\pm 45^\circ$), and Channels 2-3 control arms with joint-limit clamping and failsafe neutral parking.
> - For display: SSD1306 128x64 OLED display via I2C at `0x3C`.
> - In testing/demonstration, our `MockBus` records every register write, verifying identical protocol compliance."*

### Q5: "How is student posture calculated?"
> **Answer**: *"Rather than using an opaque black-box deep learning model for posture, we use transparent geometric calculations from MediaPipe Pose landmarks:
> 1. Mid-ear point $(x_e, y_e)$ and mid-shoulder point $(x_s, y_s)$.
> 2. Neck angle $\theta = \arctan(|\Delta x| / |\Delta y|)$ relative to the vertical axis.
> 3. Vertical ear-shoulder distance relative to shoulder width.
> If $\theta > 15^\circ$ or the vertical ratio drops below 0.50, the posture is classified as `SLOUCHING` and applies a fused penalty to the engagement score."*

---

## 6. Verification & Test Suite Summary

All unit and integration tests have been thoroughly executed and verified:

```
--- Running SmartEduSync Unit Tests ---
  [PASS] test_engagement_perception      (Rolling buffer, EAR/yaw scoring)
  [PASS] test_posture_detection          (Upright vs slouching neck angle)
  [PASS] test_intervention_state_machine (IDLE -> GENTLE -> FIRM recovery)
  [PASS] test_bkt_mastery                (Bayesian parameter update & exam risk)
  [PASS] test_persona_guardrail          (Toxic phrase rejection & fact check)
  [PASS] test_accountability_personality (Playful nudge generation & reply)
  [PASS] test_hardware_mock              (PCA9685 register writes & display)
  [PASS] test_graphrag_context_expansion (NetworkX 1-hop concept expansion)
  [PASS] test_verifier                   (Grounding checks & answer evaluation)
  [PASS] test_memory_store               (SQLite conversation, doubts & answers)
  [PASS] test_rag_and_socratic_pipeline  (End-to-end question & answer turns)
  [PASS] test_study_material_onboarding  (PDF/Text ingestion & chunking)

[SUCCESS] 12/12 Tests PASSED (100% Pass Rate)
```

---
*Created for Group 07 Capstone Presentation Defense.*
