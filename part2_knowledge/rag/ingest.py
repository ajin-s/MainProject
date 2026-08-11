"""
Phase 0 task: embed one sample text/PDF and store it in a local FAISS index. Confirms the
embedding + vector store pipeline works before hooking up real syllabus PDFs.

Run directly for a smoke test:
    python part2_knowledge/rag/ingest.py
"""
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

INDEX_PATH = Path(__file__).parent / "sample.index"
EMBED_MODEL = "all-MiniLM-L6-v2"  # small, fast, good default

SAMPLE_CHUNKS = [
    "Bayesian Knowledge Tracing models a student's mastery of a skill as a hidden binary state.",
    "GraphRAG combines a knowledge graph with vector retrieval to ground LLM answers in connected concepts.",
    "The Socratic method teaches by asking guiding questions rather than giving direct answers.",
]


def build_sample_index():
    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(SAMPLE_CHUNKS, normalize_embeddings=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype="float32"))
    faiss.write_index(index, str(INDEX_PATH))
    print(f"Indexed {len(SAMPLE_CHUNKS)} chunks -> {INDEX_PATH}")
    return model, index


def query_sample_index(model, index, query: str, k: int = 2):
    q_emb = model.encode([query], normalize_embeddings=True)
    scores, idxs = index.search(np.array(q_emb, dtype="float32"), k)
    return [(SAMPLE_CHUNKS[i], float(s)) for i, s in zip(idxs[0], scores[0])]


# TODO(Part 2 team, Phase 1): replace SAMPLE_CHUNKS with real PyMuPDF-extracted, chunked
# syllabus text, and persist chunk metadata (source, page) alongside the FAISS index so
# retrieval results can be traced back to a source document.

if __name__ == "__main__":
    model, index = build_sample_index()
    results = query_sample_index(model, index, "How does BKT track student learning?")
    print("\nTop matches:")
    for text, score in results:
        print(f"  ({score:.3f}) {text}")
