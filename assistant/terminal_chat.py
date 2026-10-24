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
    from .meta_learner import MetaLearningEngine
    from .ui import (
        Spinner, print_tutor_header, print_tutor_message, prompt_user,
        style_text, Style, print_meta_learning_card, print_styles_menu, print_boundary_card,
        print_unit_mastery_card
    )
except ImportError:
    from rag_manager import MaterialRAGManager
    from obsidian_sync import ObsidianNoteSync
    from ai_tutor import RealAITutorEngine, start_ai_server
    from meta_learner import MetaLearningEngine
    from ui import (
        Spinner, print_tutor_header, print_tutor_message, prompt_user,
        style_text, Style, print_meta_learning_card, print_styles_menu, print_boundary_card,
        print_unit_mastery_card
    )

AICHAT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".aichat"))
MATERIAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "material"))

class TerminalChatRunner:
    def __init__(self, subject: str = "spanish"):
        self.subject = subject
        self.rag_mgr = MaterialRAGManager()
        self.sync = ObsidianNoteSync()
        self.aichat_bin = "aichat"

    def check_env_keys(self) -> dict:
        """Detects available LLM credentials from env or .env file and keeps .env synchronized."""
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        env_vars[k] = v
                        if k not in os.environ and v:
                            os.environ[k] = v

        keys = {}
        for var in ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"]:
            val = os.environ.get(var)
            if val and val.strip():
                keys[var] = val.strip()
                # If exported in terminal, persist to .env so future runs work automatically
                if var not in env_vars:
                    try:
                        with open(env_path, "a", encoding="utf-8") as f:
                            f.write(f"\n{var}={val.strip()}\n")
                    except Exception:
                        pass
        return keys

    def start_session(self, interactive_repl: bool = True):
        # Default to native interactive tutor dialogue for full RAG & Obsidian grounding
        self.check_env_keys()
        self.run_direct_repl()

    def run_direct_repl(self):
        """Native interactive tutor dialogue with full RAG and Obsidian sync."""
        self.check_env_keys()

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
        meta_engine = MetaLearningEngine(subject=self.subject)
        curr_style_info = meta_engine.get_current_style()
        print(style_text(f"  🧠 Pedagogical Style: {curr_style_info['tag']}  (/style to change, /meta for assessment)", Style.DIM, Style.CYAN))
        print()

        try:
            from .db import StateManager
        except ImportError:
            from assistant.db import StateManager
        db = StateManager()
        history = db.get_chat_history(self.subject, limit=10)

        try:
            from .lesson_manager import LessonManager
        except ImportError:
            from lesson_manager import LessonManager
        lesson_mgr = LessonManager()

        try:
            from .fact_checker import BackgroundFactChecker
        except ImportError:
            from fact_checker import BackgroundFactChecker
        fact_checker = BackgroundFactChecker()

        # Check if we are resuming an ongoing session or starting fresh
        # Clean out any previous API setup errors from history so they are never resumed as questions!
        clean_history = [
            m for m in history 
            if not ("No AI provider configured" in m.get("content", "") or 
                    "Error contacting" in m.get("content", "") or
                    "Network error" in m.get("content", ""))
        ]

        if clean_history:
            last_msg = clean_history[-1]
            if last_msg["role"] == "assistant":
                # Tutor already posed a question/topic in the previous turn
                resumption_text = (
                    f"Welcome back to your study session on {curr_unit}!\n"
                    f"Picking up where we left off:\n\n"
                    f"{last_msg['content']}"
                )
                print_tutor_message(resumption_text)
            else:
                # Last message was from user - formulate immediate response to pick up the thread
                try:
                    with Spinner("Picking up from your previous note..."):
                        response = engine.formulate_response(
                            last_msg["content"],
                            history=clean_history[:-1],
                            active_unit_idx=active_idx,
                            active_unit_title=curr_unit,
                            modules=planner.modules,
                            boundary_level=planner.boundary_level
                        )
                    print_tutor_message(response)
                    clean_history.append({"role": "assistant", "content": response})
                    if not response.startswith("No AI provider"):
                        db.append_chat_message(self.subject, "assistant", response)
                    if len(response) > 200:
                        lesson_mgr.append_dialogue_to_lesson(self.subject, active_idx + 1, curr_unit, response)
                    fact_checker.verify_async(self.subject, active_idx + 1, curr_unit, last_msg["content"], response)
                except Exception:
                    default_greeting = f"Welcome back to {curr_unit}! Let's continue from where we left off."
                    print_tutor_message(default_greeting)
            history = clean_history
        else:
            # Tutor initiates dialogue proactively for a fresh session
            try:
                with Spinner("Your tutor is preparing the session..."):
                    greeting = engine.generate_opening_greeting()
                print_tutor_message(greeting)
                if not greeting.startswith("No AI provider"):
                    history.append({"role": "assistant", "content": greeting})
                    db.append_chat_message(self.subject, "assistant", greeting)
                    if len(greeting) > 200:
                        lesson_mgr.append_dialogue_to_lesson(self.subject, active_idx + 1, curr_unit, greeting)
                    fact_checker.verify_async(self.subject, active_idx + 1, curr_unit, "Start session", greeting)
            except Exception:
                default_greeting = f"Welcome to your {self.subject.replace('_',' ').title()} study session! Today we are focusing on {curr_unit} ({planner.modules[active_idx][1]}). Let's walk through the core mechanisms together."
                print_tutor_message(default_greeting)
                history.append({"role": "assistant", "content": default_greeting})
                db.append_chat_message(self.subject, "assistant", default_greeting)

        while True:
            # Check if background verifier discovered a technical nuance or correction
            pending_fact = fact_checker.get_and_clear_pending_note(self.subject)
            if pending_fact:
                print(style_text(f"  🔍 Fact-Check Note: {pending_fact}\n", Style.DIM, Style.CYAN))
                history.append({"role": "system", "content": f"[Verified Correction]: {pending_fact}"})

            user_msg = prompt_user()

            if not user_msg:
                continue

            if user_msg.lower() in ["exit", "quit", "menu", "q", ":q"]:
                lesson_path = lesson_mgr.get_lesson_path(self.subject, active_idx + 1, curr_unit)
                print(style_text(f"\n✨ Session paused. Lesson notes & diagrams saved to Obsidian:", Style.DIM, Style.GREEN))
                print(style_text(f"   {lesson_path}", Style.CYAN))
                break

            clean_cmd = user_msg.strip().lower()

            # --- Meta-Learning & ZPD Control Commands ---
            if clean_cmd in ["/meta", "meta", "/eval", "how am i doing", "meta learning", "do a meta learning analaysis of whats going on here"]:
                with Spinner("Analyzing session epistemic flow & learning dynamics..."):
                    assessment = meta_engine.run_explicit_assessment(history, curr_unit)
                meta_card = {
                    "status": assessment["status"],
                    "active_style": assessment["active_style"],
                    "recommended_style": assessment["recommended_style"],
                    "message": f"{assessment['action']} (Friction occurrences detected: {assessment['friction_events']}).",
                    "style_changed": False
                }
                print_meta_learning_card(meta_card)
                continue

            if clean_cmd.startswith("/style") or clean_cmd.startswith("style"):
                parts = clean_cmd.split(None, 1)
                if len(parts) == 1:
                    print_styles_menu(meta_engine.list_styles(), meta_engine.get_current_style()["key"])
                else:
                    target_style = parts[1]
                    if meta_engine.set_style(target_style):
                        new_s = meta_engine.get_current_style()
                        print(style_text(f"\n✓ Pedagogical style updated to: {new_s['name']} ({new_s['tag']})\n", Style.BOLD, Style.GREEN))
                    else:
                        print(style_text(f"\n⚠ Unknown style '{target_style}'. Available styles:", Style.YELLOW))
                        print_styles_menu(meta_engine.list_styles(), meta_engine.get_current_style()["key"])
                continue

            if clean_cmd in ["/boundary", "boundary", "/zpd", "zpd"]:
                forbidden = [m[0] for i, m in enumerate(planner.modules) if i > active_idx]
                print_boundary_card(curr_unit, planner.boundary_level, forbidden)
                continue

            if clean_cmd in ["/next", "next", "/advance", "advance", "/graduate", "graduate"]:
                new_level, next_title = meta_engine.advance_frontier(active_idx, planner.modules)
                print_unit_mastery_card(curr_unit, next_title, new_level)
                planner.boundary_level = new_level
                active_idx = max(0, min(len(planner.modules) - 1, int(new_level) - 1))
                curr_unit = planner.modules[active_idx][0]
                greeting = f"Welcome to **{curr_unit}**! Previous unit notes have been marked Mastered in Obsidian. What would you like to explore first?"
                print_tutor_message(greeting)
                history.append({"role": "assistant", "content": greeting})
                db.append_chat_message(self.subject, "assistant", greeting)
                continue

            if clean_cmd in ["reset", "/reset", "restart"]:
                with db._get_connection() as conn:
                    conn.cursor().execute("DELETE FROM chat_history WHERE subject = ?", (self.subject.strip().lower().replace(" ", "_"),))
                    conn.commit()
                history.clear()
                print(style_text(f"\n🔄 Chat history reset for {self.subject.replace('_', ' ').title()}. Starting a fresh session...\n", Style.DIM, Style.GREEN))
                try:
                    with Spinner("Your tutor is preparing the session..."):
                        greeting = engine.generate_opening_greeting()
                    print_tutor_message(greeting)
                    history.append({"role": "assistant", "content": greeting})
                    db.append_chat_message(self.subject, "assistant", greeting)
                except Exception:
                    pass
                continue

            # Periodic or friction/saturation-triggered meta-learning check-in
            meta_check = meta_engine.record_turn_and_check(user_msg, "", history, active_unit=curr_unit)
            if meta_check:
                if meta_check.get("is_saturation"):
                    # Concept saturation & Unit Mastery milestone reached!
                    new_level, next_title = meta_engine.advance_frontier(active_idx, planner.modules)
                    print_meta_learning_card(meta_check)
                    print_unit_mastery_card(curr_unit, next_title, new_level)

                    mastery_reply = (
                        f"You have officially mastered **{curr_unit}**!\n\n"
                        f"Every foundational mechanism has been verified: star topology point-to-point isolation, "
                        f"D+/D- resistor speed detection, the host-scheduled arbitration model, and all 4 transfer modes.\n\n"
                        f"Your Obsidian roadmap has been updated with Unit 1 marked green (Mastered). "
                        f"Would you like to wrap up today's session here, or take a look at **{next_title}**?"
                    )
                    print_tutor_message(mastery_reply)
                    history.append({"role": "user", "content": user_msg})
                    history.append({"role": "assistant", "content": mastery_reply})
                    db.append_chat_message(self.subject, "user", user_msg)
                    db.append_chat_message(self.subject, "assistant", mastery_reply)
                    planner.boundary_level = new_level
                    active_idx = max(0, min(len(planner.modules) - 1, int(new_level) - 1))
                    curr_unit = planner.modules[active_idx][0]
                    continue
                else:
                    print_meta_learning_card(meta_check)

            db.append_chat_message(self.subject, "user", user_msg)
            try:
                with Spinner("Thinking..."):
                    response = engine.formulate_response(
                        user_msg,
                        history=history,
                        active_unit_idx=active_idx,
                        active_unit_title=curr_unit,
                        modules=planner.modules,
                        boundary_level=planner.boundary_level
                    )
                print_tutor_message(response)
                history.append({"role": "user", "content": user_msg})
                history.append({"role": "assistant", "content": response})
                db.append_chat_message(self.subject, "assistant", response)
                if len(response) > 200:
                    lesson_mgr.append_dialogue_to_lesson(self.subject, active_idx + 1, curr_unit, response)
                # Launch asynchronous background verification between dialogue turns
                fact_checker.verify_async(self.subject, active_idx + 1, curr_unit, user_msg, response)
            except Exception as e:
                print(style_text(f"\n⚠ Error: {e}", Style.RED))

if __name__ == "__main__":
    runner = TerminalChatRunner()
    runner.start_session(interactive_repl=True)
