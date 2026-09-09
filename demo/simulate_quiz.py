"""
demo/simulate_quiz.py

Simulates a student answering a few questions on a topic, so update_mastery()
visibly changes p_mastery over the course of a short session. No real quiz
content needed - just correct/incorrect per question.

Usage:
    python -m demo.simulate_quiz                          # interactive, type y/n per question
    python -m demo.simulate_quiz --auto                    # scripted answers, no typing needed
    python -m demo.simulate_quiz --student s1 --topic Algebra --auto
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from part1_companion.mastery.bkt import get_mastery, init_db, update_mastery  # noqa: E402

# Used only in --auto mode, so there's something to demo without typing anything.
AUTO_ANSWERS = [True, True, False, True, False]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--student", default="demo_student")
    parser.add_argument("--topic", default="Robotics")
    parser.add_argument("--auto", action="store_true", help="use a canned answer sequence instead of typing")
    parser.add_argument("--questions", type=int, default=5, help="number of fake questions to ask")
    args = parser.parse_args()

    conn = init_db()
    p = get_mastery(conn, args.student, args.topic)
    print(f"Starting mastery for {args.student} on {args.topic!r}: {p:.3f}\n")

    for i in range(args.questions):
        if args.auto:
            correct = AUTO_ANSWERS[i % len(AUTO_ANSWERS)]
            print(f"Q{i + 1}: (auto) answered {'correctly' if correct else 'incorrectly'}")
        else:
            answer = input(f"Q{i + 1}: did the student answer correctly? (y/n): ").strip().lower()
            correct = answer.startswith("y")

        p = update_mastery(conn, args.student, args.topic, correct=correct)
        print(f"  -> p_mastery now {p:.3f}")

    print(f"\nFinal mastery after {args.questions} questions: {p:.3f}")


if __name__ == "__main__":
    main()
