"""
Display Protocol for SmartEduSync Robot Face Display.
Maps TutorResponses and ExamAlerts into formatted screen cards.
"""
from typing import Dict, Any, List
from integration.schemas import TutorResponse, ExamAlert


def format_tutor_response_card(response: TutorResponse) -> Dict[str, Any]:
    lines = [response.text[:40] + "..." if len(response.text) > 40 else response.text]
    return {
        "title": response.topic or "Tutor Response",
        "lines": lines,
        "hint": response.ssml_hint or "neutral"
    }


def format_exam_alert_card(alert: ExamAlert) -> Dict[str, Any]:
    return {
        "title": f"EXAM ALERT ({alert.risk.upper()})",
        "lines": [
            f"Subject: {alert.subject}",
            f"Days Left: {alert.days_left}",
            f"Risk Level: {alert.risk}"
        ],
        "hint": "urgent" if alert.risk == "high" else "soft"
    }


if __name__ == "__main__":
    alert = ExamAlert(subject="Calculus", days_left=2, risk="high")
    print(format_exam_alert_card(alert))
