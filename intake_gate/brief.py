"""Render a decision as a requirements brief.

The brief is what operations, creative, and engineering read at kickoff. It
is plain Markdown so it pastes into any tracker, wiki, or ticket.
"""

from __future__ import annotations

from typing import Mapping

from .gate import Decision
from .schema import ALL_FIELDS, STAGES

Intake = Mapping[str, object]


def _line(label: str, value: object) -> str:
    return f"- **{label}:** {value}"


def render(intake: Intake, decision: Decision) -> str:
    out: list[str] = []
    name = intake.get("opportunity_name") or "Untitled opportunity"
    out.append(f"# Requirements brief: {name}")
    out.append("")
    out.append(f"**Verdict:** {decision.verdict}")
    out.append("")

    if decision.signoff_blockers or decision.readiness_blockers or decision.missing_required:
        out.append("## Blocking")
        for flag in decision.signoff_blockers:
            out.append(_line(flag.title, flag.triggers))
        for key in decision.readiness_blockers:
            out.append(_line("Readiness", f"{ALL_FIELDS[key].label} is not confirmed"))
        for key in decision.missing_required:
            out.append(_line("Required field", f"{ALL_FIELDS[key].label} is missing"))
        out.append("")

    advisory = [f for f in decision.flags if not f.blocks_signoff]
    if advisory:
        out.append("## Flags")
        for flag in advisory:
            out.append(_line(flag.title, flag.triggers))
        out.append("")

    out.append("## Effort")
    out.append(_line("Band", f"{decision.effort.band} ({decision.effort.points} points)"))
    for driver in decision.effort.drivers:
        out.append(f"  - {driver}")
    out.append("- Effort only. Pricing is a sales decision and lives elsewhere.")
    out.append("")

    out.append("## Captured requirements")
    for stage in STAGES:
        answered = [(f, intake.get(f.key)) for f in stage.fields if intake.get(f.key) is not None]
        if not answered:
            continue
        out.append(f"### {stage.number} {stage.name}")
        for f, value in answered:
            out.append(_line(f.label, value))
        out.append("")

    return "\n".join(out).rstrip() + "\n"
