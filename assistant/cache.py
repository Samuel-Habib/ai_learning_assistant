"""
LLM Query & Response Cache
Provides persistent SQLite-backed caching of model completions.
Guarantees 0-token, 0-latency responses for repeated prompts, diagnostic evaluations,
and curriculum generation.
"""

import hashlib
import sqlite3
import os
from typing import Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "learning_state.db")

class LLMCache:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_cache (
                prompt_hash TEXT PRIMARY KEY,
                model TEXT,
                prompt TEXT,
                response TEXT,
                hits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()

    def _hash_key(self, prompt: str, model: str) -> str:
        content = f"{model.strip().lower()}:{prompt.strip()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, prompt: str, model: str = "") -> Optional[str]:
        """Retrieves cached response if identical prompt was previously executed."""
        h = self._hash_key(prompt, model)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT response FROM llm_cache WHERE prompt_hash = ?", (h,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE llm_cache SET hits = hits + 1, last_accessed = CURRENT_TIMESTAMP WHERE prompt_hash = ?",
                    (h,)
                )
                conn.commit()
                return row["response"]
        return None

    def set(self, prompt: str, response: str, model: str = ""):
        """Stores query and completion in persistent cache."""
        if not response or response.startswith("Error") or len(response.strip()) < 2:
            return
        h = self._hash_key(prompt, model)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO llm_cache (prompt_hash, model, prompt, response, hits)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(prompt_hash) DO UPDATE SET
                    response = excluded.response,
                    last_accessed = CURRENT_TIMESTAMP
                """,
                (h, model, prompt, response)
            )
            conn.commit()

    def get_stats(self) -> dict:
        """Returns total cached entries and hit counts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_entries, SUM(hits) as total_hits FROM llm_cache")
            row = cursor.fetchone()
            return {
                "total_entries": row["total_entries"] or 0,
                "total_hits": row["total_hits"] or 0
            }
