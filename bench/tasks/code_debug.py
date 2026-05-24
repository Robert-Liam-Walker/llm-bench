"""Debugging. Model is shown buggy code + symptom; judge grades the diagnosis + fix."""

from .base import Prompt, Task

RUBRIC = (
    "Score 1.0 if the model correctly identifies the bug AND proposes a fix that would actually work. "
    "Score 0.5 if it identifies the bug but the fix is wrong or incomplete. "
    "Score 0.0 if it misdiagnoses or hand-waves."
)

PROMPTS = [
    Prompt(
        id="off_by_one",
        length_bucket="short",
        text=(
            "This Python function should return the average of a list. It crashes on `[5]`. "
            "Identify the bug and fix it.\n\n"
            "```python\n"
            "def average(nums):\n"
            "    total = 0\n"
            "    for i in range(len(nums) - 1):\n"
            "        total += nums[i]\n"
            "    return total / len(nums)\n"
            "```"
        ),
    ),
    Prompt(
        id="mutate_during_iter",
        length_bucket="medium",
        text=(
            "Users report that this function returns the wrong items, sometimes skipping valid ones. "
            "Identify the root cause and provide a corrected version.\n\n"
            "```python\n"
            "def remove_negatives(numbers):\n"
            "    for n in numbers:\n"
            "        if n < 0:\n"
            "            numbers.remove(n)\n"
            "    return numbers\n"
            "```"
        ),
    ),
    Prompt(
        id="dict_default_mutable",
        length_bucket="long",
        text=(
            "A user reports that every call to `add_item` is mutating the same list. "
            "What's wrong, why does it happen, and how should it be fixed?\n\n"
            "```python\n"
            "class Cart:\n"
            "    def __init__(self, items=[]):\n"
            "        self.items = items\n"
            "    def add(self, x):\n"
            "        self.items.append(x)\n"
            "        return self.items\n"
            "\n"
            "def add_item(cart=Cart(), item=None):\n"
            "    return cart.add(item)\n"
            "```"
        ),
    ),
]

TASK = Task(category="code_debug", scorer_kind="judge", rubric=RUBRIC, prompts=PROMPTS)
