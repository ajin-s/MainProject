"""
Persistent Memory Store for SmartEduSync Knowledge Engine.
Manages conversation logs, doubts, and quiz answer outcomes across restarts.
"""
import sqlite3
import time
from typing import Dict, List, Optional

MEMORY_DB_PATH = "memory.db"


def init_memory_db(db_path: str = MEMORY_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_log (
            session_id TEXT,
            role TEXT,
            text TEXT,
            ts REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doubts (
            student_id TEXT,
            topic TEXT,
            note TEXT,
            ts REAL,
            PRIMARY KEY (student_id, topic)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answer_outcomes (
            student_id TEXT,
            topic TEXT,
            correct INTEGER,
            ts REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_activity (
            student_id TEXT,
            activity_type TEXT,
            detail TEXT,
            ts REAL
        )
    """)

    conn.commit()
    return conn


def log_conversation(session_id: str, role: str, text: str, db_path: str = MEMORY_DB_PATH):
    conn = init_memory_db(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversation_log (session_id, role, text, ts) VALUES (?, ?, ?, ?)",
        (session_id, role, text, time.time()),
    )
    conn.commit()
    conn.close()


def record_doubt(student_id: str, topic: str, note: str, db_path: str = MEMORY_DB_PATH):
    conn = init_memory_db(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO doubts (student_id, topic, note, ts)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(student_id, topic) DO UPDATE SET note = excluded.note, ts = excluded.ts
        """,
        (student_id, topic, note, time.time()),
    )
    conn.commit()
    conn.close()


def record_answer_outcome(
    student_id: str, topic: str, correct: bool, db_path: str = MEMORY_DB_PATH
):
    conn = init_memory_db(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO answer_outcomes (student_id, topic, correct, ts) VALUES (?, ?, ?, ?)",
        (student_id, topic, 1 if correct else 0, time.time()),
    )
    conn.commit()
    conn.close()


def record_activity(
    student_id: str, activity_type: str, detail: str, db_path: str = MEMORY_DB_PATH
):
    """Records a locally stored study interaction for the accountability personality."""
    conn = init_memory_db(db_path)
    conn.execute(
        "INSERT INTO student_activity (student_id, activity_type, detail, ts) VALUES (?, ?, ?, ?)",
        (student_id, activity_type, detail[:500], time.time()),
    )
    conn.commit()
    conn.close()


def get_recent_activities(
    student_id: str, limit: int = 5, db_path: str = MEMORY_DB_PATH
) -> List[Dict[str, str]]:
    conn = init_memory_db(db_path)
    rows = conn.execute(
        """SELECT activity_type, detail, ts FROM student_activity
           WHERE student_id = ? ORDER BY ts DESC LIMIT ?""",
        (student_id, limit),
    ).fetchall()
    conn.close()
    return [{"activity_type": row[0], "detail": row[1], "ts": row[2]} for row in rows]


def get_doubts(student_id: str, db_path: str = MEMORY_DB_PATH) -> List[Dict[str, str]]:
    conn = init_memory_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT topic, note FROM doubts WHERE student_id = ?", (student_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"topic": r[0], "note": r[1]} for r in rows]


if __name__ == "__main__":
    init_memory_db()
    record_doubt("student_1", "Calculus Integrals", "Struggled with substitution method.")
    doubts = get_doubts("student_1")
    print("Recorded doubts:", doubts)
