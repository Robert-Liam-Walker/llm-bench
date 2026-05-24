"""Orchestrator. Iterates (task × prompt × model), aggregates, writes results JSON."""

import datetime
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from . import MODELS
from .judge import Judge
from .models import Client
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

    started = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
    cells: dict[str, dict[str, list[dict]]] = {}

    total = len(tasks) * sum(len(t.prompts) for t in tasks) * len(models) // max(len(tasks), 1)
    done = 0

    for task in tasks:
        cells[task.category] = {}
        for model in models:
            per_prompt: list[dict] = []
            for prompt in task.prompts:
                done += 1
                _log(f"[{done}] {task.category}/{prompt.id} on {model['label']}...")
                if dry_run:
                    per_prompt.append({"prompt_id": prompt.id, "length": prompt.length_bucket,
                                       "score": None, "skipped": True})
                    continue
                result = _run_one(client, judge, task, prompt, model["id"])
                per_prompt.append({
                    "prompt_id": prompt.id,
                    "length": prompt.length_bucket,
                    "score": result.score,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "response": result.response,
                    "judge_reasoning": result.judge_reasoning,
                })
            cells[task.category][model["id"]] = {
                "prompts": per_prompt,
                "mean_score": _mean([p["score"] for p in per_prompt if p.get("score") is not None]),
                "total_input_tokens": sum(p.get("input_tokens", 0) for p in per_prompt),
                "total_output_tokens": sum(p.get("output_tokens", 0) for p in per_prompt),
            }

    finished = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"

    out = {
        "version": 1,
        "started_at": started,
        "finished_at": finished,
        "dry_run": dry_run,
        "models": models,
        "tasks": [{"category": t.category, "scorer_kind": t.scorer_kind, "n_prompts": len(t.prompts)} for t in tasks],
        "cells": cells,
    }

    if not dry_run:
        _write_results(out, out_dir)
    return out


def _run_one(client: Client, judge: Judge, task: Task, prompt, model_id: str) -> CellResult:
    completion = client.complete(model_id, prompt.text)
    judge_reasoning = ""
    if task.scorer_kind == "deterministic":
        score = task.score_fn(prompt, completion.text)
    else:
        score, judge_reasoning = judge.grade(prompt.text, completion.text, task.rubric)
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
    # Use a relative symlink so it works when served behind nginx
    os.symlink(fname.name, latest)
    _log(f"wrote {fname} and updated latest.json")


def _log(msg: str):
    print(msg, file=sys.stderr, flush=True)
