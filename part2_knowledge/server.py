from fastapi import FastAPI
from pydantic import BaseModel

from part2_knowledge.rag.ingest import (
    build_sample_index,
    query_sample_index,
)

from part2_knowledge.graphhrag.graph_build import (
    build_sample_graph,
    related_topics,
)

from part2_knowledge.tutor.socratic import generate_socratic_response
from part2_knowledge.llm.dialogue import ask


app = FastAPI(title="SmartEduSync Part 2 Knowledge Service")


class ChatRequest(BaseModel):
    message: str
    session_id: str
    topic: str | None = None


class ChatResponse(BaseModel):
    text: str
    ssml_hint: str | None = None
    topic: str | None = None
    confidence: float
    grounded: bool


# Load RAG model, FAISS index, and graph once at startup.
MODEL, INDEX = build_sample_index()
GRAPH = build_sample_graph()


# Keep conversation history for each session.
SESSION_HISTORY: dict[str, list[dict[str, str]]] = {}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    # Get or create session history.
    history = SESSION_HISTORY.setdefault(
        request.session_id,
        []
    )

    # Include previous conversation so follow-up questions
    # have context.
    history_text = "\n".join(
        f"{item['role']}: {item['text']}"
        for item in history[-6:]
    )

    # ---------------------------------------------------------
    # 1. RAG retrieval
    # ---------------------------------------------------------
    results = query_sample_index(
        MODEL,
        INDEX,
        request.message,
        k=2,
    )

    context = "\n".join(
        f"[source: sample, page: unknown] {text}"
        for text, score in results
    )

    # ---------------------------------------------------------
    # 2. Graph 1-hop expansion
    # ---------------------------------------------------------
    graph_context = ""

    if request.topic:
        related = related_topics(
            GRAPH,
            request.topic
        )

        if related:
            graph_context = (
                "\nRelated topics from knowledge graph: "
                + ", ".join(related)
            )

    context += graph_context

    # ---------------------------------------------------------
    # 3. Topic
    # ---------------------------------------------------------
    topic = request.topic or "general"

    # ---------------------------------------------------------
    # 4. Socratic LLM response
    # ---------------------------------------------------------
    prompt_context = (
        f"Previous conversation:\n{history_text}\n\n"
        f"Retrieved context:\n{context}"
    )

    tutor_response = generate_socratic_response(
        topic=topic,
        context=prompt_context,
        mastery=0.5,
        ask_llm_fn=ask,
    )

    # ---------------------------------------------------------
    # 5. Save conversation
    # ---------------------------------------------------------
    history.append(
        {
            "role": "user",
            "text": request.message,
        }
    )

    history.append(
        {
            "role": "assistant",
            "text": tutor_response.text,
        }
    )

    # ---------------------------------------------------------
    # Temporary grounded flag
    # ---------------------------------------------------------
    # The real LLM verifier will replace this in Task 2.
    grounded = bool(results)

    # ---------------------------------------------------------
    # Print retrieved sources and pages
    # ---------------------------------------------------------
    print("\nRetrieved sources:")

    for text, score in results:
        print(
            f"  source=sample, "
            f"page=unknown, "
            f"score={score:.3f}"
        )

        print(f"  {text}")

    # ---------------------------------------------------------
    # Return response
    # ---------------------------------------------------------
    return ChatResponse(
        text=tutor_response.text,
        ssml_hint=tutor_response.ssml_hint,
        topic=tutor_response.topic,
        confidence=tutor_response.confidence,
        grounded=grounded,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "part2_knowledge.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
