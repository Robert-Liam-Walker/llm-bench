"""Task registry. Import all 12 categories so they're available by name."""

from . import (
    code_debug,
    code_gen,
    code_refactor,
    edge_cases,
    email,
    json_extract,
    logic,
    math,
    regex,
    science,
    sql,
    summarize,
)
from .base import Prompt, Task

ALL_TASKS: list[Task] = [
    code_gen.TASK,
    code_debug.TASK,
    code_refactor.TASK,
    sql.TASK,
    regex.TASK,
    json_extract.TASK,
    math.TASK,
    science.TASK,
    summarize.TASK,
    email.TASK,
    logic.TASK,
    edge_cases.TASK,
]
