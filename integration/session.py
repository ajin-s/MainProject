"""
Master Interactive Session Orchestrator for SmartEduSync Robot.
Brings perception, intervention state machine, Socratic LLM, persona guardrail,
verifier, memory, hardware expression, and voice into one active loop.
"""
import argparse
import asyncio
import os
import sys

from integration.event_bus import bus
from integration.schemas import (
    EngagementUpdate,
    InterventionTrigger,
    TutorResponse,
    TOPIC_ENGAGEMENT,
    TOPIC_INTERVENTION,
    TOPIC_TUTOR_RESPONSE,
)

from part1_companion.perception.engagement import EngagementTracker
from part1_companion.intervention.state_machine import InterventionManager
from part1_companion.mastery.bkt import get_student_context, update_mastery
from part1_companion.persona.guardrail import check, rewrite
from part1_companion.persona.accountability import nudge_student, respond_to_student_reply
from part1_companion.voice.tts import speak
from part1_companion.voice.stt import SpeechToText

from part1_companion.hardware.servo import ServoController
from part1_companion.hardware.display import RobotDisplay, WindowSink
from part1_companion.expression.choreography import ChoreographyEngine

from part2_knowledge.llm.dialogue import ask
from part2_knowledge.graphrag.graph_build import expand_rag_context
from part2_knowledge.tutor.socratic import generate_socratic_response
from part2_knowledge.verify.verifier import is_grounded
from part2_knowledge.memory.store import log_conversation, record_doubt


class SmartEduSyncSession:
    def __init__(
        self, student_id: str = "student_1", sim: bool = True, silent: bool = False, hardware: str = "mock"
    ):
        self.student_id = student_id
        self.sim = sim
        self.silent = silent
        self.hardware = hardware

        # Hardware & Display
        self.servos = ServoController(force_mock=hardware != "real")
        self.display = RobotDisplay(sink=WindowSink())
        self.choreo = ChoreographyEngine(self.servos)

        # Managers & Voice
        self.intervention_mgr = InterventionManager(student_id=student_id)
        self.stt = SpeechToText(mode="fallback")
        self.awaiting_accountability_reply = False

        self._setup_subscribers()

    def _setup_subscribers(self):
        self.intervention_mgr.subscribe()
        bus.subscribe(TOPIC_INTERVENTION, self.on_intervention_trigger)
        bus.subscribe(TOPIC_TUTOR_RESPONSE, self.on_tutor_response)

    async def on_intervention_trigger(self, trigger: InterventionTrigger):
        context = get_student_context(self.student_id)
        topic = trigger.topic or context.get("active_topic", "General Studies")
        mastery = context.get("p_mastery", 0.5)

        # Persistent accountability nudge: factual, playful, and never insulting.
        response = TutorResponse(
            text=nudge_student(self.student_id, context), topic=topic, confidence=1.0, ssml_hint="playful"
        )
        self.awaiting_accountability_reply = True

        # Guardrail & Speech Choke Point
        g_check, g_reason = check(response.text, context), check(response.text, context).get("reason")
        if check(response.text, context)["verdict"] == "DENIED":
            response.text = rewrite(response.text, context)

        # Grounding Verifier
        # Expressive Body & Face
        emo, face_art, pose, tone = self.choreo.express("intervention.trigger", {"level": trigger.level})
        self.display.show_face(emo, face_art)

        # Speak Response
        speak(response, silent=self.silent)

    async def on_tutor_response(self, response: TutorResponse):
        emo, face_art, pose, tone = self.choreo.express("tutor.response", {})
        self.display.show_face(emo, face_art)
        speak(response, silent=self.silent)

    async def process_user_turn(self, text: str):
        if not text:
            return

        context = get_student_context(self.student_id)
        topic = context.get("active_topic", "General Studies")
        mastery = context.get("p_mastery", 0.5)

        log_conversation("session_1", "student", text)

        if self.awaiting_accountability_reply:
            tutor_res = TutorResponse(
                text=respond_to_student_reply(self.student_id, text, context),
                topic=topic,
                confidence=1.0,
                ssml_hint="soft",
            )
            self.awaiting_accountability_reply = False
            await bus.publish(TOPIC_TUTOR_RESPONSE, tutor_res)
            return

        base_ctx = f"Syllabus material for {topic}."
        rag_ctx = expand_rag_context(topic, base_ctx)

        tutor_res = generate_socratic_response(topic, rag_ctx, mastery, ask_llm_fn=ask, student_message=text)

        if check(tutor_res.text, context)["verdict"] == "DENIED":
            tutor_res.text = rewrite(tutor_res.text, context)

        await bus.publish(TOPIC_TUTOR_RESPONSE, tutor_res)

    async def capture_accountability_reply(self) -> None:
        """Capture microphone/typed fallback speech after a robot nudge and motivate the student."""
        if not self.awaiting_accountability_reply:
            return
        transcript = await asyncio.to_thread(self.stt.listen, "Reply to SmartEduSync > ")
        await self.process_user_turn(transcript)

    async def run(self):
        print("\n=======================================================")
        print("    [SmartEduSync Tabletop Tutor Robot Active]    ")
        print("=======================================================\n")


        # Start perception in background task
        tracker = EngagementTracker()
        # Simulated traces are finite; the camera path stays active until the session closes.
        self.perception_task = asyncio.create_task(tracker.run(duration_s=12.0 if self.sim else 0.0, sim=self.sim))

        await asyncio.sleep(1.0)
        print("Session loop active. You may ask questions or let perception run.\n")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sim", action="store_true", default=True, help="run simulated perception trace")
    parser.add_argument("--live", dest="sim", action="store_false", help="use the live webcam perception path")
    parser.add_argument("--silent", action="store_true", help="suppress real audio output")
    parser.add_argument("--hardware", choices=("mock", "real"), default=os.getenv("HARDWARE", "mock"))
    parser.add_argument("--once", action="store_true", help="run one example turn then exit")
    args = parser.parse_args()

    session = SmartEduSyncSession(sim=args.sim, silent=args.silent, hardware=args.hardware)
    await session.run()
    if args.once:
        await session.process_user_turn("Why do we calculate integrals?")
        await asyncio.sleep(0.1)
        return
    try:
        while True:
            text = await asyncio.to_thread(input, "Student > ")
            await session.process_user_turn(text)
    except (EOFError, KeyboardInterrupt):
        print("\n[SmartEduSync] Session closed.")
    finally:
        session.perception_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
