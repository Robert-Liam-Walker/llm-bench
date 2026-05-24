"""Shared helpers for deterministic scorers — code extraction, JSON parsing."""

import json
import re
from typing import Any


def extract_code(response: str, lang: str = "python") -> str:
    """Pull code from a ```fence or return the raw response."""
    pattern = rf"```{lang}?\n?(.*?)```"
    match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else response.strip()


def extract_json(response: str) -> Any:
    """Find the first {...} or [...] object in the response and parse it."""
    for pat in (r"```json\s*(.*?)```", r"(\{.*\})", r"(\[.*\])"):
        match = re.search(pat, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    return None


def extract_final_number(response: str) -> float | None:
    """Pull the last number from the response (handles negatives, decimals)."""
    nums = re.findall(r"-?\d+(?:\.\d+)?", response.replace(",", ""))
    if not nums:
        return None
    try:
        return float(nums[-1])
    except ValueError:
        return None


def exec_safely(code: str, name: str):
    """Exec code in an isolated namespace and return the named binding (or None)."""
    ns: dict = {}
    try:
        exec(code, ns)
    except Exception:
        return None
    return ns.get(name)
