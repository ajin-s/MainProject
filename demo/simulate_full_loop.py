"""
demo/simulate_full_loop.py

Today's integration demo: simulate a low-engagement event stream -> intervention
fires -> tutor generates a grounded nudge -> console prints it as "spoken".

By default this uses part1_companion/mock_tutor.py as a stand-in for Part 2's
real Socratic tutor, so Part 1 can run/demo this alone. Once Part 2's tutor
is wired up and publishing TutorResponse itself on TOPIC_TUTOR_RESPONSE,
run with --real-tutor to skip the mock and use theirs instead.

Usage:
    python -m demo.simulate_full_loop                 # uses the mock tutor
    python -m demo.simulate_full_loop --real-tutor     # expects Part 2's tutor to be wired in
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus  # noqa: E402
from integration.schemas import EngagementUpdate, TOPIC_ENGAGEMENT  # noqa: E402
from part1_companion.intervention.state_machine import InterventionManager  # noqa: E402
from part1_companion.voice import tts  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--real-tutor",
        action="store_true",
        help="skip the mock tutor - assumes Part 2's real tutor is already wired to the bus",
    )
    args = parser.parse_args()

    # 1. Voice: subscribe so any TutorResponse gets "spoken" automatically.
    tts.subscribe()

    # 2. Intervention: compressed thresholds so this runs in seconds, not minutes.
    manager = InterventionManager(gentle_s=0.5, firm_s=2.5, escalated_s=10.0)
    manager.subscribe()

    # 3. Tutor: mock stand-in unless told the real one is already wired up.
    if not args.real_tutor:
        from part1_companion.mock_tutor import subscribe as subscribe_mock_tutor
        subscribe_mock_tutor()
        print("(using mock_tutor.py as a stand-in for Part 2's Socratic tutor)\n")
    else:
        print("(expecting Part 2's real tutor to already be subscribed to intervention.trigger)\n")

    # 4. Simulate a dropping-engagement stream (no camera needed).
    print("Simulating a low-engagement stream...")
    base_ts = 1_000_000.0
    for i in range(6):
        msg = EngagementUpdate(E_t=0.2, emotion="distracted", ts=base_ts + i)
        await bus.publish(TOPIC_ENGAGEMENT, msg)
        await asyncio.sleep(0.2)  # give async subscribers time to run and print in order

    print("\nDone. If you saw an intervention trigger followed by a [TTS - ...] line above,")
    print("the full loop is working end to end.")


if __name__ == "__main__":
    asyncio.run(main())
