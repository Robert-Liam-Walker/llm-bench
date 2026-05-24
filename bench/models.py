"""Thin Anthropic client adapter. One concern: turn a prompt into a response + usage."""

from dataclasses import dataclass

from anthropic import Anthropic


@dataclass
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


class Client:
    def __init__(self, api_key: str | None = None):
        self._client = Anthropic(api_key=api_key)

    def complete(self, model: str, prompt: str, max_tokens: int = 2048) -> Completion:
        resp = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return Completion(
            text=text,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            model=model,
        )
