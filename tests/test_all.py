"""
Comprehensive Unit Test Suite for SmartEduSync Robot System.
"""
import os
import sys
import sqlite3
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



from part1_companion.perception.engagement import EngagementPerception
from part1_companion.intervention.state_machine import InterventionManager, InterventionState
from part1_companion.mastery.bkt import update_mastery, get_mastery, check_exam_risk, get_student_context, init_db
from part1_companion.persona.guardrail import check, rewrite
from part1_companion.persona.accountability import build_playful_nudge, respond_to_student_reply
from part1_companion.hardware.bus import MockBus
from part1_companion.hardware.servo import ServoController
from part1_companion.hardware.display import RobotDisplay, FileSink
from part1_companion.expression.face import get_face_art
from part1_companion.expression.choreography import ChoreographyEngine

from part2_knowledge.graphrag.graph_build import expand_rag_context
from part2_knowledge.verify.verifier import is_grounded, evaluate_student_answer
from part2_knowledge.memory.store import init_memory_db, log_conversation, record_doubt, get_doubts
from part2_knowledge.rag.material_library import StudyMaterialLibrary


from part1_companion.perception.posture import PostureDetector


def test_engagement_perception():
    perception = EngagementPerception(buffer_duration_sec=2.0, publish_rate_hz=5.0)
    assert perception.process_frame(False, None) is None
    e1 = perception.process_frame(True, 0.8)
    e2 = perception.process_frame(True, 0.2)
    assert e1 == 0.8
    assert e2 == 0.5
    assert perception.compute_engagement_score(0.30, 0.02) > 0.9
    assert perception.compute_engagement_score(0.10, 0.60) == 0.0


def test_posture_detection():
    detector = PostureDetector()
    # Upright keypoints
    r1 = detector.process_landmarks((0.5, 0.3), (0.4, 0.3), (0.6, 0.3), (0.35, 0.6), (0.65, 0.6))
    assert r1["posture"] == "UPRIGHT"
    assert r1["is_slouching"] is False

    # Slouching keypoints (head forward & low)
    r2 = detector.process_landmarks((0.55, 0.52), (0.45, 0.52), (0.65, 0.52), (0.35, 0.6), (0.65, 0.6))
    assert r2["posture"] == "SLOUCHING"
    assert r2["is_slouching"] is True



def test_intervention_state_machine():
    mgr = InterventionManager(gentle_s=0.5, firm_s=2.5, escalated_s=10.0)
    # Gentle escalation
    t1 = mgr.process_engagement(0.2, 1000.0)
    t2 = mgr.process_engagement(0.2, 1001.0)
    assert t2 is not None
    assert t2.level == "gentle"
    # Recovery to IDLE
    t3 = mgr.process_engagement(0.9, 1002.0)
    assert mgr.state == InterventionState.IDLE


def test_bkt_mastery():
    test_db = "test_bkt.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    conn = init_db(test_db)
    p_init = get_mastery(conn, "test_student", "Calculus")
    p_up = update_mastery(conn, "test_student", "Calculus", correct=True)
    assert p_up > p_init

    risk = check_exam_risk("Calculus", days_left=2, p_mastery=0.3)
    assert risk == "high"
    conn.close()

    if os.path.exists(test_db):
        os.remove(test_db)


def test_persona_guardrail():
    facts = {"active_topic": "Calculus", "p_mastery": 0.42, "days_left": 5, "nearest_exam": "Calculus"}
    
    # Toxic check
    r1 = check("Why can't you even do this simple problem?", facts)
    assert r1["verdict"] == "DENIED"

    # Ungrounded stat check
    r2 = check("Your mastery is 99% right now!", facts)
    assert r2["verdict"] == "DENIED"

    # Clean response check
    r3 = check("Let's focus on Calculus today!", facts)
    assert r3["verdict"] == "PASSED"


def test_accountability_personality():
    facts = {"active_topic": "Calculus", "p_mastery": 0.42, "days_left": 5, "nearest_exam": "Calculus"}
    nudge = build_playful_nudge(facts)
    assert "42%" in nudge
    assert "5 days" in nudge
    assert "hopeless" not in nudge.lower()
    assert check(nudge, facts)["verdict"] == "PASSED"
    with tempfile.TemporaryDirectory() as temp_dir:
        reply = respond_to_student_reply(
            "test_persona", "I am tired today", facts, db_path=os.path.join(temp_dir, "memory.db")
        )
        assert "two-minute" in reply


def test_hardware_mock():
    mock_bus = MockBus()
    mock_bus.write_byte_data(0x40, 0x00, 0x10)
    assert len(mock_bus.write_log) == 1

    servos = ServoController(force_mock=True)
    servos.set_angle(0, 45.0)
    assert servos.current_angles[0] == 45.0

    sink = FileSink(output_dir="artifacts")
    display = RobotDisplay(sink=sink)
    display.show_face("curious", get_face_art("curious"))
    assert os.path.exists("artifacts/face_Emotion: curious.txt")


def test_graphrag_context_expansion():
    ctx = expand_rag_context("Calculus Integrals", "Base syllabus context.")
    assert "Riemann Sums" in ctx or "Related concepts" in ctx


def test_verifier():
    grounded = is_grounded("Integrals calculate area under a curve.", ["Integrals represent the area under a curve."])
    assert grounded is True

    correct, score = evaluate_student_answer("What is integral?", ["area", "curve"], "Area under curve")
    assert correct is True
    assert score == 1.0


def test_memory_store():
    test_db = "test_memory.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    record_doubt("s1", "Linear Algebra", "Matrix multiplication rule", db_path=test_db)
    doubts = get_doubts("s1", db_path=test_db)
    assert len(doubts) == 1
    assert doubts[0]["topic"] == "Linear Algebra"

    if os.path.exists(test_db):
        os.remove(test_db)


def test_study_material_onboarding():
    with tempfile.TemporaryDirectory() as temp_dir:
        library = StudyMaterialLibrary(os.path.join(temp_dir, "materials.db"))
        result = library.ingest_bytes(
            "new_student",
            "calculus_notes.txt",
            b"Calculus Integrals use Riemann Sums. Definite Integrals measure accumulated area.",
        )
        assert result["chunks_added"] == 1
        assert result["graph"]["total_nodes"] >= 3
        status = library.onboarding_status("new_student")
        assert status["initialized"] is True
        assert status["chunks"] == 1
        context = library.retrieve_context("new_student", "How do Riemann sums help with integrals?")
        assert "Riemann Sums" in context

def run_all_tests():
    print("--- Running SmartEduSync Unit Tests ---")
    test_engagement_perception()
    print("  [PASS] test_engagement_perception")
    test_posture_detection()
    print("  [PASS] test_posture_detection")
    test_intervention_state_machine()
    print("  [PASS] test_intervention_state_machine")
    test_bkt_mastery()
    print("  [PASS] test_bkt_mastery")
    test_persona_guardrail()
    print("  [PASS] test_persona_guardrail")
    test_accountability_personality()
    print("  [PASS] test_accountability_personality")
    test_hardware_mock()
    print("  [PASS] test_hardware_mock")
    test_graphrag_context_expansion()
    print("  [PASS] test_graphrag_context_expansion")
    test_verifier()
    print("  [PASS] test_verifier")
    test_memory_store()
    print("  [PASS] test_memory_store")
    test_study_material_onboarding()
    print("  [PASS] test_study_material_onboarding")
    print("\n[SUCCESS] All unit tests PASSED successfully!")



if __name__ == "__main__":
    try:
        import pytest
        pytest.main(["-v", __file__])
    except ImportError:
        run_all_tests()
