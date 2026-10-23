"""
Terminal Chat Runner
Launches AIChat or the integrated local epistemic tutor.
Handles document attachments (-f), Obsidian note sync, and zero-friction student access.
"""

import os
import sys
import subprocess
import threading
import time

try:
    from .rag_manager import MaterialRAGManager
    from .obsidian_sync import ObsidianNoteSync
    from .ai_tutor import RealAITutorEngine, start_ai_server
except ImportError:
    from rag_manager import MaterialRAGManager
    from obsidian_sync import ObsidianNoteSync
    from ai_tutor import RealAITutorEngine, start_ai_server

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
        print("\n" + "=" * 65)
        print(f"  Interactive Study Session: {self.subject.capitalize()} Tutor")
        print("  Type your questions or answers below. Type 'exit' to return to menu.")
        print("=" * 65)

        # Sync & display student Obsidian notes for this subject
        notes = self.sync.read_scratchpad_notes(subject=self.subject)
        if notes:
            print(f"\nNotes from your Obsidian scratchpad ({self.subject.capitalize()}):")
            for n in notes:
                print(f"  • {n}")

        # Check course material status
        mats = self.rag_mgr.scan_materials()
        file_count = len(mats.get(self.subject, []))
        if file_count > 0:
            print(f"\nCourse Material: {file_count} document(s) indexed from material/{self.subject}/")
        else:
            print(f"\nCourse Material: General {self.subject.capitalize()} knowledge (drop PDFs in material/{self.subject}/ anytime)")

        print("-" * 65 + "\n")

        engine = RealAITutorEngine(subject=self.subject)
        history = []

        # Tutor initiates dialogue proactively
        print("Tutor is preparing your session...", end="", flush=True)
        try:
            greeting = engine.generate_opening_greeting()
            print("\r" + " " * 45 + "\r", end="", flush=True)
            print("Tutor > " + greeting + "\n")
            history.append({"role": "assistant", "content": greeting})
        except Exception as e:
            print("\r" + " " * 45 + "\r", end="", flush=True)
            default_greeting = f"Welcome to your {self.subject.capitalize()} study session! How would you describe your current goals or questions in this subject?"
            print("Tutor > " + default_greeting + "\n")
            history.append({"role": "assistant", "content": default_greeting})

        while True:
            try:
                user_msg = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nSession paused. Your notes are saved in learn/md/.")
                break

            if not user_msg:
                continue

            if user_msg.lower() in ["exit", "quit", "menu", "q", ":q"]:
                print("\nReturning to menu...")
                break

            print("\nTutor > ", end="", flush=True)
            try:
                response = engine.formulate_response(user_msg, history=history)
                print(response + "\n")
                history.append({"role": "user", "content": user_msg})
                history.append({"role": "assistant", "content": response})
            except Exception as e:
                print(f"Error: {e}\n")

if __name__ == "__main__":
    runner = TerminalChatRunner()
    runner.start_session(interactive_repl=True)
