"""
Local LLM Dialogue Module via Ollama with safe mock fallback.
"""
import os

MODEL_NAME = os.getenv("OLLAMA_MODEL", "phi3.5")


def ask(prompt: str, model: str = MODEL_NAME) -> str:
    """
    Query local Ollama model if installed, otherwise return structured mock Socratic response.
    """
    try:
        import ollama
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]
    except Exception:
        # Structured fallback response for offline bench testing
        if "Calculus" in prompt or "integral" in prompt.lower():
            return "What do you notice when you break the area under the curve into smaller rectangles?"
        elif "Robotics" in prompt or "kinematics" in prompt.lower():
            return "How does changing the joint angle affect the end effector's position in space?"
        else:
            return f"[Socratic Guide] What is the core principle behind this topic? Can you break it into smaller steps?"


if __name__ == "__main__":
    print(ask("Explain Bayesian Knowledge Tracing in one sentence."))

