"""Orchestrator. Iterates (task × prompt × model), aggregates, writes results JSON.

Skips any model whose provider's API key isn't set, so a partial-key install still
produces a partial leaderboard rather than crashing.
"""

import datetime
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from . import MODELS
from .index import update_index
from .judge import Judge
from .models import Client, ProviderUnavailable
from .tasks import ALL_TASKS
from .tasks.base import Task


@dataclass
class CellResult:
    score: float
    response: str
    input_tokens: int
    output_tokens: int
    judge_reasoning: str = ""


def run(
    task_filter: list[str] | None = None,
    model_filter: list[str] | None = None,
    dry_run: bool = False,
    out_dir: str = "results",
) -> dict:
    client = Client()
    judge = Judge(client)

    models = [m for m in MODELS if (model_filter is None or m["id"] in model_filter)]
    tasks = [t for t in ALL_TASKS if (task_filter is None or t.category in task_filter)]

    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cells: dict[str, dict[str, dict]] = {}
    skipped_providers: set[str] = set()
    done = 0

    for task in tasks:
        cells[task.category] = {}
        for model in models:
            per_prompt: list[dict] = []
            skipped = False
            for prompt in task.prompts:
                done += 1
                _log(f"[{done}] {task.category}/{prompt.id} on {model['label']}...")
                if dry_run:
                    per_prompt.append({"prompt_id": prompt.id, "length": prompt.length_bucket,
                                       "score": None, "skipped": True})
                    continue
                try:
                    result = _run_one(client, judge, task, prompt, model)
                except ProviderUnavailable as e:
                    skipped = True
                    skipped_providers.add(model["provider"])
                    _log(f"   skipping {model['provider']}: {e}")
                    break
                per_prompt.append({
                    "prompt_id": prompt.id,
                    "length": prompt.length_bucket,
                    "score": result.score,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "response": result.response,
                    "judge_reasoning": result.judge_reasoning,
                })
            if skipped or not per_prompt:
                continue
            cells[task.category][model["id"]] = {
                "prompts": per_prompt,
                "mean_score": _mean([p["score"] for p in per_prompt if p.get("score") is not None]),
                "total_input_tokens": sum(p.get("input_tokens", 0) for p in per_prompt),
                "total_output_tokens": sum(p.get("output_tokens", 0) for p in per_prompt),
            }

    finished = datetime.datetime.now(datetime.timezone.utc).isoformat()

    out = {
        "version": 1,
        "started_at": started,
        "finished_at": finished,
        "dry_run": dry_run,
        "skipped_providers": sorted(skipped_providers),
        "models": models,
        "tasks": [{"category": t.category, "scorer_kind": t.scorer_kind, "n_prompts": len(t.prompts)} for t in tasks],
        "cells": cells,
    }

    if not dry_run:
        _write_results(out, out_dir)
    return out


def _run_one(client: Client, judge: Judge, task: Task, prompt, model_spec: dict) -> CellResult:
    completion = client.complete(model_spec, prompt.text)
    judge_reasoning = ""
    if task.scorer_kind == "deterministic":
        score = task.score_fn(prompt, completion.text)
    else:
        try:
            score, judge_reasoning = judge.grade(prompt.text, completion.text, task.rubric)
        except ProviderUnavailable as e:
            score = 0.0
            judge_reasoning = f"judge unavailable ({e}) — score recorded as 0; rerun with ANTHROPIC_API_KEY set"
    return CellResult(
        score=score,
        response=completion.text,
        input_tokens=completion.input_tokens,
        output_tokens=completion.output_tokens,
        judge_reasoning=judge_reasoning,
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _write_results(out: dict, out_dir: str):
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = path / f"{ts}.json"
    fname.write_text(json.dumps(out, indent=2))
    latest = path / "latest.json"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    os.symlink(fname.name, latest)
    update_index(path, out)
    _log(f"wrote {fname}, updated latest.json + index.json")


def _log(msg: str):
    print(msg, file=sys.stderr, flush=True)
