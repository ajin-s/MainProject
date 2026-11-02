"""
SmartEduSync — Master Presentation Defense Runner & Interactive Control Center.
Group 07 (MBCCET) | Final Year Engineering Capstone Project

Launches the complete production system:
  1. Initializes & verifies local SQLite databases (bkt_mastery.db, memory.db, study_materials.db)
  2. Pre-populates clean syllabus materials & concept knowledge graph
  3. Launches FastAPI web dashboard & telemetry engine on http://127.0.0.1:8000
  4. Automatically opens the presentation interface in your default browser
  5. Outputs live presentation cheat-sheet and examiner defense talking points in terminal
"""
import os
import sys
import time
import sqlite3
import threading
import webbrowser

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def initialize_presentation_data():
    """Ensure all databases have rich, clean demo data for tomorrow's defense."""
    print("[1/3] Initializing SmartEduSync databases...")

    # 1. BKT Mastery Database
    bkt_db = os.path.join(PROJECT_ROOT, "bkt_mastery.db")
    conn = sqlite3.connect(bkt_db)
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS student_mastery (
                student_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                p_mastery REAL NOT NULL,
                PRIMARY KEY (student_id, topic)
            );
            CREATE TABLE IF NOT EXISTS exams (
                subject TEXT PRIMARY KEY,
                exam_date TEXT NOT NULL
            );
        """)
        # Seed students
        conn.execute("INSERT OR REPLACE INTO student_mastery VALUES ('student_1', 'Calculus Integrals', 0.75)")
        conn.execute("INSERT OR REPLACE INTO student_mastery VALUES ('student_1', 'Linear Algebra', 0.78)")
        conn.execute("INSERT OR REPLACE INTO student_mastery VALUES ('student_1', 'Robotics Kinematics', 0.62)")
        # Seed upcoming exams
        conn.execute("INSERT OR REPLACE INTO exams VALUES ('Calculus Integrals', '2026-11-05')")
        conn.execute("INSERT OR REPLACE INTO exams VALUES ('Robotics Kinematics', '2026-11-04')")
        conn.execute("INSERT OR REPLACE INTO exams VALUES ('Linear Algebra', '2026-11-12')")
    conn.close()

    # 2. Memory Database
    mem_db = os.path.join(PROJECT_ROOT, "memory.db")
    conn = sqlite3.connect(mem_db)
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS doubts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                note TEXT NOT NULL,
                timestamp REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS answer_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                correct INTEGER NOT NULL,
                timestamp REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS student_activity (
                student_id TEXT PRIMARY KEY,
                last_seen REAL NOT NULL
            );
        """)
    conn.close()

    # 3. Study Material Library
    from part2_knowledge.rag.material_library import StudyMaterialLibrary
    mat_lib = StudyMaterialLibrary(os.path.join(PROJECT_ROOT, "study_materials.db"))
    status = mat_lib.onboarding_status("student_1")
    if not status["initialized"]:
        syllabus_text = (
            "Calculus Integrals measure the total accumulation of a quantity, which is the signed area under a curve. "
            "A Riemann sum approximates an integral by adding the areas of thin rectangles under a function. "
            "The Fundamental Theorem of Calculus links differentiation and integration: the derivative of an accumulated integral "
            "recovers the original function. Definite Integrals calculate exact accumulation within upper and lower limits. "
            "Linear Algebra studies vector spaces, linear transformations, and Matrix Multiplication. Eigenvalues describe axes "
            "that a transformation only scales. In Robotics, Kinematics maps joint servo angles to end-effector positions. "
            "A PID controller reduces tracking error using Proportional, Integral, and Derivative control feedback."
        )
        mat_lib.ingest_bytes("student_1", "Syllabus_Core_Notes.txt", syllabus_text.encode("utf-8"))

    print("      [OK] BKT, Memory & GraphRAG databases verified.")


def print_banner():
    banner = """
========================================================================================
   ____                         _   ______     _       ____                   
  / ___| _ __ ___   __ _ _ __ _| |_| ____|  __| |_   _/ ___| _   _ _ __   ___ 
  \\___ \\| '_ ` _ \\ / _` | '__|_  __|  _|   / _` | | | \\___ \\| | | | '_ \\ / __|
   ___) | | | | | | (_| | |    | |_| |___ | (_| | |_| |___) | |_| | | | | (__ 
  |____/|_| |_| |_|\\__,_|_|     \\__|_____| \\__,_|\\__,_|____/ \\__, |_| |_|\\___|
                                                             |___/             
                 Privacy-First Tabletop AI Tutoring Robot
                     Group 07 Capstone Presentation Defense
========================================================================================
"""
    print(banner)


def print_cheat_sheet():
    sheet = """
----------------------------------------------------------------------------------------
                      5-MINUTE DEFENSE DEMONSTRATION SCRIPT
----------------------------------------------------------------------------------------
[STEP 1: OLED EMOTION DISPLAY & HARDWARE MAPPING]
  * Show the 8-state facial display on the dashboard (Cyber OLED Eyes or 128x64 Bitmap).
  * Point to: idle, watching, listening, thinking, curious, happy, concerned, alert.
  * Point to the PCA9685 I2C register logger (Ch 0 Pan, Ch 1 Tilt, Ch 2/3 Arms).
  * Talking Point: "We use a hardware abstraction with I2C register-level writes (0x40)
    benchtested via MockBus, fully ready for the physical Raspberry Pi 5 & MG90S servos."

[STEP 2: ERGONOMIC PERCEPTION & SLOUCH FUSION]
  * Click '🎯 1. Engagement Dip -> Nudge': Watch engagement drop to 0.20, robot face
    turns 'concerned', head tilts, and robot delivers a grounded Socratic nudge!
  * Click '🧘 2. Slouch -> Posture Alert': Watch neck angle jump to 32.5°, posture flag
    flip to SLOUCHING, and fused engagement penalty activate!
  * Talking Point: "Perception uses a 2-second rolling ring buffer (10 samples @ 5 Hz)
    fused with geometric neck-angle calculation. Not a black-box CNN, but an auditable,
    privacy-preserving rule engine."

[STEP 3: SOCRATIC TEACHING & FACT GROUNDING]
  * Click the preset question: 'Why do we calculate integrals in physics?'
  * Notice the response: It asks a guiding question rather than spoiling the answer!
  * Turn on Voice Speech: Hear the robot speak with emotion-mapped vocal prosody.
  * Click the 🎤 microphone button to demonstrate voice speech-to-text input!
  * Talking Point: "Our Socratic engine uses local RAG with MiniLM embeddings,
    gated by a Safety Guardrail and Verifier to guarantee zero hallucinations."

[STEP 4: GRAPHRAG CONCEPT MAP & DYNAMIC ONBOARDING]
  * Point to the interactive NetworkX Knowledge Graph on the right panel.
  * Show the connections between Calculus Integrals, Riemann Sums, and PID Controllers.
  * Point to the Material Onboarding box: Upload any PDF/text notes and watch the
    chunks and concept graph dynamically update!

[STEP 5: BAYESIAN KNOWLEDGE TRACING & EXAM RADAR]
  * Click '📝 4. Socratic Quiz & BKT Update': Submit an answer and watch the mastery
    percentage update live using the classic BKT parameter update formula!
  * Click '🚨 3. High Risk Exam Radar': Shows proximity and risk calculation.
----------------------------------------------------------------------------------------
"""
    print(sheet)


def launch_server():
    import uvicorn
    from integration.web_dashboard import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def main():
    print_banner()
    initialize_presentation_data()
    print("[2/3] Starting SmartEduSync Control Server on http://127.0.0.1:8000 ...")

    # Start Uvicorn in background thread
    server_thread = threading.Thread(target=launch_server, daemon=True)
    server_thread.start()

    time.sleep(1.2)
    print("[3/3] Opening presentation dashboard in your browser...")
    webbrowser.open("http://127.0.0.1:8000")

    print("\n[SUCCESS] SmartEduSync Robot Control Center is LIVE at http://127.0.0.1:8000\n")
    print_cheat_sheet()
    print("\nPress Ctrl+C to close the session.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SmartEduSync] Presentation server shut down gracefully.")


if __name__ == "__main__":
    main()
