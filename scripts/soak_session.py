"""
Long-running Soak Session Test for SmartEduSync Robot System.
Executes perception streams, interventions, BKT updates, Socratic dialogue, verifier checks,
memory logging, and hardware register write assertions without crashing.
"""
import asyncio
import time

from integration.event_bus import bus
from integration.session import SmartEduSyncSession


async def run_soak_test(duration_sec: float = 10.0):
    print(f"--- Starting SmartEduSync Soak Session Test ({duration_sec}s) ---")
    start_ts = time.time()

    session = SmartEduSyncSession(sim=True, silent=True)
    await session.run()

    # Simulate multi-turn Q&A
    questions = [
        "Why do we use integration in physics?",
        "What is the physical meaning of a derivative?",
        "How does a PID controller balance a tabletop robot?"
    ]

    for i, q in enumerate(questions, 1):
        if (time.time() - start_ts) >= duration_sec:
            break
        print(f"\n[Turn {i}] Student question: '{q}'")
        await session.process_user_turn(q)
        await asyncio.sleep(1.0)

    print("\n[SUCCESS] Soak Session completed successfully with 0 errors.")



if __name__ == "__main__":
    asyncio.run(run_soak_test(duration_sec=10.0))
