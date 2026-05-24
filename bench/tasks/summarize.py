"""Summarization. Judge grades on coverage + accuracy."""

from .base import Prompt, Task

RUBRIC = (
    "Score 1.0 if the summary captures all main points, introduces no factual errors, and is "
    "appropriately compressed (not too long, not too brief). Score 0.5 if it misses a meaningful "
    "point OR introduces a minor inaccuracy. Score 0.0 if it hallucinates content not in the source "
    "or misses the central thesis."
)

ARTICLE_SHORT = (
    "The European Space Agency announced on March 14, 2026 that the Mars Sample Return mission "
    "will be delayed by at least two years, to a target launch of 2031. The delay is attributed "
    "to budget overruns in the ascent vehicle subsystem and to coordination challenges with NASA, "
    "which is contributing the orbiter. Mission scientists insist the science value remains intact "
    "and that the samples cached by Perseverance will not degrade during the additional wait."
)

ARTICLE_MEDIUM = (
    "In a quiet announcement Friday, the Federal Reserve held its benchmark interest rate steady "
    "at 4.25%–4.50%, marking the third consecutive meeting without a change. Chair Powell, in the "
    "post-meeting press conference, acknowledged that inflation has moderated from its 2024 peak "
    "but remains above the Fed's 2% target, with the latest core PCE reading at 2.7%. He pushed "
    "back on suggestions that rate cuts are imminent, citing strength in the labor market and "
    "uncertainty around new tariffs implemented earlier this year. Bond markets responded with a "
    "slight steepening of the yield curve, and the dollar weakened modestly against the euro. "
    "Analysts polled by Bloomberg now place the probability of a rate cut at the June meeting at "
    "32%, down from 48% a month ago. Equity markets were largely unmoved, with the S&P 500 closing "
    "essentially flat. Powell also addressed concerns about commercial real estate exposure at "
    "regional banks, calling the risk 'manageable but worth monitoring.'"
)

ARTICLE_LONG = (
    "A new study published in Nature Climate Change presents the strongest evidence yet that the "
    "Atlantic Meridional Overturning Circulation (AMOC) has weakened significantly over the past "
    "century and may be approaching a tipping point. Researchers from the Potsdam Institute and "
    "Woods Hole Oceanographic Institution analyzed eleven independent proxy records — including "
    "sea surface temperature reconstructions, deep ocean sediment cores, and ice-core data — and "
    "found a coherent signal of AMOC slowdown beginning around 1950 and accelerating since 1980. "
    "The AMOC is a system of ocean currents that transports warm water from the tropics to the "
    "North Atlantic, releasing heat to the atmosphere and helping moderate European winters. A "
    "shutdown would cause sharp cooling across Northern Europe, dramatic shifts in tropical "
    "monsoon patterns, and accelerated sea level rise along the U.S. East Coast.\n\n"
    "The paper's authors emphasize that their statistical methods cannot pinpoint exactly when a "
    "tipping point might be crossed, but their best estimate places the central window between "
    "2037 and 2064 under continued high emissions. Critically, they argue the system shows early "
    "warning signs — increased variance and slower recovery from perturbations — consistent with "
    "approaching a critical transition. Climate models used in IPCC assessments have generally "
    "shown AMOC weakening but not collapse on this timescale, raising questions about whether "
    "those models underestimate the risk.\n\n"
    "Other oceanographers have pushed back. Dr. Susan Lozier of Georgia Tech notes that direct "
    "AMOC measurements from the RAPID monitoring array, which began in 2004, show year-to-year "
    "variability but no clear long-term trend. She cautions that proxy records can be biased by "
    "factors unrelated to AMOC strength. The authors counter that the RAPID record is too short "
    "to detect the gradual changes their proxies reveal, and that the proxies are independently "
    "calibrated against modern observations.\n\n"
    "Policy implications are significant. If the central estimate is correct, an AMOC collapse "
    "would unfold over decades, but the trigger could be passed within years. Some authors of the "
    "paper have called for emissions reductions explicitly framed around avoiding AMOC tipping, "
    "rather than around a global temperature target alone."
)

PROMPTS = [
    Prompt(
        id="news_short",
        length_bucket="short",
        text=f"Summarize the following news item in two sentences:\n\n{ARTICLE_SHORT}",
        reference={"source": ARTICLE_SHORT},
    ),
    Prompt(
        id="news_medium",
        length_bucket="medium",
        text=f"Summarize the following article in 3-4 sentences:\n\n{ARTICLE_MEDIUM}",
        reference={"source": ARTICLE_MEDIUM},
    ),
    Prompt(
        id="science_long",
        length_bucket="long",
        text=(
            "Summarize the following article in 5-7 sentences. Be sure to convey the central "
            f"claim, the evidence, and the main dissent.\n\n{ARTICLE_LONG}"
        ),
        reference={"source": ARTICLE_LONG},
    ),
]

TASK = Task(category="summarize", scorer_kind="judge", rubric=RUBRIC, prompts=PROMPTS)
