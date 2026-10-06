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
        print("\n" + "-"*60)
        print(f"  Study Session: {self.subject.capitalize()}")
        print("-" * 60)

        # Sync & display student Obsidian notes if present
        notes = self.sync.read_scratchpad_notes()
        if notes:
            print("\nNotes from your Obsidian scratchpad:")
            for n in notes:
                print(f"  • {n}")
            print()

        mat_files = self.rag_mgr.get_source_file_args(self.subject)
        keys = self.check_env_keys()

        if keys:
            primary_key = list(keys.keys())[0]
            env = os.environ.copy()
            env["AICHAT_CONFIG_DIR"] = AICHAT_DIR

            model_map = {
                "GEMINI_API_KEY": "gemini:gemini-1.5-flash",
                "OPENAI_API_KEY": "openai:gpt-4o",
                "ANTHROPIC_API_KEY": "claude:claude-3-5-sonnet-20241022",
                "GROQ_API_KEY": "groq:llama-3.3-70b-versatile"
            }
            chosen_model = model_map.get(primary_key, "gemini:gemini-1.5-flash")

            cmd = [self.aichat_bin, "-m", chosen_model, "-r", "accuracy-tutor", "-s", self.subject]

            try:
                proc = subprocess.run(cmd, env=env)
                if proc.returncode != 0:
                    self.run_direct_repl()
            except Exception as e:
                print(f"AIChat CLI was unable to run ({e}). Starting direct tutor session...")
                self.run_direct_repl()
        else:
            # Start real AI bridge server
            server_thread = threading.Thread(target=start_ai_server, args=(8765,), daemon=True)
            server_thread.start()
            time.sleep(0.3)

            env = os.environ.copy()
            env["AICHAT_CONFIG_DIR"] = AICHAT_DIR

            cmd = [self.aichat_bin, "-m", "local-tutor:accuracy-adaptive", "-r", "accuracy-tutor", "-s", self.subject]

            if interactive_repl:
                try:
                    proc = subprocess.run(cmd, env=env)
                    if proc.returncode != 0:
                        self.run_direct_repl()
                except KeyboardInterrupt:
                    print("\n\nSession paused. Your notes are saved in learn/md/.")
                except Exception as e:
                    print(f"AIChat CLI was unable to run ({e}). Starting direct tutor session...")
                    self.run_direct_repl()

    def run_direct_repl(self):
        """Native interactive tutor dialogue loop as a reliable fallback."""
        print("\n" + "=" * 60)
        print(f"  Interactive Dialogue: {self.subject.capitalize()} Tutor")
        print("  Type your response or question below. Type 'exit' to return to menu.")
        print("=" * 60 + "\n")

        engine = RealAITutorEngine(subject=self.subject)
        history = []

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
