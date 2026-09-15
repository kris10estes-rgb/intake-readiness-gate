"""Level-of-effort estimate.

Effort only, never dollars. Cost sits with operations, price sits with sales,
and the two never share a field.

The output is a band and a point score. The weights below are illustrative
placeholders so the model is legible and testable; a real deployment
calibrates them against its own delivery history.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

Intake = Mapping[str, object]


@dataclass(frozen=True)
class Effort:
    points: int
    band: str
    drivers: tuple[str, ...]


ENDPOINT_BANDS: tuple[tuple[int, int, str], ...] = (
    # (upper bound inclusive, points, label)
    (10, 1, "up to 10 endpoints"),
    (100, 3, "11 to 100 endpoints"),
    (1000, 6, "101 to 1,000 endpoints"),
    (10_000, 10, "1,001 to 10,000 endpoints"),
)
ENDPOINT_MAX_POINTS = 15

SCOPE_POINTS = {"Single site": 1, "Multi-site": 3, "Network-wide": 5}
ORIGINATION_POINTS = {"Client supplies": 1, "Agency supplies": 2, "Originated from concept": 5}
DELIVERABLE_POINTS = {
    "Menu boards": 2, "Daypart": 3, "LTO / promo": 2,
    "Pricing": 3, "POS-driven": 5, "Ad trafficking": 3,
}
LOCALIZATION_MULTIPLIER = {"Single": 1.0, "Bilingual": 1.5, "Three or more": 2.0}
MIGRATION_POINTS = {"None": 0, "Platform to platform": 6, "Other": 4}

BANDS: tuple[tuple[int, str], ...] = (
    (8, "Light"),
    (16, "Standard"),
    (28, "Heavy"),
)
TOP_BAND = "Program"


def endpoint_points(count: object) -> tuple[int, str]:
    if not isinstance(count, (int, float)) or isinstance(count, bool) or count < 0:
        return 0, "endpoint count not provided"
    for upper, points, label in ENDPOINT_BANDS:
        if count <= upper:
            return points, label
    return ENDPOINT_MAX_POINTS, "more than 10,000 endpoints"


def band_for(points: int) -> str:
    for upper, name in BANDS:
        if points <= upper:
            return name
    return TOP_BAND


def estimate(intake: Intake) -> Effort:
    drivers: list[str] = []
    base = 0

    ep, ep_label = endpoint_points(intake.get("endpoint_count"))
    base += ep
    drivers.append(f"{ep_label}: +{ep}")

    scope = intake.get("deployment_scope")
    if scope in SCOPE_POINTS:
        base += SCOPE_POINTS[scope]
        drivers.append(f"{scope}: +{SCOPE_POINTS[scope]}")

    origin = intake.get("origination")
    if origin in ORIGINATION_POINTS:
        base += ORIGINATION_POINTS[origin]
        drivers.append(f"{origin}: +{ORIGINATION_POINTS[origin]}")

    deliverable = intake.get("ops_deliverable")
    if deliverable in DELIVERABLE_POINTS:
        base += DELIVERABLE_POINTS[deliverable]
        drivers.append(f"{deliverable}: +{DELIVERABLE_POINTS[deliverable]}")

    migration = intake.get("migration_type")
    if migration in MIGRATION_POINTS and MIGRATION_POINTS[migration]:
        base += MIGRATION_POINTS[migration]
        drivers.append(f"Migration ({migration}): +{MIGRATION_POINTS[migration]}")

    multiplier = LOCALIZATION_MULTIPLIER.get(intake.get("localization"), 1.0)  # type: ignore[arg-type]
    if multiplier != 1.0:
        drivers.append(f"Localization x{multiplier}")

    points = int(round(base * multiplier))
    return Effort(points=points, band=band_for(points), drivers=tuple(drivers))
