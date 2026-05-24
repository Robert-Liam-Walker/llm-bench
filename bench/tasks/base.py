"""Task interface. Each category implements Task and registers its prompts."""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Prompt:
    id: str
    text: str
    reference: Any = None  # task-specific: unit tests, expected answer, schema, etc.
    length_bucket: str = "medium"  # short | medium | long


@dataclass
class Task:
    category: str
    scorer_kind: str  # "deterministic" | "judge"
    rubric: str  # used only if scorer_kind == "judge"
    prompts: list[Prompt] = field(default_factory=list)
    score_fn: Callable[[Prompt, str], float] | None = None  # used if deterministic
