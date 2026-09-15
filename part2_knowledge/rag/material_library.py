"""Persistent, privacy-first study-material library used during student onboarding.

The library stores extracted text and a concept graph locally in SQLite.  It deliberately
uses lexical retrieval as a dependable baseline; a vector index can be added as an
implementation detail without changing the onboarding or tutoring contracts.
"""
from __future__ import annotations

import io
import json
import re
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

from part2_knowledge.graphrag.graph_mapper import DynamicGraphMapper


DEFAULT_DB_PATH = "study_materials.db"
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".html", ".htm"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


class MaterialError(ValueError):
    """A material could not be safely accepted or meaningfully extracted."""


class StudyMaterialLibrary:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            with conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS study_sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT NOT NULL,
                        source_name TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        created_at REAL NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS study_chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT NOT NULL,
                        source_id INTEGER NOT NULL,
                        page INTEGER NOT NULL DEFAULT 1,
                        text TEXT NOT NULL,
                        FOREIGN KEY(source_id) REFERENCES study_sources(id)
                    );
                    CREATE TABLE IF NOT EXISTS concept_graphs (
                        student_id TEXT PRIMARY KEY,
                        graph_json TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    );
                    """
                )
        finally:
            conn.close()

    @staticmethod
    def _chunk(text: str, words_per_chunk: int = 110, overlap: int = 20) -> Iterable[str]:
        words = text.split()
        if not words:
            return []
        step = max(1, words_per_chunk - overlap)
        return (" ".join(words[i : i + words_per_chunk]) for i in range(0, len(words), step))

    @staticmethod
    def _html_to_text(html: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()

    @staticmethod
    def _ocr_image(data: bytes, filename: str) -> str:
        try:
            from PIL import Image
            import pytesseract

            text = pytesseract.image_to_string(Image.open(io.BytesIO(data))).strip()
            if text:
                return text
        except Exception:
            pass
        raise MaterialError(
            f"No readable text could be extracted from {filename}. Install Tesseract OCR or upload accompanying notes."
        )

    @staticmethod
    def _pdf_text(data: bytes, filename: str) -> List[Dict[str, Any]]:
        try:
            import fitz

            document = fitz.open(stream=data, filetype="pdf")
            pages = [
                {"page": number + 1, "text": page.get_text().strip()}
                for number, page in enumerate(document)
                if page.get_text().strip()
            ]
            document.close()
            if pages:
                return pages
        except Exception as exc:
            raise MaterialError(f"Could not read PDF {filename}: {exc}") from exc
        raise MaterialError(f"PDF {filename} has no selectable text. Upload an OCR-enabled PDF or notes.")

    def ingest_bytes(self, student_id: str, filename: str, data: bytes) -> Dict[str, Any]:
        if not student_id.strip() or not filename.strip() or not data:
            raise MaterialError("student_id, filename, and non-empty content are required.")
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            pages, source_type = self._pdf_text(data, filename), "pdf"
        elif suffix in TEXT_EXTENSIONS:
            pages, source_type = [{"page": 1, "text": data.decode("utf-8", errors="replace")}], "text"
        elif suffix in IMAGE_EXTENSIONS:
            pages, source_type = [{"page": 1, "text": self._ocr_image(data, filename)}], "image"
        elif suffix in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
            raise MaterialError("Video ingestion needs a transcript or captions. Upload its .txt/.vtt transcript as study material.")
        else:
            raise MaterialError(f"Unsupported material type: {suffix or 'unknown'}.")
        return self._store(student_id, filename, source_type, pages)

    def ingest_url(self, student_id: str, url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise MaterialError("Only absolute http(s) study-material URLs are accepted.")
        if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            raise MaterialError("Local network URLs are not accepted.")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "SmartEduSync/1.0"})
            with urllib.request.urlopen(request, timeout=10) as response:
                content = response.read(5_000_000)
                content_type = response.headers.get_content_type()
        except Exception as exc:
            raise MaterialError(f"Could not fetch the study URL: {exc}") from exc
        if content_type == "application/pdf" or parsed.path.lower().endswith(".pdf"):
            pages = self._pdf_text(content, url)
            source_type = "url-pdf"
        else:
            pages = [{"page": 1, "text": self._html_to_text(content.decode("utf-8", errors="replace"))}]
            source_type = "url"
        return self._store(student_id, url, source_type, pages)

    def _store(self, student_id: str, source_name: str, source_type: str, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        chunks = [(page["page"], chunk) for page in pages for chunk in self._chunk(page["text"]) if chunk.strip()]
        if not chunks:
            raise MaterialError("No study text could be extracted from this material.")
        conn = self._connect()
        with conn:
            cursor = conn.execute(
                "INSERT INTO study_sources(student_id, source_name, source_type, created_at) VALUES (?, ?, ?, ?)",
                (student_id, source_name, source_type, time.time()),
            )
            source_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO study_chunks(student_id, source_id, page, text) VALUES (?, ?, ?, ?)",
                [(student_id, source_id, page, chunk) for page, chunk in chunks],
            )
        conn.close()
        summary = self.rebuild_graph(student_id)
        return {"source_id": source_id, "source_name": source_name, "chunks_added": len(chunks), "graph": summary}

    def rebuild_graph(self, student_id: str) -> Dict[str, Any]:
        conn = self._connect()
        with conn:
            rows = conn.execute(
                """SELECT s.source_name, c.page, c.text FROM study_chunks c
                   JOIN study_sources s ON s.id = c.source_id WHERE c.student_id = ?""",
                (student_id,),
            ).fetchall()
        conn.close()
        mapper = DynamicGraphMapper()
        graph = mapper.map_document_to_graph([{"source": source, "page": page, "text": text} for source, page, text in rows])
        graph_json = json.dumps({"nodes": list(graph.nodes(data=True)), "edges": list(graph.edges(data=True))})
        conn = self._connect()
        with conn:
            conn.execute(
                "INSERT INTO concept_graphs(student_id, graph_json, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(student_id) DO UPDATE SET graph_json=excluded.graph_json, updated_at=excluded.updated_at",
                (student_id, graph_json, time.time()),
            )
        conn.close()
        return mapper.get_graph_summary()

    def retrieve_context(self, student_id: str, query: str, k: int = 3) -> str:
        conn = self._connect()
        with conn:
            rows = conn.execute("SELECT text FROM study_chunks WHERE student_id = ?", (student_id,)).fetchall()
            graph_row = conn.execute("SELECT graph_json FROM concept_graphs WHERE student_id = ?", (student_id,)).fetchone()
        conn.close()
        if not rows:
            return ""
        query_words = set(re.findall(r"[a-z0-9]+", query.lower()))
        ranked = sorted(rows, key=lambda row: len(query_words & set(re.findall(r"[a-z0-9]+", row[0].lower()))), reverse=True)
        passages = [row[0] for row in ranked[:k]]
        concepts: List[str] = []
        if graph_row:
            concepts = [node[0] for node in json.loads(graph_row[0]).get("nodes", [])[:12]]
        return "Study material excerpts:\n" + "\n---\n".join(passages) + (f"\nRelated concepts: {', '.join(concepts)}." if concepts else "")

    def onboarding_status(self, student_id: str) -> Dict[str, Any]:
        conn = self._connect()
        with conn:
            sources = conn.execute("SELECT source_name, source_type FROM study_sources WHERE student_id = ?", (student_id,)).fetchall()
            chunks = conn.execute("SELECT COUNT(*) FROM study_chunks WHERE student_id = ?", (student_id,)).fetchone()[0]
            graph = conn.execute("SELECT graph_json FROM concept_graphs WHERE student_id = ?", (student_id,)).fetchone()
        conn.close()
        graph_data = json.loads(graph[0]) if graph else {"nodes": [], "edges": []}
        return {"initialized": bool(sources), "sources": [{"name": name, "type": kind} for name, kind in sources], "chunks": chunks, "concepts": len(graph_data["nodes"]), "relationships": len(graph_data["edges"])}
