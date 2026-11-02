"""End-to-end loop: engagement → intervention → RAG/Socratic tutor → TTS.

Uses the production tutor pipeline (no mock tutor).

Usage:
    python -m demo.simulate_full_loop
    python -m demo.simulate_full_loop --live
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus
from integration.schemas import EngagementUpdate, InterventionTrigger, TOPIC_ENGAGEMENT, TOPIC_INTERVENTION
from part1_companion.intervention.state_machine import InterventionManager
from part1_companion.mastery.bkt import get_student_context
from part1_companion.voice import tts
from part2_knowledge.tutor.pipeline import run_tutor_turn


async def on_intervention(trigger: InterventionTrigger) -> None:
    context = get_student_context("student_1")
    topic = trigger.topic or context.get("active_topic", "Calculus Integrals")
    mastery = float(context.get("p_mastery", 0.5))
    message = (
        f"I have been looking away during {topic}. "
        f"Can you help me start again with the core idea?"
    )
    response, _diag = run_tutor_turn("student_1", message, topic, mastery, context, session_id="full_loop")
    response.ssml_hint = trigger.level if trigger.level != "gentle" else "soft"
    await tts._on_tutor_response(response)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="unused here; loop is event-driven")
    parser.parse_args()

    tts.subscribe()
    manager = InterventionManager(gentle_s=0.5, firm_s=2.5, escalated_s=10.0)
    manager.subscribe()
    bus.subscribe(TOPIC_INTERVENTION, on_intervention)

    print("Publishing a real low-engagement stream into InterventionManager...\n")
    base_ts = 1_000_000.0
    for i in range(6):
        await bus.publish(
            TOPIC_ENGAGEMENT,
            EngagementUpdate(E_t=0.2, emotion="distracted", ts=base_ts + i),
        )
        await asyncio.sleep(0.25)
    print("\nLoop finished: intervention should have produced a grounded Socratic line.")


if __name__ == "__main__":
    asyncio.run(main())
