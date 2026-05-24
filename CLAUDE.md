# llm-bench — Agent Notes

Empirical benchmark of Claude model tiers (Opus 4.7, Sonnet 4.6, Haiku 4.5) across 12 task categories. Public dashboard at the EC2 URL. The product is the **measurement infrastructure**, not a new model.

## What this is (and isn't)

- **Is:** a reproducible eval harness + a static dashboard showing how 6 LLMs (3 Claude tiers + 3 Groq-hosted open-weight models) perform on each task type. Runs monthly so you can see drift over time — does a hosted model silently get worse after the provider releases a newer tier? The drift panel + per-task trend charts make any persistent dip immediately visible.
- **Isn't:** a chatbot, a wrapper, or "AI that does X." The LLM is the *subject* of measurement, not the engine.

The point: when does Opus pay off vs Haiku (10× cheaper)? When does a free open-weight model close the gap? Nobody publishes good per-task answers; this does.

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

- **URL:** http://44.195.85.130/
- **EC2:** `i-007bf70075b46a095`, t3.micro, us-east-1, account `056195341948`. Name tag `llm-bench`, SG `llm-bench-sg` (22 + 80), key pair `llm-bench-key`.
- **SSH:** `ssh -i ~/.ssh/llm-bench-key.pem ubuntu@44.195.85.130`
- **Web:** nginx serves `/home/ubuntu/llm-bench/dashboard/` at port 80; `results/latest.json` is reachable at `/results/latest.json`. `/home/ubuntu` was chmod'd `o+x` to make traversal work for nginx (default 700 blocks www-data).
- **Schedule:** systemd timer `llm-bench-eval.timer` runs the suite on the **1st of every month at 10:00 UTC** (`OnCalendar=*-*-01 10:00:00`). Monthly cadence is deliberate: the drift-tracking story (do hosted models silently degrade after new tier launches?) needs comparable snapshots, not noisy daily ones. Service unit `llm-bench-eval.service` execs `.venv/bin/python -m bench`.
- **Secrets:** `/etc/llm-bench.env` (mode 600, root-owned) holds `ANTHROPIC_API_KEY=…` and `GROQ_API_KEY=…`. systemd unit pulls both via `EnvironmentFile`. Either can be missing — runner skips that provider's models with a log line, rest of suite still runs.

### Run a real eval immediately

```bash
ssh -i ~/.ssh/llm-bench-key.pem ubuntu@44.195.85.130
sudo nano /etc/llm-bench.env       # paste ANTHROPIC_API_KEY=sk-ant-... and/or GROQ_API_KEY=gsk_...
sudo systemctl start llm-bench-eval
journalctl -u llm-bench-eval -f    # watch progress
```

Cost per full run: ~$1–3 for the three Anthropic models. Groq models are on the free tier ($0). Free tier is rate-limited (around 30 req/min) — full Groq sweep takes ~5 min just from rate-limiting.

## Gotchas (carry over from panini deployment)

- Ubuntu MySQL root → use `sudo mysql`, not `mysql -u root` (N/A here since no DB, but heads up if you add one)
- Don't wrap `mysql < dump.sql` (or any stdin-redirected command) in a pipe under `set -e` — pipeline exit masks errors, drops/destructive ops continue thinking things succeeded
- `mysqldump` as app user needs `--no-tablespaces`

## Not done yet (intentional v1 scope)

- 3 prompts per task, not 10. Framework supports any count; expanding is `tasks/*.py` content work.
- No fine-tuned model in the leaderboard. Add a column when there's one to add.
- No CI on the repo. Eval runs are scheduled on EC2, not in GitHub Actions.
- Only Anthropic. Add OpenAI/Google/OpenRouter adapters in `bench/models.py` when keys are available.
