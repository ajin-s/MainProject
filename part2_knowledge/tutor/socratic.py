"""
Phase 1 task: given a topic + retrieved context + student's mastery level, generate a guiding
question instead of a direct answer. See SRS Section 6.4.
"""
from integration.schemas import TutorResponse

SOCRATIC_PROMPT_TEMPLATE = """You are a patient tutor using the Socratic method.
Topic: {topic}
Student's current mastery: {mastery:.0%}
Relevant syllabus context: {context}

Do NOT give the direct answer. Ask ONE guiding question that helps the student reason toward it.
If mastery is above 80%, you may give a brief direct explanation instead.
"""


def generate_socratic_response(topic: str, context: str, mastery: float, ask_llm_fn) -> TutorResponse:
    """
    `ask_llm_fn` is injected (e.g. part2_knowledge.llm.dialogue.ask) so this module has no
    hard dependency on which LLM backend is used — easier to test in isolation.
    """
    prompt = SOCRATIC_PROMPT_TEMPLATE.format(topic=topic, mastery=mastery, context=context)
    text = ask_llm_fn(prompt)
    return TutorResponse(text=text, topic=topic, confidence=0.5, ssml_hint="neutral")
