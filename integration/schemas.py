"""
Shared event schemas for SmartEduSync.

THIS FILE IS THE CONTRACT BETWEEN PART 1 AND PART 2.
Post in the team channel before changing field names here — both teams' code depends on this.

These match Section 4.2 of the SRS. Each event is a small, serializable object published on the
event bus (see event_bus.py) and consumed by whichever module subscribes to it.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional
import time


class EngagementUpdate(BaseModel):
    """Published by Part 1 Perception Service at ~5 Hz."""
    E_t: float = Field(..., ge=0.0, le=1.0, description="Fused engagement score, 0=disengaged, 1=fully engaged")
    emotion: str = Field(..., description="e.g. 'engaged', 'confused', 'frustrated', 'bored'")
    posture: Optional[str] = Field("UPRIGHT", description="e.g. 'UPRIGHT', 'SLOUCHING'")
    neck_angle: Optional[float] = Field(0.0, description="Neck inclination angle in degrees")
    is_slouching: Optional[bool] = Field(False, description="True if student is slouching")
    ts: float = Field(default_factory=time.time)



class InterventionTrigger(BaseModel):
    """Published by Part 1 Intervention Manager when it decides to act."""
    level: Literal["gentle", "firm", "escalated"]
    reason: str = Field(..., description="Short human-readable reason, e.g. 'low engagement 10min'")
    topic: Optional[str] = Field(None, description="Study topic in focus, if known")
    ts: float = Field(default_factory=time.time)


class TutorResponse(BaseModel):
    """Published by Part 2 Socratic Tutor after generating a reply."""
    text: str
    ssml_hint: Optional[str] = Field(None, description="Suggested tone: 'soft', 'neutral', 'urgent'")
    topic: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    ts: float = Field(default_factory=time.time)


class MasteryUpdate(BaseModel):
    """Published by Part 1 BKT Tracker whenever a topic's mastery probability changes."""
    topic: str
    p_mastery: float = Field(..., ge=0.0, le=1.0)
    ts: float = Field(default_factory=time.time)


class ExamAlert(BaseModel):
    """Published by Part 1 BKT Tracker when exam proximity + low mastery cross a risk threshold."""
    subject: str
    days_left: int
    risk: Literal["low", "medium", "high"]
    ts: float = Field(default_factory=time.time)


# Topic name constants — use these, not raw strings, when publishing/subscribing.
TOPIC_ENGAGEMENT = "engagement.update"
TOPIC_INTERVENTION = "intervention.trigger"
TOPIC_TUTOR_RESPONSE = "tutor.response"
TOPIC_MASTERY = "mastery.update"
TOPIC_EXAM_ALERT = "exam.alert"
