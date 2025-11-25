import re
import json
from typing import Any

def extract_json_from_text(text: str):
    """
    Try to find a JSON object or array inside a free text response.
    Returns parsed object or raises ValueError if none found.
    """
    # A naive approach: find first "{" that starts JSON and the matching closing "}"
    # Attempt to find both object and array
    text = text.strip()
    # First look for a JSON block that starts with '[' or '{'
    start = None
    for i, ch in enumerate(text):
        if ch in ["{", "["]:
            start = i
            break
    if start is None:
        raise ValueError("No JSON object found in text.")
    # Try to parse progressively larger slices until valid JSON found or exhausted
    for end in range(len(text), start, -1):
        try:
            candidate = text[start:end]
            parsed = json.loads(candidate)
            return parsed
        except Exception:
            continue
    # fallback: try to search with regex for {...}
    json_matches = re.findall(r'(\{(?:[^{}]|(?1))*\})', text)
    if json_matches:
        for jm in json_matches:
            try:
                return json.loads(jm)
            except Exception:
                continue
    raise ValueError("Could not extract JSON from text.")
