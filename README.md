# llm-bench

Reproducible benchmark of Claude model tiers across 12 task categories — code generation, debugging, SQL, regex, math, summarization, and more. Half the tasks are deterministically scored (unit tests, regex match, exact comparison); the rest use a disclosed LLM-as-judge rubric.

**Live dashboard:** _coming soon_

## What it answers

When does Claude Opus pay off versus Sonnet or Haiku (10× cheaper)? The dashboard shows per-task accuracy and per-task cost, so you can see where the cheap model is good enough and where it isn't.

## Methodology

- **Models:** Claude Opus 4.7, Sonnet 4.6, Haiku 4.5 (one provider, three tiers).
- **Tasks:** 12 categories × 3 prompts each, scoring 0.0–1.0 per response.
- **Deterministic scoring** where possible (6 of 12 categories): unit tests, SQL execution, regex application, exact match.
- **LLM-as-judge** for subjective categories (6 of 12): Opus grades against a published rubric. Yes, that's circular for Opus's own rows — flagged in the UI.

Full per-task rubrics in [`CLAUDE.md`](./CLAUDE.md).

## Run it yourself

```bash
git clone https://github.com/Robert-Liam-Walker/llm-bench
cd llm-bench
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python -m bench
```

Results land in `results/<timestamp>.json`. Open `dashboard/index.html` to see them.

## Why this exists

Public LLM evals exist (MMLU, HumanEval, GPQA), but most lump all the action into one number per model and don't show *where* a cheaper model is fine. This project is an attempt to show that surface, on tasks that look more like what people actually use these models for at work.
