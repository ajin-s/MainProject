import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Union

from integration.event_bus import bus
from integration.schemas import ExamAlert, MasteryUpdate, TOPIC_EXAM_ALERT, TOPIC_MASTERY

DB_PATH = "bkt_mastery.db"


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Initializes tables for mastery tracking and exam schedules, returning a connection."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Mastery Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_mastery (
            student_id TEXT,
            topic TEXT,
            p_mastery REAL,
            PRIMARY KEY (student_id, topic)
        )
    """)

    # 2. Exams Calendar Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            subject TEXT PRIMARY KEY,
            exam_date TEXT
        )
    """)

    # Seed mock data if empty
    cursor.execute("SELECT COUNT(*) FROM student_mastery")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO student_mastery (student_id, topic, p_mastery) VALUES (?, ?, ?)
        """, [
            ("student_1", "Calculus Integrals", 0.42),
            ("student_1", "Linear Algebra", 0.78),
            ("demo_student", "Robotics", 0.50),
        ])

    cursor.execute("SELECT COUNT(*) FROM exams")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO exams (subject, exam_date) VALUES (?, ?)
        """, [
            ("Calculus Integrals", "2026-09-18"),
            ("Linear Algebra", "2026-09-25"),
            ("Robotics", "2026-09-20"),
        ])

    conn.commit()
    return conn


def get_mastery(db: Union[sqlite3.Connection, str], student_id: str, topic: str) -> float:
    close_on_exit = False
    if isinstance(db, str):
        conn = sqlite3.connect(db)
        close_on_exit = True
    else:
        conn = db

    cursor = conn.cursor()
    cursor.execute(
        "SELECT p_mastery FROM student_mastery WHERE student_id = ? AND topic = ?",
        (student_id, topic),
    )
    row = cursor.fetchone()

    if close_on_exit:
        conn.close()

    return row[0] if row else 0.50


def update_mastery(
    db: Union[sqlite3.Connection, str],
    student_id: str,
    topic: str,
    correct: bool,
    p_transit: float = 0.1,
    p_slip: float = 0.1,
    p_guess: float = 0.2,
) -> float:
    p_prev = get_mastery(db, student_id, topic)

    if correct:
        p_obs = (p_prev * (1.0 - p_slip)) / (p_prev * (1.0 - p_slip) + (1.0 - p_prev) * p_guess)
    else:
        p_obs = (p_prev * p_slip) / (p_prev * p_slip + (1.0 - p_prev) * (1.0 - p_guess))

    p_updated = p_obs + (1.0 - p_obs) * p_transit
    p_updated = round(max(0.0, min(1.0, p_updated)), 3)

    close_on_exit = False
    if isinstance(db, str):
        conn = sqlite3.connect(db)
        close_on_exit = True
    else:
        conn = db

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO student_mastery (student_id, topic, p_mastery)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id, topic) DO UPDATE SET p_mastery = excluded.p_mastery
        """,
        (student_id, topic, p_updated),
    )
    conn.commit()

    if close_on_exit:
        conn.close()

    return p_updated


async def update_mastery_and_publish(
    db: Union[sqlite3.Connection, str], student_id: str, topic: str, correct: bool
) -> float:
    """Update BKT, publish the shared mastery event, and emit an exam alert when needed."""
    p_mastery = update_mastery(db, student_id, topic, correct)
    await bus.publish(TOPIC_MASTERY, MasteryUpdate(topic=topic, p_mastery=p_mastery))

    # Read the matching exam date when one exists; this preserves the topic/exam relationship.
    close_on_exit = isinstance(db, str)
    conn = sqlite3.connect(db) if close_on_exit else db
    try:
        row = conn.execute("SELECT exam_date FROM exams WHERE subject = ?", (topic,)).fetchone()
        if row:
            days_left = max(1, (datetime.strptime(row[0], "%Y-%m-%d") - datetime.now()).days)
            await check_exam_risk_and_publish(topic, days_left, p_mastery)
    finally:
        if close_on_exit:
            conn.close()
    return p_mastery


def check_exam_risk(topic: str, days_left: int, p_mastery: float) -> str:
    """SRS §5.4: Determines exam risk category."""
    if days_left <= 3 and p_mastery < 0.50:
        return "high"
    elif days_left <= 7 and p_mastery < 0.70:
        return "medium"
    else:
        return "low"


async def check_exam_risk_and_publish(subject: str, days_left: int, p_mastery: float):
    risk = check_exam_risk(subject, days_left, p_mastery)
    if risk in ("medium", "high"):
        alert = ExamAlert(subject=subject, days_left=days_left, risk=risk)
        await bus.publish(TOPIC_EXAM_ALERT, alert)


def get_student_context(student_id: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Retrieves student context joining mastery + exam calendar (SRS §5.4)."""
    conn = init_db(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT topic, p_mastery FROM student_mastery
        WHERE student_id = ?
        ORDER BY p_mastery ASC
        LIMIT 1
    """,
        (student_id,),
    )
    mastery_row = cursor.fetchone()

    if not mastery_row:
        topic, p_mastery = "General Studies", 0.50
    else:
        topic, p_mastery = mastery_row

    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        SELECT subject, exam_date FROM exams
        WHERE exam_date >= ?
        ORDER BY exam_date ASC
        LIMIT 1
    """,
        (today_str,),
    )
    exam_row = cursor.fetchone()

    if exam_row:
        nearest_exam, exam_date_str = exam_row
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d")
        days_left = (exam_date - datetime.now()).days
        days_left = max(1, days_left)
    else:
        nearest_exam = topic
        days_left = 7

    conn.close()

    return {
        "student_id": student_id,
        "active_topic": topic,
        "p_mastery": round(p_mastery, 2),
        "nearest_exam": nearest_exam,
        "days_left": days_left,
    }


if __name__ == "__main__":
    context = get_student_context("student_1")
    print("--- Grounded Context Output ---")
    print(context)
