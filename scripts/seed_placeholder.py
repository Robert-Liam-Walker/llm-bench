"""Write a placeholder results/latest.json so the dashboard has something to render
before the real eval has been run. Plausible numbers, clearly marked.

Usage:  python scripts/seed_placeholder.py
"""

import datetime
import json
import os
import random
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench import MODELS
from bench.tasks import ALL_TASKS

random.seed(42)

# Plausible baselines per model — Opus best, Haiku weakest, but not by a huge amount.
# Reflects real-world experience: cheap models are surprisingly close on simple tasks.
TIER_BASELINE = {
    "claude-opus-4-7":          {"mean": 0.86, "stddev": 0.10},
    "claude-sonnet-4-6":        {"mean": 0.80, "stddev": 0.12},
    "claude-haiku-4-5-20251001":{"mean": 0.66, "stddev": 0.18},
}

# Tasks where cheaper models tend to fall off harder.
HARD_FOR_HAIKU = {"code_refactor", "science", "summarize", "edge_cases", "logic"}

# Token-count seeds per length bucket (input × output).
TOK = {
    "short":  {"in": (180, 240),  "out": (220, 380)},
    "medium": {"in": (320, 480),  "out": (420, 680)},
    "long":   {"in": (520, 780),  "out": (740, 1200)},
}


def gen_score(model_id: str, task_category: str) -> float:
    base = TIER_BASELINE[model_id]
    penalty = 0.15 if (model_id == "claude-haiku-4-5-20251001" and task_category in HARD_FOR_HAIKU) else 0.0
    score = random.gauss(base["mean"] - penalty, base["stddev"])
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
                    "judge_reasoning": (
                        "Placeholder reasoning."
                        if task.scorer_kind == "judge" else ""
                    ),
                })
            cells[task.category][model["id"]] = {
                "prompts": per_prompt,
                "mean_score": round(sum(p["score"] for p in per_prompt) / len(per_prompt), 3),
                "total_input_tokens": sum(p["input_tokens"] for p in per_prompt),
                "total_output_tokens": sum(p["output_tokens"] for p in per_prompt),
            }

    out = {
        "version": 1,
        "placeholder": True,
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "dry_run": False,
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
