"""
SmartEduSync — Production Web Dashboard & Defense Presentation Interface.
Provides a modern glassmorphism GUI for real-time telemetry, live engagement graphs,
BKT student mastery progress, 8-emotion facial display, Socratic dialogue console,
and hardware servo monitoring.
"""
import asyncio
import os
import sys
import time
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from integration.event_bus import bus
from integration.schemas import EngagementUpdate, TutorResponse, TOPIC_ENGAGEMENT
from part1_companion.mastery.bkt import get_student_context, update_mastery, check_exam_risk
from part1_companion.persona.guardrail import check, rewrite
from part1_companion.persona.accountability import nudge_student, respond_to_student_reply
from part1_companion.hardware.servo import ServoController
from part1_companion.expression.face import get_face_art
from part1_companion.expression.choreography import ChoreographyEngine
from part2_knowledge.llm.dialogue import ask
from part2_knowledge.graphrag.graph_build import expand_rag_context
from part2_knowledge.tutor.socratic import generate_socratic_response
from part2_knowledge.verify.verifier import is_grounded
from part2_knowledge.memory.store import log_conversation, get_doubts
from part2_knowledge.rag.material_library import MaterialError, StudyMaterialLibrary

app = FastAPI(title="SmartEduSync Robot Control & Telemetry Dashboard", version="2.0.0")

# Shared state for real-time GUI telemetry
telemetry_state: Dict[str, Any] = {
    "student_id": "student_1",
    "E_t": 0.85,
    "emotion": "watching",
    "posture": "UPRIGHT",
    "neck_angle": 8.5,
    "is_slouching": False,
    "intervention_level": "IDLE",
    "active_topic": "Calculus Integrals",
    "p_mastery": 0.42,
    "days_left": 3,
    "nearest_exam": "Calculus Integrals",
    "exam_risk": "high",
    "servo_angles": {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0},
    "history": [],
}


servos = ServoController(force_mock=True)
choreo = ChoreographyEngine(servos)


class ChatPayload(BaseModel):
    message: str
    student_id: str = "student_1"


class SimEngagementPayload(BaseModel):
    E_t: float
    emotion: str = "distracted"


class AccountabilityReplyPayload(BaseModel):
    reply: str = ""
    student_id: str = "student_1"


@app.get("/api/status")
def get_status():
    ctx = get_student_context(telemetry_state["student_id"])
    telemetry_state["active_topic"] = ctx.get("active_topic", "Calculus Integrals")
    telemetry_state["p_mastery"] = ctx.get("p_mastery", 0.42)
    telemetry_state["days_left"] = ctx.get("days_left", 3)
    telemetry_state["nearest_exam"] = ctx.get("nearest_exam", "Calculus Integrals")
    telemetry_state["exam_risk"] = check_exam_risk(
        telemetry_state["active_topic"], telemetry_state["days_left"], telemetry_state["p_mastery"]
    )
    telemetry_state["face_art"] = get_face_art(telemetry_state["emotion"])
    telemetry_state["servo_angles"] = servos.current_angles
    return JSONResponse(content=telemetry_state)


@app.post("/api/simulate_engagement")
def simulate_engagement(payload: SimEngagementPayload):
    telemetry_state["E_t"] = max(0.0, min(1.0, payload.E_t))
    telemetry_state["emotion"] = payload.emotion
    if payload.E_t < 0.40:
        telemetry_state["intervention_level"] = "GENTLE"
        emo, face_art, pose, tone = choreo.express("intervention.trigger", {"level": "gentle"})
    else:
        telemetry_state["intervention_level"] = "IDLE"
        emo, face_art, pose, tone = choreo.express("perception.watching", {})
    return get_status()


@app.post("/api/accountability/nudge")
def accountability_nudge(student_id: str = "student_1"):
    """Generate a safe, fact-grounded playful reminder from locally stored study history."""
    context = get_student_context(student_id)
    message = nudge_student(student_id, context)
    telemetry_state["student_id"] = student_id
    telemetry_state["emotion"] = "curious"
    return {"response": message, "tone": "playful", "context": context}


@app.post("/api/accountability/reply")
def accountability_reply(payload: AccountabilityReplyPayload):
    """Accept a typed or speech-transcribed answer to the robot's reminder."""
    context = get_student_context(payload.student_id)
    response = respond_to_student_reply(payload.student_id, payload.reply, context)
    telemetry_state["student_id"] = payload.student_id
    telemetry_state["emotion"] = "happy"
    return {"response": response, "tone": "warm", "context": context}


materials = StudyMaterialLibrary()


class IngestUrlPayload(BaseModel):
    url: str
    topic: Optional[str] = "Web Ingested Material"


class IngestTextPayload(BaseModel):
    title: str
    content: str


@app.post("/api/ingest_url")
def ingest_url_endpoint(payload: IngestUrlPayload):
    try:
        result = materials.ingest_url(telemetry_state["student_id"], payload.url)
    except MaterialError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    telemetry_state["active_topic"] = payload.topic
    return {"status": "ok", **result}


@app.post("/api/ingest_text")
def ingest_text_endpoint(payload: IngestTextPayload):
    try:
        result = materials.ingest_bytes(
            telemetry_state["student_id"], f"{payload.title}.txt", payload.content.encode("utf-8")
        )
    except MaterialError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    telemetry_state["active_topic"] = payload.title
    return {"status": "ok", **result}


@app.post("/api/onboarding/material")
async def upload_study_material(
    request: Request,
    filename: str = Query(..., min_length=1),
    student_id: str = Query("student_1", min_length=1),
):
    """Accept a browser-selected PDF, text file, or image during first-run onboarding."""
    content = await request.body()
    if len(content) > 20_000_000:
        raise HTTPException(status_code=413, detail="Study material must be at most 20 MB.")
    try:
        result = materials.ingest_bytes(student_id, filename, content)
    except MaterialError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    telemetry_state["student_id"] = student_id
    return {"status": "ok", **result}


@app.get("/api/onboarding/{student_id}")
def material_onboarding_status(student_id: str):
    return materials.onboarding_status(student_id)


@app.get("/api/graph_nodes")
def get_graph_nodes():
    return JSONResponse(content=materials.onboarding_status(telemetry_state["student_id"]))




@app.post("/api/chat")
def process_chat(payload: ChatPayload):
    msg = payload.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    student_id = payload.student_id
    ctx = get_student_context(student_id)
    topic = ctx.get("active_topic", "Calculus Integrals")
    mastery = ctx.get("p_mastery", 0.42)

    log_conversation("web_session", "student", msg)

    base_ctx = materials.retrieve_context(student_id, msg) or f"Syllabus context for {topic}."
    rag_ctx = expand_rag_context(topic, base_ctx)

    tutor_res = generate_socratic_response(
        topic, rag_ctx, mastery, ask_llm_fn=ask, student_message=msg
    )

    # Safety Guardrail
    if check(tutor_res.text, ctx)["verdict"] == "DENIED":
        tutor_res.text = rewrite(tutor_res.text, ctx)

    # Grounding Verifier
    grounded = is_grounded(tutor_res.text, [rag_ctx])
    if not grounded:
        tutor_res.text = rewrite(tutor_res.text, ctx)

    # Expression & Pose
    emo, face_art, pose, tone = choreo.express("tutor.response", {})
    telemetry_state["emotion"] = "happy"
    telemetry_state["face_art"] = face_art

    log_conversation("web_session", "tutor", tutor_res.text)

    entry = {
        "user": msg,
        "tutor": tutor_res.text,
        "topic": topic,
        "grounded": grounded,
        "ts": time.strftime("%H:%M:%S"),
    }
    telemetry_state["history"].append(entry)

    return JSONResponse(
        content={
            "response": tutor_res.text,
            "topic": topic,
            "grounded": grounded,
            "ssml_hint": tutor_res.ssml_hint or "neutral",
            "telemetry": get_status().body.decode(),
        }
    )


@app.get("/", response_class=HTMLResponse)
def get_dashboard_html():
    return HTMLResponse(
        content="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartEduSync — AI Tutoring Robot Control & Telemetry</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --panel-bg: rgba(18, 26, 43, 0.75);
            --border: rgba(255, 255, 255, 0.08);
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --text: #f3f4f6;
            --text-dim: #9ca3af;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 24px;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.15), transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(139, 92, 246, 0.15), transparent 40%);
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo {
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 20px;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
        }

        .badge-team {
            background: rgba(59, 130, 246, 0.15);
            color: var(--accent-blue);
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .grid-container {
            display: grid;
            grid-template-columns: 340px 1fr 340px;
            gap: 20px;
        }

        .card {
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }

        .card-title {
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-dim);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .face-box {
            font-family: 'JetBrains Mono', monospace;
            background: #000;
            color: #00ff66;
            padding: 16px;
            border-radius: 12px;
            white-space: pre;
            font-size: 13px;
            text-align: center;
            line-height: 1.3;
            border: 1px solid rgba(0, 255, 102, 0.3);
            box-shadow: 0 0 15px rgba(0, 255, 102, 0.15);
            margin-bottom: 16px;
        }

        .stat-value {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(to right, #fff, var(--text-dim));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .progress-bar-bg {
            background: rgba(255, 255, 255, 0.1);
            height: 10px;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 8px;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(to right, var(--accent-blue), var(--accent-cyan));
            width: 42%;
            transition: width 0.5s ease;
        }

        .risk-badge {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .risk-high { background: rgba(239, 68, 68, 0.2); color: var(--accent-red); border: 1px solid var(--accent-red); }
        .risk-medium { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
        .risk-low { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }

        .chat-console {
            display: flex;
            flex-direction: column;
            height: 520px;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding-right: 8px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 16px;
        }

        .msg-bubble {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 14px;
            font-size: 14px;
            line-height: 1.5;
        }

        .msg-user {
            align-self: flex-end;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            color: #fff;
        }

        .msg-tutor {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
        }

        .chat-input-row {
            display: flex;
            gap: 10px;
        }

        input[type="text"] {
            flex: 1;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            padding: 12px 16px;
            border-radius: 10px;
            color: #fff;
            font-family: inherit;
            outline: none;
        }
        input[type="text"]:focus { border-color: var(--accent-blue); }

        button {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            color: #fff;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s, opacity 0.2s;
        }
        button:hover { opacity: 0.9; transform: translateY(-1px); }

        .servo-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .servo-box {
            background: rgba(0,0,0,0.2);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }
        .servo-val { font-family: 'JetBrains Mono'; font-weight: 600; color: var(--accent-cyan); }

        .sim-btn {
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red);
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 8px 12px;
            width: 100%;
            border-radius: 8px;
            margin-top: 10px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="brand-logo">S</div>
            <div>
                <h2>SmartEduSync</h2>
                <p style="font-size: 12px; color: var(--text-dim);">Privacy-First Tabletop AI Tutoring Robot</p>
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="badge-team">Team 1: Perception & Emotion</span>
            <span class="badge-team" style="border-color: rgba(139, 92, 246, 0.3); color: var(--accent-purple); background: rgba(139, 92, 246, 0.15);">Team 2: Socratic LLM & RAG</span>
        </div>
    </header>

    <div class="grid-container">
        <!-- Left Panel: Robot Face & Perception -->
        <div style="display: flex; flex-direction: column; gap: 20px;">
            <div class="card">
                <div class="card-title">
                    <span>OLED Display Face (128x64)</span>
                    <span id="face-emotion-badge" style="color: var(--accent-green); font-size: 11px;">WATCHING</span>
                </div>
                <div id="face-art" class="face-box">
    ( O )        ( O )    
                          
         =======          
                </div>
                <button class="sim-btn" onclick="triggerEngagementDip()">Simulate Engagement Dip (0.20)</button>
            </div>

            <div class="card">
                <div class="card-title">Engagement Telemetry (E_t)</div>
                <div id="et-value" class="stat-value">0.85</div>
                <div class="progress-bar-bg">
                    <div id="et-bar" class="progress-bar-fill" style="width: 85%;"></div>
                </div>
                <p style="font-size: 12px; color: var(--text-dim); margin-top: 8px;">Rolling 2s Ring Buffer (5 Hz)</p>
            </div>

            <div class="card">
                <div class="card-title">
                    <span>Posture & Slouch Monitor</span>
                    <span id="posture-badge" class="risk-badge risk-low">UPRIGHT</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                    <span style="font-size: 13px; color: var(--text-dim);">Neck Angle (&theta;):</span>
                    <span id="neck-angle-val" style="font-family: 'JetBrains Mono'; font-weight: 600; color: var(--accent-cyan);">8.5°</span>
                </div>
                <button class="sim-btn" style="background: rgba(245, 158, 11, 0.15); color: #f59e0b; border-color: rgba(245, 158, 11, 0.3);" onclick="triggerSlouch()">Simulate Slouching (32.5°)</button>
            </div>
        </div>


        <!-- Middle Panel: Socratic Tutor Dialogue -->
        <div class="card chat-console">
            <div class="card-title">
                <span>Socratic Dialogue & Verifier Console</span>
                <span style="font-size: 11px; color: var(--accent-blue);">Ollama / RAG Grounded</span>
            </div>
            <button style="align-self: flex-start; padding: 7px 10px; margin: -6px 0 10px;" onclick="requestStudyNudge()">Ask robot for a study nudge</button>
            <div style="margin: -4px 0 14px; padding: 10px; border: 1px dashed var(--border); border-radius: 10px; font-size: 12px;">
                <div style="margin-bottom: 8px; color: var(--text-dim);">First time here? Add your study materials to build your personal concept graph.</div>
                <input id="material-file" type="file" accept=".pdf,.txt,.md,.csv,.png,.jpg,.jpeg,.webp" multiple>
                <button style="padding: 7px 10px; margin-left: 6px;" onclick="uploadMaterials()">Analyse files</button>
                <div style="display:flex; gap:6px; margin-top:8px;"><input id="material-url" type="text" placeholder="https://… study page or PDF"><button style="padding: 7px 10px;" onclick="addMaterialUrl()">Analyse link</button></div>
                <div id="onboarding-status" style="margin-top: 7px; color: var(--accent-cyan);"></div>
            </div>
            <div id="chat-messages" class="chat-messages">
                <div class="msg-bubble msg-tutor">
                    Hello! I'm SmartEduSync. Let's work on Calculus Integrals today. Ask me any question or step through a problem.
                </div>
            </div>
            <div class="chat-input-row">
                <input type="text" id="chat-input" placeholder="Ask a question (e.g. Why do we use integrals in physics?)" onkeydown="if(event.key==='Enter') sendChat()">
                <button onclick="sendChat()">Send</button>
            </div>
        </div>

        <!-- Right Panel: BKT Mastery & Hardware Telemetry -->
        <div style="display: flex; flex-direction: column; gap: 20px;">
            <div class="card">
                <div class="card-title">
                    <span>BKT Mastery Tracker</span>
                    <span id="exam-risk" class="risk-badge risk-high">HIGH RISK</span>
                </div>
                <div style="font-size: 14px; font-weight: 600; margin-bottom: 4px;" id="topic-name">Calculus Integrals</div>
                <div id="mastery-pct" class="stat-value">42%</div>
                <div class="progress-bar-bg">
                    <div id="mastery-bar" class="progress-bar-fill" style="width: 42%;"></div>
                </div>
                <p style="font-size: 12px; color: var(--text-dim); margin-top: 12px;" id="exam-days">Nearest Exam: 3 days left</p>
            </div>

            <div class="card">
                <div class="card-title">PCA9685 Servo Angles (I2C 0x40)</div>
                <div class="servo-grid">
                    <div class="servo-box">
                        <div style="font-size: 11px; color: var(--text-dim);">Head Pan</div>
                        <div id="s0" class="servo-val">0.0°</div>
                    </div>
                    <div class="servo-box">
                        <div style="font-size: 11px; color: var(--text-dim);">Head Tilt</div>
                        <div id="s1" class="servo-val">0.0°</div>
                    </div>
                    <div class="servo-box">
                        <div style="font-size: 11px; color: var(--text-dim);">Left Arm</div>
                        <div id="s2" class="servo-val">0.0°</div>
                    </div>
                    <div class="servo-box">
                        <div style="font-size: 11px; color: var(--text-dim);">Right Arm</div>
                        <div id="s3" class="servo-val">0.0°</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let awaitingAccountabilityReply = false;

        function appendMessage(text, kind) {
            const message = document.createElement('div');
            message.className = 'msg-bubble ' + kind;
            message.textContent = text;
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.appendChild(message);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        async function uploadMaterials() {
            const files = Array.from(document.getElementById('material-file').files);
            const status = document.getElementById('onboarding-status');
            if (!files.length) { status.textContent = 'Choose one or more files first.'; return; }
            status.textContent = 'Analysing study material…';
            try {
                let chunks = 0;
                for (const file of files) {
                    const response = await fetch('/api/onboarding/material?student_id=student_1&filename=' + encodeURIComponent(file.name), {
                        method: 'POST', body: await file.arrayBuffer(), headers: { 'Content-Type': file.type || 'application/octet-stream' }
                    });
                    const result = await response.json();
                    if (!response.ok) throw new Error(result.detail || 'Upload failed');
                    chunks += result.chunks_added;
                }
                status.textContent = `Ready: analysed ${files.length} source(s), built ${chunks} study chunks.`;
            } catch (error) { status.textContent = 'Could not analyse material: ' + error.message; }
        }

        async function addMaterialUrl() {
            const input = document.getElementById('material-url');
            const status = document.getElementById('onboarding-status');
            if (!input.value.trim()) return;
            status.textContent = 'Fetching and analysing link…';
            try {
                const response = await fetch('/api/ingest_url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: input.value.trim() }) });
                const result = await response.json();
                if (!response.ok) throw new Error(result.detail || 'Link analysis failed');
                status.textContent = `Ready: added ${result.chunks_added} study chunks and updated the concept graph.`;
                input.value = '';
            } catch (error) { status.textContent = 'Could not analyse link: ' + error.message; }
        }

        async function requestStudyNudge() {
            try {
                const response = await fetch('/api/accountability/nudge', { method: 'POST' });
                const result = await response.json();
                if (!response.ok) throw new Error(result.detail || 'Could not create a nudge');
                appendMessage(result.response, 'msg-tutor');
                awaitingAccountabilityReply = true;
                document.getElementById('chat-input').placeholder = 'Reply to the robot—typed or speech-transcribed…';
            } catch (error) { console.error(error); }
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                document.getElementById('face-art').textContent = data.face_art || '';
                document.getElementById('face-emotion-badge').textContent = (data.emotion || 'watching').toUpperCase();
                document.getElementById('et-value').textContent = (data.E_t || 0).toFixed(2);
                document.getElementById('et-bar').style.width = ((data.E_t || 0) * 100) + '%';
                
                document.getElementById('topic-name').textContent = data.active_topic || '';
                const mPct = Math.round((data.p_mastery || 0) * 100);
                document.getElementById('mastery-pct').textContent = mPct + '%';
                document.getElementById('mastery-bar').style.width = mPct + '%';
                document.getElementById('exam-days').textContent = `Nearest Exam: ${data.days_left} days left (${data.nearest_exam})`;

                const riskBadge = document.getElementById('exam-risk');
                riskBadge.textContent = (data.exam_risk || 'low').toUpperCase() + ' RISK';
                riskBadge.className = 'risk-badge risk-' + (data.exam_risk || 'low');

                const postureBadge = document.getElementById('posture-badge');
                if (postureBadge) {
                    postureBadge.textContent = data.posture || 'UPRIGHT';
                    postureBadge.className = 'risk-badge risk-' + (data.is_slouching ? 'high' : 'low');
                }
                if (document.getElementById('neck-angle-val')) {
                    document.getElementById('neck-angle-val').textContent = (data.neck_angle || 0).toFixed(1) + '°';
                }

                if (data.servo_angles) {
                    document.getElementById('s0').textContent = (data.servo_angles[0] || 0).toFixed(1) + '°';
                    document.getElementById('s1').textContent = (data.servo_angles[1] || 0).toFixed(1) + '°';
                    document.getElementById('s2').textContent = (data.servo_angles[2] || 0).toFixed(1) + '°';
                    document.getElementById('s3').textContent = (data.servo_angles[3] || 0).toFixed(1) + '°';
                }
            } catch (e) {
                console.error(e);
            }
        }

        async function sendChat() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;

            const chatMessages = document.getElementById('chat-messages');
            appendMessage(text, 'msg-user');
            input.value = '';

            try {
                const endpoint = awaitingAccountabilityReply ? '/api/accountability/reply' : '/api/chat';
                const body = awaitingAccountabilityReply ? { reply: text } : { message: text };
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                appendMessage(data.response, 'msg-tutor');
                if (awaitingAccountabilityReply) {
                    awaitingAccountabilityReply = false;
                    input.placeholder = 'Ask a question (e.g. Why do we use integrals in physics?)';
                }
                fetchStatus();
            } catch (e) {
                console.error(e);
            }
        }

        async function triggerEngagementDip() {
            await fetch('/api/simulate_engagement', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ E_t: 0.20, emotion: 'frustrated' })
            });
            fetchStatus();
        }

        async function triggerSlouch() {
            await fetch('/api/simulate_slouch', { method: 'POST' });
            fetchStatus();
        }

        setInterval(fetchStatus, 2000);
        fetchStatus();
    </script>

</body>
</html>"""
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
