"""
demo/run_engagement_demo.py

Definition-of-done check for part1_companion/perception/engagement.py:
run this, look at the camera for a few seconds, then look away — E_t
printed by this subscriber should visibly drop.

Usage:
    python -m demo.run_engagement_demo --duration 10
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus  # noqa: E402
from integration.schemas import EngagementUpdate, TOPIC_ENGAGEMENT  # noqa: E402
from part1_companion.perception.engagement import EngagementTracker  # noqa: E402


async def on_engagement_update(msg: EngagementUpdate) -> None:
    bar_len = int(msg.E_t * 30)
    bar = "#" * bar_len + "-" * (30 - bar_len)
    print(f"E_t={msg.E_t:0.2f} [{bar}] emotion={msg.emotion}")


async def _async_main(args: argparse.Namespace) -> None:
    bus.subscribe(TOPIC_ENGAGEMENT, on_engagement_update)

    kwargs = {"camera_index": args.camera_index}
    if args.model_path:
        kwargs["model_path"] = args.model_path
    tracker = EngagementTracker(**kwargs)
    await tracker.run(duration_s=args.duration, sim=args.sim)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--sim", action="store_true", help="Replay the deterministic trace instead of opening a camera")
    args = parser.parse_args()

    asyncio.run(_async_main(args))


if __name__ == "__main__":
    main()
