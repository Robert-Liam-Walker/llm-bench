"""Reproducible benchmark of LLMs across 12 task categories.

Mix of Anthropic (paid) and Groq-hosted open-source models (free tier).
"""

MODELS = [
    # Anthropic — paid; pricing per million tokens
    {"id": "claude-opus-4-7",          "provider": "anthropic", "label": "Opus 4.7",     "input_per_mtok": 15.0, "output_per_mtok": 75.0},
    {"id": "claude-sonnet-4-6",        "provider": "anthropic", "label": "Sonnet 4.6",   "input_per_mtok": 3.0,  "output_per_mtok": 15.0},
    {"id": "claude-haiku-4-5-20251001","provider": "anthropic", "label": "Haiku 4.5",    "input_per_mtok": 1.0,  "output_per_mtok": 5.0},

    # Groq — open weights on free tier; cost treated as $0 for the leaderboard
    {"id": "llama-3.3-70b-versatile",        "provider": "groq", "label": "Llama 3.3 70B",   "input_per_mtok": 0.0, "output_per_mtok": 0.0},
    {"id": "deepseek-r1-distill-llama-70b",  "provider": "groq", "label": "DeepSeek R1 (70B)","input_per_mtok": 0.0, "output_per_mtok": 0.0},
    {"id": "llama-3.1-8b-instant",           "provider": "groq", "label": "Llama 3.1 8B",    "input_per_mtok": 0.0, "output_per_mtok": 0.0},
]
