"""Logic puzzles. Single correct answer; exact match."""

import re

from .base import Prompt, Task

PROMPTS = [
    Prompt(
        id="three_doors",
        length_bucket="short",
        text=(
            "You are in a room with three closed doors. Behind exactly one door is a prize. "
            "Each door has a sign:\n"
            "Door A says: 'The prize is behind door B.'\n"
            "Door B says: 'The prize is not behind this door.'\n"
            "Door C says: 'The prize is not behind door A.'\n"
            "Exactly one of the three signs is true. Which door has the prize? "
            "End your response with `Answer: <A|B|C>`."
        ),
        reference={"answer": "A"},
    ),
    Prompt(
        id="knights_knaves",
        length_bucket="medium",
        text=(
            "On the island of knights and knaves, knights always tell the truth and knaves always lie. "
            "You meet three islanders, X, Y, and Z.\n"
            "X says: 'Y is a knave.'\n"
            "Y says: 'X and Z are of the same type.'\n"
            "Z says: 'I am a knight.'\n"
            "Determine the type of each. End with `Answer: X=<knight|knave>, Y=<...>, Z=<...>`."
        ),
        reference={"answer_pattern": r"x\s*=\s*knight.*y\s*=\s*knave.*z\s*=\s*knave"},
    ),
    Prompt(
        id="seating_constraints",
        length_bucket="long",
        text=(
            "Five colleagues — Ava, Ben, Cy, Dee, and Eli — sit in a row of 5 chairs numbered 1 "
            "(leftmost) to 5 (rightmost). Constraints:\n"
            "1. Ava sits at one of the ends.\n"
            "2. Ben sits immediately to the right of Cy.\n"
            "3. Dee is in seat 3.\n"
            "4. Eli does not sit next to Ben.\n"
            "5. Cy is not in seat 1.\n"
            "Who sits in seat 5? End your response with `Answer: <name>`."
        ),
        reference={"answer": "Ben"},
    ),
]


def score(prompt: Prompt, response: str) -> float:
    text = response.lower()
    ref = prompt.reference
    if "answer" in ref:
        expected = ref["answer"].lower()
        match = re.search(r"answer\s*[:=]?\s*([a-z]+)", text)
        if match and match.group(1) == expected:
            return 1.0
        return 0.0
    if "answer_pattern" in ref:
        return 1.0 if re.search(ref["answer_pattern"], text, re.IGNORECASE) else 0.0
    return 0.0


TASK = Task(
    category="logic",
    scorer_kind="deterministic",
    rubric="",
    prompts=PROMPTS,
    score_fn=score,
)
