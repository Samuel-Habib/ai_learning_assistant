"""
Robust JSON Parser & Repair Utility
Safely extracts and parses JSON data emitted by LLMs even when surrounded
by preambles, trailing commas, single quotes, or minor syntax imperfections.
"""

import re
import json
from typing import Any, Optional

def extract_json_block(text: str) -> str:
    """Extracts the outermost JSON array or object from raw text."""
    if not text:
        return ""

    # Remove markdown code fences if present
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1)

    text = text.strip()

    # Find first '[' or '{'
    start_bracket = text.find('[')
    start_brace = text.find('{')

    if start_bracket == -1 and start_brace == -1:
        return text

    if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
        # Array starts first
        end_bracket = text.rfind(']')
        if end_bracket != -1 and end_bracket > start_bracket:
            return text[start_bracket:end_bracket + 1]
        return text[start_bracket:]
    else:
        # Object starts first
        end_brace = text.rfind('}')
        if end_brace != -1 and end_brace > start_brace:
            return text[start_brace:end_brace + 1]
        return text[start_brace:]

def repair_json_string(text: str) -> str:
    """Repairs common LLM formatting flaws in JSON strings."""
    # 1. Strip trailing commas before closing braces/brackets
    cleaned = re.sub(r',\s*([\]}])', r'\1', text)

    # 2. Fix unquoted boolean/null literals in edge cases
    cleaned = re.sub(r':\s*True\b', ': true', cleaned)
    cleaned = re.sub(r':\s*False\b', ': false', cleaned)
    cleaned = re.sub(r':\s*None\b', ': null', cleaned)

    # 3. If single quotes are used for keys/strings, try to convert safely
    if "'" in cleaned and '"' not in cleaned:
        cleaned = cleaned.replace("'", '"')

    # 4. Check balanced brackets/braces and close in proper LIFO order
    stack = []
    in_string = False
    escape = False

    for ch in cleaned:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch in '[{':
                stack.append(ch)
            elif ch == ']' and stack and stack[-1] == '[':
                stack.pop()
            elif ch == '}' and stack and stack[-1] == '{':
                stack.pop()

    # Close any unclosed delimiters in reverse order
    while stack:
        last = stack.pop()
        if last == '[':
            cleaned += ']'
        elif last == '{':
            cleaned += '}'

    return cleaned

def robust_json_loads(text: str, default: Any = None) -> Any:
    """
    Attempts to load JSON with multi-stage error recovery:
    1. Direct parse
    2. Block extraction
    3. Syntax repair (trailing commas, brackets)
    4. Default fallback on failure
    """
    if not text:
        return default

    # Stage 1: Direct parse
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Stage 2: Extract block
    extracted = extract_json_block(text)
    try:
        return json.loads(extracted)
    except Exception:
        pass

    # Stage 3: Repair common flaws
    repaired = repair_json_string(extracted)
    try:
        return json.loads(repaired)
    except Exception:
        pass

    return default
