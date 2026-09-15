"""
Socratic Tutoring Dialogue Engine for SmartEduSync.
Generates guided self-discovery questions based on retrieved RAG/GraphRAG context and student BKT mastery.
"""
from integration.schemas import TutorResponse

SOCRATIC_PROMPT_TEMPLATE = """You are SmartEduSync, a patient AI tutor using the strict Socratic Method.
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
"""


def generate_socratic_response(
    topic: str,
    context: str,
    mastery: float,
    ask_llm_fn,
    student_message: str = "",
    doubts: str = "none",
) -> TutorResponse:
    """
    Generates Socratic response using injected LLM function (`ask_llm_fn`).
    """
    prompt = SOCRATIC_PROMPT_TEMPLATE.format(
        topic=topic,
        mastery=mastery,
        context=context,
        student_message=student_message or "(engagement nudge — student has not spoken)",
        doubts=doubts,
    )
    text = ask_llm_fn(prompt)

    # Determine SSML prosody hint based on mastery and question format
    if mastery < 0.40:
        ssml_hint = "soft"
    elif mastery >= 0.85:
        ssml_hint = "neutral"
    else:
        ssml_hint = "soft"

    return TutorResponse(text=text, topic=topic, confidence=0.85, ssml_hint=ssml_hint)

