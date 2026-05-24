"""Write placeholder results/*.json so the dashboard renders the grid + drift + trend
views before any real run has happened. Each historical placeholder file is clearly
flagged with `placeholder: true`.

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
from bench.index import update_index
from bench.tasks import ALL_TASKS

# Plausible per-model baselines. Roughly: Opus > Sonnet > DeepSeek ≈ Llama 70B > Haiku > Llama 8B.
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

# Months to seed (UTC, 1st of each).
SEED_MONTHS = [
    datetime.datetime(2026, 2, 1, 10, 0, tzinfo=datetime.timezone.utc),
    datetime.datetime(2026, 3, 1, 10, 0, tzinfo=datetime.timezone.utc),
    datetime.datetime(2026, 4, 1, 10, 0, tzinfo=datetime.timezone.utc),
    datetime.datetime(2026, 5, 1, 10, 0, tzinfo=datetime.timezone.utc),
]


def gen_score(rng: random.Random, model_id: str, task_category: str) -> float:
    base = TIER_BASELINE[model_id]
    penalty = 0.15 if (model_id in SMALL_MODELS and task_category in HARD_FOR_SMALL) else 0.0
    bonus = 0.08 if (model_id in REASONING_MODELS and task_category in REASONING_BONUS) else 0.0
    score = rng.gauss(base["mean"] - penalty + bonus, base["stddev"])
    return round(max(0.0, min(1.0, score)), 2)


def gen_tokens(rng: random.Random, length: str) -> tuple[int, int]:
    bucket = TOK[length]
    return rng.randint(*bucket["in"]), rng.randint(*bucket["out"])


def build_run(when: datetime.datetime) -> dict:
    rng = random.Random(int(when.timestamp()))
    cells = {}
    for task in ALL_TASKS:
        cells[task.category] = {}
        for model in MODELS:
            per_prompt = []
            for p in task.prompts:
                score = gen_score(rng, model["id"], task.category)
                in_tok, out_tok = gen_tokens(rng, p.length_bucket)
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
    iso = when.isoformat()
    return {
        "version": 1,
        "placeholder": True,
        "started_at": iso,
        "finished_at": iso,
        "dry_run": False,
        "skipped_providers": [],
        "models": MODELS,
        "tasks": [
            {"category": t.category, "scorer_kind": t.scorer_kind, "n_prompts": len(t.prompts)}
            for t in ALL_TASKS
        ],
        "cells": cells,
    }


def main():
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)

    # Remove any previous placeholder files (anything matching the seed months) + index
    for f in out_dir.glob("*.json"):
        if f.name == "index.json":
            f.unlink()
            continue
        try:
            data = json.loads(f.read_text())
            if data.get("placeholder"):
                f.unlink()
        except Exception:
            pass

    last_file = None
    for when in SEED_MONTHS:
        run = build_run(when)
        ts = when.strftime("%Y%m%dT%H%M%SZ")
        fname = out_dir / f"{ts}.json"
        fname.write_text(json.dumps(run, indent=2))
        update_index(out_dir, run)
        last_file = fname

    latest = out_dir / "latest.json"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    os.symlink(last_file.name, latest)
    print(f"wrote {len(SEED_MONTHS)} placeholder runs, index.json, latest -> {last_file.name}")


if __name__ == "__main__":
    main()
