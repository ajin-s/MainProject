from enum import Enum, auto
from typing import Optional

from integration.event_bus import bus
from integration.schemas import (
    EngagementUpdate,
    InterventionTrigger,
    TOPIC_ENGAGEMENT,
    TOPIC_INTERVENTION,
)
from part1_companion.mastery.bkt import get_student_context


class InterventionState(Enum):
    IDLE = auto()
    GENTLE = auto()
    FIRM = auto()
    ESCALATED = auto()


class InterventionManager:
    def __init__(
        self,
        student_id: str = "student_1",
        low_threshold: float = 0.40,
        gentle_s: float = 0.5,
        firm_s: float = 2.5,
        escalated_s: float = 10.0,
    ):
        self.student_id = student_id
        self.low_threshold = low_threshold
        self.gentle_s = gentle_s
        self.firm_s = firm_s
        self.escalated_s = escalated_s
        self.state = InterventionState.IDLE
        self.low_start_ts: Optional[float] = None

    def subscribe(self):
        bus.subscribe(TOPIC_ENGAGEMENT, self.on_engagement_update)

    async def on_engagement_update(self, msg: EngagementUpdate):
        trigger = self.process_engagement(msg.E_t, msg.ts)
        if trigger:
            await bus.publish(TOPIC_INTERVENTION, trigger)

    def process_engagement(self, smoothed_E_t: float, ts: float) -> Optional[InterventionTrigger]:
        if smoothed_E_t >= self.low_threshold:
            self.state = InterventionState.IDLE
            self.low_start_ts = None
            return None

        if self.low_start_ts is None:
            self.low_start_ts = ts

        duration = ts - self.low_start_ts
        context = get_student_context(self.student_id)
        topic = context.get("active_topic", "General Studies")

        if duration >= self.escalated_s and self.state != InterventionState.ESCALATED:
            self.state = InterventionState.ESCALATED
            return InterventionTrigger(
                level="escalated",
                reason=f"Sustained low engagement ({duration:.1f}s)",
                topic=topic,
                ts=ts,
            )
        elif duration >= self.firm_s and self.state not in (InterventionState.FIRM, InterventionState.ESCALATED):
            self.state = InterventionState.FIRM
            return InterventionTrigger(
                level="firm",
                reason=f"Low engagement ({duration:.1f}s)",
                topic=topic,
                ts=ts,
            )
        elif duration >= self.gentle_s and self.state == InterventionState.IDLE:
            self.state = InterventionState.GENTLE
            return InterventionTrigger(
                level="gentle",
                reason=f"Initial engagement dip ({duration:.1f}s)",
                topic=topic,
                ts=ts,
            )

        return None

    def evaluate_trigger(self, smoothed_E_t: float, low_threshold: float = 0.40):
        """Legacy helper method for direct synchronous checks."""
        if self.state == InterventionState.IDLE and smoothed_E_t < low_threshold:
            self.state = InterventionState.GENTLE
            context = get_student_context(self.student_id)
            return {
                "reason": "sustained_low_engagement",
                "E_t": smoothed_E_t,
                "context": context,
            }
        return None