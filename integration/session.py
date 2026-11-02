"""Master session: perception, intervention, RAG/GraphRAG tutor, BKT, voice, expression."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus
from integration.schemas import (
    InterventionTrigger,
    TutorResponse,
    TOPIC_INTERVENTION,
    TOPIC_TUTOR_RESPONSE,
)
from part1_companion.perception.engagement import EngagementTracker
from part1_companion.intervention.state_machine import InterventionManager
from part1_companion.mastery.bkt import get_student_context
from part1_companion.persona.accountability import nudge_student, respond_to_student_reply
from part1_companion.voice.tts import speak
from part1_companion.voice.stt import SpeechToText
from part1_companion.hardware.servo import ServoController
from part1_companion.hardware.display import RobotDisplay, WindowSink
from part1_companion.expression.choreography import ChoreographyEngine
from part2_knowledge.tutor.pipeline import run_tutor_turn


class SmartEduSyncSession:
    def __init__(
        self, student_id: str = "student_1", sim: bool = True, silent: bool = False, hardware: str = "mock"
    ):
        self.student_id = student_id
        self.sim = sim
        self.silent = silent
        self.hardware = hardware
        self.servos = ServoController(force_mock=hardware != "real")
        self.display = RobotDisplay(sink=WindowSink())
        self.choreo = ChoreographyEngine(self.servos)
        self.intervention_mgr = InterventionManager(student_id=student_id)
        self.stt = SpeechToText(mode="fallback")
        self.awaiting_accountability_reply = False
        self.perception_task = None
        self._setup_subscribers()

    def _setup_subscribers(self):
        self.intervention_mgr.subscribe()
        bus.subscribe(TOPIC_INTERVENTION, self.on_intervention_trigger)
        bus.subscribe(TOPIC_TUTOR_RESPONSE, self.on_tutor_response)

    async def on_intervention_trigger(self, trigger: InterventionTrigger):
        context = get_student_context(self.student_id)
        topic = trigger.topic or context.get("active_topic", "General Studies")
        response = TutorResponse(
            text=nudge_student(self.student_id, context),
            topic=topic,
            confidence=1.0,
            ssml_hint="playful",
        )
        self.awaiting_accountability_reply = True
        emo, face_art, _pose, _tone = self.choreo.express("intervention.trigger", {"level": trigger.level})
        self.display.show_face(emo, face_art)
        speak(response, silent=self.silent)

    async def on_tutor_response(self, response: TutorResponse):
        emo, face_art, _pose, _tone = self.choreo.express("tutor.response", {})
        self.display.show_face(emo, face_art)
        speak(response, silent=self.silent)

    async def process_user_turn(self, text: str):
        if not text:
            return
        context = get_student_context(self.student_id)
        topic = context.get("active_topic", "General Studies")
        mastery = float(context.get("p_mastery", 0.5))

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

        tutor_res, diagnostics = run_tutor_turn(
            self.student_id, text, topic, mastery, context, session_id="session_1"
        )
        if diagnostics.get("bkt"):
            print(
                f"[BKT] correct={diagnostics['bkt']['correct']} "
                f"score={diagnostics['bkt']['score']} p_mastery={diagnostics['bkt']['p_mastery']}"
            )
        await bus.publish(TOPIC_TUTOR_RESPONSE, tutor_res)

    async def capture_accountability_reply(self) -> None:
        if not self.awaiting_accountability_reply:
            return
        transcript = await asyncio.to_thread(self.stt.listen, "Reply to SmartEduSync > ")
        await self.process_user_turn(transcript)

    async def run(self):
        print("\n=======================================================")
        print("    [SmartEduSync Tabletop Tutor Robot Active]    ")
        print("=======================================================\n")
        tracker = EngagementTracker()
        self.perception_task = asyncio.create_task(
            tracker.run(duration_s=12.0 if self.sim else 0.0, sim=self.sim)
        )
        await asyncio.sleep(1.0)
        print("Session loop active. Ask a question, or wait for engagement intervention.\n")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sim", action="store_true", default=True, help="synthetic perception trace")
    parser.add_argument("--live", dest="sim", action="store_false", help="live webcam Face Mesh + Pose")
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--hardware", choices=("mock", "real"), default=os.getenv("HARDWARE", "mock"))
    parser.add_argument("--once", action="store_true")
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
        if session.perception_task:
            session.perception_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
