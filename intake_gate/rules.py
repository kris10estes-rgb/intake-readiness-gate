"""Smart flags and gate rules.

A flag is a fact about the deal the intake form surfaces on its own, so the
person filling it in does not have to know the rule. Each flag names what it
triggers and whether it blocks sign-off. Rules only ever add work; nothing
here removes a review someone else added.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

Intake = Mapping[str, object]


@dataclass(frozen=True)
class Flag:
    code: str
    title: str
    triggers: str
    blocks_signoff: bool = False
    starts_clock: bool = False


@dataclass(frozen=True)
class Rule:
    flag: Flag
    when: Callable[[Intake], bool]


def _is(intake: Intake, key: str, *values: str) -> bool:
    return intake.get(key) in values


RULES: tuple[Rule, ...] = (
    Rule(
        Flag("ENG-REVIEW", "Engineering review",
             "More than two outputs triggers an engineering review before anything is committed.",
             blocks_signoff=True),
        lambda i: _is(i, "multi_output", "More than 2"),
    ),
    Rule(
        Flag("KICKOFF-NEW-SOLUTION", "Kickoff required",
             "A new vendor, solution, or unfamiliar hardware flags a kickoff the moment it appears."),
        lambda i: _is(i, "new_vendor", "Yes") or _is(i, "new_hardware", "Yes"),
    ),
    Rule(
        Flag("CREATIVE-LANE", "Creative lane engaged",
             "Content originated from concept engages creative, estimated separately from the ops effort."),
        lambda i: _is(i, "origination", "Originated from concept") or _is(i, "creative_engaged", "Yes"),
    ),
    Rule(
        Flag("MIGRATION-CLOCK", "Conversion clock started",
             "Any migration flags a kickoff and starts a conversion clock against the deadline.",
             starts_clock=True),
        lambda i: _is(i, "migration_type", "Platform to platform", "Other"),
    ),
    Rule(
        Flag("CAPACITY-REVIEW", "Capacity review",
             "A custom SLA blocks sign-off until capacity is reviewed.",
             blocks_signoff=True),
        lambda i: _is(i, "sla", "Custom"),
    ),
    Rule(
        Flag("AFTER-HOURS", "After-hours coverage",
             "After-hours coverage is a staffing commitment and is priced into the capacity review."),
        lambda i: _is(i, "after_hours", "Yes"),
    ),
    Rule(
        Flag("FIELD-STAGING", "Staging before install",
             "Imaging or kitting must be complete before a field tech is scheduled."),
        lambda i: _is(i, "imaging", "Yes") or _is(i, "staging", "Yes"),
    ),
    Rule(
        Flag("LOCALIZATION", "Localization multiplier",
             "Bilingual or multi-language content multiplies every deliverable."),
        lambda i: _is(i, "localization", "Bilingual", "Three or more"),
    ),
)


def evaluate_flags(intake: Intake) -> list[Flag]:
    """Return every flag whose rule fires, in rule order."""
    return [rule.flag for rule in RULES if rule.when(intake)]


READINESS_KEYS: tuple[str, ...] = (
    "opportunity_logged",
    "sow_exists",
    "owner_assigned",
    "kickoff_scheduled",
)


def readiness_blockers(intake: Intake) -> list[str]:
    """Return the readiness items still missing. Empty means the gate is clear."""
    return [key for key in READINESS_KEYS if intake.get(key) != "Yes"]
