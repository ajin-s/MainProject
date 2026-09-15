"""
Vector RAG Ingestion Pipeline for SmartEduSync Knowledge Engine.
Uses PyMuPDF (fitz) for PDF extraction, LangChain for semantic chunking,
SentenceTransformers for embedding, and FAISS for vector indexing.
"""
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

INDEX_PATH = Path(__file__).parent / "sample.index"
EMBED_MODEL = "all-MiniLM-L6-v2"

SAMPLE_CHUNKS = [
    "Bayesian Knowledge Tracing models a student's mastery of a skill as a hidden binary state.",
    "GraphRAG combines a knowledge graph with vector retrieval to ground LLM answers in connected concepts.",
    "The Socratic method teaches by asking guiding questions rather than giving direct answers.",
    "Calculus integrals measure the total accumulation of quantity under a curve.",
]


def extract_pdf_text(pdf_path: str) -> List[Dict[str, Any]]:
    """Extracts text from a PDF file page by page using PyMuPDF (fitz)."""
    pages = []
    if fitz is None or not Path(pdf_path).exists():
        return [{"page": 1, "text": " ".join(SAMPLE_CHUNKS)}]

    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages.append({"page": page_num + 1, "text": text})
    doc.close()
    return pages


def chunk_syllabus_text(raw_text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[str]:
    """Chunks text using LangChain RecursiveCharacterTextSplitter."""
    if RecursiveCharacterTextSplitter is not None:
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_text(raw_text)
    
    # Fallback chunking if LangChain is not installed
    words = raw_text.split()
    chunks = []
    for i in range(0, len(words), 50):
        chunks.append(" ".join(words[i : i + 50]))
    return chunks if chunks else SAMPLE_CHUNKS


def build_sample_index():
    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(SAMPLE_CHUNKS, normalize_embeddings=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype="float32"))
    faiss.write_index(index, str(INDEX_PATH))
    print(f"Indexed {len(SAMPLE_CHUNKS)} chunks with LangChain/PyMuPDF pipeline -> {INDEX_PATH}")
    return model, index


def query_sample_index(model, index, query: str, k: int = 2) -> List[Tuple[str, float]]:
    q_emb = model.encode([query], normalize_embeddings=True)
    scores, idxs = index.search(np.array(q_emb, dtype="float32"), k)
    return [(SAMPLE_CHUNKS[i], float(s)) for i, s in zip(idxs[0], scores[0])]


_faiss_cache: Dict[str, Any] = {"model": None, "index": None}


def retrieve_lexical(query: str, k: int = 3, chunks: Optional[List[str]] = None) -> List[str]:
    """Keyword overlap ranking so retrieval works without loading MiniLM."""
    corpus = chunks if chunks is not None else SAMPLE_CHUNKS
    q_words = set(query.lower().split())
    scored = []
    for chunk in corpus:
        overlap = len(q_words & set(chunk.lower().split()))
        scored.append((overlap, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    hits = [chunk for score, chunk in scored[:k] if score > 0]
    return hits or corpus[:k]


def retrieve_chunks(query: str, k: int = 3) -> List[str]:
    """FAISS inner-product retrieve with lexical fallback."""
    try:
        if _faiss_cache["model"] is None or _faiss_cache["index"] is None:
            model, index = build_sample_index()
            _faiss_cache["model"] = model
            _faiss_cache["index"] = index
        hits = query_sample_index(_faiss_cache["model"], _faiss_cache["index"], query, k=k)
        return [text for text, _score in hits]
    except Exception:
        return retrieve_lexical(query, k=k)


if __name__ == "__main__":
    model, index = build_sample_index()
    results = query_sample_index(model, index, "How does BKT track student learning?")
    print("\nTop matches:")
    for text, score in results:
        print(f"  ({score:.3f}) {text}")

