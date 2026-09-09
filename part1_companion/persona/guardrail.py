import re
from typing import Dict, Any, List, Tuple


# SRS 5.1 Banned toxic / demotivating phrasing
BANNED_PHRASES: List[str] = [
    "hopeless",
    "why can't you even",
    "this is easy",
    "give up",
    "you're bad at",
    "too late for you",
    "stop trying",
]


def _extract_numbers(text: str) -> List[float]:
    """Extracts all standalone numbers and percentages from text."""
    matches = re.findall(r"\b\d+(?:\.\d+)?%?", text)
    extracted = []
    for match in matches:
        clean_num = match.replace("%", "")
        try:
            val = float(clean_num)
            extracted.append(val)
        except ValueError:
            pass
    return extracted


def check(text: str, facts: Dict[str, Any]) -> Tuple[dict, str]:
    """
    Checks candidate text for toxicity, give-up instructions, and ungrounded stats.

    Args:
        text: The generated nudge/response text.
        facts: Grounded context dict containing true values (e.g., mastery, days_left).

    Returns:
        dict: {"verdict": "PASSED" | "DENIED", "reason": Optional[str]}
    """
    text_lower = text.lower()

    # Rule 1 & 2: Check for toxic phrasing or give-up instructions
    for banned in BANNED_PHRASES:
        if banned in text_lower:
            return {
                "verdict": "DENIED",
                "reason": f"Toxic or demotivating language detected: '{banned}'"
            }

    # Rule 3: Fact Grounding - check numeric claims
    extracted_nums = _extract_numbers(text)
    
    # Gather valid numerical values present in the facts dict
    valid_values = set()
    for v in facts.values():
        if isinstance(v, (int, float)):
            valid_values.add(round(float(v), 2))
            if 0.0 <= v <= 1.0:
                valid_values.add(round(v * 100, 2))

    for num in extracted_nums:
        if num not in valid_values and round(num, 2) not in valid_values:
            return {
                "verdict": "DENIED",
                "reason": f"Ungrounded stat detected: number {num} does not exist in ground-truth facts."
            }

    return {"verdict": "PASSED", "reason": None}


def rewrite(text: str, facts: Dict[str, Any]) -> str:
    """
    Rewrites a denied nudge into a clean, encouraging, grounded response using facts.
    """
    topic = facts.get("active_topic", "your current topic")
    mastery_pct = int(facts.get("p_mastery", 0.5) * 100)
    days_left = facts.get("days_left", "a few")
    exam = facts.get("nearest_exam", topic)

    return (
        f"Let's focus on {topic}. You're currently at {mastery_pct}% mastery "
        f"with {days_left} days left until your {exam} exam. You've got this!"
    )


if __name__ == "__main__":
    grounded_facts = {
        "active_topic": "Calculus Integrals",
        "p_mastery": 0.42,
        "nearest_exam": "Calculus Integrals",
        "days_left": 8
    }

    test_cases = [
        "Why can't you even focus on Calculus? It's hopeless.",
        "You only have 2 days left and your mastery is 95%!",
        "Let's spend a few minutes on Calculus Integrals. You're at 42% mastery with 8 days left!"
    ]

    print("--- Running Persona Guardrail Tests ---\n")
    for i, candidate in enumerate(test_cases, 1):
        result = check(candidate, grounded_facts)
        print(f"Test {i}: \"{candidate}\"")
        print(f"Result: {result['verdict']} | Reason: {result['reason']}")
        if result["verdict"] == "DENIED":
            safe_text = rewrite(candidate, grounded_facts)
            print(f"Rewritten: \"{safe_text}\"")
        print("-" * 60)
        