"""Run a deal through the gate and return one decision.

The decision carries everything downstream needs: which stages are complete,
which required fields are missing, every flag the deal tripped, whether
sign-off is blocked, whether operations is cleared to kick off, and the
effort estimate. It never carries a price.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .effort import Effort, estimate
from .rules import Flag, evaluate_flags, readiness_blockers
from .schema import ALL_FIELDS, STAGES

Intake = Mapping[str, object]


@dataclass(frozen=True)
class StageStatus:
    number: str
    key: str
    name: str
    answered: int
    total: int
    missing_required: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.answered == self.total


@dataclass(frozen=True)
class Decision:
    stages: tuple[StageStatus, ...]
    unknown_fields: tuple[str, ...]
    invalid_fields: tuple[str, ...]
    flags: tuple[Flag, ...]
    readiness_blockers: tuple[str, ...]
    effort: Effort

    @property
    def stages_ready(self) -> int:
        return sum(1 for s in self.stages if s.complete)

    @property
    def missing_required(self) -> tuple[str, ...]:
        return tuple(k for s in self.stages for k in s.missing_required)

    @property
    def signoff_blockers(self) -> tuple[Flag, ...]:
        return tuple(f for f in self.flags if f.blocks_signoff)

    @property
    def cleared(self) -> bool:
        """Operations proceeds only when everything below holds at once."""
        return (
            not self.unknown_fields
            and not self.invalid_fields
            and not self.missing_required
            and not self.readiness_blockers
            and not self.signoff_blockers
        )

    @property
    def verdict(self) -> str:
        if self.cleared:
            return "Cleared to kickoff"
        open_count = len(self.stages) - self.stages_ready
        return f"{self.stages_ready} of {len(self.stages)} stages ready, {open_count} open"

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "cleared": self.cleared,
            "stages_ready": self.stages_ready,
            "stages": [
                {**asdict(s), "complete": s.complete} for s in self.stages
            ],
            "unknown_fields": list(self.unknown_fields),
            "invalid_fields": list(self.invalid_fields),
            "missing_required": list(self.missing_required),
            "flags": [asdict(f) for f in self.flags],
            "signoff_blockers": [f.code for f in self.signoff_blockers],
            "readiness_blockers": list(self.readiness_blockers),
            "effort": asdict(self.effort),
        }


def evaluate(intake: Intake) -> Decision:
    unknown = tuple(sorted(k for k in intake if k not in ALL_FIELDS))
    invalid: list[str] = []
    statuses: list[StageStatus] = []

    for stage in STAGES:
        answered = 0
        missing_required: list[str] = []
        for f in stage.fields:
            value = intake.get(f.key)
            if value is None:
                if f.required:
                    missing_required.append(f.key)
                continue
            if f.accepts(value):
                answered += 1
            else:
                invalid.append(f.key)
                if f.required:
                    missing_required.append(f.key)
        statuses.append(StageStatus(
            stage.number, stage.key, stage.name,
            answered, len(stage.fields), tuple(missing_required),
        ))

    return Decision(
        stages=tuple(statuses),
        unknown_fields=unknown,
        invalid_fields=tuple(invalid),
        flags=tuple(evaluate_flags(intake)),
        readiness_blockers=tuple(readiness_blockers(intake)),
        effort=estimate(intake),
    )
