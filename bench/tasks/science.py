"""Scientific reasoning. Multi-step factual questions. Judge grades."""

from .base import Prompt, Task

RUBRIC = (
    "Score 1.0 if every factual claim is correct AND the reasoning chain is valid. "
    "Score 0.5 if the conclusion is right but the reasoning has a meaningful error. "
    "Score 0.0 if the conclusion is wrong or the reasoning is fundamentally broken."
)

PROMPTS = [
    Prompt(
        id="seasons",
        length_bucket="short",
        text=(
            "Why is it summer in the Southern Hemisphere when it is winter in the Northern Hemisphere? "
            "Answer in 2-3 sentences. The Earth's distance from the Sun varies during the year — "
            "explicitly address whether that is the main cause."
        ),
    ),
    Prompt(
        id="enzyme_temperature",
        length_bucket="medium",
        text=(
            "Most enzymes lose activity above a certain temperature. Explain what happens to the "
            "enzyme at the molecular level, why this is usually irreversible, and how this differs "
            "from the temperature dependence of a typical inorganic catalyst. Keep it under 200 words."
        ),
    ),
    Prompt(
        id="entropy_paradox",
        length_bucket="long",
        text=(
            "A common challenge to evolution: 'Evolution violates the second law of thermodynamics, "
            "because the second law says entropy must increase, but evolution produces more ordered "
            "organisms over time.' Explain precisely why this argument is wrong. Be specific about "
            "what the second law actually says, what it does and doesn't apply to, and the role of "
            "the Earth not being an isolated system. 200-300 words."
        ),
    ),
]

TASK = Task(category="science", scorer_kind="judge", rubric=RUBRIC, prompts=PROMPTS)
