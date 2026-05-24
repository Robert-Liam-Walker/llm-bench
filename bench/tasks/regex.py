"""Regex. Model writes a pattern; runner applies it to held-out match/non-match examples."""

import re

from ._util import extract_code
from .base import Prompt, Task

PROMPTS = [
    Prompt(
        id="us_zip",
        length_bucket="short",
        text=(
            "Write a Python regex (just the pattern, as a string) that matches a US ZIP code: "
            "5 digits, optionally followed by a hyphen and 4 more digits. The pattern must match "
            "the WHOLE string (use anchors). Return only the pattern wrapped in triple backticks."
        ),
        reference={
            "match": ["12345", "94110", "12345-6789", "00000-0000"],
            "no_match": ["1234", "123456", "12345-678", "abcde", "12345 6789", ""],
        },
    ),
    Prompt(
        id="iso_date",
        length_bucket="medium",
        text=(
            "Write a Python regex that matches an ISO 8601 calendar date in `YYYY-MM-DD` form. "
            "Month is 01-12, day is 01-31 (don't worry about month-specific day limits or leap years). "
            "Match the whole string with anchors. Return only the pattern in triple backticks."
        ),
        reference={
            "match": ["2026-05-23", "1999-12-31", "2000-01-01", "2026-02-29"],
            "no_match": ["2026-5-23", "26-05-23", "2026/05/23", "2026-13-01", "2026-00-15", "abc"],
        },
    ),
    Prompt(
        id="semver",
        length_bucket="long",
        text=(
            "Write a Python regex that matches a SemVer 2.0 version: `MAJOR.MINOR.PATCH` of "
            "non-negative integers without leading zeros (except `0` itself), optionally followed "
            "by `-PRERELEASE` (alphanumeric/dot-separated identifiers, no leading zeros on numeric "
            "identifiers). No build metadata. Match the whole string. Return only the pattern."
        ),
        reference={
            "match": ["1.0.0", "0.0.0", "10.20.30", "1.0.0-alpha", "1.0.0-alpha.1", "1.2.3-rc.1"],
            "no_match": ["1.0", "1.0.0.0", "01.0.0", "1.0.0-", "1.0.0-01", "v1.0.0", ""],
        },
    ),
]


def score(prompt: Prompt, response: str) -> float:
    pattern = extract_code(response).strip().strip("'").strip('"')
    if not pattern:
        return 0.0
    try:
        compiled = re.compile(pattern)
    except re.error:
        return 0.0
    ref = prompt.reference
    correct = sum(1 for s in ref["match"] if compiled.fullmatch(s))
    correct += sum(1 for s in ref["no_match"] if not compiled.fullmatch(s))
    total = len(ref["match"]) + len(ref["no_match"])
    return correct / total


TASK = Task(
    category="regex",
    scorer_kind="deterministic",
    rubric="",
    prompts=PROMPTS,
    score_fn=score,
)
