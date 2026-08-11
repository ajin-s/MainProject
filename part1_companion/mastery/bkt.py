"""
Phase 0 task: get this running end-to-end with one fake topic so the SQLite schema exists.
Phase 1 task: real BKT update rule + exam-proximity risk scoring (SRS Section 5.4).

Run directly for a smoke test:
    python part1_companion/mastery/bkt.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "mastery.db"

# Standard BKT parameters — tune per topic later, these are reasonable generic defaults.
P_INIT = 0.3      # prior probability of already knowing the skill
P_TRANSIT = 0.1   # probability of learning it after one practice opportunity
P_SLIP = 0.1       # probability of a mistake despite knowing it
P_GUESS = 0.2      # probability of a correct answer despite not knowing it


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mastery (
            student_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            p_mastery REAL NOT NULL,
            updated_at REAL NOT NULL,
            PRIMARY KEY (student_id, topic)
        )
    """)
    conn.commit()
    return conn


def get_mastery(conn, student_id: str, topic: str) -> float:
    row = conn.execute(
        "SELECT p_mastery FROM mastery WHERE student_id=? AND topic=?", (student_id, topic)
    ).fetchone()
    return row[0] if row else P_INIT


def update_mastery(conn, student_id: str, topic: str, correct: bool) -> float:
    """One step of the standard BKT update rule."""
    import time
    p_prev = get_mastery(conn, student_id, topic)

    if correct:
        numerator = p_prev * (1 - P_SLIP)
        denominator = numerator + (1 - p_prev) * P_GUESS
    else:
        numerator = p_prev * P_SLIP
        denominator = numerator + (1 - p_prev) * (1 - P_GUESS)
    p_given_evidence = numerator / denominator if denominator > 0 else p_prev

    p_new = p_given_evidence + (1 - p_given_evidence) * P_TRANSIT

    conn.execute(
        "INSERT INTO mastery (student_id, topic, p_mastery, updated_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(student_id, topic) DO UPDATE SET p_mastery=excluded.p_mastery, updated_at=excluded.updated_at",
        (student_id, topic, p_new, time.time()),
    )
    conn.commit()
    return p_new


if __name__ == "__main__":
    conn = init_db()
    print("Initial mastery (should be default P_INIT):", get_mastery(conn, "student_1", "Robotics"))
    p = update_mastery(conn, "student_1", "Robotics", correct=True)
    print("After one correct answer:", round(p, 3))
    p = update_mastery(conn, "student_1", "Robotics", correct=False)
    print("After one wrong answer:", round(p, 3))
    print(f"\nDB created at: {DB_PATH}")
