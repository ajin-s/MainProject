"""
FastAPI Server for SmartEduSync Knowledge Engine.
Exposes POST /chat endpoint with session tracking, RAG, GraphRAG, Socratic LLM, and verifier gating.
"""
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional

from part1_companion.mastery.bkt import get_student_context
from part2_knowledge.rag.material_library import MaterialError, StudyMaterialLibrary
from part2_knowledge.tutor.pipeline import run_tutor_turn

app = FastAPI(title="SmartEduSync Knowledge Engine API", version="1.0.0")
materials = StudyMaterialLibrary()


class ChatRequest(BaseModel):
    message: str = Field(..., description="Student query or input text")
    session_id: str = Field("default_session")
    student_id: str = Field("student_1")
    topic: Optional[str] = Field("Calculus Integrals")
    mastery: float = Field(0.50, ge=0.0, le=1.0)


class ChatResponse(BaseModel):
    text: str
    ssml_hint: str
    topic: str
    confidence: float
    grounded: bool


class MaterialUrlRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    url: str = Field(..., min_length=8)


@app.get("/")
def read_root():
    return {"status": "ok", "service": "SmartEduSync Knowledge Server"}


@app.get("/onboarding/{student_id}")
def onboarding_status(student_id: str):
    """Returns whether a student has completed first-run material onboarding."""
    return materials.onboarding_status(student_id)


@app.post("/onboarding/material")
async def upload_material(
    request: Request,
    student_id: str = Query(..., min_length=1),
    filename: str = Query(..., min_length=1),
):
    """Upload a PDF, text file, or image as raw request bytes.

    Raw bytes avoid requiring a multipart dependency on the Raspberry Pi. The dashboard
    sends the chosen file body and supplies its original name in the query string.
    """
    data = await request.body()
    if len(data) > 20_000_000:
        raise HTTPException(status_code=413, detail="Study material must be at most 20 MB.")
    try:
        return materials.ingest_bytes(student_id, filename, data)
    except MaterialError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/onboarding/url")
def add_material_url(payload: MaterialUrlRequest):
    """Fetch and analyse an http(s) study page or PDF, then update the concept graph."""
    try:
        return materials.ingest_url(payload.student_id, payload.url)
    except MaterialError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    facts = get_student_context(req.student_id)
    topic = req.topic or facts.get("active_topic") or "General Studies"
    mastery = req.mastery if req.mastery is not None else float(facts.get("p_mastery", 0.5))
    tutor_res, diagnostics = run_tutor_turn(
        req.student_id, req.message, topic, mastery, facts, session_id=req.session_id
    )
    return ChatResponse(
        text=tutor_res.text,
        ssml_hint=tutor_res.ssml_hint or "neutral",
        topic=topic,
        confidence=tutor_res.confidence,
        grounded=bool(diagnostics.get("grounded", True)),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
