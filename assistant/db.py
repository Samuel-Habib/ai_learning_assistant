"""
State Database & Obsidian Markdown Synchronizer
Provides persistent SQLite storage for multi-subject progress, diagnostic history,
curriculum roadmaps, and chat transcripts, paired with automatic synchronization
to user-facing Obsidian Markdown vaults in learn/md/.
"""

import os
import re
import sqlite3
import datetime
from typing import Dict, List, Optional, Tuple, Any

def clean_slug(title: str, unit_index: int) -> str:
    """Converts a unit title into a clean filename slug: e.g. 01_usb_fundamentals.md"""
    cleaned = re.sub(r'^(?:unit\s*)?\d+[\.\:\s\-]*', '', title, flags=re.IGNORECASE).strip()
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', cleaned.lower()).strip('_')
    if not slug:
        slug = f"unit_{unit_index}"
    return f"{unit_index:02d}_{slug}.md"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
MD_DIR = os.path.join(BASE_DIR, "md")
DB_PATH = os.path.join(DATA_DIR, "learning_state.db")

class StateManager:
    """Manages the SQLite database and syncs state to Obsidian Markdown files."""

    def __init__(self, db_path: str = DB_PATH, md_dir: str = MD_DIR):
        self.db_path = db_path
        self.md_dir = md_dir
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.md_dir, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes relational tables for subjects, diagnostics, roadmaps, and chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                name TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                frontier_level REAL DEFAULT 1.0,
                boundary_description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnostic_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                level REAL NOT NULL,
                topic TEXT NOT NULL,
                question TEXT NOT NULL,
                student_response TEXT NOT NULL,
                passed INTEGER NOT NULL,
                analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject) REFERENCES subjects (name)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS curriculum_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                unit_index INTEGER NOT NULL,
                title TEXT NOT NULL,
                subtitle TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (subject, unit_index),
                FOREIGN KEY (subject) REFERENCES subjects (name)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject) REFERENCES subjects (name)
            )
            """)
            conn.commit()

    # --- Subject Management ---

    def get_or_create_subject(self, name: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves an existing subject or creates a new persistent record."""
        clean_name = name.strip().lower().replace(" ", "_")
        clean_display = display_name or clean_name.replace("_", " ").title()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subjects WHERE name = ?", (clean_name,))
            row = cursor.fetchone()
            if row:
                return dict(row)

            cursor.execute(
                "INSERT INTO subjects (name, display_name, frontier_level, boundary_description) VALUES (?, ?, 1.0, '')",
                (clean_name, clean_display)
            )
            conn.commit()
            cursor.execute("SELECT * FROM subjects WHERE name = ?", (clean_name,))
            return dict(cursor.fetchone())

    def get_subject(self, name: str) -> Optional[Dict[str, Any]]:
        clean_name = name.strip().lower().replace(" ", "_")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subjects WHERE name = ?", (clean_name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_subjects(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subjects ORDER BY updated_at DESC")
            return [dict(r) for r in cursor.fetchall()]

    def set_subject_boundary(self, name: str, level: float, description: str):
        """Updates the calibrated knowledge frontier for a subject in SQLite and syncs Markdown."""
        clean_name = name.strip().lower().replace(" ", "_")
        self.get_or_create_subject(clean_name)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE subjects 
                SET frontier_level = ?, boundary_description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
                """,
                (float(level), description, clean_name)
            )
            conn.commit()

    # --- Diagnostic History ---

    def record_diagnostic_result(self, subject: str, level: float, topic: str, 
                                 question: str, response: str, passed: bool, analysis: str):
        """Records an individual diagnostic question result."""
        clean_name = subject.strip().lower().replace(" ", "_")
        self.get_or_create_subject(clean_name)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO diagnostic_history 
                (subject, level, topic, question, student_response, passed, analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (clean_name, float(level), topic, question, response, 1 if passed else 0, analysis)
            )
            conn.commit()

    def get_diagnostic_history(self, subject: str) -> List[Dict[str, Any]]:
        clean_name = subject.strip().lower().replace(" ", "_")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM diagnostic_history WHERE subject = ? ORDER BY created_at ASC",
                (clean_name,)
            )
            return [dict(r) for r in cursor.fetchall()]

    # --- Curriculum & Roadmaps ---

    def save_curriculum_modules(self, subject: str, modules: List[Tuple[str, str]], boundary_level: float):
        """Persists curriculum modules with updated mastery statuses to SQLite."""
        clean_name = subject.strip().lower().replace(" ", "_")
        self.get_or_create_subject(clean_name)
        active_idx = max(0, min(len(modules) - 1, int(boundary_level) - 1))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for idx, (title, subtitle) in enumerate(modules):
                if idx < active_idx:
                    status = "mastered"
                elif idx == active_idx:
                    status = "current"
                elif idx == active_idx + 1:
                    status = "next"
                else:
                    status = "queued"

                cursor.execute(
                    """
                    INSERT INTO curriculum_modules (subject, unit_index, title, subtitle, status)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(subject, unit_index) DO UPDATE SET
                        title = excluded.title,
                        subtitle = excluded.subtitle,
                        status = excluded.status
                    """,
                    (clean_name, idx + 1, title, subtitle, status)
                )
            conn.commit()

    def get_curriculum_modules(self, subject: str) -> List[Tuple[str, str]]:
        clean_name = subject.strip().lower().replace(" ", "_")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title, subtitle FROM curriculum_modules WHERE subject = ? ORDER BY unit_index ASC",
                (clean_name,)
            )
            rows = cursor.fetchall()
            return [(r["title"], r["subtitle"]) for r in rows]

    # --- Chat History Management ---

    def append_chat_message(self, subject: str, role: str, content: str):
        """Logs student and tutor dialogue turns to SQLite."""
        clean_name = subject.strip().lower().replace(" ", "_")
        self.get_or_create_subject(clean_name)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (subject, role, content) VALUES (?, ?, ?)",
                (clean_name, role, content)
            )
            cursor.execute(
                "UPDATE subjects SET updated_at = CURRENT_TIMESTAMP WHERE name = ?",
                (clean_name,)
            )
            conn.commit()

    def get_chat_history(self, subject: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieves recent dialogue context for the subject."""
        clean_name = subject.strip().lower().replace(" ", "_")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, content FROM chat_history 
                WHERE subject = ? ORDER BY id DESC LIMIT ?
                """,
                (clean_name, limit)
            )
            rows = cursor.fetchall()
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    # --- Obsidian Markdown Vault Generator ---

    def sync_to_obsidian(self, active_subject: Optional[str] = None):
        """
        Generates and updates user-facing Obsidian Markdown files from SQLite state:
        - md/00_INDEX_DASHBOARD.md: Master hub showing all subjects and overall progress.
        - md/subjects/<subject>/00_DASHBOARD.md: Dedicated subject study hub.
        - md/subjects/<subject>/01_ROADMAP.md: Interactive visual roadmap with Mermaid chart.
        - md/subjects/<subject>/02_DIAGNOSTICS.md: Historical diagnostic log.
        """
        subjects = self.list_subjects()
        if not subjects and active_subject:
            self.get_or_create_subject(active_subject)
            subjects = self.list_subjects()

        # 1. Update Per-Subject Vault Folders
        for subj in subjects:
            s_name = subj["name"]
            s_display = subj["display_name"]
            s_level = subj["frontier_level"]
            s_desc = subj["boundary_description"] or "In progress"

            subj_dir = os.path.join(self.md_dir, "subjects", s_name)
            os.makedirs(subj_dir, exist_ok=True)

            modules = self.get_curriculum_modules(s_name)
            diag_history = self.get_diagnostic_history(s_name)

            # Generate Mermaid diagram for subject
            mermaid_chart = self._generate_mermaid(modules, s_level)
            progress_gauge = self._generate_ascii_gauge(modules, s_level)

            # Ensure lesson notes directory and files exist (only for active subject to stay fast)
            try:
                from .lesson_manager import LessonManager
            except ImportError:
                from lesson_manager import LessonManager
            lesson_mgr = LessonManager(md_dir=self.md_dir)
            if modules and (not active_subject or s_name == active_subject):
                lesson_mgr.ensure_all_lessons(s_name, modules, s_level)

            # Generate links to individual lesson notes
            lesson_nav_links = []
            for i, (m_title, m_sub) in enumerate(modules):
                slug = clean_slug(m_title, i + 1)
                slug_stem = slug[:-3] if slug.endswith(".md") else slug
                active_idx = max(0, min(len(modules) - 1, int(s_level) - 1)) if modules else 0
                tag = "👉 **(Current Focus)**" if i == active_idx else ("*(Mastered)*" if i < active_idx else "*(Upcoming)*")
                lesson_nav_links.append(f"- [[lessons/{slug_stem}|📖 Unit {i+1}: {m_title}]] {tag}\n  - *Concepts:* {m_sub}")

            lesson_nav_str = "\n".join(lesson_nav_links) if lesson_nav_links else "- No lessons generated yet."

            # Subject Dashboard
            subj_dashboard_content = f"""# 🧭 {s_display}: Study Hub

Welcome to your study space for **{s_display}**. All roadmaps, diagnostic records, interactive lesson notes, and study guides are preserved here.

---

## 📊 Topic Progress
- **Calibrated Frontier:** Level {s_level:.2f} — *{s_desc}*

{progress_gauge}

---

## 📖 Complete Study Lessons
Read the full textbook-style explanations, circuits, and conceptual notes for each unit:

{lesson_nav_str}

---

## 🗺️ Visual Roadmap

{mermaid_chart}

---

## 🗂️ Study Navigation
- [[01_ROADMAP|Full Interactive Roadmap & Checklists]]
- [[02_DIAGNOSTICS|Diagnostic Placement & Assessment Log]]
- [[../../00_INDEX_DASHBOARD|← Return to Master Study Hub]]
"""
            with open(os.path.join(subj_dir, "00_DASHBOARD.md"), "w", encoding="utf-8") as f:
                f.write(subj_dashboard_content)

            # Subject Roadmap & Checklists (with direct links to lessons)
            checklist_items = []
            for i, (m_title, m_sub) in enumerate(modules):
                active_idx = max(0, min(len(modules) - 1, int(s_level) - 1)) if modules else 0
                checked = "[x]" if i < active_idx else "[ ]"
                status_note = "*(Mastered)*" if i < active_idx else ("👉 **(Current Focus)**" if i == active_idx else "*(Upcoming)*")
                slug = clean_slug(m_title, i + 1)
                slug_stem = slug[:-3] if slug.endswith(".md") else slug
                checklist_items.append(f"- {checked} [[lessons/{slug_stem}|**{m_title}**]] {status_note}\n  - *Concepts:* {m_sub}")

            checklist_str = "\n".join(checklist_items) if checklist_items else "- No modules generated yet."

            subj_roadmap_content = f"""# 🗺️ {s_display}: Study Roadmap & Learning Units

A structured progression from foundational axioms to independent problem solving.

---

## 🧭 Topic Sequence Chart

{mermaid_chart}

---

## ✅ Learning Unit Checklists

{checklist_str}

---

- [[00_DASHBOARD|← Back to {s_display} Hub]] | [[../../00_INDEX_DASHBOARD|Master Hub]]
"""
            with open(os.path.join(subj_dir, "01_ROADMAP.md"), "w", encoding="utf-8") as f:
                f.write(subj_roadmap_content)

            # Subject Diagnostics Log
            diag_rows = []
            for r in diag_history:
                icon = "✓ Correct" if r["passed"] else "⚠️ Needs Practice"
                diag_rows.append(
                    f"### Level {r['level']:.1f}: {r['topic']}\n"
                    f"- **Date:** {r['created_at'][:19]}\n"
                    f"- **Question:** {r['question']}\n"
                    f"- **Your Answer:** {r['student_response']}\n"
                    f"- **Tutor Evaluation:** {icon} — {r['analysis']}\n"
                )
            diag_str = "\n".join(diag_rows) if diag_rows else "*(No diagnostic probes completed yet. Run `./learn check` to assess your level.)*\n"

            subj_diag_content = f"""# 📋 {s_display}: Diagnostic & Placement History

This persistent record tracks every question assessed by your tutor and your conceptual progress over time.

- **Current Knowledge Frontier:** Level {s_level:.2f} ({s_desc})

---

{diag_str}

---

- [[00_DASHBOARD|← Back to {s_display} Hub]] | [[../../00_INDEX_DASHBOARD|Master Hub]]
"""
            with open(os.path.join(subj_dir, "02_DIAGNOSTICS.md"), "w", encoding="utf-8") as f:
                f.write(subj_diag_content)

        # 2. Update Master Hub (md/00_INDEX_DASHBOARD.md) listing ALL enrolled subjects
        master_rows = []
        for s in subjects:
            s_name = s["name"]
            s_display = s["display_name"]
            s_lvl = s["frontier_level"]
            s_desc = s["boundary_description"] or "Active"
            pct = int((s_lvl / 5.0) * 100)
            bar_len = int((pct / 100) * 15)
            progress_bar = f"[{'█' * bar_len}{'░' * (15 - bar_len)}] {pct}% (Level {s_lvl:.2f})"
            s_modules = self.get_curriculum_modules(s_name)
            active_m_idx = max(0, min(len(s_modules) - 1, int(s_lvl) - 1)) if s_modules else 0
            if s_modules:
                curr_slug = clean_slug(s_modules[active_m_idx][0], active_m_idx + 1)
                curr_slug_stem = curr_slug[:-3] if curr_slug.endswith(".md") else curr_slug
                lesson_link_str = f" · [[subjects/{s_name}/lessons/{curr_slug_stem}|📖 Current Lesson]]"
            else:
                lesson_link_str = ""

            master_rows.append(
                f"### 📚 [[subjects/{s_name}/00_DASHBOARD|{s_display}]]\n"
                f"- **Progress:** `{progress_bar}`\n"
                f"- **Current Focus:** {s_desc}\n"
                f"- **Direct Links:** [[subjects/{s_name}/01_ROADMAP|Roadmap]] · [[subjects/{s_name}/02_DIAGNOSTICS|Placement History]]{lesson_link_str}\n"
            )

        master_content = f"""# 🧭 Master Study Hub: Adaptive Learning Assistant

Welcome to your central learning vault. Track your multi-subject progress, view generated roadmaps, and review synced study notes.

---

## 📊 Enrolled Subjects ({len(subjects)})

{"".join(master_rows) if master_rows else "*(No subjects enrolled yet. Run `./learn` to choose or add a subject!)*"}

---

## 📝 Personal Notes
- [[03_STUDENT_OBSIDIAN_SCRATCHPAD|My Study Notes & Questions]] 📝 *(Auto-synced with terminal sessions)*

---

*State backed by persistent SQLite storage at `data/learning_state.db` and rendered for Obsidian.*
"""
        with open(os.path.join(self.md_dir, "00_INDEX_DASHBOARD.md"), "w", encoding="utf-8") as f:
            f.write(master_content)

        # 3. If an active subject is specified, mirror its roadmap/calibration to root for compatibility
        if active_subject:
            target = active_subject.strip().lower().replace(" ", "_")
            source_dir = os.path.join(self.md_dir, "subjects", target)
            if os.path.exists(source_dir):
                for fname, root_dest in [
                    ("01_ROADMAP.md", "01_CURRICULUM_ROADMAP.md"),
                    ("02_DIAGNOSTICS.md", "02_BOUNDARY_CALIBRATION.md")
                ]:
                    src = os.path.join(source_dir, fname)
                    dst = os.path.join(self.md_dir, root_dest)
                    if os.path.exists(src):
                        with open(src, "r", encoding="utf-8") as sf, open(dst, "w", encoding="utf-8") as df:
                            df.write(sf.read())

    def _generate_mermaid(self, modules: List[Tuple[str, str]], level: float) -> str:
        """Generates a clean Mermaid diagram with node classes."""
        if not modules:
            return "```mermaid\nflowchart TD\n    M1[\"1. Foundations\"]:::current\n```"

        lines = [
            "```mermaid",
            "flowchart TD",
            "    classDef mastered fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff;",
            "    classDef current fill:#f57c00,stroke:#e65100,stroke-width:3px,color:#fff;",
            "    classDef upcoming fill:#37474f,stroke:#263238,stroke-width:1px,color:#cfd8dc;",
            ""
        ]
        active_idx = max(0, min(len(modules) - 1, int(level) - 1))
        node_ids = []

        for i, (title, subtitle) in enumerate(modules):
            nid = f"M{i+1}"
            node_ids.append(nid)
            clean_title = title.replace('"', "'")
            clean_sub = subtitle.replace('"', "'")
            if i < active_idx:
                cls = ":::mastered"
            elif i == active_idx:
                cls = ":::current"
            else:
                cls = ":::upcoming"
            lines.append(f'    {nid}["{clean_title}<br/><i>{clean_sub}</i>"]{cls}')

        lines.append("")
        for i in range(len(node_ids) - 1):
            if i == active_idx - 1 or (active_idx == 0 and i == 0):
                lines.append(f"    {node_ids[i]} ==>|Current Frontier| {node_ids[i+1]}")
            else:
                lines.append(f"    {node_ids[i]} --> {node_ids[i+1]}")
        lines.append("```")
        return "\n".join(lines)

    def _generate_ascii_gauge(self, modules: List[Tuple[str, str]], level: float) -> str:
        """Generates an ASCII progress gauge for terminal and markdown display."""
        if not modules:
            return "```\n[░░░░░░░░░░░░░░░░░░░░] Ready to begin\n```"

        active_idx = max(0, min(len(modules) - 1, int(level) - 1))
        out = ["```"]
        for i, (title, _) in enumerate(modules):
            short_title = title[:28].ljust(30)
            if i < active_idx:
                bar = "[████████████████████] Mastered"
            elif i == active_idx:
                pct = int((level % 1.0) * 20) if level % 1.0 > 0 else 10
                bar = f"[{'█' * pct}{'░' * (20 - pct)}] Current Focus"
            elif i == active_idx + 1:
                bar = "[░░░░░░░░░░░░░░░░░░░░] Next Up"
            else:
                bar = "[░░░░░░░░░░░░░░░░░░░░] Queued"
            out.append(f"{short_title} {bar}")
        out.append("```")
        return "\n".join(out)
