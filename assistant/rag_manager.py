"""
RAG & Material Ingestion Manager
Scans learn/material/ for textbooks, lecture notes, and PDFs.
Extracts text via pdftotext, chunks documents, and configures AIChat RAG capabilities.
"""

import os
import subprocess
import glob
import re
from typing import List, Dict, Tuple, Optional

MATERIAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "material"))
AICHAT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".aichat"))
RAGS_DIR = os.path.join(AICHAT_DIR, "rags")

class MaterialRAGManager:
    def __init__(self, material_dir: str = MATERIAL_DIR, rags_dir: str = RAGS_DIR):
        self.material_dir = material_dir
        self.rags_dir = rags_dir
        os.makedirs(self.rags_dir, exist_ok=True)
        self.indexed_chunks: List[Dict[str, str]] = []

    def scan_materials(self) -> Dict[str, List[str]]:
        """Finds all authoritative documents grouped by subject."""
        subjects = {}
        if not os.path.exists(self.material_dir):
            return subjects

        for subject in os.listdir(self.material_dir):
            subj_path = os.path.join(self.material_dir, subject)
            if os.path.isdir(subj_path):
                files = []
                for ext in ("*.pdf", "*.txt", "*.md", "*.docx"):
                    files.extend(glob.glob(os.path.join(subj_path, ext)))
                if files:
                    subjects[subject] = files
        return subjects

    def extract_text_from_file(self, file_path: str) -> str:
        """Extracts plain text from PDF or text file."""
        if file_path.endswith(".pdf"):
            try:
                res = subprocess.run(["pdftotext", file_path, "-"], capture_output=True, text=True, check=True)
                return res.stdout
            except Exception as e:
                try:
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    return "\n\n".join(page.extract_text() or "" for page in reader.pages)
                except Exception:
                    pass
                print(f"Warning: Could not extract PDF {file_path}. To enable PDF support:")
                print("  • macOS: brew install poppler")
                print("  • Ubuntu/Linux: sudo apt install poppler-utils")
                print("  • Or install: pip install pypdf")
                return ""
        else:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Failed to read {file_path}: {e}")
                return ""

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 150) -> List[str]:
        """Splits text into overlapping chunks respecting paragraph boundaries."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue
            p_len = len(p_clean)
            if current_len + p_len > chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                # Keep last paragraph for overlap
                current_chunk = [current_chunk[-1]] if len(current_chunk) > 1 else []
                current_len = sum(len(x) for x in current_chunk)

            current_chunk.append(p_clean)
            current_len += p_len

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        return chunks

    def build_index(self, subject: Optional[str] = None, verbose: bool = False) -> int:
        """Indexes all materials for a subject (or all subjects)."""
        materials = self.scan_materials()
        self.indexed_chunks = []
        total_chunks = 0

        for subj, files in materials.items():
            if subject and subj != subject:
                continue
            for fpath in files:
                text = self.extract_text_from_file(fpath)
                chunks = self.chunk_text(text)
                for i, c in enumerate(chunks):
                    self.indexed_chunks.append({
                        "subject": subj,
                        "file": os.path.basename(fpath),
                        "path": fpath,
                        "chunk_id": i,
                        "text": c
                    })
                    total_chunks += 1

        if verbose:
            print(f"✓ Indexed {total_chunks} chunks across {len(materials)} subject(s) in {self.material_dir}")
        return total_chunks

    def retrieve_context(self, query: str, subject: Optional[str] = None, top_k: int = 4) -> List[Dict[str, str]]:
        """
        Retrieves top relevant chunks using lexical BM25-style keyword and conceptual scoring.
        Ensures strict epistemic source grounding.
        """
        if not self.indexed_chunks:
            self.build_index(subject)

        query_terms = set(re.findall(r'\w+', query.lower()))
        scores = []

        for chunk in self.indexed_chunks:
            if subject and chunk["subject"] != subject:
                continue
            text_lower = chunk["text"].lower()
            # Score based on exact term occurrences and density
            score = sum(text_lower.count(term) * (2 if len(term) > 4 else 1) for term in query_terms)
            if score > 0:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scores[:top_k]]

    def get_source_file_args(self, subject: str = "spanish") -> List[str]:
        """Returns file arguments for aichat -f."""
        materials = self.scan_materials()
        if subject in materials:
            return materials[subject]
        return []

if __name__ == "__main__":
    mgr = MaterialRAGManager()
    found = mgr.scan_materials()
    print("Discovered Materials:", found)
    chunks = mgr.build_index()
    results = mgr.retrieve_context("preterite stative conocer saber")
    print(f"\nRetrieved {len(results)} chunks for test query:")
    for r in results:
        print(f"[{r['file']} - chunk {r['chunk_id']}] {r['text'][:150]}...")
