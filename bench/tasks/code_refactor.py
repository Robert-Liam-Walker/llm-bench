"""Refactor. Model improves working code; judge grades on rubric."""

from .base import Prompt, Task

RUBRIC = (
    "Score 1.0 if the refactor: (a) preserves all observable behavior, (b) measurably reduces "
    "complexity or improves readability, (c) introduces no new bugs. Score 0.5 if it partially "
    "improves but introduces a regression or doesn't go far enough. Score 0.0 if it breaks "
    "behavior or makes things worse."
)

PROMPTS = [
    Prompt(
        id="nested_if",
        length_bucket="short",
        text=(
            "Refactor this for clarity. Behavior must be identical.\n\n"
            "```python\n"
            "def can_drive(age, has_license, suspended):\n"
            "    if age >= 16:\n"
            "        if has_license:\n"
            "            if not suspended:\n"
            "                return True\n"
            "            else:\n"
            "                return False\n"
            "        else:\n"
            "            return False\n"
            "    else:\n"
            "        return False\n"
            "```"
        ),
    ),
    Prompt(
        id="repeated_lookups",
        length_bucket="medium",
        text=(
            "Refactor this to eliminate repeated dictionary lookups and improve readability. "
            "Behavior must be identical.\n\n"
            "```python\n"
            "def grade(student):\n"
            "    if student['scores']['midterm'] > 90 and student['scores']['final'] > 90:\n"
            "        return 'A'\n"
            "    elif student['scores']['midterm'] > 80 and student['scores']['final'] > 80:\n"
            "        return 'B'\n"
            "    elif student['scores']['midterm'] > 70 and student['scores']['final'] > 70:\n"
            "        return 'C'\n"
            "    else:\n"
            "        return 'F'\n"
            "```"
        ),
    ),
    Prompt(
        id="god_function",
        length_bucket="long",
        text=(
            "Refactor this function. It does too many things. Split it into smaller, named "
            "functions; preserve behavior. Don't change the public signature.\n\n"
            "```python\n"
            "def process_order(order):\n"
            "    total = 0\n"
            "    for item in order['items']:\n"
            "        price = item['price'] * item['qty']\n"
            "        if item.get('discount'):\n"
            "            price *= (1 - item['discount'])\n"
            "        total += price\n"
            "    if order.get('coupon') == 'WELCOME10':\n"
            "        total *= 0.9\n"
            "    tax = total * 0.08\n"
            "    shipping = 5 if total < 50 else 0\n"
            "    final = total + tax + shipping\n"
            "    print(f'Order total: {final}')\n"
            "    return {'subtotal': total, 'tax': tax, 'shipping': shipping, 'total': final}\n"
            "```"
        ),
    ),
]

TASK = Task(category="code_refactor", scorer_kind="judge", rubric=RUBRIC, prompts=PROMPTS)
