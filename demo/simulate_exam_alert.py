"""Run exam-risk scoring on live BKT context plus the explicit high/low cases.

Usage:
    python -m demo.simulate_exam_alert
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus
from integration.schemas import ExamAlert, TOPIC_EXAM_ALERT
from part1_companion.mastery.bkt import check_exam_risk_and_publish, get_student_context

received_alerts: list[ExamAlert] = []


async def on_exam_alert(alert: ExamAlert) -> None:
    received_alerts.append(alert)
    print(f"  -> ExamAlert(subject={alert.subject!r}, days_left={alert.days_left}, risk={alert.risk!r})")


async def main() -> None:
    bus.subscribe(TOPIC_EXAM_ALERT, on_exam_alert)

    context = get_student_context("student_1")
    print("Live BKT context:", context)
    await check_exam_risk_and_publish(
        context["nearest_exam"], int(context["days_left"]), float(context["p_mastery"])
    )
    await asyncio.sleep(0.05)

    print("\nCase: exam 2 days away, p_mastery=0.3 (high risk)")
    before = len(received_alerts)
    await check_exam_risk_and_publish("Robotics", 2, 0.3)
    await asyncio.sleep(0.05)
    assert len(received_alerts) == before + 1
    assert received_alerts[-1].risk == "high"
    print("PASS: high-risk alert published.\n")

    print("Case: exam 30 days away, p_mastery=0.9 (no alert)")
    await check_exam_risk_and_publish("Robotics", 30, 0.9)
    await asyncio.sleep(0.05)
    assert len(received_alerts) == before + 1
    print("PASS: low-risk case published no extra alert.")


if __name__ == "__main__":
    asyncio.run(main())
