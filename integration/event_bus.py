"""
Minimal async pub-sub event bus. Good enough for local development on one machine before you
decide whether to add Mosquitto/MQTT for the real robot. Swap the internals later without
changing how modules publish/subscribe (same .publish() / .subscribe() interface).

Usage:
    from integration.event_bus import bus
    from integration.schemas import EngagementUpdate, TOPIC_ENGAGEMENT

    async def on_engagement(msg: EngagementUpdate):
        print("got", msg)

    bus.subscribe(TOPIC_ENGAGEMENT, on_engagement)
    await bus.publish(TOPIC_ENGAGEMENT, EngagementUpdate(E_t=0.3, emotion="frustrated"))
"""
import asyncio
from collections import defaultdict
from typing import Callable, Awaitable, Any


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Any], Awaitable[None]]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[Any], Awaitable[None]]):
        self._subscribers[topic].append(handler)

    async def publish(self, topic: str, message: Any):
        for handler in self._subscribers.get(topic, []):
            asyncio.create_task(handler(message))


# Single shared instance for the whole process. Import this, don't instantiate your own.
bus = EventBus()


# --- TODO(both teams): when moving to the real robot / multi-process setup, replace this
# --- with an MQTT-backed implementation (paho-mqtt) behind the same publish/subscribe interface.
