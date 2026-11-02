"""Exercise the production InterventionManager against a timed engagement stream.

Usage:
    python -m demo.simulate_intervention
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus
from integration.schemas import EngagementUpdate, InterventionTrigger, TOPIC_ENGAGEMENT, TOPIC_INTERVENTION
from part1_companion.intervention.state_machine import InterventionManager

received_triggers: list[InterventionTrigger] = []


async def on_intervention_trigger(trigger: InterventionTrigger) -> None:
    received_triggers.append(trigger)
    print(f"  -> InterventionTrigger(level={trigger.level!r}, reason={trigger.reason!r}, topic={trigger.topic!r})")


async def main() -> None:
    manager = InterventionManager(gentle_s=0.5, firm_s=2.5, escalated_s=10.0)
    manager.subscribe()
    bus.subscribe(TOPIC_INTERVENTION, on_intervention_trigger)

    print("Low-engagement stream (E_t=0.2)...")
    base_ts = 1_000_000.0
    for i in range(5):
        msg = EngagementUpdate(E_t=0.2, emotion="distracted", ts=base_ts + i)
        await bus.publish(TOPIC_ENGAGEMENT, msg)
        await asyncio.sleep(0.05)
        print(f"  event {i + 1}: E_t={msg.E_t} ts=+{i}s -> state={manager.state.name}")

    assert manager.state.name in ("FIRM", "ESCALATED"), manager.state.name
    assert any(t.level == "gentle" for t in received_triggers)
    assert any(t.level == "firm" for t in received_triggers)
    print("PASS: gentle -> firm with BKT topic attached.\n")

    print("Recovery stream (E_t=0.9)...")
    await bus.publish(TOPIC_ENGAGEMENT, EngagementUpdate(E_t=0.9, emotion="engaged", ts=base_ts + 5))
    await asyncio.sleep(0.05)
    assert manager.state.name == "IDLE"
    print("PASS: high engagement reset to IDLE.")


if __name__ == "__main__":
    asyncio.run(main())
