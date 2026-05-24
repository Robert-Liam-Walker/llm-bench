# llm-bench — Agent Notes

Empirical benchmark of 6 LLMs across 12 task categories, re-run on the 1st of every month so model drift is visible. Public dashboard at the EC2 URL. The product is the **measurement infrastructure**, not a new model.

## What this is (and isn't)

- **Is:** a reproducible eval harness + a static dashboard showing how 6 LLMs (3 Claude tiers + 3 Groq-hosted open-weight models) perform on each task. Runs monthly so drift over time becomes visible — does a hosted model silently get worse after the provider releases a newer tier? Drift panel + per-task trend charts make any persistent dip immediately obvious.
- **Isn't:** a chatbot, a wrapper, or "AI that does X." The LLM is the *subject* of measurement, not the engine.

The point: when does Opus pay off vs Haiku (10× cheaper)? When does a free open-weight model close the gap? Has any model degraded since last month? Nobody publishes good per-task answers; this does.

## Layout

```
bench/
  __init__.py          # MODELS list — provider, id, label, pricing per million tokens
  models.py            # Client adapter; dispatches to Anthropic or Groq based on `provider`
                       #   field; raises ProviderUnavailable if the key isn't set
  judge.py             # LLM-as-judge (Opus). Constructs its own model_spec dict.
  runner.py            # Orchestrator: (task × prompt × model) → results JSON + index update
  index.py             # update_index(): append-only pre-aggregated history
                       #   (per-run × per-model × per-task means → results/index.json)
  cli.py               # `python -m bench` entry
  tasks/
    base.py            # Task + Prompt dataclasses
    _util.py           # Shared helpers: code/JSON/number extraction, safe-exec
    <category>.py      # 12 modules: code_gen, code_debug, code_refactor, sql, regex,
                       #   json_extract, math, science, summarize, email, logic, edge_cases
results/
  <iso-ts>.json        # One file per run, named like 20260601T100000Z.json. Never overwritten.
  latest.json          # Symlink → most recent run file. What the dashboard grid loads first.
  index.json           # Append-only. Updated automatically by bench.index.update_index() after
                       #   each run. The dashboard's drift panel + trend charts read this.
dashboard/
  index.html           # Static. Fetches latest.json + index.json + per-run files on demand.
  main.js              # Renders grid + run picker + drift panel + 12 SVG trend charts. No deps.
  style.css            # Dark theme. CSS vars at the top.
scripts/
  seed_placeholder.py  # Generates 4 monthly placeholder runs so dashboard renders pre-launch.
                       #   Skips files already marked placeholder:true, so it never wipes real
                       #   run data. Safe to re-run.
```

## Running locally

```bash
export ANTHROPIC_API_KEY=sk-ant-...    # required for Claude rows + the judge
export GROQ_API_KEY=gsk_...            # required for Llama / DeepSeek rows; free tier
pip install -r requirements.txt
python -m bench                        # all 12 tasks × all 6 models
python -m bench --task code_gen        # one task category
python -m bench --model claude-haiku-4-5-20251001   # one model
python -m bench --dry-run              # no API calls; print plan
```

If a key is missing, the runner logs a skip for that provider and continues with whatever it can call. Judge-scored tasks need `ANTHROPIC_API_KEY` even when scoring Groq models — a missing judge gives `score=0` with a `judge unavailable` note in the drill-in.

Then open `dashboard/index.html` in a browser (you'll need to serve it via a local web server because of `fetch`, e.g. `python -m http.server` from the project root).

## Scoring rubric (per task)

| Category | Scorer | Why |
|---|---|---|
| code_gen | run generated code, execute unit tests | objective, ungameable |
| code_debug | LLM-judge (bug identified + fix works) | semi-objective |
| code_refactor | LLM-judge (behavior preserved, complexity down) | subjective |
| sql | execute query against SQLite fixture, compare result rows | objective |
| regex | apply pattern to held-out match/non-match examples | objective |
| json_extract | jsonschema validate + key field accuracy | objective |
| math | extract final number, exact match (1‰ tolerance) | objective |
| science | LLM-judge (each claim correct, reasoning sound) | partial |
| summarize | LLM-judge (coverage + accuracy, no hallucinations) | subjective |
| email | LLM-judge (tone + completeness) | subjective |
| logic | exact match / regex pattern on stated answer | objective |
| edge_cases | LLM-judge (appropriate hedge / refusal / catches trick) | rubric |

Half are deterministic. That's deliberate — keeps the leaderboard credible. Judge is Opus on a 0–1 scale; rubrics published in `bench/tasks/*.py` and surfaced in the dashboard's methodology section.

## Production

- **URL:** http://44.195.85.130/
- **EC2:** `i-007bf70075b46a095`, t3.micro Ubuntu 22.04, us-east-1, account `056195341948`. Name tag `llm-bench`, SG `llm-bench-sg` (22 + 80), key pair `llm-bench-key`.
- **SSH:** `ssh -i ~/.ssh/llm-bench-key.pem ubuntu@44.195.85.130`
- **Web:** nginx serves `/home/ubuntu/llm-bench/dashboard/` at port 80. `results/` exposed at `/results/`. `/home/ubuntu` was chmod'd `o+x` to make traversal work for nginx (default 700 blocks www-data).
- **Schedule:** systemd timer `llm-bench-eval.timer` runs the suite on the **1st of every month at 10:00 UTC** (`OnCalendar=*-*-01 10:00:00`). Monthly cadence is deliberate — comparable snapshots, not noisy daily ones. Service unit `llm-bench-eval.service` execs `.venv/bin/python -m bench`.
- **Secrets:** `/etc/llm-bench.env` (mode 600, root-owned) holds `ANTHROPIC_API_KEY=…` and `GROQ_API_KEY=…`. systemd unit pulls both via `EnvironmentFile`. Either can be missing — runner skips that provider's models with a log line, rest of suite still runs.

### Run an eval right now (don't wait for the 1st)

```bash
ssh -i ~/.ssh/llm-bench-key.pem ubuntu@44.195.85.130
sudo nano /etc/llm-bench.env           # paste keys
sudo systemctl start llm-bench-eval
journalctl -u llm-bench-eval -f        # watch progress
```

Cost per full run: ~$1–3 for the three Anthropic models. Groq models are free tier ($0). Groq free tier is rate-limited (~30 req/min), so a full Groq sweep takes ~5 min just from throttling.

## Adding a new model

1. Append to `MODELS` in `bench/__init__.py` with `provider`, `id`, `label`, `input_per_mtok`, `output_per_mtok`.
2. If new provider: add a branch in `bench/models.py:Client.complete()` and a new SDK to `requirements.txt`. Use the existing `ProviderUnavailable` pattern when the env key is missing.
3. Add a color for the model in `dashboard/main.js:MODEL_COLORS` (otherwise it renders gray).
4. Optionally add it to `TIER_BASELINE` in `scripts/seed_placeholder.py` so historical placeholder data covers it.

## Adding a new task

1. Create `bench/tasks/<category>.py` with `PROMPTS = [Prompt(...)]` and either a deterministic `score(prompt, response) -> float` function or just leave `score_fn=None` and provide a `rubric` for the judge.
2. Register in `bench/tasks/__init__.py`: add to the imports tuple and `ALL_TASKS` list.
3. Add a methodology row to `dashboard/index.html`'s methodology `<ul>`.

## Gotchas

### From this project

- **Never `git add -A` without scanning for secret-shaped files.** Once during dev, an `api-key.txt` containing the Groq key was created in the repo root and got swept into a commit. GitHub's secret scanning blocked the push; otherwise it would have leaked. `.gitignore` now lists `api-key.txt` and `*.key`. Better: keep keys in `~/.ssh/` or a password manager, never in the repo dir.
- **`seed_placeholder.py` will not wipe real run data** because it only deletes files with `placeholder: true`. Safe to re-run on EC2 even after real runs accumulate. But: it *will* rewrite `latest.json` to point at the most recent placeholder, which is wrong after a real run lands. After running real evals, don't re-seed.
- **Trend chart caveat:** with only 1 real data point, every line is a single dot. Drift becomes legible at 3+ data points, and statistically meaningful at 6+. Be patient or front-load by triggering manual runs.
- **The judge is Opus** — on the six judge-scored tasks, Opus is grading itself. Surfaced in the dashboard methodology section. Don't try to "fix" this by switching judge to Sonnet; the rationale for using the strongest grader is stronger than the rationale for avoiding self-judging when it's disclosed.

### Carried over from panini deployment

- Ubuntu's `mysql -u root` uses auth_socket → use `sudo mysql` (N/A here since no DB, but heads up if you add one).
- Don't wrap any stdin-redirected command (`cmd < file.sql`) in a pipe under `set -e` — pipeline exit code masks `cmd`'s failure, destructive next steps run thinking it succeeded.
- `mysqldump` as an app user (no global PROCESS privilege) needs `--no-tablespaces`.

## Not done yet (intentional v1 scope)

- **3 prompts per task, not 10.** Framework supports any count — expanding is `tasks/*.py` content work, not engineering.
- **No fine-tuned column.** Add one when there's something fine-tuned to add (LoRA on Llama 8B for one of the deterministic tasks would be a natural follow-on).
- **No OpenAI/Google adapters.** Same pattern as Groq — add a branch in `Client.complete()` and an SDK. User explicitly skipped these in v1.
- **No CI.** Eval runs are scheduled on EC2, not in GitHub Actions. Don't add CI for evals (would 6× the API spend); CI for unit tests on the framework itself would be reasonable.
- **No statistical significance display.** Trend chart shows raw scores, not confidence intervals. With 3 prompts/cell, CIs are wide; meaningful intervals need 10+ prompts.
