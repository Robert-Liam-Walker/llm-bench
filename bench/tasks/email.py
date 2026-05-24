"""Workplace writing. Judge grades on tone, clarity, completeness."""

from .base import Prompt, Task

RUBRIC = (
    "Score 1.0 if the email: (a) hits a professional tone appropriate to the audience, "
    "(b) addresses every point the scenario asks for, (c) is concise without omitting required info. "
    "Score 0.5 if it misses one element or has a tonal misstep. Score 0.0 if it's wildly off "
    "(too long, missing key info, unprofessional)."
)

PROMPTS = [
    Prompt(
        id="schedule_conflict",
        length_bucket="short",
        text=(
            "Write a short email to your manager (Pat) declining a recurring 9am Friday standup "
            "because of a class you have at that time. Suggest moving it to 10am or 1pm Friday. "
            "Keep it under 80 words. Sign off as 'Liam'."
        ),
    ),
    Prompt(
        id="bug_report_followup",
        length_bucket="medium",
        text=(
            "Write an email to a customer (Maria Chen) who reported a payment-processing bug 5 days "
            "ago. The bug is fixed and deployed today. Apologize for the delay, explain in plain "
            "language what the bug was (a race condition during checkout that caused some orders "
            "to be charged twice), tell her that her account has been credited for the duplicate "
            "charge, and offer to hop on a call if she has questions. Keep it under 200 words. "
            "Sign off as 'Liam Walker, Engineering Support'."
        ),
    ),
    Prompt(
        id="cross_team_proposal",
        length_bucket="long",
        text=(
            "Write an email to the heads of three teams (data platform, security, product) "
            "proposing a 4-week initiative to migrate user PII from your service's database into a "
            "centralized vault. The motivation: (a) reduces compliance scope, (b) unblocks a planned "
            "EU expansion, (c) prevents the recent incident pattern (3 incidents in the last quarter). "
            "You need: 2 engineers from data platform, 1 security review, 1 product decision on "
            "whether to expose the change to users. Request a 30-minute scoping meeting next week. "
            "Sign off as 'Liam Walker, Lead Engineer, Payments'."
        ),
    ),
]

TASK = Task(category="email", scorer_kind="judge", rubric=RUBRIC, prompts=PROMPTS)
