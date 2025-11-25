import os
import requests
import json
from typing import Dict, Any
from .utils import extract_json_from_text

API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generate")

def build_prompt(description: str) -> str:
    """
    Builds a clear instruction prompt for the LLM.
    We ask the LLM to return strictly a JSON object with "notes" and "relationships".
    """
    return (
        "You are given a user's knowledge-graph description. "
        "Return ONLY valid JSON in this exact schema:\n\n"
        "{\n"
        '  "notes": [\n'
        "    {\n"
        '      "id": "<unique-id>",\n'
        '      "title": "<short title>",\n'
        '      "content": "<one-paragraph content>",\n'
        '      "color": "#hex",\n'
        '      "x": 100,\n'
        '      "y": 100\n'
        "    }\n"
        "  ],\n"
        '  "relationships": [\n'
        "    {\n"
        '      "fromId": "<note-id>",\n'
        '      "toId": "<note-id>",\n'
        '      "type": "supports|relates|contradicts",\n'
        '      "label": "<label text>"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Constraints:\n"
        "- Use at most 12 notes for initial output.\n"
        "- Provide numeric x,y values suitable for a 1400x800 board (between 0 and 1400/800).\n"
        "- IDs must be unique and safe to use as strings (no newlines).\n\n"
        "User description:\n"
        f"{description}\n\n"
        "Return only JSON. Do not include any commentary."
    )

def call_gemini(prompt: str) -> str:
    """
    Calls the configured LLM endpoint. Returns text response (raw).
    NOTE: This implementation uses the Google Generative Language REST endpoint format.
    If you use a different provider, replace this function accordingly.
    """
    if not API_KEY:
        raise EnvironmentError("GEMINI_API_KEY not set in environment.")

    # Example request body for Google's Generative API (approximate)
    body = {
        "prompt": {
            "text": prompt
        },
        # Optional parameters; adjust as needed
        "temperature": 0.2,
        "maxOutputTokens": 1024
    }
    params = {"key": API_KEY}
    headers = {"Content-Type": "application/json"}
    resp = requests.post(API_URL, params=params, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # The exact path to the generated text depends on provider response format.
    # For Google Generative API (v1beta2), the field is often something like:
    # data['candidates'][0]['output'] or data['results'][0]['candidates'][0]['content']
    # We'll attempt common possibilities, then fallback to raw text.
    # Inspect the data in logs if needed.
    if isinstance(data, dict):
        # Common patterns:
        for key in ("candidates", "results", "output", "text"):
            if key in data and isinstance(data[key], list) and data[key]:
                # candidates list maybe contain {'content': '...'}
                first = data[key][0]
                if isinstance(first, dict):
                    # try some keys
                    for sub in ("content", "output", "text"):
                        if sub in first:
                            return first[sub]
                elif isinstance(first, str):
                    return first
        # Fallback: try to join any text-like fields
        for v in data.values():
            if isinstance(v, str):
                return v
    # If we get here, return the raw JSON as string
    return json.dumps(data)

def generate_notes_and_relationships(description: str) -> Dict[str, Any]:
    """
    High-level helper: build prompt, call Gemini, parse JSON, return dict with notes and relationships.
    """
    prompt = build_prompt(description)
    raw = call_gemini(prompt)

    # Attempt to parse JSON from raw
    try:
        parsed = extract_json_from_text(raw)
    except Exception as e:
        # Raise a helpful error containing snippet for debugging
        raise ValueError(f"LLM did not return parseable JSON. Raw output excerpt: {raw[:1000]}") from e

    # Basic structure validation
    if not isinstance(parsed, dict) or "notes" not in parsed or "relationships" not in parsed:
        raise ValueError(f"LLM JSON missing required keys 'notes'/'relationships'. Parsed: {parsed}")

    return parsed
