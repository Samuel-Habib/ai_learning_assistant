"""
Curriculum Planner & Mermaid Visualization Generator
Generates full end-to-end learning pathways from the student's calibrated boundary
to target mastery for ANY subject, rendering Mermaid sequence and flow diagrams into Obsidian markdown.
"""

import os
import re
import json
from typing import List, Tuple, Dict, Optional

try:
    from .rag_manager import MaterialRAGManager
    from .ai_tutor import call_real_ai
except ImportError:
    from rag_manager import MaterialRAGManager
    from ai_tutor import call_real_ai

MD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "md"))

class CurriculumPlanner:
    def __init__(self, subject: str = "spanish", boundary_level: float = 3.65, md_dir: str = MD_DIR):
        self.subject = subject.lower().strip()
        self.boundary_level = boundary_level
        self.md_dir = md_dir
        self.rag = MaterialRAGManager()
        self.modules: List[Tuple[str, str]] = self._get_modules()

    def _get_modules(self) -> List[Tuple[str, str]]:
        """Returns 5-6 structured progression modules for the given subject."""
        if self.subject == "spanish":
            return [
                ("1. Present Tense Foundations", "Regulars, Pronoun-Drop, Agreement"),
                ("2. Ser vs. Estar & Stem Changers", "Essence vs State, Boot Alternation"),
                ("3. Preterite vs Imperfect Aspect", "Completed vs Ongoing Past"),
                ("4. Stative Verbs in Past Tenses", "Conocer, Saber, Querer, Poder"),
                ("5. The Subjunctive Mood", "Wishes, Doubts, Impersonal Triggers"),
                ("6. Narrative Synthesis & Practice", "Complex Sentences & Composition")
            ]

        # Try to dynamically extract modules from course materials using AI
        chunks = self.rag.retrieve_context("contents syllabus chapters overview introduction", subject=self.subject, top_k=4)
        context = ""
        for c in chunks:
            context += f"{c['text'][:350]}\n"

        if context:
            prompt = f"""For the subject '{self.subject.capitalize()}', extract or create 5 to 6 sequential learning units from foundational to advanced mastery based on:
{context}

Respond strictly in valid JSON format:
[
  {{"title": "1. Short Unit Name", "subtitle": "Core concept summary"}},
  {{"title": "2. Short Unit Name", "subtitle": "Core concept summary"}},
  {{"title": "3. Short Unit Name", "subtitle": "Core concept summary"}},
  {{"title": "4. Short Unit Name", "subtitle": "Core concept summary"}},
  {{"title": "5. Short Unit Name", "subtitle": "Core concept summary"}}
]"""
            try:
                out = call_real_ai(prompt)
                clean_json = out.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                if isinstance(data, list) and len(data) >= 3:
                    return [(str(item.get("title", f"Unit {i+1}")), str(item.get("subtitle", ""))) for i, item in enumerate(data[:6])]
            except Exception:
                pass

        # Standard generic curriculum structure
        return [
            (f"1. Foundations of {self.subject.capitalize()}", "Core Terminology & Axioms"),
            (f"2. Primary Mechanics of {self.subject.capitalize()}", "Standard Rules & Direct Applications"),
            (f"3. Core Procedural Methods", "Multi-step Reasoning & Problem Solving"),
            (f"4. Nuances & Edge Cases", "Subtle Distinctions & Misconceptions"),
            (f"5. Advanced Theory & Synthesis", "Complex Integration & Systemic Analysis"),
            (f"6. Practical Transfer & Mastery", "Unassisted Problem Solving")
        ]

    def generate_mermaid_diagram(self) -> str:
        """Generates a clean Mermaid roadmap diagram reflecting current focus."""
        lines = [
            "```mermaid",
            "flowchart TD",
            "    classDef mastered fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff;",
            "    classDef current fill:#f57c00,stroke:#e65100,stroke-width:3px,color:#fff;",
            "    classDef upcoming fill:#37474f,stroke:#263238,stroke-width:1px,color:#cfd8dc;",
            ""
        ]

        active_idx = max(0, min(len(self.modules) - 1, int(self.boundary_level) - 1))

        node_ids = []
        for i, (title, subtitle) in enumerate(self.modules):
            nid = f"M{i+1}"
            node_ids.append(nid)
            clean_title = title.replace('"', "'")
            clean_sub = subtitle.replace('"', "'")

            if i < active_idx:
                style_class = ":::mastered"
            elif i == active_idx:
                style_class = ":::current"
            else:
                style_class = ":::upcoming"

            lines.append(f'    {nid}["{clean_title}<br/><i>{clean_sub}</i>"]{style_class}')

        lines.append("")
        for i in range(len(node_ids) - 1):
            if i == active_idx - 1 or (active_idx == 0 and i == 0):
                lines.append(f"    {node_ids[i]} ==>|Current Frontier| {node_ids[i+1]}")
            else:
                lines.append(f"    {node_ids[i]} --> {node_ids[i+1]}")

        lines.append("```")
        return "\n".join(lines)

    def generate_progress_gauge(self) -> str:
        """Renders a clean topic progress tracker."""
        active_idx = max(0, min(len(self.modules) - 1, int(self.boundary_level) - 1))
        out = ["```"]
        for i, (title, _) in enumerate(self.modules):
            short_title = title[:30].ljust(32)
            if i < active_idx:
                bar = "[████████████████████] Mastered"
            elif i == active_idx:
                pct = int((self.boundary_level % 1.0) * 20) if self.boundary_level % 1.0 > 0 else 10
                bar = f"[{'█' * pct}{'░' * (20 - pct)}] Current Focus"
            elif i == active_idx + 1:
                bar = "[░░░░░░░░░░░░░░░░░░░░] Next Up"
            else:
                bar = "[░░░░░░░░░░░░░░░░░░░░] Queued"
            out.append(f"{short_title} {bar}")
        out.append("```")
        return "\n".join(out)

    def update_dashboard(self) -> None:
        """Updates the master dashboard in 00_INDEX_DASHBOARD.md."""
        dashboard_file = os.path.join(self.md_dir, "00_INDEX_DASHBOARD.md")
        roadmap_file = os.path.join(self.md_dir, "01_CURRICULUM_ROADMAP.md")
        os.makedirs(self.md_dir, exist_ok=True)

        gauge = self.generate_progress_gauge()
        mermaid = self.generate_mermaid_diagram()

        dashboard_content = f"""# 🧭 {self.subject.capitalize()}: Study Hub & Dashboard

Welcome to your study dashboard. This space organizes your syllabus, visual concept maps, and interactive practice exercises.

---

## 📊 Topic Progress
- **Subject:** {self.subject.capitalize()}
- **Calibrated Frontier:** Level {self.boundary_level:.2f}

{gauge}

---

## 🗺️ Study Roadmap

{mermaid}

---

## 🗂️ Study Units
- [[01_CURRICULUM_ROADMAP|Full Study Roadmap & Timeline Visuals]]
- [[02_BOUNDARY_CALIBRATION|Placement Summary & Assessment Notes]]
- [[03_STUDENT_OBSIDIAN_SCRATCHPAD|My Study Notes & Questions]] 📝 *(Auto-synced with terminal sessions)*
"""
        try:
            with open(dashboard_file, "w", encoding="utf-8") as f:
                f.write(dashboard_content)
            print(f"✓ Updated Obsidian dashboard at {dashboard_file} ({self.subject.capitalize()} - Level {self.boundary_level:.2f})")
        except Exception as e:
            print(f"Warning: Failed to update dashboard: {e}")

        # Update Roadmap
        roadmap_content = f"""# 🗺️ {self.subject.capitalize()} Study Roadmap

A structured learning progression from foundational concepts to advanced independent mastery.

---

## 🧭 Topic Sequence

{mermaid}

---

## 📊 Progress Overview

{gauge}
"""
        try:
            with open(roadmap_file, "w", encoding="utf-8") as f:
                f.write(roadmap_content)
        except Exception:
            pass

if __name__ == "__main__":
    import sys
    subj = sys.argv[1] if len(sys.argv) > 1 else "spanish"
    lvl = float(sys.argv[2]) if len(sys.argv) > 2 else 3.65
    planner = CurriculumPlanner(subject=subj, boundary_level=lvl)
    print("Generated Mermaid:\n", planner.generate_mermaid_diagram())
    print("\nGenerated ASCII Progress:\n", planner.generate_progress_gauge())
    planner.update_dashboard()
