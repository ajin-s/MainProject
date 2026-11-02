"""Socratic quiz from RAG chunks, scored with keyword overlap and BKT updates.

Usage:
    python -m demo.simulate_quiz --auto
    python -m demo.simulate_quiz --student student_1 --topic "Calculus Integrals"
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from part1_companion.mastery.bkt import get_mastery, init_db, update_mastery
from part2_knowledge.memory.store import record_answer_outcome
from part2_knowledge.tutor.quiz import generate_quiz
from part2_knowledge.verify.verifier import evaluate_student_answer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--student", default="student_1")
    parser.add_argument("--topic", default="Calculus Integrals")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--questions", type=int, default=5)
    args = parser.parse_args()

    conn = init_db()
    p = get_mastery(conn, args.student, args.topic)
    print(f"Starting mastery for {args.student} on {args.topic!r}: {p:.3f}\n")

    items = generate_quiz(args.topic, n=args.questions)
    for i, item in enumerate(items, 1):
        print(f"Q{i}: {item['question']}")
        keywords = list(item["expected_keywords"])
        if args.auto:
            correct_answer = " ".join(keywords[:4]) or item["source"]
            student_text = correct_answer if i % 2 == 1 else "I am not sure about this yet."
            print(f"  (auto) {student_text}")
        else:
            student_text = input("  Your answer: ").strip()

        correct, score = evaluate_student_answer(item["question"], keywords, student_text)
        p = update_mastery(conn, args.student, args.topic, correct=correct)
        record_answer_outcome(args.student, args.topic, correct)
        print(f"  -> {'correct' if correct else 'needs review'} (score={score:.2f}) p_mastery={p:.3f}\n")

    print(f"Final mastery after {args.questions} questions: {p:.3f}")


if __name__ == "__main__":
    main()
