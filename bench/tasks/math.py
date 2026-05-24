"""Math word problems. Score is exact match on the final numeric answer."""

from ._util import extract_final_number
from .base import Prompt, Task

PROMPTS = [
    Prompt(
        id="bookstore",
        length_bucket="short",
        text=(
            "A bookstore had 240 books. They sold 35% of them on Monday and 28 more on Tuesday. "
            "How many books are left? Show work and end with `Final answer: <number>`."
        ),
        reference={"answer": 128.0},
    ),
    Prompt(
        id="train_meet",
        length_bucket="medium",
        text=(
            "Two trains start 360 miles apart and head toward each other. The first travels at "
            "60 mph, the second at 80 mph. How many hours until they meet? "
            "Show work and end with `Final answer: <number>`."
        ),
        reference={"answer": 2.571429},  # 360/140 ≈ 2.571
    ),
    Prompt(
        id="compound_with_deposits",
        length_bucket="long",
        text=(
            "An account starts with $1000 and earns 5% annual interest, compounded yearly. "
            "At the end of each year (after interest), $200 is deposited. What is the account "
            "balance at the end of year 3 (after the year-3 deposit)? Show your work and end "
            "with `Final answer: <number>`. Round to the nearest cent."
        ),
        # Year 1: 1000*1.05 + 200 = 1250
        # Year 2: 1250*1.05 + 200 = 1512.50
        # Year 3: 1512.50*1.05 + 200 = 1788.125 ≈ 1788.13
        reference={"answer": 1788.13},
    ),
]


def score(prompt: Prompt, response: str) -> float:
    actual = extract_final_number(response)
    if actual is None:
        return 0.0
    expected = prompt.reference["answer"]
    tolerance = max(abs(expected) * 0.001, 0.01)
    return 1.0 if abs(actual - expected) <= tolerance else 0.0


TASK = Task(
    category="math",
    scorer_kind="deterministic",
    rubric="",
    prompts=PROMPTS,
    score_fn=score,
)
