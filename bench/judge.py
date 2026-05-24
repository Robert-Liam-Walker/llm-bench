"""LLM-as-judge. Uses Opus to grade subjective task outputs against a rubric."""

import json
import re

from .models import Client

JUDGE_MODEL = "claude-opus-4-7"

JUDGE_PROMPT = """You are grading an LLM's response against a rubric. Be strict but fair.

PROMPT GIVEN TO THE MODEL:
{prompt}

MODEL'S RESPONSE:
{response}

RUBRIC:
{rubric}

Return ONLY a JSON object on a single line, no markdown fences, in this exact shape:
{{"score": <number between 0.0 and 1.0>, "reasoning": "<one-sentence justification>"}}
"""


class Judge:
    def __init__(self, client: Client, model: str = JUDGE_MODEL):
        self.client = client
        self.model = model

    def grade(self, prompt: str, response: str, rubric: str) -> tuple[float, str]:
        judge_input = JUDGE_PROMPT.format(prompt=prompt, response=response, rubric=rubric)
        completion = self.client.complete(self.model, judge_input, max_tokens=400)
        match = re.search(r"\{.*\}", completion.text, re.DOTALL)
        if not match:
            return 0.0, f"judge returned no JSON: {completion.text[:100]}"
        try:
            parsed = json.loads(match.group(0))
            score = float(parsed["score"])
            return max(0.0, min(1.0, score)), str(parsed.get("reasoning", ""))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return 0.0, f"judge parse error: {e}"
