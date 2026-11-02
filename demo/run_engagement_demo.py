"""Live (or synthetic) engagement + posture perception on the real event bus.

Usage:
    python -m demo.run_engagement_demo --live --duration 15
    python -m demo.run_engagement_demo --sim --duration 8
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.event_bus import bus
from integration.schemas import EngagementUpdate, TOPIC_ENGAGEMENT
from part1_companion.perception.engagement import EngagementTracker


async def on_engagement_update(msg: EngagementUpdate) -> None:
    bar_len = int(msg.E_t * 30)
    bar = "#" * bar_len + "-" * (30 - bar_len)
    posture = msg.posture or "UPRIGHT"
    print(
        f"E_t={msg.E_t:0.2f} [{bar}] emotion={msg.emotion} "
        f"posture={posture} slouch={bool(msg.is_slouching)} neck={msg.neck_angle}"
    )


async def _async_main(args: argparse.Namespace) -> None:
    bus.subscribe(TOPIC_ENGAGEMENT, on_engagement_update)
    tracker = EngagementTracker(camera_index=args.camera_index)
    await tracker.run(duration_s=args.duration, sim=not args.live)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--live", action="store_true", help="webcam Face Mesh + Pose")
    parser.add_argument("--sim", dest="live", action="store_false", help="synthetic lab trace")
    parser.set_defaults(live=False)
    args = parser.parse_args()
    asyncio.run(_async_main(args))


if __name__ == "__main__":
    main()
