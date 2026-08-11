"""
Phase 0 task: get a local LLM responding via Ollama.

Setup (do this once, per machine):
    1. Install Ollama from https://ollama.com
    2. ollama pull phi3.5          # small, fast, good for a Pi later
       # or: ollama pull llama3.1  # bigger, better quality, needs more RAM
    3. pip install ollama          # not in requirements.txt yet — add once you confirm it works

Run directly for a smoke test:
    python part2_knowledge/llm/dialogue.py
"""

MODEL_NAME = "phi3.5"  # change to whatever you pulled


def ask(prompt: str, model: str = MODEL_NAME) -> str:
    """
    TODO(Part 2 team): once `pip install ollama` works, replace the body with:

        import ollama
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]

    Left as a mock for day 1 so anyone without Ollama installed yet can still run the rest
    of the pipeline (RAG, Socratic prompts) against a fake response.
    """
    return f"[MOCK LLM RESPONSE to: '{prompt}'] — replace this once Ollama is wired up."


if __name__ == "__main__":
    print(ask("Explain Bayesian Knowledge Tracing in one sentence."))
