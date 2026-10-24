"""
Lesson Manager for Obsidian
Generates, links, and synchronizes rich, structured textbook-style lesson markdown
notes in md/subjects/<subject>/lessons/ directly accessible in Obsidian.
"""

import os
import re
from typing import List, Tuple, Optional, Dict, Any

try:
    from .rag_manager import MaterialRAGManager
    from .ai_tutor import call_real_ai
except ImportError:
    from rag_manager import MaterialRAGManager
    from ai_tutor import call_real_ai

MD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "md"))

def clean_slug(title: str, unit_index: int) -> str:
    """Converts a unit title into a clean filename slug: e.g. 01_usb_fundamentals.md"""
    # Strip leading numbers like '1. ' or 'Unit 1: '
    cleaned = re.sub(r'^(?:unit\s*)?\d+[\.\:\s\-]*', '', title, flags=re.IGNORECASE).strip()
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', cleaned.lower()).strip('_')
    if not slug:
        slug = f"unit_{unit_index}"
    return f"{unit_index:02d}_{slug}.md"

class LessonManager:
    def __init__(self, md_dir: str = MD_DIR):
        self.md_dir = md_dir
        self.rag = MaterialRAGManager()

    def get_lessons_dir(self, subject: str) -> str:
        clean_subj = subject.strip().lower().replace(" ", "_")
        d = os.path.join(self.md_dir, "subjects", clean_subj, "lessons")
        os.makedirs(d, exist_ok=True)
        return d

    def get_lesson_path(self, subject: str, unit_index: int, title: str) -> str:
        lessons_dir = self.get_lessons_dir(subject)
        fname = clean_slug(title, unit_index)
        return os.path.join(lessons_dir, fname)

    def ensure_all_lessons(self, subject: str, modules: List[Tuple[str, str]], boundary_level: float = 1.0, generate_ai: bool = False):
        """Ensures that every module unit has an Obsidian lesson note."""
        clean_subj = subject.strip().lower().replace(" ", "_")
        active_idx = max(0, min(len(modules) - 1, int(boundary_level) - 1)) if modules else 0

        for idx, (title, subtitle) in enumerate(modules, 1):
            path = self.get_lesson_path(clean_subj, idx, title)
            if not os.path.exists(path) or os.path.getsize(path) < 100:
                if generate_ai and idx - 1 == active_idx:
                    content = self.generate_lesson_content(clean_subj, idx, title, subtitle, boundary_level)
                else:
                    content = self._build_fallback_lesson(clean_subj, clean_subj.replace("_", " ").title(), idx, title, subtitle)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

    def generate_lesson_content(self, subject: str, unit_index: int, title: str, subtitle: str, boundary_level: float) -> str:
        """Generates a rich, publication-quality Obsidian lesson markdown file."""
        clean_subj = subject.strip().lower().replace(" ", "_")
        display_subj = clean_subj.replace("_", " ").title()

        # Retrieve relevant course materials if available
        query = f"{title} {subtitle} fundamentals principles overview architecture"
        chunks = self.rag.retrieve_context(query, subject=clean_subj, top_k=4)
        context = ""
        if chunks:
            for c in chunks:
                context += f"--- Excerpt from {c['file']} ---\n{c['text'][:600]}\n"

        prompt = (
            f"Generate a comprehensive, engaging, and clear study lesson note in Markdown for an academic curriculum.\n\n"
            f"Subject: {display_subj}\n"
            f"Unit {unit_index}: {title}\n"
            f"Core Concepts: {subtitle}\n"
            f"Calibrated Student Level: {boundary_level:.2f}\n\n"
            f"Course Material Excerpts:\n{context if context else 'Use authoritative domain knowledge.'}\n\n"
            f"Required Lesson Format (Must be formatted cleanly for Obsidian):\n"
            f"# 📖 Unit {unit_index}: {title}\n\n"
            f"> [!NOTE] Focus: {subtitle}\n"
            f"> **Subject:** {display_subj} · **Unit:** {unit_index}\n\n"
            f"Include the following detailed sections:\n"
            f"1. ## 🧭 1. Core Foundations & Intuition\n"
            f"   - Explain the foundational concepts and mental models in depth.\n"
            f"   - Contrast with familiar baselines or everyday real-world examples.\n"
            f"   - Explain WHY things work the way they do (cause and effect).\n"
            f"2. ## 🔍 2. Structure, Mechanisms & Visuals\n"
            f"   - Include clear text/ASCII diagrams, flowcharts, or structural breakdowns.\n"
            f"   - Walk through step-by-step processes or timelines.\n"
            f"3. ## 📊 3. Key Classifications & Concepts\n"
            f"   - Include Markdown comparison tables classifying categories, types, or principles.\n"
            f"4. ## ⚖️ 4. Critical Trade-Offs & Cause-and-Effect\n"
            f"   - Analyze core trade-offs, advantages, limitations, or differing perspectives.\n"
            f"5. ## 🧠 5. Self-Check & Conceptual Mastery\n"
            f"   - Provide 2 thought-provoking scenario questions with collapsible Obsidian callouts for solutions:\n"
            f"     > [!QUESTION] Scenario Question\n"
            f"     > ...\n"
            f"     >\n"
            f"     > > [!TIP]- Reveal Solution\n"
            f"     > > ...\n\n"
            f"Write substantive, complete explanations with genuine clarity and depth (no placeholders or 'TODO's)."
        )

        try:
            lesson_body = call_real_ai(prompt)
            if lesson_body and len(lesson_body.strip()) > 300:
                # Append Obsidian footer navigation
                footer = (
                    f"\n---\n\n"
                    f"## 🗂️ Navigation\n"
                    f"- [[../00_DASHBOARD|← Return to {display_subj} Hub]]\n"
                    f"- [[../01_ROADMAP|View Full {display_subj} Roadmap]]\n"
                    f"- [[../../../00_INDEX_DASHBOARD|Master Study Hub]]\n"
                )
                return lesson_body.strip() + footer
        except Exception:
            pass

        # Robust fallback lesson template if AI offline
        return self._build_fallback_lesson(clean_subj, display_subj, unit_index, title, subtitle)

    def append_dialogue_to_lesson(self, subject: str, unit_index: int, title: str, explanation: str):
        """Appends rich explanations from an interactive study session into the lesson note."""
        path = self.get_lesson_path(subject, unit_index, title)
        if not os.path.exists(path):
            self.ensure_all_lessons(subject, [(title, "")], boundary_level=1.0)

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            dialogue_header = "## 💬 Interactive Classroom Deep Dives"
            new_entry = f"\n\n### 💡 Key Concept Breakdown\n\n{explanation.strip()}\n"

            if dialogue_header in content:
                # Insert before the navigation footer
                parts = content.split("## 🗂️ Navigation", 1)
                updated = parts[0] + new_entry + "\n---\n\n## 🗂️ Navigation" + (parts[1] if len(parts) > 1 else "")
            else:
                parts = content.split("## 🗂️ Navigation", 1)
                updated = parts[0] + f"\n---\n\n{dialogue_header}\n" + new_entry + "\n---\n\n## 🗂️ Navigation" + (parts[1] if len(parts) > 1 else "")

            with open(path, "w", encoding="utf-8") as f:
                f.write(updated)
        except Exception as e:
            print(f"Warning: Failed to update lesson note: {e}")

    def _build_fallback_lesson(self, clean_subj: str, display_subj: str, unit_index: int, title: str, subtitle: str) -> str:
        """Constructs an initial structured lesson note template."""
        return f"""# 📖 Unit {unit_index}: {title}

> [!NOTE] Focus: {subtitle}
> **Subject:** {display_subj} · **Unit:** {unit_index}

---

## 🧭 1. Architectural & Conceptual Foundations
Welcome to **Unit {unit_index}** for **{display_subj}**. In this module, we focus on **{subtitle}**.

### Core Principles
- Foundations and terminology establish the governing rules of the domain.
- Understanding the physical and procedural constraints ensures reliable design and analysis.

---

## 🔌 2. Mechanisms & Systems Overview
```
+-------------------------------------------------------------+
|                 Unit {unit_index}: System Overview                    |
|  Topic: {title[:45]} |
+-------------------------------------------------------------+
```

---

## ⚖️ 3. Key Design Trade-Offs & Decisions
- **Correctness vs. Performance:** Evaluating failure modes and reliability.
- **Latency vs. Throughput:** Balancing bandwidth allocation and processing overhead.

---

## 💬 Interactive Classroom Deep Dives
*(Key explanations and diagrams from your terminal study sessions are automatically recorded here).*

---

## 🗂️ Navigation
- [[../00_DASHBOARD|← Return to {display_subj} Hub]]
- [[../01_ROADMAP|View Full {display_subj} Roadmap]]
- [[../../../00_INDEX_DASHBOARD|Master Study Hub]]
"""
