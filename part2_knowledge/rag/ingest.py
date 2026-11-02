"""Vector RAG: chunk syllabus text, embed with MiniLM, retrieve with FAISS IP."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import fitz
except ImportError:
    fitz = None

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

INDEX_PATH = Path(__file__).parent / "sample.index"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Default local syllabus used until the student uploads their own notes.
SAMPLE_CHUNKS = [
    "Bayesian Knowledge Tracing models a student's mastery of a skill as a hidden binary state that updates after each correct or incorrect response.",
    "GraphRAG combines a knowledge graph with vector retrieval to ground LLM answers in connected syllabus concepts.",
    "The Socratic method teaches by asking guiding questions rather than giving direct answers so the student reconstructs the idea.",
    "Calculus integrals measure the total accumulation of a quantity, which is the signed area under a curve.",
    "A Riemann sum approximates an integral by adding the areas of thin rectangles under a function.",
    "The Fundamental Theorem of Calculus links differentiation and integration: the derivative of an accumulated integral recovers the original function.",
    "Linear algebra studies vector spaces, linear maps, and matrices that represent those maps.",
    "Matrix multiplication composes linear transformations; eigenvalues describe axes that a transformation only scales.",
    "Robot kinematics maps joint angles to the position and orientation of an end effector in space.",
    "A PID controller reduces tracking error with proportional, integral, and derivative feedback terms.",
]


def extract_pdf_text(pdf_path: str) -> List[Dict[str, Any]]:
    if fitz is None or not Path(pdf_path).exists():
        return [{"page": 1, "text": " ".join(SAMPLE_CHUNKS)}]
    doc = fitz.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        if text.strip():
            pages.append({"page": page_num + 1, "text": text})
    doc.close()
    return pages or [{"page": 1, "text": " ".join(SAMPLE_CHUNKS)}]


def chunk_syllabus_text(raw_text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[str]:
    if RecursiveCharacterTextSplitter is not None:
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_text(raw_text)
    words = raw_text.split()
    chunks = [" ".join(words[i : i + 50]) for i in range(0, len(words), 50)]
    return [c for c in chunks if c.strip()] or list(SAMPLE_CHUNKS)


def retrieve_lexical(query: str, k: int = 3, chunks: Optional[List[str]] = None) -> List[str]:
    corpus = chunks if chunks is not None else SAMPLE_CHUNKS
    q_words = set(query.lower().split())
    scored = [(len(q_words & set(chunk.lower().split())), chunk) for chunk in corpus]
    scored.sort(key=lambda item: item[0], reverse=True)
    hits = [chunk for score, chunk in scored[:k] if score > 0]
    return hits or corpus[:k]


class VectorStore:
    """In-process FAISS inner-product index with lexical fallback."""

    def __init__(self, seed: Optional[List[str]] = None):
        self.chunks: List[str] = list(seed if seed is not None else SAMPLE_CHUNKS)
        self._model = None
        self._index = None

    def add_chunks(self, texts: List[str]) -> None:
        for text in texts:
            clean = text.strip()
            if clean and clean not in self.chunks:
                self.chunks.append(clean)
        self._index = None

    def _ensure_index(self) -> None:
        if self._index is not None or faiss is None or SentenceTransformer is None:
            return
        if self._model is None:
            self._model = SentenceTransformer(EMBED_MODEL)
        embeddings = self._model.encode(self.chunks, normalize_embeddings=True)
        index = faiss.IndexFlatIP(int(embeddings.shape[1]))
        index.add(np.array(embeddings, dtype="float32"))
        self._index = index

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        try:
            self._ensure_index()
            if self._index is None or self._model is None:
                return [(chunk, 1.0) for chunk in retrieve_lexical(query, k=k, chunks=self.chunks)]
            q_emb = self._model.encode([query], normalize_embeddings=True)
            scores, idxs = self._index.search(np.array(q_emb, dtype="float32"), min(k, len(self.chunks)))
            return [(self.chunks[i], float(s)) for i, s in zip(idxs[0], scores[0]) if 0 <= i < len(self.chunks)]
        except Exception:
            return [(chunk, 1.0) for chunk in retrieve_lexical(query, k=k, chunks=self.chunks)]


_store = VectorStore()


def build_sample_index():
    store = VectorStore()
    hits = store.retrieve("How does BKT track student learning?", k=2)
    try:
        store._ensure_index()
        if store._index is not None:
            faiss.write_index(store._index, str(INDEX_PATH))
    except Exception:
        pass
    return store._model, store._index, hits


def query_sample_index(model, index, query: str, k: int = 2) -> List[Tuple[str, float]]:
    return _store.retrieve(query, k=k)


def retrieve_chunks(query: str, k: int = 3, extra_chunks: Optional[List[str]] = None) -> List[str]:
    if extra_chunks:
        merged = VectorStore(seed=_store.chunks + extra_chunks)
        return [text for text, _ in merged.retrieve(query, k=k)]
    return [text for text, _ in _store.retrieve(query, k=k)]


if __name__ == "__main__":
    _, _, results = build_sample_index()
    print("Top matches:")
    for text, score in results:
        print(f"  ({score:.3f}) {text}")
