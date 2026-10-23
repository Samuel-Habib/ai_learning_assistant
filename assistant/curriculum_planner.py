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
    from .db import StateManager
    from .json_utils import robust_json_loads
except ImportError:
    from rag_manager import MaterialRAGManager
    from ai_tutor import call_real_ai
    from db import StateManager
    from json_utils import robust_json_loads

try:
    from .ui import style_text, Style
except ImportError:
    try:
        from ui import style_text, Style
    except ImportError:
        # Graceful fallback if ui module isn't available
        def style_text(text, *s): return text
        class Style:
            RESET = BOLD = DIM = ITALIC = UNDERLINE = ""
            GREEN = YELLOW = CYAN = WHITE = RED = BLUE = MAGENTA = ""
            BRIGHT_GREEN = BRIGHT_YELLOW = BRIGHT_BLUE = BRIGHT_CYAN = ""

MD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "md"))

class CurriculumPlanner:
    def __init__(self, subject: str = "spanish", boundary_level: Optional[float] = None, md_dir: str = MD_DIR):
        self.subject = subject.lower().strip()
        self.md_dir = md_dir
        self.db = StateManager(md_dir=self.md_dir)
        subj_record = self.db.get_or_create_subject(self.subject)

        if boundary_level is not None:
            self.boundary_level = float(boundary_level)
            self.db.set_subject_boundary(self.subject, self.boundary_level, subj_record.get('boundary_description', ''))
        else:
            self.boundary_level = float(subj_record.get('frontier_level', 1.0))

        self.rag = MaterialRAGManager()
        self.modules: List[Tuple[str, str]] = self._get_modules()

    def _get_modules(self) -> List[Tuple[str, str]]:
        """Returns 5-6 structured progression modules for the given subject (from SQLite or dynamic AI)."""
        # 1. Check if modules already exist in persistent SQLite database
        saved_modules = self.db.get_curriculum_modules(self.subject)
        if saved_modules and len(saved_modules) >= 3:
            return saved_modules

        # 2. Try to dynamically extract modules from course materials using AI
        chunks = self.rag.retrieve_context("contents syllabus chapters overview introduction", subject=self.subject, top_k=4)
        context = ""
        for c in chunks:
            context += f"{c['text'][:350]}\n"

        if not context:
            materials = self.rag.scan_materials()
            if self.subject in materials:
                for f in materials[self.subject][:2]:
                    text = self.rag.extract_text_from_file(f)
                    if text:
                        context += f"{text[:600]}\n"

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
                data = robust_json_loads(out, default=[])
                if isinstance(data, list) and len(data) >= 3:
                    extracted = [(str(item.get("title", f"Unit {i+1}")), str(item.get("subtitle", ""))) for i, item in enumerate(data[:6])]
                    self.db.save_curriculum_modules(self.subject, extracted, self.boundary_level)
                    return extracted
            except Exception:
                pass

        if self.subject == "spanish":
            default_spanish = [
                ("1. Present Tense Foundations", "Regulars, Pronoun-Drop, Agreement"),
                ("2. Ser vs. Estar & Stem Changers", "Essence vs State, Boot Alternation"),
                ("3. Preterite vs Imperfect Aspect", "Completed vs Ongoing Past"),
                ("4. Stative Verbs in Past Tenses", "Conocer, Saber, Querer, Poder"),
                ("5. The Subjunctive Mood", "Wishes, Doubts, Impersonal Triggers"),
                ("6. Narrative Synthesis & Practice", "Complex Sentences & Composition")
            ]
            self.db.save_curriculum_modules(self.subject, default_spanish, self.boundary_level)
            return default_spanish

        # Standard generic curriculum structure
        default_generic = [
            (f"1. Foundations of {self.subject.capitalize()}", "Core Terminology & Axioms"),
            (f"2. Primary Mechanics of {self.subject.capitalize()}", "Standard Rules & Direct Applications"),
            (f"3. Core Procedural Methods", "Multi-step Reasoning & Problem Solving"),
            (f"4. Nuances & Edge Cases", "Subtle Distinctions & Misconceptions"),
            (f"5. Advanced Theory & Synthesis", "Complex Integration & Systemic Analysis"),
            (f"6. Practical Transfer & Mastery", "Unassisted Problem Solving")
        ]
        self.db.save_curriculum_modules(self.subject, default_generic, self.boundary_level)
        return default_generic

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

    def print_terminal_roadmap(self) -> None:
        """Prints a clean, formatted study plan directly to stdout."""
        active_idx = max(0, min(len(self.modules) - 1, int(self.boundary_level) - 1))

        border = style_text("━" * 65, Style.BRIGHT_CYAN)
        subj_title = self.subject.replace("_", " ").title()
        level_str = style_text(f"Level {self.boundary_level:.2f}", Style.BOLD, Style.BRIGHT_CYAN)

        print(f"\n{border}")
        print(style_text(f"  📊 Study Plan: {subj_title}", Style.BOLD, Style.WHITE) + f"  (Frontier: {level_str})")
        print(f"{border}\n")

        print(style_text("  Topic Progress:", Style.BOLD))
        for i, (title, _) in enumerate(self.modules):
            short_title = title[:30].ljust(32)
            if i < active_idx:
                bar_fill = style_text("████████████████████", Style.GREEN)
                label = style_text("Mastered", Style.GREEN)
                print(f"  {short_title} [{bar_fill}] {label}")
            elif i == active_idx:
                pct = int((self.boundary_level % 1.0) * 20) if self.boundary_level % 1.0 > 0 else 10
                filled = style_text("█" * pct, Style.BRIGHT_CYAN)
                empty = style_text("░" * (20 - pct), Style.DIM)
                label = style_text("Current Focus", Style.BOLD, Style.BRIGHT_CYAN)
                print(f"  {short_title} [{filled}{empty}] {label}")
            elif i == active_idx + 1:
                empty = style_text("░" * 20, Style.DIM)
                label = style_text("Next Up", Style.YELLOW)
                print(f"  {short_title} [{empty}] {label}")
            else:
                empty = style_text("░" * 20, Style.DIM)
                label = style_text("Queued", Style.DIM)
                print(f"  {short_title} [{empty}] {label}")

        print(style_text("\n  Learning Path:", Style.BOLD))
        for i, (title, subtitle) in enumerate(self.modules):
            if i < active_idx:
                icon = style_text("  ✓", Style.GREEN)
                name = style_text(title, Style.DIM)
                tag = style_text("[Mastered]", Style.DIM, Style.GREEN)
            elif i == active_idx:
                icon = style_text("  ►", Style.BOLD, Style.BRIGHT_CYAN)
                name = style_text(title, Style.BOLD, Style.WHITE)
                tag = style_text("👉 [Current Focus]", Style.BOLD, Style.BRIGHT_CYAN)
            elif i == active_idx + 1:
                icon = style_text("  ○", Style.YELLOW)
                name = title
                tag = style_text("⏳ [Next Up]", Style.YELLOW)
            else:
                icon = style_text("  ·", Style.DIM)
                name = style_text(title, Style.DIM)
                tag = style_text("[Queued]", Style.DIM)
            print(f"{icon} {name} {tag}")
            if subtitle:
                print(style_text(f"       └─ {subtitle}", Style.DIM))

        curr_title = self.modules[active_idx][0]
        print(f"\n{border}")
        tip = style_text(f"./learn chat {self.subject}", Style.BOLD, Style.BRIGHT_CYAN)
        print(f"  💡 Next Step: Run {tip} to begin practicing {curr_title}.")
        print(f"{border}\n")

    def update_dashboard(self) -> None:
        """Updates persistent SQLite state and synchronizes Obsidian Markdown vaults."""
        active_idx = max(0, min(len(self.modules) - 1, int(self.boundary_level) - 1)) if self.modules else 0
        desc = self.modules[active_idx][0] if self.modules else "In progress"
        self.db.set_subject_boundary(self.subject, self.boundary_level, desc)
        self.db.save_curriculum_modules(self.subject, self.modules, self.boundary_level)
        self.db.sync_to_obsidian(active_subject=self.subject)
        print(f"✓ Synchronized Obsidian vault in md/ ({self.subject.capitalize()} - Level {self.boundary_level:.2f})")

if __name__ == "__main__":
    import sys
    subj = sys.argv[1] if len(sys.argv) > 1 else "spanish"
    lvl = float(sys.argv[2]) if len(sys.argv) > 2 else 3.65
    planner = CurriculumPlanner(subject=subj, boundary_level=lvl)
    print("Generated Mermaid:\n", planner.generate_mermaid_diagram())
    print("\nGenerated ASCII Progress:\n", planner.generate_progress_gauge())
    planner.update_dashboard()
