"""
Phase 1 task: state machine that watches EngagementUpdate events and decides when to publish
an InterventionTrigger. Start here once Perception (engagement.py) is emitting real scores.

States: idle -> watching -> gentle -> firm -> escalated
"""
from enum import Enum, auto
from integration.schemas import EngagementUpdate, InterventionTrigger

ENGAGEMENT_THRESHOLD = 0.45  # matches SRS Goal 3 default


class State(Enum):
    IDLE = auto()
    WATCHING = auto()
    GENTLE = auto()
    FIRM = auto()
    ESCALATED = auto()


class InterventionManager:
    def __init__(self):
        self.state = State.IDLE
        self.low_engagement_since: float | None = None

    def on_engagement_update(self, msg: EngagementUpdate) -> InterventionTrigger | None:
        """
        TODO(Part 1 team): implement the real escalation logic.
        Skeleton behavior for Phase 0/1: if E_t stays below threshold, escalate; otherwise reset.
        """
        if msg.E_t < ENGAGEMENT_THRESHOLD:
            if self.low_engagement_since is None:
                self.low_engagement_since = msg.ts
            elapsed = msg.ts - self.low_engagement_since
            if elapsed > 600:  # 10 minutes — tune this
                self.state = State.ESCALATED
            elif elapsed > 180:
                self.state = State.FIRM
            elif elapsed > 30:
                self.state = State.GENTLE
            else:
                self.state = State.WATCHING

            if self.state in (State.GENTLE, State.FIRM, State.ESCALATED):
                return InterventionTrigger(
                    level="gentle" if self.state == State.GENTLE else
                          "firm" if self.state == State.FIRM else "escalated",
                    reason=f"engagement below {ENGAGEMENT_THRESHOLD} for {int(elapsed)}s",
                )
        else:
            self.low_engagement_since = None
            self.state = State.IDLE

        return None
