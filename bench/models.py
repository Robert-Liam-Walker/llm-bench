"""Client adapter. One method: complete(model_spec, prompt) -> Completion.

Dispatches to Anthropic or Groq based on the `provider` field in model_spec.
Missing API keys → ProviderUnavailable, caught by the runner so unaffected models
still run.
"""

import os
from dataclasses import dataclass

from anthropic import Anthropic
from groq import Groq


class ProviderUnavailable(Exception):
    """Raised when the API key for a provider isn't set in the env."""


@dataclass
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


class Client:
    def __init__(self):
        self._anthropic = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None
        self._groq = Groq() if os.environ.get("GROQ_API_KEY") else None

    def complete(self, model_spec: dict, prompt: str, max_tokens: int = 2048) -> Completion:
        provider = model_spec["provider"]
        model_id = model_spec["id"]
        if provider == "anthropic":
            return self._complete_anthropic(model_id, prompt, max_tokens)
        if provider == "groq":
            return self._complete_groq(model_id, prompt, max_tokens)
        raise ValueError(f"unknown provider: {provider}")

    def _complete_anthropic(self, model_id: str, prompt: str, max_tokens: int) -> Completion:
        if self._anthropic is None:
            raise ProviderUnavailable("ANTHROPIC_API_KEY not set")
        resp = self._anthropic.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return Completion(text, resp.usage.input_tokens, resp.usage.output_tokens, model_id)

    def _complete_groq(self, model_id: str, prompt: str, max_tokens: int) -> Completion:
        if self._groq is None:
            raise ProviderUnavailable("GROQ_API_KEY not set")
        resp = self._groq.chat.completions.create(
            model=model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return Completion(
            text=resp.choices[0].message.content or "",
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            model=model_id,
        )
