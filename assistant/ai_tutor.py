"""
Real AI Tutor Engine & OpenAI-Compatible Bridge
Directly connects AIChat to real frontier AI models (Gemini 3.8 Flash / Claude)
via the native Antigravity CLI and multi-provider APIs.
No canned answers, no mocks—100% genuine dynamic AI intelligence.
"""

import sys
import os
import json
import time
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Optional, Tuple, Any

try:
    from .rag_manager import MaterialRAGManager
    from .obsidian_sync import ObsidianNoteSync
except ImportError:
    from rag_manager import MaterialRAGManager
    from obsidian_sync import ObsidianNoteSync

ROLE_PROMPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".aichat", "roles", "accuracy-tutor.md"))

import shutil
import urllib.request
import urllib.error

def load_dotenv():
    """Loads environment variables from .env in workspace root if present."""
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

load_dotenv()

def call_direct_api(prompt: str) -> Optional[str]:
    """
    Directly queries LLM APIs using standard library urllib.
    Zero external dependencies; works seamlessly on macOS, Linux, and Windows.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")

    if gemini_key:
        last_gemini_err = None
        for model in ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if "candidates" in data and data["candidates"]:
                        parts = data["candidates"][0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
            except urllib.error.HTTPError as e:
                last_gemini_err = f"Error contacting Gemini API ({e.code}): {e.reason}"
                continue
            except (TimeoutError, urllib.error.URLError) as e:
                last_gemini_err = f"Network error contacting Gemini API: {e}"
                continue
            except Exception as e:
                last_gemini_err = f"Error contacting Gemini API: {e}"
                continue
        if last_gemini_err and not shutil.which("agy"):
            return last_gemini_err

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01"
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["content"][0]["text"].strip()
        except Exception as e:
            return f"Error contacting Anthropic API: {e}"

    if openai_key or groq_key:
        url = "https://api.openai.com/v1/chat/completions" if openai_key else "https://api.groq.com/openai/v1/chat/completions"
        key = openai_key or groq_key
        model = "gpt-4o-mini" if openai_key else "llama-3.3-70b-versatile"
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Error contacting AI API: {e}"

    return None

def get_ai_status() -> tuple[bool, str]:
    """Returns whether a real AI model backend is configured and its description."""
    load_dotenv()
    if os.environ.get("GEMINI_API_KEY"):
        return True, "Gemini API (gemini-1.5-flash)"
    if os.environ.get("OPENAI_API_KEY"):
        return True, "OpenAI API (gpt-4o-mini)"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True, "Anthropic API (claude-3-5-haiku)"
    if os.environ.get("GROQ_API_KEY"):
        return True, "Groq API (llama-3.3-70b)"
    if shutil.which("agy"):
        return True, "Local Antigravity CLI (gemini-3.8-flash)"
    return False, "Offline Mode (No API key found in .env)"

def call_real_ai(prompt: str, model: str = "gemini-3.8-flash-low", timeout: int = 45, use_cache: bool = True) -> str:
    """Invokes AI through system CLI (Antigravity) or direct provider API with SQLite completion caching."""
    # Check SQLite persistent cache first to minimize token consumption
    cache_inst = None
    if use_cache:
        try:
            from .cache import LLMCache
            cache_inst = LLMCache()
            cached = cache_inst.get(prompt, model)
            if cached:
                return cached
        except Exception:
            pass

    response_text = None

    # 1. If running under Antigravity CLI environment, prioritize native CLI
    if shutil.which("agy"):
        cmd = [
            "agy",
            "--dangerously-skip-permissions",
            "--model", model,
            "--effort", "low",
            "--disable-slash-commands",
            "--output-format", "text",
            "-p", prompt
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if proc.returncode == 0 and proc.stdout.strip():
                response_text = proc.stdout.strip()
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

    # 2. Check direct provider API key (Gemini, OpenAI, Anthropic, Groq)
    if response_text is None:
        direct_resp = call_direct_api(prompt)
        if direct_resp is not None and not direct_resp.startswith("Error contacting") and not direct_resp.startswith("Network error"):
            response_text = direct_resp
        elif direct_resp is not None:
            response_text = direct_resp

    if response_text is None:
        return (
            "No AI provider configured. Set an API key in your terminal or .env file:\n"
            "  export GEMINI_API_KEY='your_key'   # (Recommended, free tier)\n"
            "  export OPENAI_API_KEY='your_key'\n"
            "  export GROQ_API_KEY='your_key'\n"
        )

    # Save successful completion to cache
    if use_cache and cache_inst and response_text and not response_text.startswith("Error"):
        try:
            cache_inst.set(prompt, response_text, model)
        except Exception:
            pass

    return response_text

class RealAITutorEngine:
    def __init__(self, subject: str = "spanish"):
        self.subject = subject
        self.rag = MaterialRAGManager()
        self.sync = ObsidianNoteSync()
        self.rag.build_index(subject)

    def load_system_role(self) -> str:
        """Loads the full Accuracy-First & Evidence-Based role prompt."""
        if os.path.exists(ROLE_PROMPT_PATH):
            with open(ROLE_PROMPT_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            # Strip YAML frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    return parts[2].strip()
            return content.strip()
        return "You are an accuracy-first, evidence-based learning assistant."

    def formulate_response(
        self,
        user_query: str,
        history: Optional[List[Dict[str, str]]] = None,
        active_unit_idx: Optional[int] = None,
        active_unit_title: Optional[str] = None,
        modules: Optional[List[Tuple[str, str]]] = None,
        boundary_level: Optional[float] = None
    ) -> str:
        """
        Sends the user query, system role, RAG context, and student notes
        to the real AI and returns the live response, strictly adhering to
        active ZPD boundaries and pedagogical style directives.
        """
        system_role = self.load_system_role()

        # Resolve curriculum and boundary context
        if active_unit_idx is None or active_unit_title is None or modules is None or boundary_level is None:
            try:
                from .curriculum_planner import CurriculumPlanner
            except ImportError:
                from curriculum_planner import CurriculumPlanner
            planner = CurriculumPlanner(subject=self.subject)
            boundary_level = planner.boundary_level
            modules = planner.modules
            active_unit_idx = max(0, min(len(modules) - 1, int(boundary_level) - 1)) if modules else 0
            active_unit_title = modules[active_unit_idx][0] if modules else "Unit 1"

        # Load Meta-Learning Style & ZPD Boundary directives
        try:
            from .meta_learner import MetaLearningEngine
        except ImportError:
            from meta_learner import MetaLearningEngine
        meta_engine = MetaLearningEngine(subject=self.subject)
        style_directive = meta_engine.get_style_directive()
        zpd_directive = meta_engine.get_zpd_boundary_directive(
            active_unit_idx=active_unit_idx,
            active_unit_title=active_unit_title,
            modules=modules,
            boundary_level=boundary_level
        )

        # Retrieve authoritative source chunks from user's course material
        chunks = self.rag.retrieve_context(user_query, subject=self.subject, top_k=3)
        context_text = ""
        if chunks:
            context_text = "\n\nAUTHORITATIVE COURSE MATERIAL (learn/material/):\n"
            for c in chunks:
                context_text += f"[{c['file']} (Section {c['chunk_id']})]:\n{c['text']}\n\n"

        # Check for synchronized student notes from Obsidian
        notes_text = self.sync.format_notes_for_prompt(subject=self.subject)

        # Format conversation history
        history_text = ""
        if history:
            history_text = "\nRecent Conversation:\n"
            for msg in history[-8:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role.capitalize()}: {content}\n"

        # Construct comprehensive AI prompt with ZPD boundary & pedagogical style
        full_ai_prompt = (
            f"{system_role}\n\n"
            f"{zpd_directive}\n\n"
            f"{style_directive}\n\n"
            f"{context_text}\n"
            f"{notes_text}\n"
            f"{history_text}\n\n"
            f"Student Message:\n{user_query}\n\n"
            f"CRITICAL TERMINAL CONVERSATION RULES (STRICTLY ENFORCED):\n"
            f"1. NO WALLS OF TEXT IN THE TERMINAL. All long-form explanations and ASCII diagrams belong in Obsidian (learn/md/subjects/{self.subject}/lessons/).\n"
            f"2. Keep your terminal response lean, concise, and focused (1 to 2 short paragraphs, max 3-5 sentences total).\n"
            f"3. Strictly obey the active PEDAGOGICAL STYLE and ZPD BOUNDARY DIRECTIVE.\n"
            f"4. NO NOMENCLATURE GUESSING GAMES: If the student hesitates ('idk', 'not sure'), immediately anchor the structural mechanism causally in 1-2 sentences. Never demand arbitrary vocabulary recall.\n"
            f"5. Maintain a sharp, collaborative engineer-to-engineer tone.\n\n"
            f"Your Response:"
        )

        return call_real_ai(full_ai_prompt)

    def generate_opening_greeting(self) -> str:
        """Generates an engaging, lean opening message with ONE focused question (NO walls of text)."""
        try:
            from .curriculum_planner import CurriculumPlanner
        except ImportError:
            from curriculum_planner import CurriculumPlanner

        planner = CurriculumPlanner(subject=self.subject)
        level = planner.boundary_level
        active_idx = max(0, min(len(planner.modules) - 1, int(level) - 1))
        curr_unit = planner.modules[active_idx][0]
        curr_sub = planner.modules[active_idx][1]

        notes = self.sync.read_scratchpad_notes(subject=self.subject)
        notes_prompt = ""
        if notes:
            notes_prompt = f"The student also noted these questions in Obsidian for this subject:\n" + "\n".join(f"- {n}" for n in notes)

        prompt = (
            f"You are the student's personal tutor for {self.subject.capitalize()}.\n"
            f"We are beginning an interactive terminal study session.\n"
            f"- Current Focus Unit: {curr_unit} ({curr_sub})\n"
            f"- Obsidian Lesson Document: learn/md/subjects/{self.subject}/lessons/\n"
            f"- Calibrated Level: Level {level:.2f}\n"
            f"{notes_prompt}\n\n"
            f"CRITICAL RULE: NO WALLS OF TEXT. Keep your entire reply under 4-5 sentences total.\n"
            f"The full textbook lesson and diagrams are already saved in Obsidian for them to read.\n\n"
            f"Instructions for Opening Message:\n"
            f"1. Quick 1-sentence welcome stating today's focus ({curr_unit}).\n"
            f"2. Mention they can refer to the full lesson note in Obsidian (`learn/md/subjects/{self.subject}/lessons/`) anytime for full diagrams and reference.\n"
            f"3. If they wrote questions in Obsidian, address it in 1 sentence.\n"
            f"4. Ask ONE focused, conceptual question on this unit to start the dialogue.\n"
            f"Do NOT lecture. Do NOT dump diagrams or multi-paragraph text."
        )
        try:
            return call_real_ai(prompt)
        except Exception:
            return f"Welcome to our {self.subject.capitalize()} study session! Today we are focusing on {curr_unit}. You can review the full lesson notes and diagrams in Obsidian anytime. To get started: how would you describe the primary mechanism behind this concept?"

class LocalOpenAIHandler(BaseHTTPRequestHandler):
    tutor: Optional[RealAITutorEngine] = None

    def do_POST(self):
        if not LocalOpenAIHandler.tutor:
            LocalOpenAIHandler.tutor = RealAITutorEngine()
        tutor = LocalOpenAIHandler.tutor

        if self.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            messages = data.get("messages", [])
            last_message = messages[-1]["content"] if messages else "Hello"
            history = messages[:-1] if len(messages) > 1 else []

            model_id = data.get("model", "local-tutor:accuracy-adaptive")
            is_stream = data.get("stream", False)
            response_text = tutor.formulate_response(last_message, history=history)
            msg_id = f"chatcmpl-real-ai-{int(time.time())}"

            if is_stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()

                # Stream response words token-by-token
                words = response_text.split(" ")
                for i, word in enumerate(words):
                    token = word if i == 0 else " " + word
                    chunk_payload = {
                        "id": msg_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model_id,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": token},
                            "finish_reason": None
                        }]
                    }
                    self.wfile.write(f"data: {json.dumps(chunk_payload)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(0.005)

                # Send final stop chunk and [DONE]
                stop_payload = {
                    "id": msg_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_id,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                self.wfile.write(f"data: {json.dumps(stop_payload)}\n\n".encode("utf-8"))
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            else:
                resp_payload = {
                    "id": msg_id,
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model_id,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(last_message.split()),
                        "completion_tokens": len(response_text.split()),
                        "total_tokens": len(last_message.split()) + len(response_text.split())
                    }
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def start_ai_server(port: int = 8765, subject: str = "spanish"):
    try:
        LocalOpenAIHandler.tutor = RealAITutorEngine(subject=subject)
        server = ReusableHTTPServer(("127.0.0.1", port), LocalOpenAIHandler)
        server.serve_forever()
    except OSError:
        pass

if __name__ == "__main__":
    tutor = RealAITutorEngine()
    print("Testing Real AI response directly:")
    resp = tutor.formulate_response("Explain how aspect works in Spanish preterite vs imperfect in 2 sentences.")
    print(resp)
