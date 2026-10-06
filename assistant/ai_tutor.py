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
from typing import Dict, List, Optional

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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            return f"Error contacting Gemini API: {e}"

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

def call_real_ai(prompt: str, model: str = "gemini-3.8-flash-low", timeout: int = 60) -> str:
    """Invokes AI through direct API (macOS/cross-platform) or system CLI."""
    # 1. Check direct provider API key
    direct_resp = call_direct_api(prompt)
    if direct_resp is not None:
        return direct_resp

    # 2. Check local CLI
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
                return proc.stdout.strip()
            else:
                err = proc.stderr.strip() or "CLI exited with non-zero code."
                return f"Error communicating with AI model: {err}"
        except subprocess.TimeoutExpired:
            return "AI request timed out. Please try again."
        except Exception as e:
            return f"Error contacting AI engine: {e}"

    return (
        "No AI provider configured. Set an API key in your terminal or .env file:\n"
        "  export GEMINI_API_KEY='your_key'   # (Recommended, free tier)\n"
        "  export OPENAI_API_KEY='your_key'\n"
        "  export GROQ_API_KEY='your_key'\n"
    )

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

    def formulate_response(self, user_query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Sends the user query, system role, RAG context, and student notes
        to the real AI and returns the live response.
        """
        system_role = self.load_system_role()

        # Retrieve authoritative source chunks from user's course material
        chunks = self.rag.retrieve_context(user_query, subject=self.subject, top_k=3)
        context_text = ""
        if chunks:
            context_text = "\n\nAUTHORITATIVE COURSE MATERIAL (learn/material/):\n"
            for c in chunks:
                context_text += f"[{c['file']} (Section {c['chunk_id']})]:\n{c['text']}\n\n"

        # Check for synchronized student notes from Obsidian
        notes_text = self.sync.format_notes_for_prompt()

        # Format conversation history
        history_text = ""
        if history:
            history_text = "\nRecent Conversation:\n"
            for msg in history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role.capitalize()}: {content}\n"

        # Construct comprehensive AI prompt
        full_ai_prompt = (
            f"{system_role}\n\n"
            f"{context_text}\n"
            f"{notes_text}\n"
            f"{history_text}\n\n"
            f"Student Question / Message:\n{user_query}\n\n"
            f"Your Response (speak naturally as an expert instructor; evaluate reasoning before providing answers):"
        )

        return call_real_ai(full_ai_prompt)

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
