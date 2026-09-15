"""
Socratic Model Alignment & Fine-Tuning Dataset Generator for Ollama / Phi-3.5-mini.
Generates an Ollama Modelfile and instruction dataset enforcing strict Socratic tutoring rules.
"""
import json
import os
from pathlib import Path

MODELFILE_CONTENT = """FROM phi3.5

SYSTEM \"\"\"You are SmartEduSync, an empathetic, highly specialized Socratic AI Tutor.
RULES:
1. NEVER provide direct answers or solutions upfront unless student mastery is above 85%.
2. Always reply with ONE targeted guiding question that encourages self-discovery.
3. If the student makes a mistake, pinpoint the conceptual gap without judgment and provide an intuitive analogy.
4. Keep responses concise, warm, and clear (under 3 sentences).\"\"\"

PARAMETER temperature 0.4
PARAMETER top_p 0.9
"""

SOCRATIC_EXAMPLES = [
    {
        "instruction": "Explain how integration works in Calculus.",
        "context": "Calculus integrals measure accumulation of area under a curve.",
        "mastery": 0.42,
        "socratic_output": "Imagine dividing a curved shape into thousands of tiny rectangles. What happens to the accuracy of your total area calculation as those rectangles become infinitely thin?"
    },
    {
        "instruction": "I got x = 5 for the equation 2x + 4 = 10, is that right?",
        "context": "Solving linear equation 2x + 4 = 10 -> 2x = 6 -> x = 3.",
        "mastery": 0.50,
        "socratic_output": "Let's check your answer together! If you plug x = 5 back into 2(5) + 4, what result do you get compared to 10?"
    },
    {
        "instruction": "What is a PID controller in robotics?",
        "context": "PID controllers use Proportional, Integral, and Derivative feedback terms to minimize error.",
        "mastery": 0.35,
        "socratic_output": "Think about steering a bicycle to stay in the center of a lane. What happens if you only react to where you are right now versus predicting how fast you are drifting?"
    }
]


def generate_socratic_modelfile(output_dir: str = "part2_knowledge/llm") -> str:
    path = Path(output_dir) / "Modelfile.socratic"
    with open(path, "w", encoding="utf-8") as f:
        f.write(MODELFILE_CONTENT)
    print(f"[Socratic Trainer] Ollama Modelfile generated -> {path}")
    return str(path)


def generate_training_dataset(output_path: str = "part2_knowledge/llm/socratic_dataset.jsonl"):
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in SOCRATIC_EXAMPLES:
            f.write(json.dumps(ex) + "\n")
    print(f"[Socratic Trainer] Training dataset saved -> {output_path}")


if __name__ == "__main__":
    generate_socratic_modelfile()
    generate_training_dataset()
