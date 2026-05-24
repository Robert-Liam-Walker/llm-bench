"""Write a placeholder results/latest.json so the dashboard has something to render
before the real eval has been run. Plausible numbers, clearly marked.

Usage:  python scripts/seed_placeholder.py
"""

import datetime
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench import MODELS
from bench.tasks import ALL_TASKS

random.seed(42)

# Plausible per-model baselines. Reflects rough public benchmark intuitions:
# Opus > Sonnet > Llama 70B ≈ DeepSeek R1 ≳ Haiku > Llama 8B.
TIER_BASELINE = {
    "claude-opus-4-7":                {"mean": 0.86, "stddev": 0.10},
    "claude-sonnet-4-6":              {"mean": 0.80, "stddev": 0.12},
    "claude-haiku-4-5-20251001":      {"mean": 0.66, "stddev": 0.18},
    "llama-3.3-70b-versatile":        {"mean": 0.74, "stddev": 0.14},
    "deepseek-r1-distill-llama-70b":  {"mean": 0.76, "stddev": 0.16},
    "llama-3.1-8b-instant":           {"mean": 0.52, "stddev": 0.20},
}

HARD_FOR_SMALL = {"code_refactor", "science", "summarize", "edge_cases", "logic"}
SMALL_MODELS = {"claude-haiku-4-5-20251001", "llama-3.1-8b-instant"}
REASONING_BONUS = {"math", "logic", "code_debug"}
REASONING_MODELS = {"deepseek-r1-distill-llama-70b"}

TOK = {
    "short":  {"in": (180, 240),  "out": (220, 380)},
    "medium": {"in": (320, 480),  "out": (420, 680)},
    "long":   {"in": (520, 780),  "out": (740, 1200)},
}


def gen_score(model_id: str, task_category: str) -> float:
    base = TIER_BASELINE[model_id]
    penalty = 0.15 if (model_id in SMALL_MODELS and task_category in HARD_FOR_SMALL) else 0.0
    bonus = 0.08 if (model_id in REASONING_MODELS and task_category in REASONING_BONUS) else 0.0
    score = random.gauss(base["mean"] - penalty + bonus, base["stddev"])
    return round(max(0.0, min(1.0, score)), 2)


def gen_tokens(length: str) -> tuple[int, int]:
    bucket = TOK[length]
    return random.randint(*bucket["in"]), random.randint(*bucket["out"])


def main():
    cells = {}
    for task in ALL_TASKS:
        cells[task.category] = {}
        for model in MODELS:
            per_prompt = []
            for p in task.prompts:
                score = gen_score(model["id"], task.category)
                in_tok, out_tok = gen_tokens(p.length_bucket)
                per_prompt.append({
                    "prompt_id": p.id,
                    "length": p.length_bucket,
                    "score": score,
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "response": "(placeholder response — run `python -m bench` to populate.)",
                    "judge_reasoning": "Placeholder reasoning." if task.scorer_kind == "judge" else "",
                })
            cells[task.category][model["id"]] = {
                "prompts": per_prompt,
                "mean_score": round(sum(p["score"] for p in per_prompt) / len(per_prompt), 3),
                "total_input_tokens": sum(p["input_tokens"] for p in per_prompt),
                "total_output_tokens": sum(p["output_tokens"] for p in per_prompt),
            }

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out = {
        "version": 1,
        "placeholder": True,
        "started_at": now,
        "finished_at": now,
        "dry_run": False,
        "skipped_providers": [],
        "models": MODELS,
        "tasks": [
            {"category": t.category, "scorer_kind": t.scorer_kind, "n_prompts": len(t.prompts)}
            for t in ALL_TASKS
        ],
        "cells": cells,
    }

    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    target = out_dir / "placeholder.json"
    target.write_text(json.dumps(out, indent=2))
    latest = out_dir / "latest.json"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    os.symlink("placeholder.json", latest)
    print(f"wrote {target} and latest.json -> placeholder.json")


if __name__ == "__main__":
    main()
