"""
demo/simulate_exam_alert.py

Definition-of-done check for check_exam_risk()/check_exam_risk_and_publish()
in part1_companion/mastery/bkt.py: a fake exam 2 days away with low mastery
should produce exactly one ExamAlert event on the bus.

Usage:
    python -m demo.simulate_exam_alert
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus  # noqa: E402
from integration.schemas import ExamAlert, TOPIC_EXAM_ALERT  # noqa: E402
from part1_companion.mastery.bkt import check_exam_risk_and_publish  # noqa: E402

received_alerts: list[ExamAlert] = []


async def on_exam_alert(alert: ExamAlert) -> None:
    received_alerts.append(alert)
    print(f"  -> ExamAlert(subject={alert.subject!r}, days_left={alert.days_left}, risk={alert.risk!r})")


async def main() -> None:
    bus.subscribe(TOPIC_EXAM_ALERT, on_exam_alert)

    print("Case: exam 2 days away, p_mastery=0.3 (should trigger high risk alert)")
    await check_exam_risk_and_publish(subject="Robotics", days_left=2, p_mastery=0.3)
    await asyncio.sleep(0.05)  # let the asyncio.create_task'd handler run

    assert len(received_alerts) == 1, f"expected exactly 1 alert, got {len(received_alerts)}"
    assert received_alerts[0].risk == "high", f"expected high risk, got {received_alerts[0].risk}"
    print("PASS: exactly one ExamAlert published, risk='high'.\n")

    print("Case: exam 30 days away, p_mastery=0.9 (should NOT trigger an alert)")
    await check_exam_risk_and_publish(subject="Robotics", days_left=30, p_mastery=0.9)
    await asyncio.sleep(0.05)

    assert len(received_alerts) == 1, f"expected still only 1 alert total, got {len(received_alerts)}"
    print("PASS: low-risk case correctly published no alert.")


if __name__ == "__main__":
    asyncio.run(main())
