"""
Adaptive Study Assistant - Terminal UI & Presentation Layer
Provides zero-dependency ANSI styling, thread-safe loading spinners,
rich markdown rendering for terminal displays, and clean box panels.
"""

import os
import sys
import time
import threading
import re
import shutil
from typing import Optional, List, Tuple

try:
    import readline
except ImportError:
    pass

# Detect color capability
COLOR_ENABLED = sys.stdout.isatty() and "NO_COLOR" not in os.environ

class Style:
    RESET = "\033[0m" if COLOR_ENABLED else ""
    BOLD = "\033[1m" if COLOR_ENABLED else ""
    DIM = "\033[2m" if COLOR_ENABLED else ""
    ITALIC = "\033[3m" if COLOR_ENABLED else ""
    UNDERLINE = "\033[4m" if COLOR_ENABLED else ""

    # Foreground colors
    BLACK = "\033[30m" if COLOR_ENABLED else ""
    RED = "\033[31m" if COLOR_ENABLED else ""
    GREEN = "\033[32m" if COLOR_ENABLED else ""
    YELLOW = "\033[33m" if COLOR_ENABLED else ""
    BLUE = "\033[34m" if COLOR_ENABLED else ""
    MAGENTA = "\033[35m" if COLOR_ENABLED else ""
    CYAN = "\033[36m" if COLOR_ENABLED else ""
    WHITE = "\033[37m" if COLOR_ENABLED else ""

    # Bright foregrounds
    BRIGHT_GREEN = "\033[92m" if COLOR_ENABLED else ""
    BRIGHT_YELLOW = "\033[93m" if COLOR_ENABLED else ""
    BRIGHT_BLUE = "\033[94m" if COLOR_ENABLED else ""
    BRIGHT_CYAN = "\033[96m" if COLOR_ENABLED else ""

def style_text(text: str, *styles: str) -> str:
    """Applies ANSI styles to text and resets at the end."""
    if not COLOR_ENABLED or not styles:
        return text
    return "".join(styles) + text + Style.RESET

class Spinner:
    """
    A lightweight, thread-safe terminal loading spinner.
    Ensures zero dangling threads and clean line restoration on exit.
    """
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Thinking..."):
        self.message = message
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        if not sys.stdout.isatty():
            sys.stdout.write(f"⏳ {self.message}\n")
            sys.stdout.flush()
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def update_message(self, new_message: str):
        self.message = new_message

    def _spin(self):
        idx = 0
        while not self.stop_event.is_set():
            frame = self.FRAMES[idx % len(self.FRAMES)]
            colored_frame = style_text(frame, Style.BRIGHT_CYAN, Style.BOLD)
            dim_msg = style_text(self.message, Style.DIM)
            sys.stdout.write(f"\r{colored_frame} {dim_msg}  ")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.08)

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=0.3)
        if sys.stdout.isatty():
            # Clear spinner line cleanly
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()

def format_terminal_markdown(text: str) -> str:
    """
    Transforms basic markdown formatting (bold, headers, bullets, code blocks)
    into formatted ANSI colored text for the terminal.
    """
    if not COLOR_ENABLED:
        return text

    lines = text.split("\n")
    formatted_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # Code block toggles
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            lang = stripped[3:].strip()
            if in_code_block:
                formatted_lines.append(style_text(f"  ┌─── Code ({lang or 'text'}) ───", Style.DIM))
            else:
                formatted_lines.append(style_text("  └────────────────────────", Style.DIM))
            continue

        if in_code_block:
            formatted_lines.append(f"  │ {style_text(line, Style.CYAN)}")
            continue

        # Markdown Headers
        if line.startswith("### "):
            formatted_lines.append(style_text(f"\n◆ {line[4:].strip()}", Style.BOLD, Style.BRIGHT_CYAN))
            continue
        elif line.startswith("## "):
            formatted_lines.append(style_text(f"\n■ {line[3:].strip()}", Style.BOLD, Style.GREEN))
            continue
        elif line.startswith("# "):
            formatted_lines.append(style_text(f"\n━ {line[2:].strip()} ━", Style.BOLD, Style.BRIGHT_GREEN))
            continue

        # Bullet lists
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            content = line.strip()[2:]
            line = f"  • {content}"

        # Inline Code `code`
        line = re.sub(r'`([^`]+)`', lambda m: style_text(f" {m.group(1)} ", Style.YELLOW, Style.DIM), line)

        # Bold **text**
        line = re.sub(r'\*\*([^*]+)\*\*', lambda m: style_text(m.group(1), Style.BOLD, Style.WHITE), line)

        # Italic *text*
        line = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', lambda m: style_text(m.group(1), Style.ITALIC), line)

        formatted_lines.append(line)

    return "\n".join(formatted_lines)

def visible_len(text: str) -> int:
    """Calculates visible character width of text ignoring ANSI escape sequences."""
    return len(re.sub(r'\033\[[0-9;]*m', '', text))

def wrap_text_cleanly(text: str, max_width: Optional[int] = None) -> str:
    """
    Wraps text on word boundaries cleanly, respecting ANSI styles and terminal columns.
    Never splits words in half (e.g. 'detail' will never break as 'detai' + 'l').
    Preserves code blocks and ASCII box diagrams intact.
    """
    term_cols = shutil.get_terminal_size((80, 24)).columns
    target_width = max_width or max(40, min(term_cols - 2, 88))

    lines = text.split("\n")
    wrapped_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("┌──"):
            in_code_block = True
        elif stripped.startswith("└──"):
            in_code_block = False

        # Never break code blocks, ASCII borders, or headers
        if in_code_block or any(b in line for b in ["│", "─", "┌", "└", "┼", "┤", "├", "━", "═"]):
            wrapped_lines.append(line)
            continue

        if visible_len(line) <= target_width:
            wrapped_lines.append(line)
            continue

        # Handle bullet points or numbered list hanging indents
        indent_match = re.match(r"^(\s*(?:[•\-\*]|\d+\.)\s+)", line)
        if indent_match:
            first_prefix = indent_match.group(1)
            sub_prefix = " " * visible_len(first_prefix)
            rest_of_line = line[len(first_prefix):]
        else:
            first_prefix = ""
            sub_prefix = "  " if line.startswith("  ") else ""
            rest_of_line = line

        words = rest_of_line.split(" ")
        cur_line = []
        cur_vlen = visible_len(first_prefix)
        is_first = True

        for w in words:
            if not w:
                continue
            wlen = visible_len(w)
            if cur_line and (cur_vlen + 1 + wlen > target_width):
                prefix = first_prefix if is_first else sub_prefix
                wrapped_lines.append(prefix + " ".join(cur_line))
                cur_line = [w]
                cur_vlen = visible_len(sub_prefix) + wlen
                is_first = False
            else:
                cur_line.append(w)
                cur_vlen += (1 if len(cur_line) > 1 else 0) + wlen

        if cur_line:
            prefix = first_prefix if is_first else sub_prefix
            wrapped_lines.append(prefix + " ".join(cur_line))

    return "\n".join(wrapped_lines)

def print_tutor_header(subject: str, unit: str = "", level: float = 1.0):
    """Prints a styled header for the tutor study session."""
    border = "═" * 66
    print(style_text(border, Style.BRIGHT_CYAN))
    print(style_text(f"  🧑‍🏫 Interactive Study Session: {subject.replace('_', ' ').title()}", Style.BOLD, Style.WHITE))
    if unit:
        print(style_text(f"  🎯 Focus Unit: {unit}  (Frontier: Level {level:.2f})", Style.DIM, Style.CYAN))
    print(style_text("  💡 Type 'exit' to pause and return to menu.", Style.DIM))
    print(style_text(border, Style.BRIGHT_CYAN))
    print()

def print_tutor_message(message: str):
    """Displays tutor output with styled speaker tag, formatted markdown, and clean word wrapping."""
    tag = style_text("🧑‍🏫 Tutor", Style.BOLD, Style.BRIGHT_GREEN)
    formatted = format_terminal_markdown(message.strip())
    wrapped = wrap_text_cleanly(formatted)
    print(f"\n{tag} > {wrapped}\n")

def prompt_user(prompt_text: str = "You > ") -> str:
    """
    Prompts student with an attractive colored prompt, robustly handling
    multi-line clipboard pastes and stripping terminal escape artifacts.
    """
    tag = style_text("👤 You", Style.BOLD, Style.BRIGHT_BLUE)
    try:
        first_line = input(f"{tag} > ").strip()
        lines = [first_line]

        # Handle multi-line clipboard paste without line-buffer glitching
        if sys.stdin.isatty():
            import select
            while select.select([sys.stdin], [], [], 0.05)[0]:
                extra = sys.stdin.readline()
                if not extra:
                    break
                lines.append(extra.rstrip("\r\n"))

        full_text = "\n".join(lines).strip()
        # Clean stray terminal control codes (e.g. ^[E, bracketed paste tags)
        cleaned = re.sub(r'\x1b\[[0-9;]*[a-zA-Z~]', '', full_text)
        cleaned = re.sub(r'\x1b[A-Za-z]', '', cleaned)
        return cleaned.strip()
    except (EOFError, KeyboardInterrupt):
        return "exit"
