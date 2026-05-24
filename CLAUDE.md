# llm-bench — Agent Notes

Empirical benchmark of Claude model tiers (Opus 4.7, Sonnet 4.6, Haiku 4.5) across 12 task categories. Public dashboard at the EC2 URL. The product is the **measurement infrastructure**, not a new model.

## What this is (and isn't)

- **Is:** a reproducible eval harness + a static dashboard showing how each Claude tier performs on each task type, with per-task scoring methodology you can drill into.
- **Isn't:** a chatbot, a wrapper, or "AI that does X." The LLM is the *subject* of measurement, not the engine.

The point: when does Opus pay off vs Haiku (10× cheaper)? Nobody publishes good per-task answers; this does.

## Layout

```
bench/
  models.py            # Anthropic client adapter — one method: complete(model, prompt) -> str
  judge.py             # LLM-as-judge: uses Opus to grade subjective outputs against a rubric
  runner.py            # Orchestrator: iterates (model × task × prompt), aggregates, writes results/<ts>.json
  cli.py               # `python -m bench` entry
  tasks/
    base.py            # Task base class — .prompts: list, .score(prompt, response) -> float
    <category>.py      # One module per task category (12 of them)
results/
  <iso-ts>.json        # One file per run; latest.json symlinks to most recent
  schema.md            # Documents the result file format
dashboard/
  index.html           # Static, fetches /results/latest.json, renders 12×3 grid
  main.js
  style.css
scripts/
  run-eval.sh          # cron entry on EC2
```

## Running locally

```bash
export ANTHROPIC_API_KEY=sk-ant-...
pip install -r requirements.txt
python -m bench                    # runs all 12 task categories × 3 models
python -m bench --task code_gen    # single category
python -m bench --dry-run          # no API calls; print plan
```

Results land in `results/<timestamp>.json`. Open `dashboard/index.html` in a browser pointing at it.

## Scoring rubric (per task type)

| Category | Scorer | Why |
|---|---|---|
| code_gen | pytest unit tests against generated code | objective, ungameable |
| code_debug | LLM-judge (rubric: bug correctly identified + fix runs) | semi-objective |
| code_refactor | LLM-judge (rubric: behavior preserved, complexity down) | subjective |
| sql | execute against SQLite, compare result set | objective |
| regex | apply to held-out match/non-match examples | objective |
| json_extract | jsonschema validate + field accuracy | objective |
| math | extract final number, exact match | objective |
| science | LLM-judge (rubric: each claim correct) | partial |
| summarize | LLM-judge (rubric: coverage + accuracy) | subjective |
| email | LLM-judge (rubric: tone + completeness) | subjective |
| logic | exact match on final answer | objective |
| edge_cases | LLM-judge (does model appropriately hedge/refuse?) | rubric |

Half the categories are deterministic (no judge), which makes the leaderboard credible. The judge is Opus, scoring on a 0–1 scale per rubric — disclosed in the dashboard.

## Production

- **URL:** TBD (EC2 t3.micro)
- **SSH:** `ssh -i ~/.ssh/llm-bench-key.pem ubuntu@<ip>`
- **Cron:** runs full suite weekly (cost: ~$1/run × 4 = $4/mo at current pricing)
- **Web:** nginx serves `dashboard/` and `results/latest.json` as static files
- **Secrets:** `ANTHROPIC_API_KEY` in `/etc/llm-bench.env`, loaded by systemd

## Gotchas (carry over from panini deployment)

- Ubuntu MySQL root → use `sudo mysql`, not `mysql -u root` (N/A here since no DB, but heads up if you add one)
- Don't wrap `mysql < dump.sql` (or any stdin-redirected command) in a pipe under `set -e` — pipeline exit masks errors, drops/destructive ops continue thinking things succeeded
- `mysqldump` as app user needs `--no-tablespaces`

## Not done yet (intentional v1 scope)

- 3 prompts per task, not 10. Framework supports any count; expanding is `tasks/*.py` content work.
- No fine-tuned model in the leaderboard. Add a column when there's one to add.
- No CI on the repo. Eval runs are scheduled on EC2, not in GitHub Actions.
- Only Anthropic. Add OpenAI/Google/OpenRouter adapters in `bench/models.py` when keys are available.
