"""Reproducible benchmark of Claude tiers across 12 task categories."""

MODELS = [
    {"id": "claude-opus-4-7", "label": "Opus 4.7", "input_per_mtok": 15.0, "output_per_mtok": 75.0},
    {"id": "claude-sonnet-4-6", "label": "Sonnet 4.6", "input_per_mtok": 3.0, "output_per_mtok": 15.0},
    {"id": "claude-haiku-4-5-20251001", "label": "Haiku 4.5", "input_per_mtok": 1.0, "output_per_mtok": 5.0},
]
