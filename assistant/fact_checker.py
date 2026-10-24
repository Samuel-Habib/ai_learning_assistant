"""
Asynchronous Background Fact-Checker
Validates tutor technical statements in the background in between dialogue turns.
Zero terminal latency: runs asynchronously on worker threads, cross-checks claims
against local course materials and domain standards, and records verified errata
into Obsidian lesson notes.
"""

import threading
import os
import re
from typing import Optional, Dict

try:
    from .rag_manager import MaterialRAGManager
    from .ai_tutor import call_real_ai
    from .db import StateManager
    from .lesson_manager import LessonManager, clean_slug
except ImportError:
    from rag_manager import MaterialRAGManager
    from ai_tutor import call_real_ai
    from db import StateManager
    from lesson_manager import LessonManager, clean_slug

class BackgroundFactChecker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BackgroundFactChecker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.rag = MaterialRAGManager()
        self.db = StateManager()
        self.lesson_mgr = LessonManager()
        self.pending_notes: Dict[str, str] = {}
        self.active_threads = []
        self._initialized = True

    def verify_async(self, subject: str, unit_index: int, unit_title: str, user_msg: str, tutor_msg: str):
        """Spawns an asynchronous background thread to fact-check the tutor's response."""
        thread = threading.Thread(
            target=self._run_verification,
            args=(subject, unit_index, unit_title, user_msg, tutor_msg),
            daemon=True
        )
        self.active_threads.append(thread)
        thread.start()

    def _run_verification(self, subject: str, unit_index: int, unit_title: str, user_msg: str, tutor_msg: str):
        """Worker thread logic checking technical claims against course materials."""
        clean_subj = subject.strip().lower().replace(" ", "_")

        # 1. Retrieve authoritative excerpts from local materials
        chunks = self.rag.retrieve_context(tutor_msg[:250], subject=clean_subj, top_k=2)
        doc_context = ""
        if chunks:
            for c in chunks:
                doc_context += f"[{c['file']}]: {c['text'][:400]}\n"

        prompt = (
            f"You are an asynchronous technical accuracy auditor verifying technical instruction for {clean_subj}.\n\n"
            f"Unit: {unit_title}\n"
            f"Student Message: {user_msg}\n"
            f"Tutor Response: {tutor_msg}\n\n"
            f"Course Material Grounding:\n{doc_context if doc_context else 'Verify against official technical specifications.'}\n\n"
            f"Task:\n"
            f"1. Check if the tutor's explanation is factually accurate and consistent with official technical standards.\n"
            f"2. If accurate with no misleading claims, respond strictly with 'VERIFIED'.\n"
            f"3. If there is a subtle inaccuracy, register mismatch, or essential caveat that should be clarified, respond strictly in this format:\n"
            f"CORRECTION: <1-2 sentences stating the precise technical clarification>\n"
            f"Do not lecture. Respond strictly with 'VERIFIED' or 'CORRECTION: ...'"
        )

        try:
            verdict = call_real_ai(prompt, timeout=25).strip()

            if verdict.startswith("CORRECTION:"):
                correction_text = verdict[len("CORRECTION:"):].strip()
                # Store pending note to present seamlessly on the next turn
                self.pending_notes[clean_subj] = correction_text

                # Record in SQLite state
                self._record_to_db(clean_subj, tutor_msg[:100], "CORRECTION", correction_text)

                # Append verified errata to the Obsidian lesson note
                self._append_factcheck_to_obsidian(clean_subj, unit_index, unit_title, correction_text)
            elif "VERIFIED" in verdict:
                self._record_to_db(clean_subj, tutor_msg[:100], "VERIFIED", "Claims verified against spec.")
        except Exception:
            pass

    def get_and_clear_pending_note(self, subject: str) -> Optional[str]:
        """Returns any pending background fact-check correction for the subject."""
        clean_subj = subject.strip().lower().replace(" ", "_")
        return self.pending_notes.pop(clean_subj, None)

    def _record_to_db(self, subject: str, claim: str, status: str, notes: str):
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS fact_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    claim_summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                cursor.execute(
                    "INSERT INTO fact_checks (subject, claim_summary, status, notes) VALUES (?, ?, ?, ?)",
                    (subject, claim, status, notes)
                )
                conn.commit()
        except Exception:
            pass

    def _append_factcheck_to_obsidian(self, subject: str, unit_index: int, title: str, note: str):
        path = self.lesson_mgr.get_lesson_path(subject, unit_index, title)
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            section_header = "## 🔍 Verified Technical Notes & Fact-Checks"
            entry = f"\n- **Auto-Verified Note:** {note}\n"

            if section_header in content:
                parts = content.split("## 🗂️ Navigation", 1)
                updated = parts[0] + entry + "\n---\n\n## 🗂️ Navigation" + (parts[1] if len(parts) > 1 else "")
            else:
                parts = content.split("## 🗂️ Navigation", 1)
                updated = parts[0] + f"\n---\n\n{section_header}\n" + entry + "\n---\n\n## 🗂️ Navigation" + (parts[1] if len(parts) > 1 else "")

            with open(path, "w", encoding="utf-8") as f:
                f.write(updated)
        except Exception:
            pass
