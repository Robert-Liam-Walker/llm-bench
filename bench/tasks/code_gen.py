"""Code generation. Model writes a function; we run unit tests against it."""

from ._util import exec_safely, extract_code
from .base import Prompt, Task

PROMPTS = [
    Prompt(
        id="palindrome",
        length_bucket="short",
        text=(
            "Write a Python function `is_palindrome(s: str) -> bool` that returns True if `s` "
            "reads the same forwards and backwards, ignoring case, spaces, and punctuation. "
            "Return only the function, no explanation."
        ),
        reference={
            "func": "is_palindrome",
            "tests": [
                ("racecar", True),
                ("hello", False),
                ("A man, a plan, a canal: Panama", True),
                ("", True),
                ("Was it a car or a cat I saw?", True),
                ("not a palindrome", False),
            ],
        },
    ),
    Prompt(
        id="flatten",
        length_bucket="medium",
        text=(
            "Write a Python function `flatten(nested)` that takes an arbitrarily nested list "
            "(lists may contain other lists to any depth) and returns a flat list of all the "
            "non-list elements, in left-to-right order. Return only the function."
        ),
        reference={
            "func": "flatten",
            "tests": [
                ([1, 2, 3], [1, 2, 3]),
                ([1, [2, 3]], [1, 2, 3]),
                ([[1, [2, [3, [4]]]], 5], [1, 2, 3, 4, 5]),
                ([], []),
                ([[], [[]], [[[]]]], []),
            ],
        },
    ),
    Prompt(
        id="merge_intervals",
        length_bucket="long",
        text=(
            "Write a Python function `merge_intervals(intervals)` where `intervals` is a list "
            "of `(start, end)` tuples with `start <= end`. Return a new list of merged intervals "
            "(any overlapping or touching intervals combined), sorted by start. Example: "
            "`[(1,3),(2,6),(8,10),(15,18)]` -> `[(1,6),(8,10),(15,18)]`. Touching counts as "
            "overlap: `[(1,4),(4,5)]` -> `[(1,5)]`. Return only the function."
        ),
        reference={
            "func": "merge_intervals",
            "tests": [
                ([(1, 3), (2, 6), (8, 10), (15, 18)], [(1, 6), (8, 10), (15, 18)]),
                ([(1, 4), (4, 5)], [(1, 5)]),
                ([], []),
                ([(1, 10)], [(1, 10)]),
                ([(5, 7), (1, 3)], [(1, 3), (5, 7)]),
            ],
        },
    ),
]


def score(prompt: Prompt, response: str) -> float:
    code = extract_code(response)
    ref = prompt.reference
    fn = exec_safely(code, ref["func"])
    if fn is None:
        return 0.0
    passed = 0
    for args, expected in ref["tests"]:
        try:
            actual = fn(args)
            if isinstance(expected, list) and isinstance(actual, list):
                if actual == expected:
                    passed += 1
            elif actual == expected:
                passed += 1
        except Exception:
            pass
    return passed / len(ref["tests"])


TASK = Task(
    category="code_gen",
    scorer_kind="deterministic",
    rubric="",
    prompts=PROMPTS,
    score_fn=score,
)
