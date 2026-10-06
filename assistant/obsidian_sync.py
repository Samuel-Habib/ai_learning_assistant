"""
Obsidian Sync Utility
Monitors interactive markdown files in learn/md/ for student notes, questions,
and reflections, and formats them for injection into the AIChat terminal session.
"""

import os
import re
from typing import Dict, List, Optional

MD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "md"))
SCRATCHPAD_PATH = os.path.join(MD_DIR, "03_STUDENT_OBSIDIAN_SCRATCHPAD.md")

class ObsidianNoteSync:
    def __init__(self, md_dir: str = MD_DIR):
        self.md_dir = md_dir
        self.scratchpad_path = os.path.join(self.md_dir, "03_STUDENT_OBSIDIAN_SCRATCHPAD.md")

    def read_scratchpad_notes(self) -> List[str]:
        """Extracts student-written notes and questions from the scratchpad."""
        if not os.path.exists(self.scratchpad_path):
            return []

        with open(self.scratchpad_path, "r", encoding="utf-8") as f:
            content = f.read()

        notes = []
        in_scratch_area = False
        for line in content.splitlines():
            line_str = line.strip()
            if any(h in line_str for h in ["## 📌", "## Questions", "## My Notes"]):
                in_scratch_area = True
                continue
            elif line_str.startswith("## ") and in_scratch_area:
                in_scratch_area = False

            if in_scratch_area:
                if line_str.startswith("- ") and not line_str.startswith("- *("):
                    clean = line_str[2:].strip()
                    if clean:
                        notes.append(clean)

        return notes

    def scan_all_module_notes(self) -> Dict[str, List[str]]:
        """Scans all markdown modules for student notes."""
        results = {}
        if not os.path.exists(self.md_dir):
            return results

        for root, _, files in os.walk(self.md_dir):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    rel_name = os.path.relpath(full_path, self.md_dir)
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    file_notes = []
                    in_notes = False
                    for line in lines:
                        if re.search(r'##.*(?:Student Notes|Scratch)', line, re.IGNORECASE):
                            in_notes = True
                            continue
                        elif in_notes and line.strip().startswith("## "):
                            in_notes = False
                        if in_notes:
                            stripped = line.strip()
                            if stripped.startswith("- Note:") and len(stripped) > 8:
                                file_notes.append(stripped)
                            elif stripped.startswith("- ") and not stripped.startswith("- *") and len(stripped) > 3:
                                file_notes.append(stripped)
                    if file_notes:
                        results[rel_name] = file_notes
        return results

    def format_notes_for_prompt(self) -> str:
        """Formats discovered notes cleanly for the tutor."""
        scratch_notes = self.read_scratchpad_notes()
        module_notes = self.scan_all_module_notes()

        if not scratch_notes and not module_notes:
            return ""

        output = ["\nNotes from the student's Obsidian vault:"]
        if scratch_notes:
            for n in scratch_notes:
                output.append(f"  • {n}")
        if module_notes:
            for mod, n_list in module_notes.items():
                if mod != "03_STUDENT_OBSIDIAN_SCRATCHPAD.md":
                    for n in n_list:
                        output.append(f"  • [{mod}] {n}")

        output.append("Address these questions and reflections naturally in your lesson.\n")
        return "\n".join(output)

if __name__ == "__main__":
    sync = ObsidianNoteSync()
    print("Scratchpad notes:", sync.read_scratchpad_notes())
    print("\nFormatted prompt addition:\n", sync.format_notes_for_prompt())
