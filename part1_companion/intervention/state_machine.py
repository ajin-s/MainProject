from part1_companion.mastery.bkt import get_student_context

class InterventionManager:
    def __init__(self, student_id: str = "student_1"):
        self.student_id = student_id
        self.state = "IDLE"

    def evaluate_trigger(self, smoothed_E_t: float, low_threshold: float = 0.40):
        """
        Transitions state when low engagement is detected and attaches DB grounded context.
        """
        if self.state == "IDLE" and smoothed_E_t < low_threshold:
            self.state = "INTERVENING"
            
            # SRS §5.4: Read grounded context directly from SQLite DB
            context = get_student_context(self.student_id)
            
            trigger_event = {
                "reason": "sustained_low_engagement",
                "E_t": smoothed_E_t,
                "context": context  # Real numbers attached directly!
            }
            return trigger_event
            
        return None