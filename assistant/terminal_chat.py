"""
Terminal Chat Runner
Launches AIChat or the integrated local epistemic tutor.
Handles document attachments (-f), Obsidian note sync, and zero-friction student access.
"""

import os
import sys
import subprocess

try:
    from .rag_manager import MaterialRAGManager
    from .obsidian_sync import ObsidianNoteSync
    from .ai_tutor import RealAITutorEngine, start_ai_server
    from .ui import Spinner, print_tutor_header, print_tutor_message, prompt_user, style_text, Style
except ImportError:
    from rag_manager import MaterialRAGManager
    from obsidian_sync import ObsidianNoteSync
    from ai_tutor import RealAITutorEngine, start_ai_server
    from ui import Spinner, print_tutor_header, print_tutor_message, prompt_user, style_text, Style

AICHAT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".aichat"))
MATERIAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "material"))

class TerminalChatRunner:
    def __init__(self, subject: str = "spanish"):
        self.subject = subject
        self.rag_mgr = MaterialRAGManager()
        self.sync = ObsidianNoteSync()
        self.aichat_bin = "aichat"

    def check_env_keys(self) -> dict:
        """Detects available LLM credentials from env or .env file."""
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ and v:
                            os.environ[k] = v

        keys = {}
        for var in ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"]:
            val = os.environ.get(var)
            if val and val.strip():
                keys[var] = val.strip()
        return keys

    def start_session(self, interactive_repl: bool = True):
        # Default to native interactive tutor dialogue for full RAG & Obsidian grounding
        self.run_direct_repl()

    def run_direct_repl(self):
        """Native interactive tutor dialogue with full RAG and Obsidian sync."""

        # Determine current curriculum unit and frontier level
        try:
            from .curriculum_planner import CurriculumPlanner
        except ImportError:
            from curriculum_planner import CurriculumPlanner
        planner = CurriculumPlanner(subject=self.subject)
        active_idx = max(0, min(len(planner.modules) - 1, int(planner.boundary_level) - 1))
        curr_unit = planner.modules[active_idx][0]
        print_tutor_header(self.subject, curr_unit, planner.boundary_level)

        # Sync & display student Obsidian notes for this subject
        notes = self.sync.read_scratchpad_notes(subject=self.subject)
        if notes:
            print(style_text(f"  📝 Your {self.subject.replace('_',' ').title()} notes:", Style.DIM))
            for n in notes:
                print(style_text(f"     • {n}", Style.DIM))
            print()

        # Check course material status
        mats = self.rag_mgr.scan_materials()
        file_count = len(mats.get(self.subject, []))
        if file_count > 0:
            print(style_text(f"  📚 Course Material: {file_count} document(s) indexed from material/{self.subject}/", Style.DIM))
        else:
            print(style_text(f"  📚 Course Material: General {self.subject.replace('_',' ').title()} knowledge (drop PDFs in material/{self.subject}/ anytime)", Style.DIM))

        print()

        engine = RealAITutorEngine(subject=self.subject)
        history = []

        # Tutor initiates dialogue proactively
        try:
            with Spinner("Your tutor is preparing the session..."):
                greeting = engine.generate_opening_greeting()
            print_tutor_message(greeting)
            history.append({"role": "assistant", "content": greeting})
        except Exception:
            default_greeting = f"Welcome to your {self.subject.replace('_',' ').title()} study session! How would you describe your current goals or questions in this subject?"
            print_tutor_message(default_greeting)
            history.append({"role": "assistant", "content": default_greeting})

        while True:
            user_msg = prompt_user()

            if not user_msg:
                continue

            if user_msg.lower() in ["exit", "quit", "menu", "q", ":q"]:
                print(style_text("\n✨ Session paused. Your notes are saved in learn/md/.", Style.DIM, Style.GREEN))
                break

            try:
                with Spinner("Thinking..."):
                    response = engine.formulate_response(user_msg, history=history)
                print_tutor_message(response)
                history.append({"role": "user", "content": user_msg})
                history.append({"role": "assistant", "content": response})
            except Exception as e:
                print(style_text(f"\n⚠ Error: {e}", Style.RED))

if __name__ == "__main__":
    runner = TerminalChatRunner()
    runner.start_session(interactive_repl=True)
