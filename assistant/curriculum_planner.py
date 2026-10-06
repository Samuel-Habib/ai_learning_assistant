"""
Curriculum Planner & Mermaid Visualization Generator
Generates full end-to-end learning pathways from the student's calibrated boundary
to target mastery, rendering Mermaid sequence and flow diagrams into Obsidian markdown.
"""

import os
import re

MD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "md"))

class CurriculumPlanner:
    def __init__(self, boundary_level: float = 3.65, md_dir: str = MD_DIR):
        self.boundary_level = boundary_level
        self.md_dir = md_dir

    def generate_mermaid_diagram(self) -> str:
        """Generates a clean Mermaid roadmap diagram reflecting current focus."""
        return f"""```mermaid
flowchart TD
    classDef mastered fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff;
    classDef current fill:#f57c00,stroke:#e65100,stroke-width:3px,color:#fff;
    classDef upcoming fill:#37474f,stroke:#263238,stroke-width:1px,color:#cfd8dc;

    M1["1. Present Tense Foundations<br/><i>Regulars, Pronoun-Drop, Agreement</i>"]:::mastered
    M2["2. Ser vs. Estar & Stem Changers<br/><i>Essence vs State, Boot Alternation</i>"]:::mastered
    M3["3. Preterite vs Imperfect Aspect<br/><i><b>Current Focus: Completed vs Ongoing</b></i>"]:::current
    M4["4. Stative Verbs in Past Tenses<br/><i>Conocer, Saber, Querer, Poder</i>"]:::upcoming
    M5["5. The Subjunctive Mood<br/><i>Wishes, Doubts, Impersonal Triggers</i>"]:::upcoming
    M6["6. Narrative Synthesis & Practice<br/><i>Complex Sentences & Composition</i>"]:::upcoming

    M1 --> M2
    M2 --> M3
    M3 ==>|Current Focus| M4
    M4 --> M5
    M5 --> M6
```"""

    def generate_progress_gauge(self) -> str:
        """Renders a clean topic progress tracker."""
        return f"""```
Present Tense Foundations       [████████████████████] Mastered
Ser vs. Estar & Stem Changers   [████████████████████] Mastered
Preterite vs. Imperfect Aspect  [████████████░░░░░░░░] Current Focus
Stative Past Nuances            [░░░░░░░░░░░░░░░░░░░░] Next Up
Subjunctive Mood                [░░░░░░░░░░░░░░░░░░░░] Queued
Narrative Synthesis             [░░░░░░░░░░░░░░░░░░░░] Queued
```"""

    def update_dashboard(self) -> None:
        """Updates the master dashboard in 00_INDEX_DASHBOARD.md."""
        dashboard_file = os.path.join(self.md_dir, "00_INDEX_DASHBOARD.md")
        if not os.path.exists(dashboard_file):
            return

        with open(dashboard_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Update ZPD Header line
        content = re.sub(
            r'\[ZPD\]\s+Level [0-9\.]+',
            f'[ZPD]     Level {self.boundary_level:.2f}',
            content
        )

        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✓ Updated Obsidian dashboard at {dashboard_file} (ZPD: Level {self.boundary_level:.2f})")

if __name__ == "__main__":
    planner = CurriculumPlanner(boundary_level=3.65)
    print("Generated Mermaid:\n", planner.generate_mermaid_diagram())
    print("\nGenerated ASCII Progress:\n", planner.generate_progress_gauge())
    planner.update_dashboard()
