"""
demo/simulate_intervention.py

Definition-of-done check for part1_companion/intervention/state_machine.py:
feeds 5 fake low-engagement events in a row and confirms the manager escalates
gentle -> firm, then feeds one high-engagement event and confirms it resets to idle.
No camera / perception module needed - this publishes fake EngagementUpdate
messages directly onto the real event bus.

Usage:
    python -m demo.simulate_intervention
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus  # noqa: E402
from integration.schemas import EngagementUpdate, InterventionTrigger, TOPIC_INTERVENTION  # noqa: E402
from part1_companion.intervention.state_machine import InterventionManager  # noqa: E402

received_triggers: list[InterventionTrigger] = []


async def on_intervention_trigger(trigger: InterventionTrigger) -> None:
    received_triggers.append(trigger)
    print(f"  -> InterventionTrigger(level={trigger.level!r}, reason={trigger.reason!r})")


async def main() -> None:
    # Compressed thresholds so we don't wait 10 real minutes: gentle after 0.5s
    # of low engagement, firm after 2.5s, escalated after 10s (of *simulated*
    # elapsed time via fake timestamps below, not real wall-clock waiting).
    manager = InterventionManager(gentle_s=0.5, firm_s=2.5, escalated_s=10.0)
    manager.subscribe()
    bus.subscribe(TOPIC_INTERVENTION, on_intervention_trigger)

    print("Feeding 5 fake low-engagement events (E_t=0.2, one per simulated second)...")
    base_ts = 1_000_000.0  # arbitrary fixed start time, easier to reason about than time.time()
    for i in range(5):
        msg = EngagementUpdate(E_t=0.2, emotion="distracted", ts=base_ts + i)
        await bus.publish("engagement.update", msg)
        await asyncio.sleep(0.05)  # let asyncio.create_task'd handlers actually run
        print(f"  event {i + 1}: E_t={msg.E_t} ts=+{i}s -> state={manager.state.name}")

    assert manager.state.name in ("FIRM", "ESCALATED"), (
        f"expected escalation to FIRM by event 5, got {manager.state.name}"
    )
    assert any(t.level == "gentle" for t in received_triggers), "expected a gentle trigger somewhere in the stream"
    assert any(t.level == "firm" for t in received_triggers), "expected a firm trigger by the 5th event"
    print("PASS: escalated gentle -> firm across 5 low-engagement events.\n")

    print("Feeding 1 fake high-engagement event (E_t=0.9)...")
    high_msg = EngagementUpdate(E_t=0.9, emotion="engaged", ts=base_ts + 5)
    await bus.publish("engagement.update", high_msg)
    await asyncio.sleep(0.05)
    print(f"  -> state={manager.state.name}")

    assert manager.state.name == "IDLE", f"expected reset to IDLE, got {manager.state.name}"
    print("PASS: high engagement reset the state machine to IDLE.")


if __name__ == "__main__":
    asyncio.run(main())
