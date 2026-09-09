import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

DB_PATH = "bkt_mastery.db"

def init_db(db_path: str = DB_PATH):
    """Initializes tables for mastery tracking and exam schedules."""
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
    
    # 2. Exams Calendar Table (SRS Requirement)
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
            ("student_2", "Python Basics", 0.85)
        ])
        
    cursor.execute("SELECT COUNT(*) FROM exams")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO exams (subject, exam_date) VALUES (?, ?)
        """, [
            ("Calculus Integrals", "2026-09-15"),
            ("Linear Algebra", "2026-09-22")
        ])
        
    conn.commit()
    conn.close()


def get_student_context(student_id: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Retrieves student context joining mastery + exam calendar (SRS §5.4).
    
    Returns:
        dict containing active_topic, p_mastery, nearest_exam, days_left
    """
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query lowest-mastery topic for the student
    cursor.execute("""
        SELECT topic, p_mastery FROM student_mastery
        WHERE student_id = ?
        ORDER BY p_mastery ASC
        LIMIT 1
    """, (student_id,))
    mastery_row = cursor.fetchone()
    
    if not mastery_row:
        # Fallback default values
        topic, p_mastery = "General Studies", 0.50
    else:
        topic, p_mastery = mastery_row

    # Query nearest upcoming exam
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT subject, exam_date FROM exams
        WHERE exam_date >= ?
        ORDER BY exam_date ASC
        LIMIT 1
    """, (today_str,))
    exam_row = cursor.fetchone()

    if exam_row:
        nearest_exam, exam_date_str = exam_row
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d")
        days_left = (exam_date - datetime.now()).days
        # Ensure days_left doesn't print negative on same-day exam
        days_left = max(1, days_left)
    else:
        nearest_exam = topic
        days_left = 7  # Fallback standard timeline

    conn.close()

    return {
        "student_id": student_id,
        "active_topic": topic,
        "p_mastery": round(p_mastery, 2),
        "nearest_exam": nearest_exam,
        "days_left": days_left
    }


if __name__ == "__main__":
    # Test context function directly
    context = get_student_context("student_1")
    print("--- Grounded Context Output ---")
    print(context)