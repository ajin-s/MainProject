# SmartEduSync — Tabletop AI Tutoring Robot & Control Console

A privacy-first, emotion-aware tabletop AI tutoring robot web application built with **React**, **TypeScript**, and **Tailwind CSS**. Ported from the Capstone Group 07 architecture into a modern, unified control & telemetry interface.

---

## 🚀 Key Features

1. **Simulated SSD1306 128×64 OLED Face Display**:
   - 8 emotion states: `idle`, `watching`, `listening`, `thinking`, `curious`, `happy`, `concerned`, `alert`.
   - CRT phosphor scanline effects with real-time ASCII and state updates.

2. **Computer Vision & Perception Telemetry**:
   - Live engagement score ($E_t \in [0.0, 1.0]$) with rolling 2s ring buffer visualization (5 Hz).
   - Posture & slouch monitoring with neck angle ($\theta$), 25° threshold detection, and automatic intervention state transitions (`IDLE`, `GENTLE`, `MODERATE`, `HIGH`).
   - Interactive simulation sliders and triggers for defense demonstrations.

3. **Bayesian Knowledge Tracing (BKT) Engine**:
   - Probabilistic student mastery modeling with parameters $P(\text{transit}) = 0.1$, $P(\text{slip}) = 0.1$, and $P(\text{guess}) = 0.2$.
   - Exam risk classification (`high`, `medium`, `low`) joining active topic mastery and days left.
   - Interactive quiz mode allowing live answering and instantaneous $P(L_t)$ probability updates.

4. **Socratic Dialogue & Safety Guardrails**:
   - Pedagogical responses adapted to BKT mastery levels: scaffolding & intuitive analogies for low mastery, guided questioning for medium mastery, edge-case challenges for high mastery.
   - Persona guardrails enforcing non-toxic tone and strict factual numeric grounding.
   - Grounding verifier badge confirming syllabus alignment.

5. **Persistent Playful Accountability System**:
   - "Ask robot for a study nudge": generates witty, encouraging accountability reminders referencing student history and exam deadlines.
   - Contextual excuse and reply handling that prompts manageable next steps.

6. **GraphRAG Concept Topology**:
   - Interactive concept graph visualizer with 1-hop prerequisite and subtopic neighbor expansions.

7. **PCA9685 4-Axis Servo Telemetry (I2C 0x40)**:
   - Live monitoring of Head Pan, Head Tilt, Left Arm, and Right Arm MG90S servo angles.
   - Choreography action presets: "Nod Yes", "Shake No", "Celebration Wave", "Alert Pose", "Curious Tilt", and "Reset".

---

## 🛠️ Development & Execution

```bash
# Install dependencies
npm install

# Start development server on port 3000
npm run dev

# Build production bundle
npm run build
```
