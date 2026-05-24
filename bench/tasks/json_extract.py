"""Structured extraction. Model returns JSON conforming to a schema; runner validates."""

from jsonschema import Draft7Validator

from ._util import extract_json
from .base import Prompt, Task

PROMPTS = [
    Prompt(
        id="contact_card",
        length_bucket="short",
        text=(
            "Extract a contact record from this text as JSON with exactly these fields: "
            '`{"name": str, "email": str, "phone": str}`. Return only the JSON.\n\n'
            "Hi, my name is Maria Sanchez. You can reach me at maria.sanchez@example.com "
            "or call 415-555-0142."
        ),
        reference={
            "schema": {
                "type": "object",
                "required": ["name", "email", "phone"],
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                },
            },
            "expected_substrings": {"name": "Maria", "email": "maria.sanchez@example.com", "phone": "415"},
        },
    ),
    Prompt(
        id="invoice",
        length_bucket="medium",
        text=(
            "Extract an invoice record from this text as JSON: "
            '`{"invoice_id": str, "total": number, "currency": str, "line_items": [{"description": str, "qty": int, "unit_price": number}]}`. '
            "Return only the JSON.\n\n"
            "INVOICE #INV-2026-0451\n"
            "  - 2x Widget @ $12.50 = $25.00\n"
            "  - 1x Sprocket @ $8.75 = $8.75\n"
            "TOTAL: USD 33.75"
        ),
        reference={
            "schema": {
                "type": "object",
                "required": ["invoice_id", "total", "currency", "line_items"],
                "properties": {
                    "invoice_id": {"type": "string"},
                    "total": {"type": "number"},
                    "currency": {"type": "string"},
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["description", "qty", "unit_price"],
                            "properties": {
                                "description": {"type": "string"},
                                "qty": {"type": "integer"},
                                "unit_price": {"type": "number"},
                            },
                        },
                    },
                },
            },
            "expected_values": {"total": 33.75, "currency": "USD", "n_items": 2},
        },
    ),
    Prompt(
        id="meeting_minutes",
        length_bucket="long",
        text=(
            "Extract structured meeting minutes from the text below. Schema: "
            '`{"date": "YYYY-MM-DD", "attendees": [str], "decisions": [str], "action_items": [{"owner": str, "task": str, "due": "YYYY-MM-DD"}]}`. '
            "Return only the JSON.\n\n"
            "Notes from March 15, 2026 standup. Present: Lin, Marcus, Priya, Tom.\n"
            "Decisions: ship v2.1 next Friday; freeze new features until launch.\n"
            "Action items:\n"
            "- Lin will draft the release notes by March 18.\n"
            "- Marcus owns the QA pass; deadline March 20."
        ),
        reference={
            "schema": {
                "type": "object",
                "required": ["date", "attendees", "decisions", "action_items"],
                "properties": {
                    "date": {"type": "string"},
                    "attendees": {"type": "array"},
                    "decisions": {"type": "array"},
                    "action_items": {"type": "array"},
                },
            },
            "expected_values": {"date": "2026-03-15", "n_attendees": 4, "n_actions": 2},
        },
    ),
]


def score(prompt: Prompt, response: str) -> float:
    parsed = extract_json(response)
    if parsed is None:
        return 0.0
    ref = prompt.reference
    validator = Draft7Validator(ref["schema"])
    if validator.iter_errors(parsed):
        errors = list(validator.iter_errors(parsed))
        if errors:
            return 0.0
    points = 1.0  # passed schema validation
    expected_subs = ref.get("expected_substrings", {})
    expected_vals = ref.get("expected_values", {})
    checks = len(expected_subs) + len(expected_vals)
    if checks == 0:
        return points
    passed_checks = 0
    for k, v in expected_subs.items():
        val = parsed.get(k, "")
        if isinstance(val, str) and v.lower() in val.lower():
            passed_checks += 1
    for k, v in expected_vals.items():
        if k.startswith("n_"):
            real_key = k[2:]
            arr = parsed.get(real_key, [])
            if isinstance(arr, list) and len(arr) == v:
                passed_checks += 1
        elif parsed.get(k) == v:
            passed_checks += 1
    return passed_checks / checks


TASK = Task(
    category="json_extract",
    scorer_kind="deterministic",
    rubric="",
    prompts=PROMPTS,
    score_fn=score,
)
