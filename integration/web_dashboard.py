"""
SmartEduSync — Production Web Dashboard & Defense Presentation Interface.
Provides a modern glassmorphism GUI for real-time telemetry, live engagement graphs,
BKT student mastery progress, 8-emotion facial display, Socratic dialogue console,
GraphRAG concept visualization, and hardware servo monitoring.
"""
import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from part1_companion.mastery.bkt import get_student_context, check_exam_risk, update_mastery, init_db
from part1_companion.persona.accountability import nudge_student, respond_to_student_reply
from part1_companion.hardware.servo import ServoController
from part1_companion.expression.face import get_face_art, FACE_BITMAPS
from part1_companion.expression.choreography import ChoreographyEngine
from part2_knowledge.rag.material_library import MaterialError, StudyMaterialLibrary
from part2_knowledge.tutor.pipeline import run_tutor_turn
from part2_knowledge.graphrag.graph_build import build_sample_graph
from part2_knowledge.tutor.quiz import generate_quiz_item
from part2_knowledge.verify.verifier import evaluate_student_answer
from part2_knowledge.memory.store import record_answer_outcome

app = FastAPI(title="SmartEduSync Robot Control & Telemetry Dashboard", version="2.2.0")

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
    "p_mastery": 0.75,
    "days_left": 3,
    "nearest_exam": "Calculus Integrals",
    "exam_risk": "low",
    "servo_angles": {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0},
    "history": [],
}

servos = ServoController(force_mock=True)
choreo = ChoreographyEngine(servos)
materials = StudyMaterialLibrary()

# Seed default materials if database is fresh
def _seed_default_materials():
    try:
        status = materials.onboarding_status("student_1")
        if not status["initialized"]:
            sample_content = (
                "Calculus Integrals measure the total accumulation of a quantity, which is the signed area under a curve. "
                "A Riemann sum approximates an integral by adding the areas of thin rectangles under a function. "
                "The Fundamental Theorem of Calculus links differentiation and integration: the derivative of an accumulated integral "
                "recovers the original function. Definite Integrals calculate exact accumulation within upper and lower limits. "
                "Linear Algebra studies vector spaces, linear transformations, and Matrix Multiplication. Eigenvalues describe axes "
                "that a transformation only scales. In Robotics, Kinematics maps joint servo angles to end-effector positions. "
                "A PID controller reduces tracking error using Proportional, Integral, and Derivative control feedback."
            )
            materials.ingest_bytes("student_1", "Syllabus_Core_Concepts.txt", sample_content.encode("utf-8"))
    except Exception as e:
        print(f"[Seed] Material seed notice: {e}")

_seed_default_materials()


def format_i2c_log(write_log: List[Tuple[int, int, int]]) -> List[Dict[str, str]]:
    meaning_map = {
        0x00: "MODE1 (Normal/Sleep)",
        0x01: "MODE2 (Output Logic)",
        0xFE: "PRESCALE (50Hz Clock)",
        0x06: "Ch0 Pan ON_L",
        0x07: "Ch0 Pan ON_H",
        0x08: "Ch0 Pan OFF_L",
        0x09: "Ch0 Pan OFF_H",
        0x0A: "Ch1 Tilt ON_L",
        0x0B: "Ch1 Tilt ON_H",
        0x0C: "Ch1 Tilt OFF_L",
        0x0D: "Ch1 Tilt OFF_H",
        0x0E: "Ch2 LeftArm ON_L",
        0x0F: "Ch2 LeftArm ON_H",
        0x10: "Ch2 LeftArm OFF_L",
        0x11: "Ch2 LeftArm OFF_H",
        0x12: "Ch3 RightArm ON_L",
        0x13: "Ch3 RightArm ON_H",
        0x14: "Ch3 RightArm OFF_L",
        0x15: "Ch3 RightArm OFF_H",
    }
    formatted = []
    for addr, reg, val in write_log[-20:]:
        formatted.append({
            "addr": f"0x{addr:02X}",
            "reg": f"0x{reg:02X}",
            "val": f"0x{val:02X}",
            "desc": meaning_map.get(reg, f"PCA9685 Register 0x{reg:02X}")
        })
    return formatted


class ChatPayload(BaseModel):
    message: str
    student_id: str = "student_1"


class SimEngagementPayload(BaseModel):
    E_t: float
    emotion: str = "distracted"


class AccountabilityReplyPayload(BaseModel):
    reply: str = ""
    student_id: str = "student_1"


class QuizSubmitPayload(BaseModel):
    topic: str
    question: str
    student_answer: str
    expected_keywords: List[str] = []
    student_id: str = "student_1"


@app.get("/api/status")
def get_status():
    ctx = get_student_context(telemetry_state["student_id"])
    telemetry_state["active_topic"] = ctx.get("active_topic", "Calculus Integrals")
    telemetry_state["p_mastery"] = ctx.get("p_mastery", 0.75)
    telemetry_state["days_left"] = ctx.get("days_left", 3)
    telemetry_state["nearest_exam"] = ctx.get("nearest_exam", "Calculus Integrals")
    telemetry_state["exam_risk"] = check_exam_risk(
        telemetry_state["active_topic"], telemetry_state["days_left"], telemetry_state["p_mastery"]
    )
    telemetry_state["face_art"] = get_face_art(telemetry_state["emotion"])
    telemetry_state["servo_angles"] = servos.current_angles
    telemetry_state["i2c_write_count"] = len(servos.bus.write_log) if hasattr(servos.bus, "write_log") else 0
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


@app.post("/api/simulate_slouch")
def simulate_slouch():
    """Simulates student neck angle dropping past 30 deg (slouching)."""
    telemetry_state["posture"] = "SLOUCHING"
    telemetry_state["neck_angle"] = 32.5
    telemetry_state["is_slouching"] = True
    # Fused penalty applied to engagement
    penalty = 0.22
    telemetry_state["E_t"] = max(0.15, round(telemetry_state["E_t"] - penalty, 2))
    telemetry_state["emotion"] = "concerned"
    telemetry_state["intervention_level"] = "GENTLE"
    emo, face_art, pose, tone = choreo.express("intervention.trigger", {"level": "firm"})
    telemetry_state["face_art"] = face_art
    telemetry_state["servo_angles"] = servos.current_angles
    return get_status()


@app.post("/api/simulate_upright")
def simulate_upright():
    """Restores student posture to healthy upright alignment."""
    telemetry_state["posture"] = "UPRIGHT"
    telemetry_state["neck_angle"] = 7.8
    telemetry_state["is_slouching"] = False
    telemetry_state["E_t"] = 0.88
    telemetry_state["emotion"] = "watching"
    telemetry_state["intervention_level"] = "IDLE"
    emo, face_art, pose, tone = choreo.express("perception.watching", {})
    telemetry_state["face_art"] = face_art
    telemetry_state["servo_angles"] = servos.current_angles
    return get_status()


@app.post("/api/simulate_exam_alert")
def simulate_exam_alert():
    """Triggers high-risk upcoming exam escalation."""
    telemetry_state["days_left"] = 2
    telemetry_state["p_mastery"] = 0.35
    telemetry_state["exam_risk"] = "high"
    telemetry_state["emotion"] = "alert"
    telemetry_state["intervention_level"] = "ESCALATED"
    emo, face_art, pose, tone = choreo.express("exam.alert", {"level": "escalated"})
    telemetry_state["face_art"] = face_art
    telemetry_state["servo_angles"] = servos.current_angles
    return get_status()


@app.post("/api/set_emotion/{emotion}")
def set_emotion(emotion: str):
    """Directly sets one of the 8 robot facial vocabulary states."""
    valid = ("idle", "watching", "listening", "thinking", "curious", "happy", "concerned", "alert")
    emo = emotion.lower() if emotion.lower() in valid else "watching"
    telemetry_state["emotion"] = emo
    emo, face_art, pose, tone = choreo.express("manual.set", {"emotion": emo})
    telemetry_state["face_art"] = face_art
    telemetry_state["servo_angles"] = servos.current_angles
    return get_status()


@app.get("/api/hardware/i2c_log")
def get_i2c_log():
    """Returns the live MockBus register write trace."""
    if hasattr(servos.bus, "write_log"):
        return JSONResponse(content={"log": format_i2c_log(servos.bus.write_log)})
    return JSONResponse(content={"log": []})


@app.get("/api/graph_data")
def get_graph_data():
    """Returns nodes and edges for the GraphRAG interactive canvas."""
    default_nodes = [
        {"id": "Calculus Integrals", "category": "core", "x": 310, "y": 180, "desc": "Accumulation & signed area under curve"},
        {"id": "Riemann Sums", "category": "method", "x": 140, "y": 110, "desc": "Approximates integrals via thin rectangles"},
        {"id": "Definite Integrals", "category": "concept", "x": 480, "y": 110, "desc": "Accumulation over defined bounds [a, b]"},
        {"id": "Fundamental Theorem of Calculus", "category": "theorem", "x": 310, "y": 300, "desc": "Inversion between derivatives and integrals"},
        {"id": "Area Under Curve", "category": "concept", "x": 120, "y": 240, "desc": "Physical & geometric meaning of integral"},
        {"id": "Differentiation", "category": "prerequisite", "x": 500, "y": 290, "desc": "Instantaneous rate of change"},
        {"id": "Robotics Kinematics", "category": "application", "x": 500, "y": 190, "desc": "Mapping joint angles to spatial position"},
        {"id": "PID Controllers", "category": "application", "x": 130, "y": 340, "desc": "Error feedback with integral term"},
    ]
    default_edges = [
        {"source": "Calculus Integrals", "target": "Riemann Sums", "relation": "approximated_by"},
        {"source": "Calculus Integrals", "target": "Definite Integrals", "relation": "subtopic"},
        {"source": "Calculus Integrals", "target": "Fundamental Theorem of Calculus", "relation": "linked_by"},
        {"source": "Calculus Integrals", "target": "Area Under Curve", "relation": "measures"},
        {"source": "Fundamental Theorem of Calculus", "target": "Differentiation", "relation": "inverses"},
        {"source": "Robotics Kinematics", "target": "PID Controllers", "relation": "stabilized_by"},
        {"source": "PID Controllers", "target": "Calculus Integrals", "relation": "uses_integral_term"},
    ]
    return JSONResponse(content={"nodes": default_nodes, "edges": default_edges})


@app.get("/api/quiz/generate")
def get_quiz_question(topic: str = "Calculus Integrals"):
    """Generates a grounded Socratic quiz question on the active topic."""
    item = generate_quiz_item(topic)
    return JSONResponse(content=item)


@app.post("/api/quiz/submit")
def submit_quiz_answer(payload: QuizSubmitPayload):
    """Evaluates student quiz answer, updates BKT mastery, and logs memory outcome."""
    correct, score = evaluate_student_answer(payload.question, payload.expected_keywords, payload.student_answer)
    conn = init_db()
    new_mastery = update_mastery(conn, payload.student_id, payload.topic, correct=correct)
    record_answer_outcome(payload.student_id, payload.topic, correct)
    telemetry_state["p_mastery"] = new_mastery
    if correct:
        telemetry_state["emotion"] = "happy"
        emo, face_art, pose, tone = choreo.express("tutor.response", {})
    else:
        telemetry_state["emotion"] = "concerned"
        emo, face_art, pose, tone = choreo.express("intervention.trigger", {"level": "firm"})
    telemetry_state["face_art"] = face_art
    telemetry_state["servo_angles"] = servos.current_angles

    return JSONResponse(content={
        "correct": correct,
        "score": score,
        "new_mastery": new_mastery,
        "feedback": "Excellent reasoning! Your explanation aligns with syllabus concepts." if correct else "Good attempt! Review how thin rectangles approximate the accumulated area.",
    })


@app.post("/api/accountability/nudge")
def accountability_nudge(student_id: str = "student_1"):
    """Generate a safe, fact-grounded playful reminder from locally stored study history."""
    context = get_student_context(student_id)
    message = nudge_student(student_id, context)
    telemetry_state["student_id"] = student_id
    telemetry_state["emotion"] = "curious"
    emo, face_art, pose, tone = choreo.express("intervention.trigger", {"level": "gentle"})
    telemetry_state["face_art"] = face_art
    telemetry_state["servo_angles"] = servos.current_angles
    return {"response": message, "tone": "playful", "context": context}


@app.post("/api/accountability/reply")
def accountability_reply(payload: AccountabilityReplyPayload):
    """Accept a typed or speech-transcribed answer to the robot's reminder."""
    context = get_student_context(payload.student_id)
    response = respond_to_student_reply(payload.student_id, payload.reply, context)
    telemetry_state["student_id"] = payload.student_id
    telemetry_state["emotion"] = "happy"
    emo, face_art, pose, tone = choreo.express("tutor.response", {})
    telemetry_state["face_art"] = face_art
    telemetry_state["servo_angles"] = servos.current_angles
    return {"response": response, "tone": "warm", "context": context}


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


@app.post("/api/chat")
def process_chat(payload: ChatPayload):
    msg = payload.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    student_id = payload.student_id
    ctx = get_student_context(student_id)
    topic = ctx.get("active_topic", "Calculus Integrals")
    mastery = ctx.get("p_mastery", 0.75)

    tutor_res, diagnostics = run_tutor_turn(
        student_id, msg, topic, mastery, ctx, session_id="web_session"
    )
    grounded = bool(diagnostics.get("grounded", True))
    if diagnostics.get("bkt"):
        telemetry_state["p_mastery"] = diagnostics["bkt"]["p_mastery"]

    emo, face_art, pose, tone = choreo.express("tutor.response", {})
    telemetry_state["emotion"] = "happy"
    telemetry_state["face_art"] = face_art
    telemetry_state["servo_angles"] = servos.current_angles

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
    <title>SmartEduSync — Tabletop AI Tutoring Robot Control Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #070b13;
            --panel-bg: rgba(15, 23, 42, 0.78);
            --panel-border: rgba(255, 255, 255, 0.08);
            --panel-glow: rgba(59, 130, 246, 0.08);
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
            --text-dark: #64748b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            padding: 18px 24px 28px;
            background-image: 
                radial-gradient(circle at 10% 10%, rgba(59, 130, 246, 0.12), transparent 45%),
                radial-gradient(circle at 90% 90%, rgba(139, 92, 246, 0.12), transparent 45%),
                radial-gradient(circle at 50% 50%, rgba(6, 182, 212, 0.04), transparent 60%);
            background-attachment: fixed;
        }

        /* HEADER */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--panel-border);
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .brand-container {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-logo {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue), var(--accent-purple));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 22px;
            box-shadow: 0 0 25px rgba(6, 182, 212, 0.45);
        }

        .brand-text h1 {
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #fff, var(--text-dim));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-text p {
            font-size: 12px;
            color: var(--text-dim);
            font-weight: 400;
        }

        .header-pills {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--panel-border);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            color: var(--text-dim);
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 8px var(--accent-green);
        }

        /* DEFENSE SCENARIOS BAR */
        .scenarios-bar {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(59, 130, 246, 0.25);
            backdrop-filter: blur(16px);
            border-radius: 14px;
            padding: 10px 16px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
        }

        .scenarios-title {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--accent-cyan);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .scenarios-btns {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .sc-btn {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--panel-border);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .sc-btn:hover {
            background: var(--accent-blue);
            color: #fff;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
        }
        .sc-btn.danger:hover {
            background: var(--accent-red);
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35);
        }
        .sc-btn.amber:hover {
            background: var(--accent-amber);
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
        }

        /* GRID LAYOUT */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 350px 1fr 370px;
            gap: 20px;
        }

        @media (max-width: 1280px) {
            .dashboard-grid {
                grid-template-columns: 320px 1fr 340px;
                gap: 16px;
            }
        }

        @media (max-width: 1024px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        /* CARDS */
        .card {
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
            position: relative;
        }

        .card-title {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-dim);
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* ROBOT FACE OLED CONTAINER */
        .face-container {
            background: #000;
            border-radius: 14px;
            padding: 14px;
            border: 1px solid rgba(6, 182, 212, 0.3);
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.15) inset, 0 4px 16px rgba(0,0,0,0.5);
            position: relative;
            overflow: hidden;
            margin-bottom: 12px;
        }

        .face-scanlines {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(rgba(0,0,0,0) 0px, rgba(0,0,0,0) 2px, rgba(0, 255, 150, 0.03) 3px, rgba(0,0,0,0) 4px);
            pointer-events: none;
            z-index: 2;
        }

        /* SVG DIGITAL ROBOT FACE */
        .digital-face-svg {
            width: 100%;
            height: 120px;
            display: block;
        }

        .face-ascii-box {
            font-family: 'JetBrains Mono', monospace;
            color: #00ff88;
            white-space: pre;
            font-size: 13px;
            line-height: 1.35;
            text-align: center;
            display: none;
            padding: 10px 0;
        }

        .face-tab-row {
            display: flex;
            gap: 6px;
            margin-bottom: 10px;
        }

        .tab-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--panel-border);
            color: var(--text-dim);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
        }
        .tab-btn.active {
            background: rgba(6, 182, 212, 0.2);
            color: var(--accent-cyan);
            border-color: rgba(6, 182, 212, 0.4);
        }

        /* EMOTION PILLS */
        .emotion-pills {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 5px;
            margin-top: 10px;
        }

        .emo-pill {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--panel-border);
            color: var(--text-dim);
            padding: 5px 4px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.15s;
        }
        .emo-pill:hover, .emo-pill.active {
            background: rgba(6, 182, 212, 0.2);
            color: var(--accent-cyan);
            border-color: var(--accent-cyan);
        }

        /* METRIC CARDS */
        .stat-value {
            font-size: 34px;
            font-weight: 800;
            letter-spacing: -1px;
            background: linear-gradient(to right, #fff, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .progress-bar-bg {
            background: rgba(255, 255, 255, 0.08);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(to right, var(--accent-cyan), var(--accent-blue));
            width: 85%;
            transition: width 0.4s ease;
        }

        .risk-badge {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .risk-high { background: rgba(239, 68, 68, 0.2); color: var(--accent-red); border: 1px solid var(--accent-red); }
        .risk-medium { background: rgba(245, 158, 11, 0.2); color: var(--accent-amber); border: 1px solid var(--accent-amber); }
        .risk-low { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }

        /* POSTURE AVATAR */
        .posture-flex {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 6px;
        }

        /* CHAT CONSOLE */
        .chat-console {
            display: flex;
            flex-direction: column;
            height: 620px;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding-right: 6px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 14px;
        }

        .msg-bubble {
            max-width: 88%;
            padding: 12px 16px;
            border-radius: 14px;
            font-size: 13.5px;
            line-height: 1.55;
            position: relative;
        }

        .msg-user {
            align-self: flex-end;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            color: #fff;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }

        .msg-tutor {
            align-self: flex-start;
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid var(--panel-border);
            border-bottom-left-radius: 4px;
        }

        .msg-badge {
            display: inline-block;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            padding: 2px 7px;
            border-radius: 4px;
            margin-bottom: 6px;
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .chat-presets {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-bottom: 8px;
        }

        .preset-chip {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--panel-border);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            white-space: nowrap;
            color: var(--text-dim);
            cursor: pointer;
            transition: all 0.15s;
        }
        .preset-chip:hover {
            background: rgba(6, 182, 212, 0.15);
            color: var(--accent-cyan);
            border-color: var(--accent-cyan);
        }

        .chat-input-row {
            display: flex;
            gap: 8px;
        }

        input[type="text"] {
            flex: 1;
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--panel-border);
            padding: 11px 14px;
            border-radius: 10px;
            color: #fff;
            font-family: inherit;
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s;
        }
        input[type="text"]:focus { border-color: var(--accent-cyan); }

        button.btn-primary {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            color: #fff;
            border: none;
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
        }
        button.btn-primary:hover { opacity: 0.92; transform: translateY(-1px); }

        .btn-mic {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--panel-border);
            color: var(--text-dim);
            width: 42px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            transition: all 0.2s;
        }
        .btn-mic.listening {
            background: rgba(239, 68, 68, 0.2);
            color: var(--accent-red);
            border-color: var(--accent-red);
            animation: pulse 1s infinite;
        }

        /* GRAPH CANVAS */
        #graph-canvas {
            width: 100%;
            height: 220px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            border: 1px solid var(--panel-border);
            display: block;
        }

        /* SERVO GAUGES */
        .servo-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
        }

        .servo-box {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--panel-border);
            padding: 10px 6px;
            border-radius: 8px;
            text-align: center;
        }
        .servo-label { font-size: 10px; color: var(--text-dim); text-transform: uppercase; }
        .servo-val { font-family: 'JetBrains Mono'; font-weight: 700; color: var(--accent-cyan); font-size: 14px; margin-top: 3px; }

        /* I2C TERMINAL */
        .i2c-term {
            font-family: 'JetBrains Mono', monospace;
            background: #000;
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            padding: 10px;
            height: 120px;
            overflow-y: auto;
            font-size: 11px;
            color: #a3e635;
        }
        .i2c-line { margin-bottom: 2px; }

        /* QUIZ POPUP */
        .quiz-card {
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid var(--accent-blue);
            border-radius: 12px;
            padding: 14px;
            margin-top: 12px;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.08); }
            100% { transform: scale(1); }
        }

        .sound-wave {
            display: inline-flex;
            gap: 2px;
            align-items: center;
            height: 12px;
            margin-left: 6px;
        }
        .sound-bar {
            width: 3px;
            height: 4px;
            background: var(--accent-cyan);
            border-radius: 2px;
            animation: wave 0.8s ease-in-out infinite alternate;
        }
        .sound-bar:nth-child(2) { animation-delay: 0.2s; }
        .sound-bar:nth-child(3) { animation-delay: 0.4s; }

        @keyframes wave {
            0% { height: 4px; }
            100% { height: 14px; }
        }
    </style>
</head>
<body>

    <!-- TOP HEADER -->
    <header>
        <div class="brand-container">
            <div class="brand-logo">S</div>
            <div class="brand-text">
                <h1>SmartEduSync</h1>
                <p>Privacy-First Tabletop AI Tutoring Robot &bull; Group 07 (MBCCET)</p>
            </div>
        </div>
        <div class="header-pills">
            <div class="status-pill"><span class="status-dot"></span> Event Bus Active</div>
            <div class="status-pill"><span class="status-dot" style="background: var(--accent-cyan); box-shadow: 0 0 8px var(--accent-cyan);"></span> PCA9685 I2C (0x40)</div>
            <div class="status-pill"><span class="status-dot" style="background: var(--accent-purple); box-shadow: 0 0 8px var(--accent-purple);"></span> Socratic GraphRAG</div>
            <button class="sc-btn" id="tts-toggle-btn" onclick="toggleSpeech()" style="padding: 5px 10px;">
                <span id="tts-icon">🔊</span> Voice Speech: <b id="tts-state">ON</b>
            </button>
        </div>
    </header>

    <!-- DEFENSE SCENARIOS BAR -->
    <div class="scenarios-bar">
        <div class="scenarios-title">
            <span>⚡ Presentation Defense Scenarios</span>
        </div>
        <div class="scenarios-btns">
            <button class="sc-btn" onclick="scenarioEngagementDip()">🎯 1. Engagement Dip &rarr; Nudge</button>
            <button class="sc-btn amber" onclick="scenarioSlouch()">🧘 2. Slouch &rarr; Posture Alert</button>
            <button class="sc-btn danger" onclick="scenarioExamAlert()">🚨 3. High Risk Exam Radar</button>
            <button class="sc-btn" onclick="scenarioTestQuiz()">📝 4. Socratic Quiz &amp; BKT Update</button>
            <button class="sc-btn" onclick="scenarioReset()">🔄 Reset Normal</button>
        </div>
    </div>

    <!-- MAIN 3-COLUMN DASHBOARD GRID -->
    <div class="dashboard-grid">

        <!-- LEFT COLUMN: Perception & Robot Face -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
            
            <!-- Robot Face OLED Display -->
            <div class="card">
                <div class="card-title">
                    <span>OLED Robot Face (128&times;64)</span>
                    <span id="face-emotion-badge" class="risk-badge" style="background: rgba(6, 182, 212, 0.2); color: var(--accent-cyan); border: 1px solid var(--accent-cyan);">WATCHING</span>
                </div>

                <div class="face-tab-row">
                    <button id="tab-digital" class="tab-btn active" onclick="switchFaceTab('digital')">Cyber OLED Eyes</button>
                    <button id="tab-ascii" class="tab-btn" onclick="switchFaceTab('ascii')">Raw 128x64 Bitmap</button>
                </div>

                <div class="face-container">
                    <div class="face-scanlines"></div>
                    
                    <!-- Digital Animated Face SVG -->
                    <svg id="digital-face-svg" class="digital-face-svg" viewBox="0 0 280 120">
                        <defs>
                            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                                <feGaussianBlur stdDeviation="3" result="blur" />
                                <feComposite in="SourceGraphic" in2="blur" operator="over" />
                            </filter>
                        </defs>
                        <!-- Left Eyebrow -->
                        <path id="left-brow" d="M 60 30 Q 90 28 115 32" stroke="#00ffcc" stroke-width="4" stroke-linecap="round" fill="none" filter="url(#glow)"/>
                        <!-- Right Eyebrow -->
                        <path id="right-brow" d="M 165 32 Q 190 28 220 30" stroke="#00ffcc" stroke-width="4" stroke-linecap="round" fill="none" filter="url(#glow)"/>
                        <!-- Left Eye -->
                        <ellipse id="left-eye" cx="85" cy="58" rx="26" ry="24" fill="#000" stroke="#00ffcc" stroke-width="3" filter="url(#glow)"/>
                        <circle id="left-pupil" cx="85" cy="58" r="10" fill="#00ffcc"/>
                        <!-- Right Eye -->
                        <ellipse id="right-eye" cx="195" cy="58" rx="26" ry="24" fill="#000" stroke="#00ffcc" stroke-width="3" filter="url(#glow)"/>
                        <circle id="right-pupil" cx="195" cy="58" r="10" fill="#00ffcc"/>
                        <!-- Mouth -->
                        <path id="face-mouth" d="M 115 95 Q 140 102 165 95" stroke="#00ffcc" stroke-width="4" stroke-linecap="round" fill="none" filter="url(#glow)"/>
                    </svg>

                    <!-- ASCII Box fallback view -->
                    <div id="face-ascii" class="face-ascii-box"></div>
                </div>

                <!-- 8 Vocabulary Emotions Selector -->
                <div class="emotion-pills">
                    <div class="emo-pill" onclick="setEmotion('idle')">idle</div>
                    <div class="emo-pill active" onclick="setEmotion('watching')">watching</div>
                    <div class="emo-pill" onclick="setEmotion('listening')">listening</div>
                    <div class="emo-pill" onclick="setEmotion('thinking')">thinking</div>
                    <div class="emo-pill" onclick="setEmotion('curious')">curious</div>
                    <div class="emo-pill" onclick="setEmotion('happy')">happy</div>
                    <div class="emo-pill" onclick="setEmotion('concerned')">concerned</div>
                    <div class="emo-pill" onclick="setEmotion('alert')">alert</div>
                </div>
            </div>

            <!-- Real-time Engagement Telemetry (E_t) -->
            <div class="card">
                <div class="card-title">
                    <span>Rolling Engagement Index (E_t)</span>
                    <span id="et-tag" style="font-size: 11px; color: var(--accent-green);">ENGAGED</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <div id="et-value" class="stat-value">0.85</div>
                    <div style="font-size: 11px; color: var(--text-dim); font-family: 'JetBrains Mono';">Buffer: 10 samples @ 5 Hz</div>
                </div>
                <div class="progress-bar-bg">
                    <div id="et-bar" class="progress-bar-fill" style="width: 85%;"></div>
                </div>
                <div style="display: flex; gap: 8px; margin-top: 14px;">
                    <button class="sc-btn danger" style="flex: 1;" onclick="triggerEngagementDip()">Look Away (0.20)</button>
                    <button class="sc-btn" style="flex: 1;" onclick="triggerEngagementHigh()">Focus (0.90)</button>
                </div>
            </div>

            <!-- Ergonomic Posture Monitor -->
            <div class="card">
                <div class="card-title">
                    <span>Posture &amp; Neck Inclination (&theta;)</span>
                    <span id="posture-badge" class="risk-badge risk-low">UPRIGHT</span>
                </div>
                <div class="posture-flex">
                    <div>
                        <div style="font-size: 12px; color: var(--text-dim);">Neck Tilt Angle:</div>
                        <div id="neck-angle-val" style="font-family: 'JetBrains Mono'; font-weight: 700; color: var(--accent-cyan); font-size: 26px;">8.5&deg;</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 12px; color: var(--text-dim);">Slouch Threshold:</div>
                        <div style="font-family: 'JetBrains Mono'; color: var(--text-dim); font-size: 14px;">&gt; 15.0&deg;</div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px; margin-top: 12px;">
                    <button class="sc-btn amber" style="flex: 1;" onclick="triggerSlouch()">Simulate Slouch (32.5&deg;)</button>
                    <button class="sc-btn" style="flex: 1;" onclick="triggerUpright()">Sit Upright (7.8&deg;)</button>
                </div>
            </div>

        </div>

        <!-- CENTER COLUMN: Socratic Tutor & Dialogue Console -->
        <div class="card chat-console">
            <div class="card-title">
                <span>Socratic Dialogue &amp; Verifier Console</span>
                <span style="font-size: 11px; color: var(--accent-cyan); display: flex; align-items: center;">
                    Local Grounded RAG 
                    <span id="sound-indicator" class="sound-wave" style="display: none;">
                        <span class="sound-bar"></span><span class="sound-bar"></span><span class="sound-bar"></span>
                    </span>
                </span>
            </div>

            <!-- Quick Action Pills -->
            <div class="chat-presets">
                <span class="preset-chip" onclick="quickSend('Why do we calculate integrals in physics?')">❓ Why integrate in physics?</span>
                <span class="preset-chip" onclick="quickSend('What is the physical meaning of a Riemann sum?')">📐 Riemann Sum meaning?</span>
                <span class="preset-chip" onclick="quickSend('How does Fundamental Theorem of Calculus link derivatives and integrals?')">🔗 Fundamental Theorem?</span>
                <span class="preset-chip" onclick="quickSend('The area under the curve represents the total accumulation.')">💡 Answer: Area under curve</span>
            </div>

            <!-- Message Stream -->
            <div id="chat-messages" class="chat-messages">
                <div class="msg-bubble msg-tutor">
                    <span class="msg-badge">🛡️ Grounded in Syllabus</span>
                    <div>Hello! I'm SmartEduSync, your Socratic study partner. We are exploring <b>Calculus Integrals</b> today. Ask me a question or reason through a concept together!</div>
                </div>
            </div>

            <!-- Input Row -->
            <div class="chat-input-row">
                <button id="mic-btn" class="btn-mic" onclick="toggleMic()" title="Click to speak using laptop microphone">🎤</button>
                <input type="text" id="chat-input" placeholder="Ask a question or explain a concept in your own words..." onkeydown="if(event.key==='Enter') sendChat()">
                <button class="btn-primary" onclick="sendChat()">Send</button>
            </div>

            <!-- Study Material Upload Dropzone -->
            <div style="margin-top: 14px; padding: 10px 12px; border: 1px dashed var(--panel-border); border-radius: 10px; font-size: 12px; background: rgba(0,0,0,0.15);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="color: var(--text-dim); font-weight: 600;">📚 Ingest Syllabus Material (PDF/Text)</span>
                    <button class="sc-btn" style="padding: 2px 8px; font-size: 10px;" onclick="requestStudyNudge()">Trigger Study Nudge</button>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <input id="material-file" type="file" accept=".pdf,.txt,.md" style="font-size: 11px; color: var(--text-dim); flex: 1;">
                    <button class="sc-btn" style="padding: 5px 10px;" onclick="uploadMaterials()">Analyze &amp; Map</button>
                </div>
                <div id="onboarding-status" style="margin-top: 6px; font-size: 11px; color: var(--accent-cyan);"></div>
            </div>
        </div>

        <!-- RIGHT COLUMN: Knowledge Graph, BKT & Servos -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
            
            <!-- GraphRAG Concept Knowledge Graph -->
            <div class="card">
                <div class="card-title">
                    <span>GraphRAG Concept Map (NetworkX)</span>
                    <span style="font-size: 11px; color: var(--accent-purple);">8 Active Nodes</span>
                </div>
                <canvas id="graph-canvas"></canvas>
                <div style="font-size: 11px; color: var(--text-dim); margin-top: 6px; text-align: center;">
                    &bull; Blue: Core &bull; Cyan: Methods &bull; Purple: Theorems &bull; Amber: Applications
                </div>
            </div>

            <!-- Bayesian Knowledge Tracing (BKT) Tracker -->
            <div class="card">
                <div class="card-title">
                    <span>BKT Student Mastery Tracker</span>
                    <span id="exam-risk" class="risk-badge risk-low">LOW RISK</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <div>
                        <div style="font-size: 14px; font-weight: 700; color: #fff;" id="topic-name">Calculus Integrals</div>
                        <p style="font-size: 11px; color: var(--text-dim);" id="exam-days">Nearest Exam: 3 days left</p>
                    </div>
                    <div id="mastery-pct" class="stat-value" style="color: var(--accent-green);">75%</div>
                </div>
                <div class="progress-bar-bg">
                    <div id="mastery-bar" class="progress-bar-fill" style="width: 75%; background: linear-gradient(to right, var(--accent-blue), var(--accent-green));"></div>
                </div>

                <!-- Live Socratic Quiz Button -->
                <button class="sc-btn" style="width: 100%; margin-top: 12px; justify-content: center; background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.3);" onclick="openSocraticQuiz()">
                    ⚡ Test Student Knowledge (Update BKT)
                </button>

                <!-- Socratic Quiz Inline Form -->
                <div id="quiz-container" class="quiz-card" style="display: none;">
                    <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 4px;">ACTIVE QUIZ ITEM:</div>
                    <div id="quiz-question-text" style="font-size: 12px; margin-bottom: 8px;"></div>
                    <input type="text" id="quiz-answer-input" placeholder="Type answer (e.g. Area under curve using rectangles)" style="width: 100%; margin-bottom: 8px;">
                    <div style="display: flex; gap: 6px;">
                        <button class="btn-primary" style="padding: 6px 12px; font-size: 11px;" onclick="submitQuiz()">Submit for Evaluation</button>
                        <button class="sc-btn" style="padding: 6px 10px; font-size: 11px;" onclick="closeQuiz()">Cancel</button>
                    </div>
                    <div id="quiz-result-feedback" style="margin-top: 8px; font-size: 11px; font-weight: 600;"></div>
                </div>
            </div>

            <!-- Hardware Servos & I2C Bus Monitor -->
            <div class="card">
                <div class="card-title">
                    <span>PCA9685 Servos &amp; I2C Bus (0x40)</span>
                    <span id="i2c-writes-badge" style="font-size: 10px; font-family: 'JetBrains Mono'; color: var(--accent-green);">0 WRITES</span>
                </div>
                <div class="servo-grid">
                    <div class="servo-box">
                        <div class="servo-label">Ch0 Yaw</div>
                        <div id="s0" class="servo-val">0.0&deg;</div>
                    </div>
                    <div class="servo-box">
                        <div class="servo-label">Ch1 Pitch</div>
                        <div id="s1" class="servo-val">0.0&deg;</div>
                    </div>
                    <div class="servo-box">
                        <div class="servo-label">Ch2 L-Arm</div>
                        <div id="s2" class="servo-val">0.0&deg;</div>
                    </div>
                    <div class="servo-box">
                        <div class="servo-label">Ch3 R-Arm</div>
                        <div id="s3" class="servo-val">0.0&deg;</div>
                    </div>
                </div>

                <!-- I2C Bus Register Stream -->
                <div style="margin-top: 12px;">
                    <div style="font-size: 11px; color: var(--text-dim); margin-bottom: 4px; display: flex; justify-content: space-between;">
                        <span>Live I2C Register Writes:</span>
                        <span style="color: var(--accent-cyan);">50 Hz PWM</span>
                    </div>
                    <div id="i2c-term" class="i2c-term">
                        <div class="i2c-line">[PCA9685 @ 0x40] REG 0xFE &larr; 0x79 | Prescale (50Hz)</div>
                        <div class="i2c-line">[PCA9685 @ 0x40] REG 0x00 &larr; 0x00 | Mode1 Normal</div>
                    </div>
                </div>
            </div>

        </div>

    </div>

    <script>
        let awaitingAccountabilityReply = false;
        let speechEnabled = true;
        let isListeningMic = false;
        let speechRecognition = null;
        let activeFaceTab = 'digital';
        let currentEmotion = 'watching';
        let activeQuizItem = null;

        // Initialize Web Speech Synthesis
        function speakText(text, tone) {
            if (!speechEnabled || !('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = tone === 'urgent' ? 1.15 : (tone === 'soft' ? 0.90 : 1.0);
            utterance.pitch = tone === 'urgent' ? 1.2 : (tone === 'soft' ? 1.1 : 1.0);
            
            const soundIndicator = document.getElementById('sound-indicator');
            utterance.onstart = () => { if (soundIndicator) soundIndicator.style.display = 'inline-flex'; };
            utterance.onend = () => { if (soundIndicator) soundIndicator.style.display = 'none'; };
            utterance.onerror = () => { if (soundIndicator) soundIndicator.style.display = 'none'; };
            window.speechSynthesis.speak(utterance);
        }

        function toggleSpeech() {
            speechEnabled = !speechEnabled;
            document.getElementById('tts-state').textContent = speechEnabled ? 'ON' : 'OFF';
            document.getElementById('tts-icon').textContent = speechEnabled ? '🔊' : '🔇';
            if (!speechEnabled && ('speechSynthesis' in window)) {
                window.speechSynthesis.cancel();
            }
        }

        // Web Speech Recognition (Microphone)
        function toggleMic() {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRec) {
                alert('Web Speech Recognition is not supported in this browser. Please use Google Chrome or Edge.');
                return;
            }

            const micBtn = document.getElementById('mic-btn');
            if (isListeningMic) {
                if (speechRecognition) speechRecognition.stop();
                isListeningMic = false;
                micBtn.classList.remove('listening');
                return;
            }

            speechRecognition = new SpeechRec();
            speechRecognition.continuous = false;
            speechRecognition.interimResults = false;
            speechRecognition.lang = 'en-US';

            speechRecognition.onstart = () => {
                isListeningMic = true;
                micBtn.classList.add('listening');
                document.getElementById('chat-input').placeholder = 'Listening... Speak your question now.';
            };

            speechRecognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('chat-input').value = transcript;
                sendChat();
            };

            speechRecognition.onerror = (e) => {
                console.error('Speech recognition error:', e);
                isListeningMic = false;
                micBtn.classList.remove('listening');
                document.getElementById('chat-input').placeholder = 'Ask a question or explain a concept...';
            };

            speechRecognition.onend = () => {
                isListeningMic = false;
                micBtn.classList.remove('listening');
                document.getElementById('chat-input').placeholder = 'Ask a question or explain a concept...';
            };

            speechRecognition.start();
        }

        function switchFaceTab(tab) {
            activeFaceTab = tab;
            document.getElementById('tab-digital').className = 'tab-btn ' + (tab === 'digital' ? 'active' : '');
            document.getElementById('tab-ascii').className = 'tab-btn ' + (tab === 'ascii' ? 'active' : '');
            document.getElementById('digital-face-svg').style.display = tab === 'digital' ? 'block' : 'none';
            document.getElementById('face-ascii').style.display = tab === 'ascii' ? 'block' : 'none';
        }

        // Animated SVG Face Morphing according to 8 emotions
        function updateDigitalFace(emotion) {
            currentEmotion = emotion.toLowerCase();
            const leftEye = document.getElementById('left-eye');
            const rightEye = document.getElementById('right-eye');
            const leftPupil = document.getElementById('left-pupil');
            const rightPupil = document.getElementById('right-pupil');
            const leftBrow = document.getElementById('left-brow');
            const rightBrow = document.getElementById('right-brow');
            const mouth = document.getElementById('face-mouth');

            // Reset transitions
            [leftEye, rightEye, leftPupil, rightPupil, leftBrow, rightBrow, mouth].forEach(el => {
                if (el) el.style.transition = 'all 0.3s ease';
            });

            if (currentEmotion === 'happy') {
                leftEye.setAttribute('rx', '24'); leftEye.setAttribute('ry', '14');
                rightEye.setAttribute('rx', '24'); rightEye.setAttribute('ry', '14');
                leftBrow.setAttribute('d', 'M 60 26 Q 90 20 115 26');
                rightBrow.setAttribute('d', 'M 165 26 Q 190 20 220 26');
                mouth.setAttribute('d', 'M 110 88 Q 140 110 170 88');
                leftPupil.setAttribute('cy', '54'); rightPupil.setAttribute('cy', '54');
            } else if (currentEmotion === 'curious') {
                leftEye.setAttribute('rx', '26'); leftEye.setAttribute('ry', '28');
                rightEye.setAttribute('rx', '28'); rightEye.setAttribute('ry', '30');
                leftBrow.setAttribute('d', 'M 60 22 Q 90 18 115 30');
                rightBrow.setAttribute('d', 'M 165 20 Q 190 14 220 24');
                mouth.setAttribute('d', 'M 130 96 A 10 10 0 1 0 150 96 A 10 10 0 1 0 130 96');
                leftPupil.setAttribute('cx', '92'); rightPupil.setAttribute('cx', '202');
            } else if (currentEmotion === 'concerned') {
                leftEye.setAttribute('rx', '24'); leftEye.setAttribute('ry', '20');
                rightEye.setAttribute('rx', '24'); rightEye.setAttribute('ry', '20');
                leftBrow.setAttribute('d', 'M 60 36 Q 90 26 115 20');
                rightBrow.setAttribute('d', 'M 165 20 Q 190 26 220 36');
                mouth.setAttribute('d', 'M 115 102 Q 140 88 165 102');
            } else if (currentEmotion === 'alert') {
                leftEye.setAttribute('rx', '30'); leftEye.setAttribute('ry', '30');
                rightEye.setAttribute('rx', '30'); rightEye.setAttribute('ry', '30');
                leftBrow.setAttribute('d', 'M 60 18 Q 90 16 115 24');
                rightBrow.setAttribute('d', 'M 165 24 Q 190 16 220 18');
                mouth.setAttribute('d', 'M 110 95 L 170 95');
                leftEye.setAttribute('stroke', '#ef4444');
                rightEye.setAttribute('stroke', '#ef4444');
                leftPupil.setAttribute('fill', '#ef4444');
                rightPupil.setAttribute('fill', '#ef4444');
            } else if (currentEmotion === 'thinking') {
                leftEye.setAttribute('rx', '20'); leftEye.setAttribute('ry', '24');
                rightEye.setAttribute('rx', '20'); rightEye.setAttribute('ry', '24');
                leftBrow.setAttribute('d', 'M 60 26 Q 90 22 115 26');
                rightBrow.setAttribute('d', 'M 165 24 Q 190 18 220 22');
                mouth.setAttribute('d', 'M 125 94 L 155 94');
                leftPupil.setAttribute('cx', '76'); rightPupil.setAttribute('cx', '186');
            } else if (currentEmotion === 'listening') {
                leftEye.setAttribute('rx', '25'); leftEye.setAttribute('ry', '25');
                rightEye.setAttribute('rx', '25'); rightEye.setAttribute('ry', '25');
                leftBrow.setAttribute('d', 'M 60 28 Q 90 26 115 30');
                rightBrow.setAttribute('d', 'M 165 30 Q 190 26 220 28');
                mouth.setAttribute('d', 'M 120 95 Q 140 98 160 95');
            } else if (currentEmotion === 'idle') {
                leftEye.setAttribute('rx', '24'); leftEye.setAttribute('ry', '6');
                rightEye.setAttribute('rx', '24'); rightEye.setAttribute('ry', '6');
                leftBrow.setAttribute('d', 'M 60 32 Q 90 32 115 32');
                rightBrow.setAttribute('d', 'M 165 32 Q 190 32 220 32');
                mouth.setAttribute('d', 'M 125 96 L 155 96');
            } else { // watching
                leftEye.setAttribute('rx', '26'); leftEye.setAttribute('ry', '24');
                rightEye.setAttribute('rx', '26'); rightEye.setAttribute('ry', '24');
                leftBrow.setAttribute('d', 'M 60 30 Q 90 28 115 32');
                rightBrow.setAttribute('d', 'M 165 32 Q 190 28 220 30');
                mouth.setAttribute('d', 'M 115 95 Q 140 100 165 95');
                leftEye.setAttribute('stroke', '#00ffcc');
                rightEye.setAttribute('stroke', '#00ffcc');
                leftPupil.setAttribute('fill', '#00ffcc');
                rightPupil.setAttribute('fill', '#00ffcc');
                leftPupil.setAttribute('cx', '85'); rightPupil.setAttribute('cx', '195');
            }

            // Update pills
            document.querySelectorAll('.emo-pill').forEach(pill => {
                pill.classList.toggle('active', pill.textContent.toLowerCase() === currentEmotion);
            });
        }

        // Automatic Eye Blinking Loop
        setInterval(() => {
            if (currentEmotion === 'alert' || currentEmotion === 'idle') return;
            const leftEye = document.getElementById('left-eye');
            const rightEye = document.getElementById('right-eye');
            if (!leftEye || !rightEye) return;
            const origY = leftEye.getAttribute('ry');
            leftEye.setAttribute('ry', '3');
            rightEye.setAttribute('ry', '3');
            setTimeout(() => {
                leftEye.setAttribute('ry', origY);
                rightEye.setAttribute('ry', origY);
            }, 180);
        }, 4000);

        function appendMessage(text, kind, badgeText) {
            const container = document.getElementById('chat-messages');
            const bubble = document.createElement('div');
            bubble.className = 'msg-bubble ' + kind;
            if (badgeText) {
                const b = document.createElement('span');
                b.className = 'msg-badge';
                b.textContent = badgeText;
                bubble.appendChild(b);
            }
            const content = document.createElement('div');
            content.textContent = text;
            bubble.appendChild(content);
            container.appendChild(bubble);
            container.scrollTop = container.scrollHeight;
        }

        function quickSend(text) {
            document.getElementById('chat-input').value = text;
            sendChat();
        }

        async function sendChat() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;

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
                appendMessage(data.response, 'msg-tutor', data.grounded ? '🛡️ Grounded in Syllabus' : '🤖 Socratic Guide');
                speakText(data.response, data.ssml_hint || 'neutral');
                if (awaitingAccountabilityReply) {
                    awaitingAccountabilityReply = false;
                    input.placeholder = 'Ask a question or explain a concept...';
                }
                fetchStatus();
                fetchI2CLog();
            } catch (e) {
                console.error(e);
            }
        }

        async function setEmotion(emo) {
            await fetch('/api/set_emotion/' + emo, { method: 'POST' });
            fetchStatus();
            fetchI2CLog();
        }

        async function triggerEngagementDip() {
            await fetch('/api/simulate_engagement', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ E_t: 0.20, emotion: 'frustrated' })
            });
            fetchStatus();
            fetchI2CLog();
        }

        async function triggerEngagementHigh() {
            await fetch('/api/simulate_engagement', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ E_t: 0.90, emotion: 'watching' })
            });
            fetchStatus();
            fetchI2CLog();
        }

        async function triggerSlouch() {
            await fetch('/api/simulate_slouch', { method: 'POST' });
            fetchStatus();
            fetchI2CLog();
        }

        async function triggerUpright() {
            await fetch('/api/simulate_upright', { method: 'POST' });
            fetchStatus();
            fetchI2CLog();
        }

        async function requestStudyNudge() {
            try {
                const response = await fetch('/api/accountability/nudge', { method: 'POST' });
                const result = await response.json();
                appendMessage(result.response, 'msg-tutor', '🎯 Socratic Study Nudge');
                speakText(result.response, 'playful');
                awaitingAccountabilityReply = true;
                document.getElementById('chat-input').placeholder = 'Reply to the robot—typed or via mic…';
                fetchStatus();
                fetchI2CLog();
            } catch (error) { console.error(error); }
        }

        // DEFENSE SCENARIOS
        async function scenarioEngagementDip() {
            await triggerEngagementDip();
            setTimeout(requestStudyNudge, 600);
        }

        async function scenarioSlouch() {
            await triggerSlouch();
        }

        async function scenarioExamAlert() {
            await fetch('/api/simulate_exam_alert', { method: 'POST' });
            fetchStatus();
            fetchI2CLog();
        }

        async function scenarioTestQuiz() {
            openSocraticQuiz();
        }

        async function scenarioReset() {
            await triggerUpright();
            await fetch('/api/set_emotion/watching', { method: 'POST' });
            fetchStatus();
            fetchI2CLog();
        }

        // Socratic Quiz Handlers
        async function openSocraticQuiz() {
            const res = await fetch('/api/quiz/generate?topic=Calculus%20Integrals');
            activeQuizItem = await res.json();
            document.getElementById('quiz-question-text').textContent = activeQuizItem.question;
            document.getElementById('quiz-result-feedback').textContent = '';
            document.getElementById('quiz-answer-input').value = '';
            document.getElementById('quiz-container').style.display = 'block';
        }

        function closeQuiz() {
            document.getElementById('quiz-container').style.display = 'none';
        }

        async function submitQuiz() {
            if (!activeQuizItem) return;
            const ans = document.getElementById('quiz-answer-input').value.trim();
            if (!ans) return;

            const res = await fetch('/api/quiz/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: activeQuizItem.topic,
                    question: activeQuizItem.question,
                    student_answer: ans,
                    expected_keywords: activeQuizItem.expected_keywords || []
                })
            });
            const data = await res.json();
            const feedbackEl = document.getElementById('quiz-result-feedback');
            feedbackEl.textContent = (data.correct ? '✓ ' : '⚠ ') + data.feedback + ` (Score: ${Math.round(data.score * 100)}%, New Mastery: ${Math.round(data.new_mastery * 100)}%)`;
            feedbackEl.style.color = data.correct ? 'var(--accent-green)' : 'var(--accent-amber)';
            fetchStatus();
            fetchI2CLog();
        }

        // Onboarding Upload
        async function uploadMaterials() {
            const files = Array.from(document.getElementById('material-file').files);
            const status = document.getElementById('onboarding-status');
            if (!files.length) { status.textContent = 'Choose one or more files first.'; return; }
            status.textContent = 'Analysing study material and mapping GraphRAG concepts…';
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
                status.textContent = `Ready: mapped ${files.length} source(s), built ${chunks} study chunks.`;
                loadGraphCanvas();
            } catch (error) { status.textContent = 'Could not analyse material: ' + error.message; }
        }

        // Fetch Telemetry Status
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                updateDigitalFace(data.emotion || 'watching');
                document.getElementById('face-ascii').textContent = data.face_art || '';
                document.getElementById('face-emotion-badge').textContent = (data.emotion || 'watching').toUpperCase();

                const et = data.E_t || 0;
                document.getElementById('et-value').textContent = et.toFixed(2);
                document.getElementById('et-bar').style.width = (et * 100) + '%';
                const etTag = document.getElementById('et-tag');
                if (et >= 0.70) { etTag.textContent = 'ENGAGED'; etTag.style.color = 'var(--accent-green)'; }
                else if (et >= 0.40) { etTag.textContent = 'DISTRACTED'; etTag.style.color = 'var(--accent-amber)'; }
                else { etTag.textContent = 'DISENGAGED'; etTag.style.color = 'var(--accent-red)'; }

                document.getElementById('topic-name').textContent = data.active_topic || 'Calculus Integrals';
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

                if (document.getElementById('i2c-writes-badge')) {
                    document.getElementById('i2c-writes-badge').textContent = (data.i2c_write_count || 0) + ' WRITES';
                }
            } catch (e) {
                console.error(e);
            }
        }

        // Fetch Live I2C Log
        async function fetchI2CLog() {
            try {
                const res = await fetch('/api/hardware/i2c_log');
                const data = await res.json();
                const term = document.getElementById('i2c-term');
                if (!term || !data.log || !data.log.length) return;
                term.innerHTML = '';
                data.log.forEach(item => {
                    const row = document.createElement('div');
                    row.className = 'i2c-line';
                    row.textContent = `[PCA9685 @ ${item.addr}] REG ${item.reg} <- ${item.val} | ${item.desc}`;
                    term.appendChild(row);
                });
                term.scrollTop = term.scrollHeight;
            } catch (e) {
                console.error(e);
            }
        }

        // Interactive GraphRAG HTML5 Canvas
        let graphData = null;
        async function loadGraphCanvas() {
            const canvas = document.getElementById('graph-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;
            canvas.width = canvas.clientWidth * dpr;
            canvas.height = canvas.clientHeight * dpr;
            ctx.scale(dpr, dpr);

            if (!graphData) {
                try {
                    const res = await fetch('/api/graph_data');
                    graphData = await res.json();
                } catch (e) {
                    return;
                }
            }

            const w = canvas.clientWidth;
            const h = canvas.clientHeight;

            // Draw Background grid
            ctx.clearRect(0, 0, w, h);

            // Scale coords
            const nodes = graphData.nodes.map(n => ({
                ...n,
                cx: (n.x / 620) * w,
                cy: (n.y / 440) * h
            }));

            // Draw Edges
            graphData.edges.forEach(edge => {
                const s = nodes.find(n => n.id === edge.source);
                const t = nodes.find(n => n.id === edge.target);
                if (s && t) {
                    ctx.beginPath();
                    ctx.moveTo(s.cx, s.cy);
                    ctx.lineTo(t.cx, t.cy);
                    ctx.strokeStyle = 'rgba(59, 130, 246, 0.35)';
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                }
            });

            // Draw Nodes
            nodes.forEach(node => {
                ctx.beginPath();
                ctx.arc(node.cx, node.cy, node.category === 'core' ? 14 : 9, 0, Math.PI * 2);
                let color = '#3b82f6';
                if (node.category === 'method') color = '#06b6d4';
                if (node.category === 'theorem') color = '#8b5cf6';
                if (node.category === 'application') color = '#f59e0b';
                ctx.fillStyle = color;
                ctx.shadowColor = color;
                ctx.shadowBlur = 10;
                ctx.fill();
                ctx.shadowBlur = 0;

                ctx.font = '9px Outfit, sans-serif';
                ctx.fillStyle = '#cbd5e1';
                ctx.textAlign = 'center';
                ctx.fillText(node.id.split(' ')[0], node.cx, node.cy + 20);
            });
        }

        setInterval(fetchStatus, 2500);
        setInterval(fetchI2CLog, 3000);
        fetchStatus();
        fetchI2CLog();
        setTimeout(loadGraphCanvas, 500);
        window.addEventListener('resize', loadGraphCanvas);
    </script>

</body>
</html>"""
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
