"""Append-only index of historical runs. Pre-aggregates per-run / per-model / per-task means
so the dashboard can render trend charts from a single fetch."""

import json
from pathlib import Path


def update_index(results_dir: Path, run: dict) -> None:
    """Add this run's summary to results/index.json (creating if missing)."""
    index_path = results_dir / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text())
    else:
        index = {"version": 1, "runs": []}

    summary = _summarize_run(run)
    index["runs"] = [r for r in index["runs"] if r["timestamp"] != summary["timestamp"]]
    index["runs"].append(summary)
    index["runs"].sort(key=lambda r: r["timestamp"])

    index_path.write_text(json.dumps(index, indent=2))


def _summarize_run(run: dict) -> dict:
    # Derive a stable timestamp from finished_at: strip fractional seconds + tz, then compact.
    finished = run.get("finished_at", "")
    core = finished.split(".")[0].split("+")[0]  # "2026-05-01T10:00:00"
    ts = core.replace("-", "").replace(":", "") + "Z"  # "20260501T100000Z"

    model_ids = [m["id"] for m in run.get("models", [])]
    task_categories = [t["category"] for t in run.get("tasks", [])]

    task_model_means: dict[str, dict[str, float]] = {}
    model_means: dict[str, list[float]] = {mid: [] for mid in model_ids}

    for cat in task_categories:
        task_model_means[cat] = {}
        for mid in model_ids:
            cell = run.get("cells", {}).get(cat, {}).get(mid)
            if cell and "mean_score" in cell:
                task_model_means[cat][mid] = round(cell["mean_score"], 3)
                model_means[mid].append(cell["mean_score"])

    overall = {
        mid: round(sum(scores) / len(scores), 3) if scores else None
        for mid, scores in model_means.items()
    }

    return {
        "timestamp": ts,
        "finished_at": finished,
        "placeholder": bool(run.get("placeholder", False)),
        "overall_model_means": overall,
        "task_model_means": task_model_means,
    }
