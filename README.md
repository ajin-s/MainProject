# SmartEduSync — Tabletop AI Tutoring Robot
**Group 07 (MBCCET) — Final Year Capstone Project**

SmartEduSync is a privacy-first, emotion-aware tabletop AI tutoring robot. It merges computer vision posture & engagement sensing with a local Socratic LLM, Retrieval-Augmented Generation (RAG), Bayesian Knowledge Tracing (BKT), NetworkX concept graphs, safety guardrails, and 4-axis servo movement.

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

## 🏗️ Architecture & Dual-Team Breakdown

- `part1_companion/` — **Team 1**: Perception (Engagement $E_t$ + Posture Slouch Detection), Intervention State Machine, BKT Mastery Tracking, Persona Safety Guardrails, Voice TTS/STT, PCA9685 Servo Hardware Drivers, SSD1306 Display.
- `part2_knowledge/` — **Team 2**: Local LLM Dialogue (Ollama), PyMuPDF + FAISS Vector RAG, NetworkX GraphRAG, Socratic Tutor Generator, Response Verifier, Persistent Memory Store, FastAPI Server.
- `integration/` — **Shared Integration**: Async Pub/Sub Event Bus, Pydantic Schemas, Display Protocol, Master Session Runner, Web Presentation Dashboard.

---

## 🚀 Quick Start & Execution Commands

```bash
# 1. Activate environment & verify dependencies
.venv\Scripts\activate
python scripts/smoke_test.py

# 2. Run master unit test suite (9 test suites)
python tests/test_all.py

# 3. Run master interactive session loop
python -m integration.session

# 4. Launch presentation Web Dashboard (http://127.0.0.1:8000)
python -m integration.web_dashboard

# 5. Run long-running session soak test
python -m scripts.soak_session
```

## 📚 First-Run Study Material Onboarding

On the dashboard, a student can add their personal study material before beginning a session.
The robot keeps extracted material locally in `study_materials.db`, builds a per-student concept
graph, and retrieves the relevant excerpts for every Socratic tutor response.

- Upload: text/Markdown/CSV notes, text-based PDFs, and images with OCR available.
- Link: public `http(s)` study pages or PDFs.
- Video: upload the accompanying transcript/captions as `.txt` or `.vtt` (video speech extraction
  is intentionally not bundled yet).

The same capability is available in the API:

```bash
# Raw body upload (PowerShell)
Invoke-WebRequest -Method Post -InFile .\notes.pdf `
  "http://127.0.0.1:8000/api/onboarding/material?student_id=student_1&filename=notes.pdf"

# Public web page or PDF
Invoke-RestMethod -Method Post -ContentType "application/json" `
  -Body '{"url":"https://example.com/study-notes"}' `
  http://127.0.0.1:8000/api/ingest_url
```

## 🤖 Persistent Playful Accountability

The robot keeps a local activity history in `memory.db`. It can recall recent interactions,
current BKT mastery, and the nearest exam to make short study reminders. Its sarcasm is playful
and directed at procrastination or itself—not the student—and every reminder ends with a small,
encouraging next action.

In the dashboard, select **Ask robot for a study nudge**, then type or speech-transcribe a reply
in the chat box. The robot stores that reply locally and responds with a supportive next step.

---

## 📄 Key Project Documentation Artifacts
- 📘 [`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md) — **Complete technical documentation**: all algorithms, methodologies, models & training, datasets, schemas, hardware, testing, and privacy.
- 📑 [`docs/PROJECT_DETAILS.md`](docs/PROJECT_DETAILS.md) — Comprehensive technical design doc.
- 🎓 [`docs/FINAL_YEAR_PROJECT_THESIS_GUIDE.md`](docs/FINAL_YEAR_PROJECT_THESIS_GUIDE.md) — Capstone thesis & defense guide with Q&A.
- 📌 [`docs/UPDATES_AND_NEXT_STEPS.md`](docs/UPDATES_AND_NEXT_STEPS.md) — System updates summary & hardware deployment roadmap.
- 📝 [`docs/EXECUTION_WALKTHROUGH.md`](docs/EXECUTION_WALKTHROUGH.md) — Step-by-step execution walkthrough.

