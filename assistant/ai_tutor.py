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

def call_real_ai(prompt: str, model: str = "gemini-3.8-flash-low", timeout: int = 60) -> str:
    """Invokes real frontier AI through the system CLI with low-latency parameters."""
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
    tutor = RealAITutorEngine()

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            messages = data.get("messages", [])
            last_message = messages[-1]["content"] if messages else "Hello"
            history = messages[:-1] if len(messages) > 1 else []

            model_id = data.get("model", "local-tutor:accuracy-adaptive")
            is_stream = data.get("stream", False)
            response_text = self.tutor.formulate_response(last_message, history=history)
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

def start_ai_server(port: int = 8765):
    try:
        server = ReusableHTTPServer(("127.0.0.1", port), LocalOpenAIHandler)
        server.serve_forever()
    except OSError:
        pass

if __name__ == "__main__":
    tutor = RealAITutorEngine()
    print("Testing Real AI response directly:")
    resp = tutor.formulate_response("Explain how aspect works in Spanish preterite vs imperfect in 2 sentences.")
    print(resp)
